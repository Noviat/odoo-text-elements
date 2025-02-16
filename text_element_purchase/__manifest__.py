# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Text Elements - Purchase module",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat, Elneo",
    "website": "https://github.com/jdideren/odoo-text-elements",
    "category": "Purchases",
    "summary": "Text Elements - Purchases module",
    "depends": ["text_element_base", "purchase"],
    "data": [
        "views/purchase_order_views.xml",
        "views/purchase_order_templates.xml",
        "views/purchase_quotation_templates.xml",
    ],
    "installable": True,
    "post_init_hook": "_enable_text_element_on_purchase",
}
