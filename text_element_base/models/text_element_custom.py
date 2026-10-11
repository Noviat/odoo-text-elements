# Copyright 2009 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from textwrap import shorten

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext

from .text_element import POSITION_SEQUENCE, POSITIONS


class TextElementCustom(models.Model):
    """A text printed on one document.

    A line either follows a catalogue element (its content is read live from
    the catalogue), personalises one (its own content, the catalogue's
    conditions), or is a free text (its own content, no condition).
    """

    _name = "text.element.custom"
    _description = "Document Text"
    _order = "position_sequence, sequence, id"
    _check_company_auto = True

    model = fields.Char(string="Document Model", required=True, index=True)
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Document type",
        compute="_compute_model_id",
        store=True,
        ondelete="cascade",
    )
    res_id = fields.Many2oneReference(
        required=True, model_field="model", string="Record ID", index=True
    )
    company_id = fields.Many2one(comodel_name="res.company")
    text_element_id = fields.Many2one(
        comodel_name="text.element",
        string="Catalogue text",
        ondelete="set null",
        check_company=True,
    )
    is_personalized = fields.Boolean(string="Personalised")
    origin = fields.Selection(
        [("auto", "Added automatically"), ("manual", "Added manually")],
        default="manual",
        required=True,
    )
    name = fields.Char(
        compute="_compute_from_catalogue", store=True, readonly=False, precompute=True
    )
    content = fields.Html(sanitize=True, sanitize_style=True)
    catalogue_content = fields.Html(
        related="text_element_id.content", string="Catalogue content"
    )
    position = fields.Selection(
        POSITIONS,
        compute="_compute_from_catalogue",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
    )
    position_sequence = fields.Integer(compute="_compute_position_sequence", store=True)
    sequence = fields.Integer(
        compute="_compute_from_catalogue", store=True, readonly=False, precompute=True
    )
    page_break_before = fields.Boolean(
        compute="_compute_from_catalogue", store=True, readonly=False, precompute=True
    )
    page_break_after = fields.Boolean(
        compute="_compute_from_catalogue", store=True, readonly=False, precompute=True
    )
    kind = fields.Selection(
        [
            ("catalogue", "Catalogue"),
            ("personalized", "Personalised"),
            ("free", "Free text"),
        ],
        string="Source",
        compute="_compute_kind",
    )
    print_status = fields.Selection(
        [
            ("printed", "Printed"),
            ("condition_not_met", "Condition not met"),
            ("out_of_period", "Out of validity period"),
            ("archived", "Catalogue text archived"),
        ],
        compute="_compute_print_status",
    )

    @api.depends("model")
    def _compute_model_id(self):
        for line in self:
            line.model_id = line.model and self.env["ir.model"]._get(line.model)

    @api.depends("text_element_id")
    def _compute_from_catalogue(self):
        for line in self:
            element = line.text_element_id
            if element:
                line.name = element.name
                line.position = element.position
                line.sequence = element.sequence
                line.page_break_before = element.page_break_before
                line.page_break_after = element.page_break_after
            else:
                line.name = line.name
                line.position = line.position or "after"
                line.sequence = line.sequence or 10
                line.page_break_before = line.page_break_before
                line.page_break_after = line.page_break_after

    @api.depends("position")
    def _compute_position_sequence(self):
        for line in self:
            line.position_sequence = POSITION_SEQUENCE.get(line.position, 0)

    @api.depends("text_element_id", "is_personalized")
    def _compute_kind(self):
        for line in self:
            if not line.text_element_id:
                line.kind = "free"
            elif line.is_personalized:
                line.kind = "personalized"
            else:
                line.kind = "catalogue"

    @api.depends(
        "text_element_id.filter_domain",
        "text_element_id.date_from",
        "text_element_id.date_to",
        "text_element_id.active",
        "res_id",
    )
    def _compute_print_status(self):
        for line in self:
            document = line._get_document()
            if not line.text_element_id or not document:
                line.print_status = "printed"
            else:
                line.print_status = line.text_element_id._get_print_status(document)

    @api.depends("name", "content", "text_element_id")
    def _compute_display_name(self):
        for line in self:
            line.display_name = line.name or shorten(
                html2plaintext(line.content or ""), 60, placeholder="…"
            )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "model" in fields_list and not res.get("model"):
            res["model"] = self.env.context.get(
                "text_element_parent_model"
            ) or self.env.context.get("default_res_model")
        return res

    @api.model_create_multi
    def create(self, vals_list):
        parent_model = self.env.context.get("text_element_parent_model")
        for vals in vals_list:
            # A text given with a catalogue reference is an adaptation of it.
            if (
                vals.get("text_element_id")
                and vals.get("content")
                and "is_personalized" not in vals
            ):
                vals["is_personalized"] = True
            if not vals.get("model") and vals.get("model_id"):
                vals["model"] = self.env["ir.model"].browse(vals["model_id"]).model
            if not vals.get("model") and parent_model:
                vals["model"] = parent_model
            if "company_id" not in vals and vals.get("model") and vals.get("res_id"):
                document = self.env[vals["model"]].browse(vals["res_id"])
                if "company_id" in document._fields:
                    vals["company_id"] = document.company_id.id
        return super().create(vals_list)

    @api.constrains("model")
    def _check_model(self):
        for line in self:
            if line.model not in self.env:
                raise ValidationError(
                    self.env._("A document text must be linked to a document.")
                )

    def _get_document(self):
        self.ensure_one()
        if not self.model or not self.res_id or self.model not in self.env:
            return None
        return self.env[self.model].browse(self.res_id).exists() or None

    def _get_document_lang(self):
        document = self._get_document()
        if document and "partner_id" in document._fields and document.partner_id.lang:
            return document.partner_id.lang
        return self.env.lang

    def _is_printable(self, record):
        self.ensure_one()
        if not self.text_element_id:
            return True
        status = self.text_element_id._get_print_status(record, check_context=True)
        return status == "printed"

    def _get_content_interpreted(self, record):
        self.ensure_one()
        if self.kind == "catalogue":
            return self.text_element_id._render_for(record)
        # Rendered through a virtual catalogue record so that modules
        # extending text.element._get_content_interpreted apply here too.
        virtual = self.env["text.element"].new(
            {"content": self.content, "model_id": self.model_id.id}
        )
        return virtual._render_for(record)

    def action_personalize(self):
        TextElement = self.env["text.element"]
        for line in self.filtered(lambda line: line.kind == "catalogue"):
            element = line.text_element_id.with_context(lang=line._get_document_lang())
            line.write(
                {
                    "is_personalized": True,
                    "name": element.name,
                    "content": TextElement._convert_tout_to_brackets(element.content),
                }
            )

    def action_revert_to_catalogue(self):
        for line in self.filtered(lambda line: line.kind == "personalized"):
            line.write(
                {
                    "is_personalized": False,
                    "content": False,
                    "name": line.text_element_id.name,
                }
            )
