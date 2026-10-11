# Copyright 2009 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Text Elements - Sale",
    "version": "18.0.3.0.0",
    "license": "AGPL-3",
    "author": "Noviat, Elneo",
    "website": "https://www.noviat.com/",
    "category": "Sales",
    "summary": "Text elements on quotations and sales orders",
    "depends": ["text_element_base", "sale"],
    "data": [
        "views/sale_order_report.xml",
        "views/sale_order_views.xml",
    ],
    "images": ["static/description/banner.png"],
    "installable": True,
}
