# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Text Elements - Base module",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat, Elneo",
    "website": "https://github.com/jdideren/odoo-text-elements",
    "category": "Tools",
    "summary": "Text Elements - Base module",
    "depends": ["base", "web"],
    "data": [
        "security/ir.model.access.csv",
        "security/text_element_security.xml",
        "views/menus.xml",
        "views/report_templates.xml",
        "views/text_element_views.xml",
        "views/text_element_custom_views.xml",
        "wizards/add_text_element_wizard.xml",
        "wizards/edit_sale_element_wizard_view.xml",
    ],
    "installable": True,
}
