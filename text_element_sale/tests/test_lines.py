# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.fields import Command
from odoo.tests import tagged

from .common import TextElementSaleCase


@tagged("post_install", "-at_install")
class TestLines(TextElementSaleCase):
    def _line(self, order, element):
        return order.text_element_custom_ids.filtered(
            lambda line: line.text_element_id == element
        )

    def test_catalogue_line_follows_catalogue_content(self):
        order = self._order()
        line = self._line(order, self.auto_all)
        self.auto_all.content = "<p>Updated</p>"
        self.assertEqual(str(line._get_content_interpreted(order)), "<p>Updated</p>")

    def test_personalise_and_revert(self):
        order = self._order()
        line = self._line(order, self.auto_all)
        line.action_personalize()
        self.assertEqual(line.kind, "personalized")
        self.assertIn("[[partner_id.name]]", line.content)
        line.content = "<p>Adapted for [[partner_id.name]]</p>"
        self.auto_all.content = "<p>Catalogue changed</p>"
        self.assertEqual(
            str(line._get_content_interpreted(order)), "<p>Adapted for Client BE</p>"
        )
        line.action_revert_to_catalogue()
        self.assertEqual(line.kind, "catalogue")
        self.assertEqual(
            str(line._get_content_interpreted(order)), "<p>Catalogue changed</p>"
        )

    def test_personalise_converts_native_placeholders(self):
        self.auto_all.content = '<p><t t-out="object.partner_id.name">x</t></p>'
        order = self._order()
        line = self._line(order, self.auto_all)
        line.action_personalize()
        self.assertIn("[[partner_id.name]]", line.content)
        self.assertIn("Client BE", str(line._get_content_interpreted(order)))

    def test_personalise_copies_partner_language(self):
        self.env["res.lang"]._activate_lang("fr_FR")
        self.auto_all.with_context(lang="fr_FR").content = "<p>Texte FR</p>"
        self.partner_be.lang = "fr_FR"
        order = self._order()
        line = self._line(order, self.auto_all)
        line.action_personalize()
        self.assertEqual(line.content, "<p>Texte FR</p>")

    def test_personalised_line_keeps_catalogue_conditions(self):
        order = self._order(self.partner_be)
        line = self._line(order, self.auto_be)
        line.action_personalize()
        self.assertTrue(line._is_printable(order))
        self.auto_be.filter_domain = "[('partner_id.country_id.code', '=', 'NL')]"
        self.assertFalse(line._is_printable(order))
        self.assertEqual(line.print_status, "condition_not_met")

    def test_free_text_always_printed(self):
        order = self._order()
        order.write(
            {"text_element_custom_ids": [Command.create({"content": "<p>Free</p>"})]}
        )
        free = order.text_element_custom_ids.filtered(
            lambda line: not line.text_element_id
        )
        self.assertEqual(free.model, "sale.order")
        self.assertEqual(free.kind, "free")
        self.assertTrue(free._is_printable(order))

    def test_compat_field_reads_and_writes(self):
        order = self._order()
        self.assertEqual(order.text_element_ids, self.auto_all | self.auto_be)
        order.text_element_ids = self.auto_all | self.manual
        self.assertEqual(
            order.text_element_custom_ids.text_element_id, self.auto_all | self.manual
        )

    def test_deleting_catalogue_text(self):
        order = self._order()
        personalised = self._line(order, self.auto_be)
        personalised.action_personalize()
        self.auto_all.unlink()
        self.auto_be.unlink()
        self.assertEqual(order.text_element_custom_ids, personalised)
        self.assertEqual(personalised.kind, "free")

    def test_copy_document_copies_lines(self):
        order = self._order()
        order.action_add_text_elements(self.manual.ids)
        copy = order.copy()
        self.assertEqual(
            copy.text_element_custom_ids.text_element_id,
            order.text_element_custom_ids.text_element_id,
        )
        self.assertEqual(set(copy.text_element_custom_ids.mapped("res_id")), {copy.id})

    def test_preview_on_sample_order(self):
        order = self._order(self.partner_nl)
        self.auto_be.preview_record = order
        self.assertEqual(self.auto_be.preview_status, "condition_not_met")
        self.assertIn("Automatic for Belgium for Client NL", self.auto_be.preview_html)

    def test_archived_catalogue_text_not_printed(self):
        order = self._order()
        line = self._line(order, self.auto_all)
        self.auto_all.active = False
        self.assertFalse(line._is_printable(order))

    def test_legacy_create_with_content_is_personalised(self):
        order = self._order()
        line = self.env["text.element.custom"].create(
            {
                "model": "sale.order",
                "res_id": order.id,
                "text_element_id": self.manual.id,
                "content": "<p>Adapted</p>",
            }
        )
        self.assertEqual(line.kind, "personalized")

    def test_legacy_add_wizard_action(self):
        order = self._order()
        action = order.action_add_element_wizard()
        self.assertEqual(action["tag"], "text_element_add_from_catalogue")
        self.assertEqual(action["params"]["res_id"], order.id)
