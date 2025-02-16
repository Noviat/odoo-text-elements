# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models


class EditTextElementWizard(models.TransientModel):
    _name = "edit.text.element.wizard"
    _description = "Edit Text Element"

    text_element_id = fields.Many2one(
        comodel_name="text.element", string="Text Element"
    )
    text_element_domain = fields.Binary(compute="_compute_text_element_domain")
    text_element_custom_id = fields.Many2one(
        comodel_name="text.element.custom", string="Custom Text Element"
    )
    text_element_custom_domain = fields.Binary(
        compute="_compute_text_element_custom_domain"
    )
    name = fields.Char(required=True)
    content = fields.Html()
    position = fields.Selection([("before", "Before"), ("after", "After")])
    page_break_before = fields.Boolean()
    page_break_after = fields.Boolean()
    sequence = fields.Integer()
    lang = fields.Selection(
        selection=lambda self: self._selection_lang_get(),
        compute="_compute_lang",
    )
    res_id = fields.Integer(default=lambda self: self._default_res_id())
    res_model = fields.Char(default=lambda self: self._default_res_model())

    def _default_res_id(self):
        return self.env.context.get("active_id")

    def _default_res_model(self):
        return self.env.context.get("active_model")

    @api.model
    def _selection_lang_get(self):
        return self.env["res.lang"].get_installed()

    @api.depends("res_model", "lang")
    def _compute_text_element_domain(self):
        for wizard in self:
            if wizard.res_model:
                wizard.text_element_domain = [
                    ("res_model", "in", (wizard.res_model, "all")),
                    ("lang", "=", wizard.lang),
                ]
            else:
                wizard.text_element_domain = [("res_model", "=", "all")]

    @api.depends("res_model", "res_id", "lang")
    def _compute_lang(self):
        for wizard in self:
            if wizard.res_id and wizard.res_model:
                current_record = self.env[wizard.res_model].browse(wizard.res_id)
                wizard.lang = current_record.report_lang
            else:
                wizard.lang = False

    @api.depends("res_model", "res_id")
    def _compute_text_element_custom_domain(self):
        for wizard in self:
            if wizard.res_model and wizard.res_id:
                wizard.text_element_custom_domain = [
                    ("res_model", "=", wizard.res_model),
                    ("res_id", "=", wizard.res_id),
                ]
            else:
                wizard.text_element_custom_domain = [("res_id", "=", 0)]

    @api.onchange("text_element_id", "text_element_custom_id")
    def _onchange_sale_text_element_id(self):
        for wizard in self:
            if wizard.text_element_id:
                wizard.name = wizard.text_element_id.name
                wizard.content = wizard.text_element_id.content
                wizard.position = wizard.text_element_id.position
                wizard.page_break_before = wizard.text_element_id.page_break_before
                wizard.page_break_after = wizard.text_element_id.page_break_after
                wizard.sequence = wizard.text_element_id.sequence
            elif wizard.text_element_custom_id:
                wizard.name = wizard.text_element_custom_id.name
                wizard.content = wizard.text_element_custom_id.content
                wizard.position = wizard.text_element_custom_id.position
                wizard.page_break_before = (
                    wizard.text_element_custom_id.page_break_before
                )
                wizard.page_break_after = wizard.text_element_custom_id.page_break_after
                wizard.sequence = wizard.text_element_custom_id.sequence
            else:
                wizard.name = ""
                wizard.content = ""
                wizard.position = "before"
                wizard.page_break_before = False
                wizard.page_break_after = False
                wizard.sequence = 0

    def _edit_text_element(self):
        if self.text_element_id:
            self.env["text.element.custom"].create(
                {
                    "name": self.name,
                    "content": self.content,
                    "position": self.position,
                    "page_break_before": self.page_break_before,
                    "page_break_after": self.page_break_after,
                    "sequence": self.sequence,
                    "res_model": self.env.context.get("active_model"),
                    "res_id": self.env.context.get("active_id"),
                    "text_element_id": self.text_element_id.id,
                }
            )
            current_record = self.env[self.res_model].browse(self.res_id)
            if self.text_element_id.id in current_record.text_element_ids.ids:
                current_record.write(
                    {"text_element_ids": [(3, self.text_element_id.id)]}
                )
        if self.text_element_custom_id:
            self.text_element_custom_id.update(
                {
                    "name": self.name,
                    "content": self.content,
                    "position": self.position,
                    "page_break_before": self.page_break_before,
                    "page_break_after": self.page_break_after,
                    "sequence": self.sequence,
                }
            )

    def action_edit_and_close(self):
        self.ensure_one()
        self._edit_text_element()
        return {"type": "ir.actions.act_window_close"}

    def action_edit_and_continue(self):
        self.ensure_one()
        self._edit_text_element()
        context = self.env.context.copy()
        context.update(
            {
                "active_id": self.env.context.get("active_id"),
                "active_model": self.env.context.get("active_model"),
            }
        )
        return {
            "name": _("Edit Text Element"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "edit.text.element.wizard",
            "target": "new",
            "context": context,
        }
