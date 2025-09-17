# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "text.element.abstract"]

    text_element_ids = fields.Many2many(
        domain=["|", ("model", "=", "account.move"), ("model", "=", False)]
    )
    text_element_custom_ids = fields.One2many(
        domain=["|", ("model", "=", "account.move"), ("model", "=", False)]
    )

    @api.depends("partner_id")
    def _compute_text_elements(self):
        return super()._compute_text_elements()
