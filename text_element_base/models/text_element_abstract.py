# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class TextElement(models.AbstractModel):
    _name = "text.element.abstract"
    _description = "Text elements (Abstract)"

    report_lang = fields.Selection(
        selection=lambda self: self._selection_lang_get(),
        required=False,
        compute="_compute_report_lang",
        store=True,
        readonly=False,
    )
    text_element_ids = fields.Many2many(
        comodel_name="text.element",
        string="Text Elements",
        copy=True,
        compute="_compute_text_elements",
        store=True,
        readonly=False,
    )
    text_element_custom_ids = fields.One2many(
        comodel_name="text.element.custom",
        inverse_name="res_id",
        string="Custom Text Elements",
        copy=True,
    )

    @api.model
    def _selection_lang_get(self):
        return self.env["res.lang"].get_installed()

    def _compute_report_lang(self):
        for rec in self:
            rec.report_lang = self.env.lang

    @api.depends("report_lang")
    def _compute_text_elements(self):
        for record in self:
            elements = self.env["text.element"].search(
                record._get_computed_elements_domain()
            )
            record.text_element_ids = elements

    def action_add_element_wizard(self):
        self.ensure_one()
        return {
            "name": _("Add Text Element"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "add.text.element.wizard",
            "target": "new",
        }

    def action_edit_element_wizard(self):
        self.ensure_one()
        return {
            "name": _("Edit Text Element"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "edit.text.element.wizard",
            "target": "new",
        }

    def _get_computed_elements_domain(self):
        self.ensure_one()
        return [
            ("default", "=", True),
            ("lang", "=", self.report_lang),
            "|",
            ("res_model", "=", self._name),
            ("res_model", "=", "all"),
            "|",
            ("user_id", "=", False),
            ("user_id", "=", self.env.user.id),
        ]

    def _get_text_elements(self, position):
        self.ensure_one()
        text_elements, custom_text_elements = self._get_text_element_records(position)
        text_elements_list = []
        for element in text_elements:
            text_elements_list.append(element)
        for element in custom_text_elements:
            text_elements_list.append(element)
        return sorted(text_elements_list, key=lambda e: e.sequence)

    def _get_text_element_records(self, position):
        text_elements = self.text_element_ids.filtered(lambda r: r.position == position)
        custom_text_elements = self.text_element_custom_ids.filtered(
            lambda r: r.position == position
        )
        return text_elements, custom_text_elements
