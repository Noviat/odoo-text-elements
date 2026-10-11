# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Text Elements - Purchase",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Purchases",
    "summary": "Text elements on requests for quotation and purchase orders",
    "depends": ["text_element_base", "purchase"],
    "data": [
        "views/purchase_order_views.xml",
        "views/purchase_order_report.xml",
    ],
    "images": ["static/description/banner.png"],
    "installable": True,
}
