# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "text.element.abstract"]

    text_element_ids = fields.Many2many(
        domain=[("res_model", "in", ("account.move", "all"))]
    )
    text_element_custom_ids = fields.One2many(
        domain=[("res_model", "in", ("account.move", "all"))]
    )
    report_lang = fields.Selection(
        required=False,
    )

    @api.depends("partner_id")
    def _compute_report_lang(self):
        for rec in self:
            if rec.partner_id.lang:
                rec.report_lang = rec.partner_id.lang
            else:
                rec.report_lang = self.env.lang
