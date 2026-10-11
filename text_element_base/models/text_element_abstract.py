# Copyright 2009 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.fields import Command


class TextElementAbstract(models.AbstractModel):
    """Give a model a list of texts printed on its reports.

    ``text_element_custom_ids`` is that list. ``text_element_ids`` only
    exposes the catalogue texts a document follows, for code written against
    the former Many2many.
    """

    _name = "text.element.abstract"
    _description = "Text elements (Abstract)"

    text_element_custom_ids = fields.One2many(
        comodel_name="text.element.custom",
        inverse_name="res_id",
        string="Text Elements",
        copy=True,
    )
    text_element_ids = fields.Many2many(
        comodel_name="text.element",
        string="Catalogue Text Elements",
        compute="_compute_text_elements",
        inverse="_inverse_text_elements",
    )

    @api.depends(
        "text_element_custom_ids.text_element_id",
        "text_element_custom_ids.is_personalized",
    )
    def _compute_text_elements(self):
        for record in self:
            record.text_element_ids = record._get_catalogue_lines().text_element_id

    def _inverse_text_elements(self):
        for record in self:
            lines = record._get_catalogue_lines()
            wanted = record.text_element_ids
            present = lines.text_element_id
            lines.filtered(
                lambda line, wanted=wanted: line.text_element_id not in wanted
            ).unlink()
            record._add_text_element_lines(wanted - present, "manual")

    def _get_catalogue_lines(self):
        self.ensure_one()
        return self.text_element_custom_ids.filtered(
            lambda line: line.text_element_id and not line.is_personalized
        )

    # ------------------------------------------------------------------
    # Lines creation
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._set_text_element_line_model(vals)
        records = super().create(vals_list)
        if not self.env.context.get("skip_text_element_defaults"):
            records._apply_default_text_elements()
        return records

    def write(self, vals):
        self._set_text_element_line_model(vals)
        res = super().write(vals)
        triggers = self._text_element_default_triggers()
        if triggers & vals.keys() and not self.env.context.get(
            "skip_text_element_defaults"
        ):
            self._apply_default_text_elements()
        return res

    def _set_text_element_line_model(self, vals):
        """Lines created through the One2many only receive ``res_id``."""
        commands = vals.get("text_element_custom_ids")
        if not commands:
            return
        new_commands = []
        for command in commands:
            if command[0] == Command.CREATE:
                values = dict(command[2] or {}, model=self._name)
                command = (Command.CREATE, command[1], values)
            new_commands.append(command)
        vals["text_element_custom_ids"] = new_commands

    def _add_text_element_lines(self, elements, origin):
        self.ensure_one()
        if not elements:
            return self.env["text.element.custom"]
        return self.env["text.element.custom"].create(
            [
                {
                    "model": self._name,
                    "res_id": self.id,
                    "text_element_id": element.id,
                    "origin": origin,
                }
                for element in elements
            ]
        )

    # ------------------------------------------------------------------
    # Automatic texts
    # ------------------------------------------------------------------

    def _text_element_default_triggers(self):
        """Fields whose change re-applies the automatic texts."""
        return {name for name in ("partner_id", "company_id") if name in self._fields}

    def _get_computed_elements_domain(self):
        self.ensure_one()
        today = fields.Date.context_today(self)
        domain = [
            ("default", "=", True),
            ("model", "in", (self._name, False)),
            ("user_id", "in", (self.env.user.id, False)),
            "|",
            ("date_to", "=", False),
            ("date_to", ">=", today),
        ]
        if "company_id" in self._fields:
            domain.append(("company_id", "in", (self.company_id.id, False)))
        return domain

    def _apply_default_text_elements(self):
        """Merge the automatic texts into the documents.

        Adds the automatic texts a document lacks and removes the untouched
        automatic lines that no longer apply. Lines added by hand or
        personalised are never removed.

        :return: (number of lines added, number of lines removed)
        """
        added = removed = 0
        TextElement = self.env["text.element"]
        for record in self:
            wanted = TextElement.search(record._get_computed_elements_domain())
            present = record.text_element_custom_ids.text_element_id
            stale = record.text_element_custom_ids.filtered(
                lambda line, wanted=wanted: line.origin == "auto"
                and not line.is_personalized
                and line.text_element_id not in wanted
            )
            removed += len(stale)
            stale.unlink()
            added += len(record._add_text_element_lines(wanted - present, "auto"))
        return added, removed

    def action_reapply_default_text_elements(self):
        added, removed = self._apply_default_text_elements()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "info",
                "message": self.env._(
                    "%(added)s text(s) added, %(removed)s removed.",
                    added=added,
                    removed=removed,
                ),
                "next": {"type": "ir.actions.client", "tag": "soft_reload"},
            },
        }

    def action_reload_default_text_elements(self):
        # Former name, kept for views of client modules.
        return self.action_reapply_default_text_elements()

    # ------------------------------------------------------------------
    # Add from catalogue
    # ------------------------------------------------------------------

    def get_text_element_catalogue_domain(self):
        """Domain of the catalogue texts that can still be added."""
        self.ensure_one()
        today = fields.Date.context_today(self)
        domain = [
            ("model", "in", (self._name, False)),
            ("id", "not in", self.text_element_custom_ids.text_element_id.ids),
            "|",
            ("date_to", "=", False),
            ("date_to", ">=", today),
        ]
        if "company_id" in self._fields:
            domain.append(("company_id", "in", (self.company_id.id, False)))
        return domain

    def action_add_element_wizard(self):
        # Former "Add Existing Text Element" button, still in client views.
        self.ensure_one()
        return {
            "type": "ir.actions.client",
            "tag": "text_element_add_from_catalogue",
            "params": {"res_model": self._name, "res_id": self.id},
        }

    def action_add_text_elements(self, element_ids):
        self.ensure_one()
        elements = self.env["text.element"].browse(element_ids).exists()
        present = self.text_element_custom_ids.text_element_id
        self._add_text_element_lines(elements - present, "manual")
        return True

    # ------------------------------------------------------------------
    # Report
    # ------------------------------------------------------------------

    def _get_text_elements(self, position):
        """Lines of ``position`` to print, in their order."""
        self.ensure_one()
        lines = self.text_element_custom_ids.filtered(
            lambda line: line.position == position and line._is_printable(self)
        )
        return lines.sorted(lambda line: (line.sequence, line.id))
