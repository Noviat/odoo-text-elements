# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Text Elements - Sale module",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat, Elneo",
    "website": "https://github.com/jdideren/odoo-text-elements",
    "category": "Sales",
    "summary": "Text Elements - Sale module",
    "depends": ["text_element_base", "sale"],
    "data": [
        "views/sale_order_report.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
}
