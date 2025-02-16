# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class TextElement(models.AbstractModel):
    _name = "text.element.abstract"
    _description = "Text elements (Abstract)"

    report_lang = fields.Selection(
        selection=lambda self: self._selection_lang_get(),
        required=True,
        default=lambda self: self.env.lang,
    )
    text_element_ids = fields.Many2many(
        comodel_name="text.element", string="Text Elements", copy=True
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

    @api.onchange("report_lang")
    def _onchange_report_lang(self):
        elements = self.text_element_ids = self.env["text.element"].search(
            [
                ("default", "=", True),
                ("lang", "=", self.report_lang),
                "|",
                ("res_model", "=", self._name),
                ("res_model", "=", "all"),
                "|",
                ("user_id", "=", False),
                ("user_id", "=", self.env.user.id),
            ]
        )
        self.text_element_ids = elements

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

    def _get_text_elements_before(self):
        self.ensure_one()
        text_elements_before = self.text_element_ids.filtered(
            lambda r: r.position == "before"
        )
        custom_text_elements_before = self.text_element_custom_ids.filtered(
            lambda r: r.position == "before"
        )
        text_elements = []
        for element in text_elements_before:
            text_elements.append(element)
        for element in custom_text_elements_before:
            text_elements.append(element)
        return sorted(text_elements, key=lambda e: e.sequence)

    def _get_text_elements_after(self):
        self.ensure_one()
        text_elements_before = self.text_element_ids.filtered(
            lambda r: r.position == "after"
        )
        custom_text_elements_before = self.text_element_custom_ids.filtered(
            lambda r: r.position == "after"
        )
        text_elements = []
        for element in text_elements_before:
            text_elements.append(element)
        for element in custom_text_elements_before:
            text_elements.append(element)
        return sorted(text_elements, key=lambda e: e.sequence)
