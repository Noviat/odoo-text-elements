# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "text.element.abstract"]

    text_element_ids = fields.Many2many(
        domain=[("res_model", "in", ("sale.order", "all"))]
    )
    text_element_custom_ids = fields.One2many(
        domain=[("res_model", "in", ("sale.order", "all"))]
    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for sale in self:
            if sale.partner_id:
                sale.report_lang = sale.partner_id.lang
