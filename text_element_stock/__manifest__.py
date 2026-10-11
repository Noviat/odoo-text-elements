# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Text Elements - Stock module",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Inventory",
    "summary": "Print text elements on stock documents",
    "depends": ["text_element_base", "stock"],
    "data": [
        "views/stock_picking_views.xml",
        "views/stock_picking_report.xml",
    ],
    "installable": True,
}
