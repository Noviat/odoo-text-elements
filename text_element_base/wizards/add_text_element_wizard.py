# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AddTextElementWizard(models.TransientModel):
    _name = "add.text.element.wizard"
    _description = "Add Text Element on record"

    text_element_id = fields.Many2one(
        comodel_name="text.element", string="Text Element"
    )
    text_element_domain = fields.Binary(
        compute="_compute_text_element_domain", store=False
    )
    is_edit = fields.Boolean(
        string="Must be edited",
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

    @api.onchange("text_element_id")
    def _onchange_text_element_id(self):
        for wizard in self:
            current_record = self.env[self.env.context.get("active_model")].browse(
                self.env.context.get("active_id")
            )
            if wizard.text_element_id:
                if (
                    wizard.text_element_id.id in current_record.text_element_ids.ids
                    or current_record.text_element_custom_ids.filtered(
                        lambda tec, wiz=wizard: tec.text_element_id.id
                        == wiz.text_element_id.id
                    )
                ):
                    raise UserError(
                        _("This text element is already in the related record")
                    )
                wizard.name = wizard.text_element_id.name
                wizard.content = wizard.text_element_id.content
                wizard.position = wizard.text_element_id.position
                wizard.page_break_before = wizard.text_element_id.page_break_before
                wizard.page_break_after = wizard.text_element_id.page_break_after
                wizard.sequence = wizard.text_element_id.sequence
            else:
                wizard.name = ""
                wizard.content = ""
                wizard.position = "before"
                wizard.page_break_before = False
                wizard.page_break_after = False
                wizard.sequence = 0

    def _create_text_element(self):
        current_record = self.env[self.env.context.get("active_model")].browse(
            self.env.context.get("active_id")
        )
        if self.is_edit:
            values = {
                "name": self.name,
                "content": self.content,
                "position": self.position,
                "page_break_before": self.page_break_before,
                "page_break_after": self.page_break_after,
                "sequence": self.sequence,
                "res_model": self.env.context.get("active_model"),
                "res_id": self.env.context.get("active_id"),
            }
            if self.text_element_id:
                values.update(
                    {
                        "text_element_id": self.text_element_id.id,
                    }
                )
            self.env["text.element.custom"].create(values)
        else:
            current_record.update({"text_element_ids": [(4, self.text_element_id.id)]})

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
            "name": _("Add Text Element"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "add.text.element.wizard",
            "target": "new",
            "context": context,
        }
