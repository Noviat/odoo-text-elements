# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models

FIELD_TYPES = [(key, key) for key in sorted(fields.Field.by_type)]


class IrModel(models.Model):
    _inherit = "ir.model"

    can_be_used_with_text_elements = fields.Boolean()
