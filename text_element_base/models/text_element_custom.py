# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


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
