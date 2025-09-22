# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "text.element.abstract"]

    text_element_ids = fields.Many2many(
        domain=["|", ("model", "=", "sale.order"), ("model", "=", False)]
    )
    text_element_custom_ids = fields.One2many(
        domain=["|", ("model", "=", "sale.order"), ("model", "=", False)]
    )

    @api.depends("partner_id", "company_id")
    def _compute_text_elements(self):
        return super()._compute_text_elements()
