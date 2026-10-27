# Copyright 2009 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import re

from markupsafe import Markup, escape

from odoo import api, fields, models
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

POSITIONS = [
    ("before", "Top of document"),
    ("before_line", "Before lines"),
    ("after_line", "After totals"),
    ("after", "Bottom of document"),
]
POSITION_SEQUENCE = {key: index for index, (key, _label) in enumerate(POSITIONS)}

# [[partner_id.name]] or [[date_order::full_date]]
BRACKET_RE = re.compile(r"\[\[([^\[\]]*)\]\]")
# What the native dynamic placeholder plugin of the HTML editor inserts:
# <t t-out="object.partner_id.name">default</t>
TOUT_RE = re.compile(
    r"<t\b[^>]*?\bt-out=\"object\.([^\"]*)\"[^>]*?(?:/>|>(.*?)</t>)",
    re.DOTALL,
)
PATH_RE = re.compile(r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$")
# [[invoice_ids.name::lines]]: how the values of several records are laid out
LAYOUTS = ("lines", "list")


class TextElement(models.Model):
    _name = "text.element"
    _description = "Text elements"
    _order = "model_id, position_sequence, sequence, id"
    _check_company_auto = True

    name = fields.Char(required=True, translate=True)
    content = fields.Html(
        translate=True,
        sanitize=False,
    )
    position = fields.Selection(POSITIONS, default="before", required=True)
    position_sequence = fields.Integer(compute="_compute_position_sequence", store=True)
    page_break_before = fields.Boolean(help="Start the text on a new page.")
    page_break_after = fields.Boolean(help="Start a new page after the text.")
    sequence = fields.Integer(
        default=10, help="Order of the texts sharing the same position."
    )
    default = fields.Boolean(
        string="Add automatically to new documents",
        help="Added to every new document of this type. Users can still remove it "
        "from a document, or add a text that is not automatic.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        help="Only added automatically on the documents of this user.",
    )
    active = fields.Boolean(default=True)
    model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Document type",
        ondelete="cascade",
        domain="[('can_be_used_with_text_elements', '=', True)]",
        help="Leave empty to make the text available on every document type.",
    )
    model = fields.Char(
        "Related Document Model",
        related="model_id.model",
        index=True,
        store=True,
        readonly=True,
    )
    filter_domain = fields.Char(
        string="Condition",
        compute="_compute_filter_domain",
        store=True,
        readonly=False,
        help="The text is printed only when the document matches this condition, "
        "evaluated when the document is printed.",
    )
    has_condition = fields.Boolean(compute="_compute_has_condition")
    date_from = fields.Date(string="Valid from")
    date_to = fields.Date(string="Valid until")
    context_params = fields.Char(
        string="Print context",
        help="Context keys separated with a semicolon, prefixed with an "
        "exclamation mark to negate them (e.g. proforma;!from_portal).",
    )
    preview_record = fields.Reference(
        selection="_selection_preview_record",
        string="Sample document",
        store=False,
    )
    preview_status = fields.Selection(
        [
            ("printed", "Would be printed"),
            ("condition_not_met", "Condition not met"),
            ("out_of_period", "Out of validity period"),
            ("context_mismatch", "Print context not met"),
            ("archived", "Archived"),
        ],
        compute="_compute_preview",
    )
    preview_html = fields.Html(compute="_compute_preview", sanitize=False)

    _sql_constraints = [
        (
            "date_range",
            "CHECK(date_from IS NULL OR date_to IS NULL OR date_from <= date_to)",
            "The validity start date must be before its end date.",
        ),
    ]

    @api.model
    def _selection_preview_record(self):
        models_ = self.env["ir.model"].search(
            [("can_be_used_with_text_elements", "=", True)]
        )
        return [(m.model, m.name) for m in models_]

    @api.depends("position")
    def _compute_position_sequence(self):
        for record in self:
            record.position_sequence = POSITION_SEQUENCE.get(record.position, 0)

    @api.depends("model_id")
    def _compute_filter_domain(self):
        for record in self:
            if not record.model_id:
                record.filter_domain = False

    @api.depends("filter_domain")
    def _compute_has_condition(self):
        for record in self:
            record.has_condition = record.filter_domain not in (False, "", "[]")

    @api.depends(
        "preview_record",
        "content",
        "filter_domain",
        "date_from",
        "date_to",
        "context_params",
    )
    def _compute_preview(self):
        for element in self:
            document = element.preview_record
            if not document or (element.model and document._name != element.model):
                element.preview_status = False
                element.preview_html = False
                continue
            element.preview_status = element._get_print_status(
                document, check_context=True
            )
            lang = (
                "partner_id" in document._fields and document.partner_id.lang
            ) or self.env.lang
            element.preview_html = element.with_context(lang=lang)._render_for(document)

    @api.constrains("content", "model_id")
    def _check_placeholders(self):
        langs = [code for code, _name in self.env["res.lang"].get_installed()]
        for element in self.filtered("model"):
            invalid = set()
            for lang in langs:
                invalid.update(
                    element._find_invalid_placeholders(
                        element.model, element.with_context(lang=lang).content
                    )
                )
            if invalid:
                raise ValidationError(
                    self.env._(
                        "These placeholders do not match a field of %(model)s: "
                        "%(paths)s",
                        model=element.model_id.name,
                        paths=", ".join(sorted(invalid)),
                    )
                )

    # ------------------------------------------------------------------
    # Conditions
    # ------------------------------------------------------------------

    def _get_print_status(self, record, check_context=False):
        """Tell whether this element prints on ``record`` and, if not, why.

        The print context can only be judged while printing, so the document
        tab leaves it out and the report and the preview include it.
        """
        self.ensure_one()
        if not self.active:
            return "archived"
        today = fields.Date.context_today(self)
        if (self.date_from and self.date_from > today) or (
            self.date_to and self.date_to < today
        ):
            return "out_of_period"
        if self.filter_domain:
            domain = safe_eval(self.filter_domain)
            if domain and not record.sudo().filtered_domain(domain):
                return "condition_not_met"
        if check_context and not self._match_print_context():
            return "context_mismatch"
        return "printed"

    def _match_print_context(self):
        self.ensure_one()
        for param in (self.context_params or "").split(";"):
            param = param.strip()
            if not param:
                continue
            negate = param.startswith("!")
            key = param[1:] if negate else param
            if bool(self.env.context.get(key)) == negate:
                return False
        return True

    # ------------------------------------------------------------------
    # Placeholders
    # ------------------------------------------------------------------

    def _get_content_interpreted(self, record):
        self.ensure_one()
        return self._render_placeholders(record, self.content or "")

    def _render_for(self, record):
        """Render the content on ``record``: the entry point of reports.

        Native ``<t t-out>`` placeholders are resolved here first, so that
        modules overriding ``_get_content_interpreted`` with their own
        bracket parser keep working: they only receive brackets.
        """
        self.ensure_one()
        content = self.content or ""
        resolved = self._render_tout(record, content)
        if resolved == content:
            return self._get_content_interpreted(record)
        virtual = self.new({"content": resolved, "model_id": self.model_id.id})
        return virtual._get_content_interpreted(record)

    @api.model
    def _render_tout(self, record, content):
        def replace_tout(match):
            value = self._resolve_placeholder(record, match.group(1).strip())
            return value or (match.group(2) or "")

        return TOUT_RE.sub(replace_tout, str(content)) if content else content

    @api.model
    def _render_placeholders(self, record, content):
        if not content:
            return ""

        def replace_bracket(match):
            path, _sep, option = match.group(1).partition("::")
            return self._resolve_placeholder(record, path.strip(), option.strip())

        content = self._render_tout(record, content)
        # Sanitized html field content; _resolve_placeholder escapes the values
        return Markup(BRACKET_RE.sub(replace_bracket, content))  # noqa: S704

    @api.model
    def _resolve_placeholder(self, record, path, option=""):
        """Return the formatted value of ``path`` on ``record``, or "".

        Walks the fields one by one instead of evaluating an expression, and
        never raises: a placeholder must not make a report fail.

        A path through a one2many or a many2many yields several values,
        joined with commas, or laid out by the ``lines`` and ``list``
        options. Those combine with a format option: ``full::lines``.
        """
        options = [opt.strip() for opt in option.split("::")] if option else []
        layout = next((opt for opt in options if opt in LAYOUTS), "")
        option = next((opt for opt in options if opt not in LAYOUTS), "")
        try:
            field, owners = self._walk_path(record, path)
            if field is None:
                return ""
            if field.relational:
                # One value per related record, not one per owner: an
                # x2many at the end of the path is split like the others.
                values = [
                    escape(name)
                    for name in owners[field.name].mapped("display_name")
                    if name
                ]
            else:
                values = [
                    self._format_value(field, owner[field.name], option, owner)
                    for owner in owners
                ]
        except (KeyError, ValueError, AccessError, MissingError) as error:
            _logger.warning(
                "Text element placeholder %r cannot be rendered on %s: %s",
                path,
                record._name,
                error,
            )
            return ""
        return self._join_values([value for value in values if value], layout)

    @api.model
    def _join_values(self, values, layout=""):
        if not values:
            return ""
        if layout == "lines":
            return Markup("<br/>").join(values)
        if layout == "list":
            items = Markup("").join(Markup("<li>%s</li>") % value for value in values)
            return Markup("<ul>%s</ul>") % items
        return Markup(", ").join(values)

    @api.model
    def _walk_path(self, record, path):
        """Return the last field of ``path`` and the records holding it."""
        if not PATH_RE.match(path or ""):
            raise ValueError(path)
        names = path.split(".")
        current = record
        for name in names[:-1]:
            field = current._fields[name]
            if not field.relational:
                raise ValueError(path)
            current = current[name]
            if not current:
                return None, current
        return current._fields[names[-1]], current

    @api.model
    def _find_invalid_placeholders(self, model_name, content):
        if not content or model_name not in self.env:
            return []
        paths = [m.partition("::")[0].strip() for m in BRACKET_RE.findall(content)]
        paths += [m[0].strip() for m in TOUT_RE.findall(content)]
        custom = self._get_custom_placeholder_names(model_name)
        return [
            path
            for path in paths
            if path not in custom and not self._is_valid_path(model_name, path)
        ]

    @api.model
    def _get_custom_placeholder_names(self, model_name):
        """Placeholders that are not fields, rendered by an override.

        A module that extends ``_get_content_interpreted`` with its own
        placeholders lists them here so that saving the text accepts them.
        """
        return set()

    @api.model
    def _is_valid_path(self, model_name, path):
        if not PATH_RE.match(path or ""):
            return False
        model = self.env[model_name]
        names = path.split(".")
        for index, name in enumerate(names):
            field = model._fields.get(name)
            if field is None:
                return False
            if index < len(names) - 1:
                if not field.relational:
                    return False
                model = self.env[field.comodel_name]
        return True

    @api.model
    def _format_value(self, field, value, option="", owner=None):
        if value is None or value is False or value == "":
            return ""
        lang = self.env.lang
        if field.type == "monetary":
            currency_field = owner is not None and field.get_currency_field(owner)
            currency = currency_field and owner[currency_field]
            if currency:
                return (
                    self.env["ir.qweb.field.monetary"]
                    .with_context(lang=lang)
                    .value_to_html(value, {"display_currency": currency})
                )
            return self._get_formated_value(float(value), lang)
        if field.type in ("datetime", "date", "binary"):
            return self._get_formated_value(value, lang, field.type, option)
        if field.type in ("integer", "float"):
            return self._get_formated_value(value, lang)
        if field.relational:
            return escape(", ".join(value.mapped("display_name")))
        if field.type == "selection":
            selection = dict(field._description_selection(self.env))
            return escape(selection.get(value, value))
        if field.type == "html":
            return Markup(value)  # noqa: S704 - html fields are sanitized
        return escape(str(value))

    @api.model
    def _get_formated_value(self, value, lang, field_type="str", options=""):
        """Format a date, a number or an image; extension point for modules."""
        if value is None or value == "" or not value:
            return ""
        if field_type == "datetime":
            options = {
                "date": {"date_only": True},
                "time": {"time_only": True},
                "full_date": {"format": "d MMMM yyyy"},
            }.get(options, {})
            return (
                self.env["ir.qweb.field.datetime"]
                .with_context(lang=lang)
                .value_to_html(value, options)
            )
        if field_type == "date":
            options = {"format": "d MMMM yyyy"} if options == "full" else {}
            return (
                self.env["ir.qweb.field.date"]
                .with_context(lang=lang)
                .value_to_html(value, options)
            )
        if field_type == "binary":
            return self.env["ir.qweb.field.image"].value_to_html(value, {})
        if isinstance(value, int):
            return self.env["ir.qweb.field.integer"].value_to_html(value, {})
        if isinstance(value, float):
            return self.env["ir.qweb.field.float"].value_to_html(
                value, {"precision": 2}
            )
        return escape(str(value))

    def _get_value_for_field(self, record, field_found, orm_fields, lang):
        """Former entry point, kept for modules overriding the rendering."""
        path, _sep, option = field_found.partition("::")
        return self.with_context(lang=lang)._resolve_placeholder(
            record, path.strip(), option.strip()
        )

    @api.model
    def _convert_tout_to_brackets(self, content):
        """Rewrite native ``<t t-out>`` placeholders as ``[[path]]``.

        The HTML sanitizer of document lines drops ``<t>`` elements, the
        bracket syntax survives it.
        """
        if not content:
            return content
        return TOUT_RE.sub(lambda m: f"[[{m.group(1).strip()}]]", str(content))

    def unlink(self):
        # Lines following these texts would print nothing once they are gone;
        # personalised lines keep their own content and become free texts.
        self.env["text.element.custom"].search(
            [("text_element_id", "in", self.ids), ("is_personalized", "=", False)]
        ).unlink()
        return super().unlink()
