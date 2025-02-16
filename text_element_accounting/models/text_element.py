# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class TextElement(models.Model):
    _inherit = "text.element"

    @api.model
    def _selection_model(self):
        res = super()._selection_model()
        res.append(["account.move", "Invoices"])
        return res
