# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import AccessError
from odoo.tests import new_test_user, tagged

from .common import TextElementSaleCase


@tagged("post_install", "-at_install")
class TestAccess(TextElementSaleCase):
    def test_salesman_reads_catalogue_and_edits_document_lines(self):
        user = new_test_user(
            self.env, login="te_salesman", groups="sales_team.group_sale_salesman"
        )
        order = (
            self.env["sale.order"]
            .create(
                {
                    "partner_id": self.partner_be.id,
                    "user_id": user.id,
                    "team_id": self.team.id,
                }
            )
            .with_user(user)
        )
        with self.assertRaises(AccessError):
            self.auto_all.with_user(user).write({"name": "Changed"})
        self.assertTrue(self.auto_all.with_user(user).name)
        line = order.text_element_custom_ids[:1]
        line.action_personalize()
        line.content = "<p>Adapted</p>"
        self.assertEqual(line.content, "<p>Adapted</p>")

    def test_manager_edits_catalogue(self):
        user = new_test_user(
            self.env,
            login="te_manager",
            groups="base.group_user,text_element_base.group_text_element_manager",
        )
        self.auto_all.with_user(user).write({"name": "Changed"})
        self.assertEqual(self.auto_all.name, "Changed")
