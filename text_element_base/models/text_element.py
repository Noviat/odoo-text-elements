# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError

FIELD_TYPES = [(key, key) for key in sorted(fields.Field.by_type)]


class TextElement(models.Model):
    _name = "text.element"
    _description = "Text elements"
    _order = "position desc, lang, sequence, id"
    _check_company_auto = True

    name = fields.Char(required=True)
    content = fields.Html()
    position = fields.Selection(
        [
            ("before", "Before"),
            ("before_line", "Before Lines"),
            ("after_line", "After Lines"),
            ("after", "After"),
        ],
        default="before",
    )
    page_break_before = fields.Boolean(help="Add a page break before element")
    page_break_after = fields.Boolean(help="Add a page break after element")
    sequence = fields.Integer(help="Order of displayed text elements in the report.")
    default = fields.Boolean()
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        required=False,
    )
    lang = fields.Selection(
        selection=lambda self: self._selection_lang_get(),
        string="Language",
        default=lambda self: self.env.lang,
        required=True,
    )
    active = fields.Boolean(default=True)
    res_model = fields.Selection(
        string="Model",
        selection=lambda self: self._selection_model(),
        default="all",
        required=True,
    )
    # expression builder
    model_object_field = fields.Many2one(
        "ir.model.fields",
        string="Field",
        store=False,
        help="Select target field from the related document model.\n"
        "If it is a relationship field you will be able to select "
        "a target field at the destination of the relationship.",
    )
    sub_object = fields.Many2one(
        "ir.model",
        "Sub-model",
        readonly=True,
        store=False,
        help="When a relationship field is selected as first field, "
        "this field shows the document model the relationship goes to.",
        compute="_compute_dynamic_placeholder",
    )
    sub_model_object_field = fields.Many2one(
        "ir.model.fields",
        "Sub-field",
        store=False,
        readonly=False,
        help="When a relationship field is selected as first field, "
        "this field lets you select the target field within the "
        "destination document model (sub-model).",
        compute="_compute_dynamic_placeholder",
    )
    copyvalue = fields.Char(
        "Placeholder Expression",
        store=False,
        readonly=False,
        help="Final placeholder expression, "
        "to be copy-pasted in the desired template field.",
        compute="_compute_dynamic_placeholder",
    )
    field_ttype = fields.Selection(
        selection=FIELD_TYPES, string="Field Type", compute="_compute_field_ttype"
    )
    datetime_options = fields.Selection(
        selection=[
            ("date", "Only show the date"),
            ("time", "Only show the time"),
            ("full_date", "Only show the date and in full text"),
        ],
        store=False,
        readonly=False,
    )
    date_options = fields.Selection(
        selection=[("full", "Only show the date and in full text")],
        store=False,
        readonly=False,
    )

    @api.model
    def _selection_lang_get(self):
        return self.env["res.lang"].get_installed()

    @api.model
    def _selection_model(self):
        return [("all", "All")]

    @api.depends(
        "model_object_field",
        "sub_model_object_field",
        "datetime_options",
        "date_options",
    )
    def _compute_dynamic_placeholder(self):
        for record in self:
            if record.model_object_field:
                option = None
                if record.datetime_options:
                    option = record.datetime_options
                elif record.date_options:
                    option = record.date_options
                if record.model_object_field.ttype in [
                    "many2one",
                    "one2many",
                    "many2many",
                ]:
                    model = self.env["ir.model"]._get(
                        record.model_object_field.relation
                    )
                    if model:
                        record.sub_object = model.id
                        sub_field_name = record.sub_model_object_field.name
                        record.copyvalue = self._build_expression(
                            record.model_object_field.name,
                            sub_field_name,
                            option=option,
                        )
                else:
                    record.sub_object = False
                    record.sub_model_object_field = False
                    record.copyvalue = self._build_expression(
                        record.model_object_field.name, False, option=option
                    )
            else:
                record.sub_object = False
                record.copyvalue = False
                record.sub_model_object_field = False

    @api.depends("model_object_field", "sub_model_object_field")
    def _compute_field_ttype(self):
        for record in self:
            if record.sub_model_object_field:
                record.field_ttype = record.sub_model_object_field.ttype
            elif record.model_object_field:
                record.field_ttype = record.model_object_field.ttype
            else:
                record.field_ttype = False

    def action_remove(self):
        current_record = False
        if self.env.context.get("active_model", False) and self.env.context.get(
            "active_id", 0
        ):
            current_record = self.env[self.env.context.get("active_model")].browse(
                self.env.context.get("active_id")
            )
        else:
            params = self.env.context.get("params")
            if params and "model" in params and "id" in params:
                current_record = self.env[params["model"]].browse(params["id"])
        if current_record:
            current_record.write({"text_element_ids": [(3, self.id)]})
        return

    @api.model
    def _get_formated_value(self, value, lang, field_type="str", options=""):
        if not value:
            return ""
        if field_type == "datetime":
            if options == "date":
                options = {"date_only": True}
            elif options == "time":
                options = {"time_only": True}
            elif options == "full_date":
                options = {"format": "d MMMM yyyy"}
            else:
                options = {}
            return (
                self.env["ir.qweb.field.datetime"]
                .with_context(lang=lang)
                .value_to_html(value, options)
            )
        elif field_type == "date":
            if options == "full":
                options = {"format": "d MMMM yyyy"}
            else:
                options = {}
            return (
                self.env["ir.qweb.field.date"]
                .with_context(lang=lang)
                .value_to_html(value, options)
            )
        elif field_type == "binary":
            return self.env["ir.qweb.field.image"].value_to_html(value, {})
        else:
            return value

    def _get_content_interpreted(self, record):
        self.ensure_one()
        if self.content:
            lang = record.report_lang
            orm_fields = record.fields_get()
            fields_found = re.findall(r"\[\[([^\]\]]*)\]\]*", self.content)
            content_interpreted = self.content
            for field_found in fields_found:
                value = self._get_value_for_field(record, field_found, orm_fields, lang)
                if value:
                    content_interpreted = content_interpreted.replace(
                        "[[" + field_found + "]]", value
                    )
                else:
                    content_interpreted = content_interpreted.replace(
                        "[[" + field_found + "]]", ""
                    )
            return content_interpreted
        return ""

    def _get_value_for_field(self, record, field_found, orm_fields, lang):
        value = ""
        sub_fields = field_found.split(".")
        if len(sub_fields) > 2:
            raise NotImplementedError(
                _("Fields with several subfields is not supported (several dots)")
            )
        elif len(sub_fields) == 2:
            field = sub_fields[0]
            subfield = sub_fields[1]
            if field in orm_fields and orm_fields[field].get("type", "") != "many2one":
                raise UserError(
                    _("The field %s must a many2one in order to use subfields") % field
                )
            subrecord = getattr(record, field)
            if subrecord:
                orm_sub_fields = subrecord.fields_get()
                subfield_options = subfield.split("::")
                if len(subfield_options) > 1:
                    subfield = subfield_options[0]
                    subfield_option = subfield_options[1]
                else:
                    subfield = subfield_options[0]
                    subfield_option = ""
                value = self._get_formated_value(
                    getattr(subrecord, subfield),
                    lang,
                    orm_sub_fields[subfield].get("type", ""),
                    subfield_option,
                )
        else:
            field_options = field_found.split("::")
            if len(field_options) > 1:
                field = field_options[0]
                option = field_options[1]
            else:
                field = field_options[0]
                option = ""
            value = self._get_formated_value(
                getattr(record, field),
                lang,
                orm_fields[field].get("type", ""),
                option,
            )
        return value

    @api.model
    def _build_expression(self, field_name, sub_field_name, option=None):
        """Returns a placeholder expression for use in a template field,
        based on the values provided in the placeholder assistant.

        :param field_name: main field name
        :param sub_field_name: sub field name (M2O)
        :return: final placeholder expression"""
        expression = ""
        if field_name:
            expression = "[[" + field_name
            if sub_field_name:
                expression += "." + sub_field_name
            if option:
                expression += "::" + option
            expression += "]]"
        return expression
