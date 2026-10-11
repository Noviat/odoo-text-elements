# Copyright 2009 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class IrModel(models.Model):
    _inherit = "ir.model"

    can_be_used_with_text_elements = fields.Boolean(
        compute="_compute_can_be_used_with_text_elements",
        inverse="_inverse_can_be_used_with_text_elements",
        search="_search_can_be_used_with_text_elements",
        help="The model inherits text.element.abstract.",
    )

    def _get_text_element_models(self):
        abstract = self.env.registry["text.element.abstract"]
        return [
            name
            for name, model in self.env.registry.items()
            if not model._abstract and issubclass(model, abstract)
        ]

    def _compute_can_be_used_with_text_elements(self):
        models_ = set(self._get_text_element_models())
        for record in self:
            record.can_be_used_with_text_elements = record.model in models_

    def _inverse_can_be_used_with_text_elements(self):
        # Derived from the code since 18.0.3.0.0; modules that still set it
        # in a hook keep working.
        return

    def _search_can_be_used_with_text_elements(self, operator, value):
        if operator not in ("=", "!="):
            return NotImplemented
        positive = (operator == "=") == bool(value)
        return [
            ("model", "in" if positive else "not in", self._get_text_element_models())
        ]
