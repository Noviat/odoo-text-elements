# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

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

    def _get_computed_elements_domain(self):
        domain = super()._get_computed_elements_domain()
        domain.append(("move_type", "in", ["all", self.move_type]))
        return domain

    def _get_text_element_records(self, position):
        self.ensure_one()
        text_elements, custom_text_elements = super()._get_text_element_records(
            position
        )
        text_elements = text_elements.filtered(
            lambda te: te.move_type == "all" or te.move_type == self.move_type
        )
        custom_text_elements = custom_text_elements.filtered(
            lambda te: te.move_type == "all" or te.move_type == self.move_type
        )
        if not self.env.context.get("proforma_invoice"):
            text_elements = text_elements.filtered(
                lambda te: not te.only_shown_in_proforma
            )
            custom_text_elements = custom_text_elements.filtered(
                lambda te: not te.only_shown_in_proforma
            )
        return text_elements, custom_text_elements
