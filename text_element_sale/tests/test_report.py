# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from .common import TextElementSaleCase


@tagged("post_install", "-at_install")
class TestReport(TextElementSaleCase):
    def _html(self, order):
        html, _type = self.env["ir.actions.report"]._render_qweb_html(
            "sale.action_report_saleorder", order.ids
        )
        return html.decode()

    def test_texts_printed_with_placeholders(self):
        top = self._element("Top text", default=True, position="before")
        order = self._order(self.partner_be)
        html = self._html(order)
        self.assertIn("Automatic for all for Client BE", html)
        self.assertIn("Automatic for Belgium for Client BE", html)
        self.assertIn("Top text for Client BE", html)
        self.assertTrue(top)

    def test_condition_not_met_is_not_printed(self):
        order = self._order(self.partner_nl)
        order.action_add_text_elements(self.auto_be.ids)
        html = self._html(order)
        self.assertNotIn("Automatic for Belgium", html)

    def test_invalid_placeholder_does_not_break_report(self):
        order = self._order()
        self.env.cr.execute(
            "UPDATE text_element SET content = %s WHERE id = %s",
            ['{"en_US": "<p>Broken [[gone_field]]</p>"}', self.auto_all.id],
        )
        self.auto_all.invalidate_recordset()
        html = self._html(order)
        self.assertIn("Broken ", html)
