# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class AddTextElementWizard(models.TransientModel):
    _name = "add.text.element.wizard"
    _description = "Add Text Element on record"

    text_element_id = fields.Many2one(
        comodel_name="text.element", string="Text Element"
    )
    text_element_domain = fields.Binary(
        compute="_compute_text_element_domain", store=False
    )
    res_id = fields.Many2oneReference(
        default=lambda self: self._default_res_id(), model_field="res_model"
    )
    res_model = fields.Char(default=lambda self: self._default_res_model())

    def _default_res_id(self):
        return self.env.context.get("active_id")

    def _default_res_model(self):
        return self.env.context.get("active_model")

    @api.model
    def _selection_lang_get(self):
        return self.env["res.lang"].get_installed()

    @api.depends("res_model")
    def _compute_text_element_domain(self):
        for wizard in self:
            if wizard.res_model:
                current_record = self.env[self.env.context.get("active_model")].browse(
                    self.env.context.get("active_id")
                )
                wizard.text_element_domain = [
                    "|",
                    ("model", "=", wizard.res_model),
                    ("model", "=", False),
                    ("id", "not in", current_record.text_element_ids.ids),
                    (
                        "id",
                        "not in",
                        current_record.text_element_custom_ids.mapped(
                            "text_element_id"
                        ).ids,
                    ),
                ]
            else:
                wizard.text_element_domain = [("model", "=", False)]

    def action_add_and_close(self):
        self.ensure_one()
        self._create_text_element()
        return {"type": "ir.actions.act_window_close"}

    def action_add(self):
        self.ensure_one()
        self._create_text_element()
        context = self.env.context.copy()
        context.update(
            {
                "active_id": self.env.context.get("active_id"),
                "active_model": self.env.context.get("active_model"),
            }
        )
        return {
            "name": self.env._("Add Text Element"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "add.text.element.wizard",
            "target": "new",
            "context": context,
        }

    def _create_text_element(self):
        current_record = self.env[self.env.context.get("active_model")].browse(
            self.env.context.get("active_id")
        )
        current_record.update({"text_element_ids": [(4, self.text_element_id.id)]})
