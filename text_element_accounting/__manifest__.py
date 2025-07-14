# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Text Elements - Accounting module",
    "version": "18.0.2.1.0",
    "license": "AGPL-3",
    "author": "Noviat, Elneo",
    "website": "https://www.noviat.com/",
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
