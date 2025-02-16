# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "text.element.abstract"]

    text_element_ids = fields.Many2many(
        domain=[("res_model", "in", ("purchase.order", "all"))]
    )
    text_element_custom_ids = fields.One2many(
        domain=[("res_model", "in", ("purchase.order", "all"))]
    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        for purchase in self:
            if purchase.partner_id:
                purchase.report_lang = purchase.partner_id.lang
