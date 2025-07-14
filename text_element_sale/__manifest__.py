# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Text Elements - Sale module",
    "version": "18.0.2.1.0",
    "license": "AGPL-3",
    "author": "Noviat, Elneo",
    "website": "https://www.noviat.com/",
    "category": "Sales",
    "summary": "Text Elements - Sale module",
    "depends": ["text_element_base", "sale"],
    "data": [
        "views/sale_order_report.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "post_init_hook": "_enable_text_element_on_sale",
}
