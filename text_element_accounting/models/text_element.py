# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class TextElement(models.Model):
    _inherit = "text.element"

    only_shown_in_proforma = fields.Boolean()
    move_type = fields.Selection(
        selection=[
            ("all", "All"),
            ("entry", "Journal Entry"),
            ("out_invoice", "Customer Invoice"),
            ("out_refund", "Customer Credit Note"),
            ("in_invoice", "Vendor Bill"),
            ("in_refund", "Vendor Credit Note"),
            ("out_receipt", "Sales Receipt"),
            ("in_receipt", "Purchase Receipt"),
        ],
        default="all",
    )

    @api.model
    def _selection_model(self):
        res = super()._selection_model()
        res.append(["account.move", "Invoices"])
        return res
