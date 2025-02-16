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

    @api.depends("partner_id")
    def _compute_report_lang(self):
        for rec in self:
            if rec.partner_id.lang:
                rec.report_lang = rec.partner_id.lang
            else:
                rec.report_lang = self.env.lang
