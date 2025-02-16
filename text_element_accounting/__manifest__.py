# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Text Elements - Accounting module",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat, Elneo",
    "website": "https://github.com/jdideren/odoo-text-elements",
    "category": "Accounting",
    "summary": "Text Elements - Accounting module",
    "depends": ["text_element_base", "account"],
    "data": [
        "views/account_move_views.xml",
        "views/invoice_report.xml",
    ],
    "installable": True,
    "post_init_hook": "_enable_text_element_on_aml",
}
