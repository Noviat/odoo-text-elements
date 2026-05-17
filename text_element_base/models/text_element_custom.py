# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TextElementCustom(models.Model):
    _name = "text.element.custom"
    _inherit = [
        "text.element",
    ]
    _description = "Custom text elements"
    _order = "sequence, id"
    _check_company_auto = True

    res_id = fields.Many2oneReference(
        required=True, model_field="model", string="Record ID"
    )
    text_element_id = fields.Many2one(
        comodel_name="text.element", string="Text Element"
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "model_id" in fields_list and not res.get("model_id"):
            parent_model = self.env.context.get(
                "text_element_parent_model"
            ) or self.env.context.get("default_res_model")
            if parent_model:
                res["model_id"] = self.env["ir.model"]._get_id(parent_model)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        parent_model = self.env.context.get("text_element_parent_model")
        if parent_model:
            model_id = self.env["ir.model"]._get_id(parent_model)
            for vals in vals_list:
                if not vals.get("model_id"):
                    vals["model_id"] = model_id
        return super().create(vals_list)

    @api.constrains("model_id")
    def _check_model_id(self):
        for record in self:
            if not record.model_id:
                raise ValidationError(
                    self.env._(
                        "A custom text element must be linked to a model "
                        "(field 'Applies to')."
                    )
                )
