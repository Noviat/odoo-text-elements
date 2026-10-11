# Copyright 2009 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Text Elements - Base module",
    "version": "19.0.2.0.0",
    "license": "AGPL-3",
    "author": "Noviat, Elneo",
    "website": "https://www.noviat.com/",
    "category": "Tools",
    "summary": "Text Elements - Base module",
    "depends": ["base", "web", "mail", "html_editor"],
    "data": [
        "security/text_element_security.xml",
        "security/ir.model.access.csv",
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
}
