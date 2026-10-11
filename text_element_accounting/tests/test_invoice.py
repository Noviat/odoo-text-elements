# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestInvoice(AccountTestInvoicingCommon):
    @classmethod
    def get_default_groups(cls):
        # Databases may grant contact creation through this group only; the
        # test company and its partners are created by the test user.
        return super().get_default_groups() | cls.env.ref("base.group_partner_manager")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        TextElement = cls.env["text.element"]
        TextElement.search([("default", "=", True)]).write({"default": False})
        cls.move_model = cls.env["ir.model"]._get("account.move")
        cls.payment_terms = TextElement.create(
            {
                "name": "Payment reminder",
                "model_id": cls.move_model.id,
                "position": "before_line",
                "default": True,
                "content": "<p>Invoice for [[partner_id.name]]</p>",
            }
        )
        cls.total_notice = TextElement.create(
            {
                "name": "Amount due",
                "model_id": cls.move_model.id,
                "position": "after_line",
                "default": True,
                "content": "<p>Amount due: [[amount_total]]</p>",
            }
        )
        cls.partner_a.name = "Customer A"

    def _invoice(self, partner=None, post=False):
        return self.init_invoice(
            "out_invoice",
            partner=partner or self.partner_a,
            products=self.product_a,
            post=post,
        )

    def _html(self, invoice):
        html, _type = self.env["ir.actions.report"]._render_qweb_html(
            "account.account_invoices", invoice.ids
        )
        return html.decode()

    def test_invoice_report_positions_and_placeholders(self):
        invoice = self._invoice(post=True)
        html = self._html(invoice)
        self.assertIn("Invoice for Customer A", html)
        # The report renders in the customer's language.
        lang = invoice.partner_id.lang or "en_US"
        amount = (
            self.env["ir.qweb.field.monetary"]
            .with_context(lang=lang)
            .value_to_html(
                invoice.amount_total, {"display_currency": invoice.currency_id}
            )
        )
        self.assertIn(f"Amount due: {amount}", html)
        self.assertLess(html.index("Invoice for"), html.index("Amount due"))

    def test_condition_not_met(self):
        self.total_notice.filter_domain = "[('amount_total', '>', 1000000)]"
        html = self._html(self._invoice(post=True))
        self.assertIn("Invoice for Customer A", html)
        self.assertNotIn("Amount due", html)

    def test_partner_change_on_draft_merges(self):
        invoice = self._invoice()
        manual = self.env["text.element"].create(
            {"name": "Manual", "model_id": self.move_model.id, "content": "<p>M</p>"}
        )
        invoice.action_add_text_elements(manual.ids)
        self.payment_terms.default = False
        invoice.partner_id = self.partner_b
        elements = invoice.text_element_custom_ids.text_element_id
        self.assertIn(manual, elements)
        self.assertNotIn(self.payment_terms, elements)
        self.assertIn(self.total_notice, elements)

    def test_posted_invoice_does_not_gain_new_automatic_text(self):
        invoice = self._invoice(post=True)
        later = self.env["text.element"].create(
            {
                "name": "Later",
                "model_id": self.move_model.id,
                "default": True,
                "content": "<p>Added later</p>",
            }
        )
        self.assertNotIn(later, invoice.text_element_custom_ids.text_element_id)
        self.assertNotIn("Added later", self._html(invoice))
