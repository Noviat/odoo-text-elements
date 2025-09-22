# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class TextElement(models.AbstractModel):
    _name = "text.element.abstract"
    _description = "Text elements (Abstract)"

    text_element_ids = fields.Many2many(
        comodel_name="text.element",
        string="Text Elements",
        copy=True,
        compute="_compute_text_elements",
        store=True,
        readonly=False,
    )
    text_element_custom_ids = fields.One2many(
        comodel_name="text.element.custom",
        inverse_name="res_id",
        string="Custom Text Elements",
        copy=True,
    )

    def _compute_text_elements(self):
        for record in self:
            elements = self.env["text.element"].search(
                record._get_computed_elements_domain()
            )
            record.text_element_ids = elements

    def action_add_element_wizard(self):
        self.ensure_one()
        return {
            "name": self.env._("Add Text Element"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "add.text.element.wizard",
            "target": "new",
        }

    def _get_computed_elements_domain(self):
        self.ensure_one()
        domain = [
            ("default", "=", True),
            "|",
            ("model", "=", self._name),
            ("model", "=", False),
            "|",
            ("user_id", "=", False),
            ("user_id", "=", self.env.user.id),
        ]
        if "company_id" in self._fields:
            domain.append(("company_id", "in", (self.company_id.id, False)))
        return domain

    def _get_text_elements(self, position):
        self.ensure_one()
        text_elements, custom_text_elements = self._get_text_element_records(position)
        text_elements_list = []
        for element in text_elements:
            text_elements_list.append(element)
        for element in custom_text_elements:
            text_elements_list.append(element)
        return sorted(text_elements_list, key=lambda e: e.sequence)

    def _get_text_element_records(self, position):
        text_elements = self.text_element_ids.filtered(lambda r: r.position == position)
        custom_text_elements = self.text_element_custom_ids.filtered(
            lambda r: r.position == position
        )
        text_elements = self._get_text_element_records_filter_domain(text_elements)
        custom_text_elements = self._get_text_element_records_filter_domain(
            custom_text_elements
        )
        text_elements = self._get_text_element_records_context_params(text_elements)
        custom_text_elements = self._get_text_element_records_context_params(
            custom_text_elements
        )
        return text_elements, custom_text_elements

    def _get_text_element_records_filter_domain(self, text_elements):
        if text_elements._name == "text.element":
            new_text_elements = self.env["text.element"]
        else:
            new_text_elements = self.env["text.element.custom"]
        for text_element in text_elements:
            if text_element.filter_domain:
                domain = safe_eval(text_element.filter_domain)
                record = self.sudo().filtered_domain(domain)
                if record:
                    new_text_elements |= text_element
            else:
                new_text_elements |= text_element
        return new_text_elements

    def _get_text_element_records_context_params(self, text_elements):
        if text_elements._name == "text.element":
            new_text_elements = self.env["text.element"]
        else:
            new_text_elements = self.env["text.element.custom"]
        for text_element in text_elements:
            if text_element.context_params:
                element_valid = True
                for context_param in text_element.context_params.split(";"):
                    not_context = False
                    context = context_param
                    if context_param.startswith("!"):
                        not_context = True
                        context = context_param[1:]
                    if not_context and self.env.context.get(context, False):
                        element_valid = False
                    if not not_context and not self.env.context.get(context, False):
                        element_valid = False
                if element_valid:
                    new_text_elements |= text_element
            else:
                new_text_elements |= text_element
        return new_text_elements
