# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestConditions(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Customer", "country_id": cls.env.ref("base.be").id}
        )
        cls.element = cls.env["text.element"].create(
            {
                "name": "Belgian notice",
                "model_id": cls.env["ir.model"]._get("res.partner").id,
                "content": "<p>Notice</p>",
            }
        )
        cls.today = fields.Date.context_today(cls.element)

    def test_no_condition_prints(self):
        self.assertEqual(self.element._get_print_status(self.partner), "printed")

    def test_domain_condition(self):
        self.element.filter_domain = "[('country_id.code', '=', 'BE')]"
        self.assertEqual(self.element._get_print_status(self.partner), "printed")
        self.element.filter_domain = "[('country_id.code', '=', 'NL')]"
        self.assertEqual(
            self.element._get_print_status(self.partner), "condition_not_met"
        )

    def test_validity_period(self):
        self.element.write(
            {"date_from": self.today + timedelta(days=1), "date_to": False}
        )
        self.assertEqual(self.element._get_print_status(self.partner), "out_of_period")
        self.element.write(
            {
                "date_from": self.today - timedelta(days=10),
                "date_to": self.today - timedelta(days=1),
            }
        )
        self.assertEqual(self.element._get_print_status(self.partner), "out_of_period")
        self.element.write({"date_to": self.today})
        self.assertEqual(self.element._get_print_status(self.partner), "printed")

    def test_print_context(self):
        self.element.context_params = "proforma"
        self.assertEqual(
            self.element._get_print_status(self.partner, check_context=False),
            "printed",
        )
        self.assertEqual(
            self.element._get_print_status(self.partner, check_context=True),
            "context_mismatch",
        )
        element = self.element.with_context(proforma=True)
        self.assertEqual(
            element._get_print_status(self.partner, check_context=True), "printed"
        )
        self.element.context_params = "!proforma"
        self.assertEqual(
            element._get_print_status(self.partner, check_context=True),
            "context_mismatch",
        )

    def test_archived_not_printed(self):
        self.element.active = False
        self.assertEqual(self.element._get_print_status(self.partner), "archived")
