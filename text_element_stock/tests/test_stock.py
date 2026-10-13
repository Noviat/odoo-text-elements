# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        TextElement = cls.env["text.element"]
        TextElement.search([("default", "=", True)]).write({"default": False})
        model = cls.env["ir.model"]._get("stock.picking")
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.partner = cls.env["res.partner"].create({"name": "Consignee"})
        cls.product = cls.env["product.product"].create(
            {"name": "Text element product", "is_storable": True}
        )
        cls.handling = TextElement.create(
            {
                "name": "Handling",
                "model_id": model.id,
                "position": "before_line",
                "default": True,
                "content": "<p>Handle with care, [[partner_id.name]]</p>",
            }
        )
        cls.outgoing_only = TextElement.create(
            {
                "name": "Return policy",
                "model_id": model.id,
                "position": "after_line",
                "default": True,
                "filter_domain": "[('picking_type_code', '=', 'outgoing')]",
                "content": "<p>Returns accepted within 30 days</p>",
            }
        )

    def _picking(self, picking_type):
        return self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id
                or self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": picking_type.default_location_dest_id.id
                or self.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "uom_id": self.product.uom_id.id,
                        },
                    )
                ],
            }
        )

    def _html(self, picking):
        html, _type = self.env["ir.actions.report"]._render_qweb_html(
            "stock.action_report_delivery", picking.ids
        )
        return html.decode()

    def test_delivery_slip(self):
        picking = self._picking(self.warehouse.out_type_id)
        self.assertEqual(
            picking.text_element_custom_ids.text_element_id,
            self.handling | self.outgoing_only,
        )
        html = self._html(picking)
        self.assertIn("Handle with care, Consignee", html)
        self.assertIn("Returns accepted within 30 days", html)
        self.assertLess(html.index("Handle with care"), html.index("Returns accepted"))

    def test_receipt_skips_outgoing_text(self):
        picking = self._picking(self.warehouse.in_type_id)
        html = self._html(picking)
        self.assertIn("Handle with care", html)
        self.assertNotIn("Returns accepted", html)
