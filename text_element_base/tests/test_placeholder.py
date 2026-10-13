# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date
from unittest.mock import patch

from markupsafe import escape

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPlaceholder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TextElement = cls.env["text.element"]
        cls.country = cls.env.ref("base.be")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Noviat <script>",
                "email": "info@example.com",
                "country_id": cls.country.id,
                "parent_id": cls.env["res.partner"].create({"name": "Parent"}).id,
            }
        )
        cls.partner_model = cls.env["ir.model"]._get("res.partner")

    def _render(self, content):
        return str(self.TextElement._render_placeholders(self.partner, content))

    def test_bracket_simple_field(self):
        self.assertEqual(self._render("<p>[[email]]</p>"), "<p>info@example.com</p>")

    def test_bracket_multi_level(self):
        self.assertEqual(self._render("[[country_id.name]]"), self.country.name)
        self.assertEqual(self._render("[[parent_id.name]]"), "Parent")

    def test_native_tout_syntax(self):
        self.assertEqual(
            self._render('<t t-out="object.email">fallback</t>'), "info@example.com"
        )

    def test_native_tout_default_when_empty(self):
        self.assertEqual(
            self._render('<t t-out="object.phone">no phone</t>'), "no phone"
        )

    def test_empty_value_renders_empty(self):
        self.assertEqual(self._render("a[[phone]]b"), "ab")

    def test_empty_intermediate_record(self):
        self.partner.parent_id = False
        self.assertEqual(self._render("a[[parent_id.name]]b"), "ab")

    def test_invalid_path_never_raises(self):
        with self.assertLogs(
            "odoo.addons.text_element_base.models.text_element", level="WARNING"
        ):
            self.assertEqual(self._render("a[[no_such_field]]b"), "ab")
        self.assertEqual(self._render("a[[email.name]]b"), "ab")
        self.assertEqual(self._render("a[[__class__]]b"), "ab")

    def test_many2one_renders_display_name(self):
        self.assertEqual(self._render("[[country_id]]"), self.country.display_name)

    def _create_children(self):
        return self.env["res.partner"].create(
            [
                {
                    "name": "Child A",
                    "parent_id": self.partner.id,
                    "email": "a@example.com",
                },
                {"name": "Child B <x>", "parent_id": self.partner.id},
            ]
        )

    def test_x2many_path_joins_values(self):
        self._create_children()
        self.assertEqual(
            self._render("[[child_ids.name]]"), "Child A, Child B &lt;x&gt;"
        )

    def test_x2many_layout_lines(self):
        self._create_children()
        self.assertEqual(
            self._render("[[child_ids.name::lines]]"), "Child A<br/>Child B &lt;x&gt;"
        )

    def test_x2many_layout_list(self):
        self._create_children()
        self.assertEqual(
            self._render("[[child_ids.name::list]]"),
            "<ul><li>Child A</li><li>Child B &lt;x&gt;</li></ul>",
        )

    def test_x2many_field_split_per_record(self):
        child_a, child_b = self._create_children()
        self.assertEqual(
            self._render("[[child_ids::lines]]"),
            f"{escape(child_a.display_name)}<br/>{escape(child_b.display_name)}",
        )

    def test_layout_skips_empty_values(self):
        self._create_children()
        self.assertEqual(
            self._render("[[child_ids.email::list]]"), "<ul><li>a@example.com</li></ul>"
        )

    def test_layout_combines_with_format_option(self):
        child_a, child_b = self._create_children()
        expected = [
            str(
                self.TextElement._get_formated_value(
                    child.create_date, "en_US", "datetime", "date"
                )
            )
            for child in (child_a, child_b)
        ]
        rendered = self.TextElement.with_context(lang="en_US")._render_placeholders(
            self.partner, "[[child_ids.create_date::date::lines]]"
        )
        self.assertEqual(str(rendered), "<br/>".join(expected))

    def test_layout_on_empty_x2many_renders_nothing(self):
        self.assertEqual(self._render("a[[child_ids.name::list]]b"), "ab")

    def test_layout_option_passes_save_check(self):
        self.assertEqual(
            self.TextElement._find_invalid_placeholders(
                "res.partner", "[[child_ids.name::list]] [[bank_ids.acc_number::lines]]"
            ),
            [],
        )

    def test_char_value_is_escaped(self):
        self.assertIn("&lt;script&gt;", self._render("[[name]]"))
        self.assertNotIn("<script>", self._render("[[name]]"))

    def test_date_option_full(self):
        rendered = self.TextElement.with_context(lang="en_US")._get_formated_value(
            date(2026, 8, 21), "en_US", "date", "full"
        )
        self.assertEqual(str(rendered), "21 August 2026")

    def test_find_invalid_placeholders(self):
        content = '[[email]] [[country_id.name]] [[nope]] <t t-out="object.bad"/>'
        self.assertEqual(
            sorted(self.TextElement._find_invalid_placeholders("res.partner", content)),
            ["bad", "nope"],
        )

    def test_save_constraint_names_faulty_path(self):
        with self.assertRaisesRegex(ValidationError, "emial"):
            self.TextElement.create(
                {
                    "name": "Typo",
                    "model_id": self.partner_model.id,
                    "content": "<p>[[emial]]</p>",
                }
            )

    def test_convert_tout_to_brackets(self):
        self.assertEqual(
            self.TextElement._convert_tout_to_brackets(
                '<p><t t-out="object.partner_id.name">x</t></p>'
            ),
            "<p>[[partner_id.name]]</p>",
        )

    def test_tout_resolved_before_overridable_parser(self):
        """A module overriding _get_content_interpreted with a bracket-only
        parser (e.g. GIMI) must still render native placeholders."""
        element = self.TextElement.create(
            {
                "name": "Native",
                "model_id": self.partner_model.id,
                "content": '<p><t t-out="object.email">x</t> [[country_id.name]]</p>',
            }
        )
        seen = []
        model_class = type(self.TextElement)
        original = model_class._get_content_interpreted

        def bracket_only(record_self, record):
            seen.append(record_self.content)
            return original(record_self, record)

        with patch.object(model_class, "_get_content_interpreted", bracket_only):
            rendered = str(element._render_for(self.partner))
        self.assertNotIn("t-out", seen[0])
        self.assertIn("info@example.com", rendered)
        self.assertIn(self.country.name, rendered)
