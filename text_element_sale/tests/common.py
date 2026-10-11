# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TextElementSaleCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.TextElement = cls.env["text.element"]
        cls.sale_model = cls.env["ir.model"]._get("sale.order")
        cls.partner_be = cls.env["res.partner"].create(
            {"name": "Client BE", "country_id": cls.env.ref("base.be").id}
        )
        cls.partner_nl = cls.env["res.partner"].create(
            {"name": "Client NL", "country_id": cls.env.ref("base.nl").id}
        )
        cls.team = cls.env["crm.team"].create({"name": "Text elements tests"})
        # Isolate the tests from texts already configured in the database.
        cls.TextElement.search([("default", "=", True)]).write({"default": False})
        cls.auto_all = cls._element("Automatic for all", default=True)
        cls.auto_be = cls._element(
            "Automatic for Belgium",
            default=True,
            filter_domain="[('partner_id.country_id.code', '=', 'BE')]",
        )
        cls.manual = cls._element("Manual", position="after")

    @classmethod
    def _element(cls, name, **vals):
        return cls.TextElement.create(
            dict(
                {
                    "name": name,
                    "model_id": cls.sale_model.id,
                    "content": f"<p>{name} for [[partner_id.name]]</p>",
                    "position": "after_line",
                },
                **vals,
            )
        )

    def _order(self, partner=None):
        return self.env["sale.order"].create(
            {"partner_id": (partner or self.partner_be).id, "team_id": self.team.id}
        )
