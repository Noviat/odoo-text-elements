# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class TextElement(models.Model):
    _name = "text.element"
    _description = "Text elements"
    _order = "position desc, lang, sequence, id"
    _check_company_auto = True

    name = fields.Char(required=True)
    content = fields.Html()
    position = fields.Selection(
        [("before", "Before"), ("after", "After")], default="before"
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

    @api.model
    def _selection_lang_get(self):
        return self.env["res.lang"].get_installed()

    @api.model
    def _selection_model(self):
        return [("all", "All")]

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
        if field_type == "datetime":
            if options == "date":
                options = {"date_only": True}
            elif options == "time":
                options = {"time_only": True}
            else:
                options = {}
            return (
                self.env["ir.qweb.field.datetime"]
                .with_context(lang=lang)
                .value_to_html(value, options)
            )
        elif field_type == "date":
            return (
                self.env["ir.qweb.field.date"]
                .with_context(lang=lang)
                .value_to_html(value, {})
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
                value = ""
                sub_fields = field_found.split(".")
                if len(sub_fields) > 2:
                    raise NotImplementedError(
                        _(
                            "Fields with several subfields "
                            "is not supported (several dots)"
                        )
                    )
                elif len(sub_fields) == 2:
                    field = sub_fields[0]
                    subfield = sub_fields[1]
                    if (
                        field in orm_fields
                        and orm_fields[field].get("type", "") != "many2one"
                    ):
                        raise UserError(
                            _("The field %s must a many2one in order to use subfields")
                            % field
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
                content_interpreted = content_interpreted.replace(
                    "[[" + field_found + "]]", value
                )
            return content_interpreted
        return ""
