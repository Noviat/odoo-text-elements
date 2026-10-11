# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        TextElement = cls.env["text.element"]
        TextElement.search([("default", "=", True)]).write({"default": False})
        model = cls.env["ir.model"]._get("purchase.order")
        cls.vendor_be = cls.env["res.partner"].create(
            {"name": "Vendor BE", "country_id": cls.env.ref("base.be").id}
        )
        cls.vendor_nl = cls.env["res.partner"].create(
            {"name": "Vendor NL", "country_id": cls.env.ref("base.nl").id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Text element product", "type": "consu"}
        )
        cls.before_lines = TextElement.create(
            {
                "name": "Delivery address",
                "model_id": model.id,
                "position": "before_line",
                "default": True,
                "content": "<p>Deliver to our warehouse, [[partner_id.name]]</p>",
            }
        )
        cls.after_totals = TextElement.create(
            {
                "name": "Belgian vendors",
                "model_id": model.id,
                "position": "after_line",
                "default": True,
                "filter_domain": "[('partner_id.country_id.code', '=', 'BE')]",
                "content": "<p>Belgian clause for [[name]]</p>",
            }
        )

    def _order(self, vendor):
        return self.env["purchase.order"].create(
            {
                "partner_id": vendor.id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_qty": 2})
                ],
            }
        )

    def _html(self, report, order):
        html, _type = self.env["ir.actions.report"]._render_qweb_html(report, order.ids)
        return html.decode()

    def test_automatic_texts_added(self):
        order = self._order(self.vendor_be)
        self.assertEqual(
            order.text_element_custom_ids.text_element_id,
            self.before_lines | self.after_totals,
        )
        self.assertTrue(
            self.env["ir.model"]._get("purchase.order").can_be_used_with_text_elements
        )

    def test_purchase_order_report(self):
        order = self._order(self.vendor_be)
        order.button_confirm()
        html = self._html("purchase.action_report_purchase_order", order)
        self.assertIn("Deliver to our warehouse, Vendor BE", html)
        self.assertIn(f"Belgian clause for {order.name}", html)
        self.assertLess(
            html.index("Deliver to our warehouse"), html.index("Belgian clause")
        )

    def test_request_for_quotation_report(self):
        order = self._order(self.vendor_be)
        html = self._html("purchase.report_purchase_quotation", order)
        self.assertIn("Deliver to our warehouse, Vendor BE", html)
        self.assertIn("Belgian clause", html)

    def test_condition_not_met(self):
        order = self._order(self.vendor_nl)
        html = self._html("purchase.report_purchase_quotation", order)
        self.assertIn("Deliver to our warehouse, Vendor NL", html)
        self.assertNotIn("Belgian clause", html)
