# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (httpS://www.gnu.org/licenses/agpl).

import logging
import re

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.models import Command

_logger = logging.getLogger(__name__)


class TextElement(models.Model):
    _name = "text.element"
    _description = "Text elements"
    _order = "position desc, sequence, id"
    _check_company_auto = True

    name = fields.Char(required=True, translate=True)
    content = fields.Html(
        translate=True,
        sanitize=False,
    )
    position = fields.Selection(
        [
            ("before", "Before the document"),
            ("before_line", "Before Lines (if applicable)"),
            ("after_line", "After Lines (if applicable)"),
            ("after", "After the document"),
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
    active = fields.Boolean(default=True)
    model_id = fields.Many2one(
        "ir.model",
        "Applies to",
        ondelete="cascade",
        domain="[('can_be_used_with_text_elements','=', True)]",
    )
    model = fields.Char(
        "Related Document Model",
        related="model_id.model",
        index=True,
        store=True,
        readonly=True,
    )
    filter_domain = fields.Char(
        string="Apply on", compute="_compute_filter_domain", store=True, readonly=False
    )
    field_placeholder_generator = fields.Char(store=False)
    field_placeholder_generator_name = fields.Char(
        compute="_compute_field_placeholder_generator_name"
    )
    context_params = fields.Char(
        help="Params have to be separated with "
        "semicolon and can be prefixed with"
        "exclamation mark (e.g proforma;!proforma)"
    )

    @api.model
    def _selection_lang_get(self):
        return self.env["res.lang"].get_installed()

    @api.depends("model_id")
    def _compute_filter_domain(self):
        for record in self:
            if not record.model_id:
                record.filter_domain = False

    @api.depends(
        "field_placeholder_generator",
    )
    def _compute_field_placeholder_generator_name(self):
        for record in self:
            if record.field_placeholder_generator:
                record.field_placeholder_generator_name = (
                    f"[[{record.field_placeholder_generator}]]"
                )
            else:
                record.field_placeholder_generator_name = False

    def action_add_text_element_to_custom(self):
        self.ensure_one()
        model_id, current_record = self._get_active_record()
        if model_id and current_record:
            values = {
                "name": self.name,
                "content": self.content,
                "position": self.position,
                "page_break_before": self.page_break_before,
                "page_break_after": self.page_break_after,
                "sequence": self.sequence,
                "model_id": model_id,
                "res_id": self.env.context.get("active_id"),
                "text_element_id": self.id,
            }
            self.env["text.element.custom"].create(values)
            current_record.write({"text_element_ids": [Command.unlink(self.id)]})

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
            orm_fields = record.fields_get()
            fields_found = re.findall(r"\[\[([^\]\]]*)\]\]*", self.content)
            content_interpreted = self.content
            for field_found in fields_found:
                value = self._get_value_for_field(record, field_found, orm_fields)
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

    def _get_active_record(self):
        if self.env.context.get("active_model", False):
            model = self.env.context.get("active_model")
        elif self.env.context.get("default_res_model", False):
            model = self.env.context.get("default_res_model")
        else:
            model = False
        if self.env.context.get("active_id", False):
            active_id = self.env.context.get("active_id")
        elif self.env.context.get("default_res_id", False):
            active_id = self.env.context.get("default_res_id")
        else:
            active_id = False
        if model:
            model_id = self.env["ir.model"]._get_id(model)
        else:
            model_id = False
        if model and active_id:
            current_record = self.env[model].browse(active_id)
        else:
            current_record = False
        return model_id, current_record
