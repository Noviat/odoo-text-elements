# Copyright 2009 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Text Elements",
    "version": "20.0.1.1.0",
    "license": "AGPL-3",
    "author": "Noviat, Elneo",
    "website": "https://www.noviat.com/",
    "category": "Tools",
    "summary": "Notices, clauses and messages on PDF documents, no developer needed",
    "depends": ["base", "web", "mail", "html_editor"],
    "data": [
        "security/text_element_security.xml",
        "security/ir.access.csv",
        "views/menus.xml",
        "views/ir_model_views.xml",
        "views/report_templates.xml",
        "views/text_element_views.xml",
        "views/text_element_custom_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "text_element_base/static/src/**/*",
        ],
    },
    "images": ["static/description/banner.png"],
}
