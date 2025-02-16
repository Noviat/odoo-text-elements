# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "text.element.abstract"]

    text_element_ids = fields.Many2many(
        domain=["|", ("model", "=", "purchase.order"), ("model", "=", False)]
    )
    text_element_custom_ids = fields.One2many(
        domain=["|", ("model", "=", "purchase.order"), ("model", "=", False)]
    )
