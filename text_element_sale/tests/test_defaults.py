# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from .common import TextElementSaleCase


@tagged("post_install", "-at_install")
class TestDefaults(TextElementSaleCase):
    def test_automatic_texts_added_on_creation(self):
        order = self._order()
        lines = order.text_element_custom_ids
        self.assertEqual(lines.text_element_id, self.auto_all | self.auto_be)
        self.assertEqual(set(lines.mapped("origin")), {"auto"})
        self.assertEqual(set(lines.mapped("kind")), {"catalogue"})
        self.assertEqual(set(lines.mapped("model")), {"sale.order"})

    def test_expired_texts_not_added(self):
        self.auto_be.date_to = fields.Date.today() - timedelta(days=1)
        order = self._order()
        self.assertNotIn(self.auto_be, order.text_element_custom_ids.text_element_id)

    def test_partner_change_keeps_manual_and_personalised_lines(self):
        order = self._order()
        order.action_add_text_elements(self.manual.ids)
        personalised = order.text_element_custom_ids.filtered(
            lambda line: line.text_element_id == self.auto_all
        )
        personalised.action_personalize()
        free = order.text_element_custom_ids.create(
            {"model": "sale.order", "res_id": order.id, "content": "<p>Free</p>"}
        )
        self.auto_all.default = False

        order.partner_id = self.partner_nl

        lines = order.text_element_custom_ids
        self.assertIn(self.manual, lines.text_element_id)
        self.assertIn(personalised, lines)
        self.assertIn(free, lines)

    def test_reapply_reports_counts(self):
        order = self._order()
        self.auto_all.default = False
        new_auto = self._element("New automatic", default=True)
        added, removed = order._apply_default_text_elements()
        self.assertEqual((added, removed), (1, 1))
        self.assertIn(new_auto, order.text_element_custom_ids.text_element_id)
        self.assertNotIn(self.auto_all, order.text_element_custom_ids.text_element_id)
        action = order.action_reapply_default_text_elements()
        self.assertEqual(action["tag"], "display_notification")

    def test_new_default_not_pushed_to_existing_documents(self):
        order = self._order()
        new_auto = self._element("Later automatic", default=True)
        self.assertNotIn(new_auto, order.text_element_custom_ids.text_element_id)

    def test_catalogue_domain_excludes_present_texts(self):
        order = self._order()
        available = self.TextElement.search(order.get_text_element_catalogue_domain())
        self.assertIn(self.manual, available)
        self.assertNotIn(self.auto_all, available)
