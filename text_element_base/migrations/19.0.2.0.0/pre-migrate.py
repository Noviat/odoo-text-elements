# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo.tools import SQL, sql

_logger = logging.getLogger(__name__)

LEGACY_PAIRS = "text_element_legacy_pairs"


def _snapshot_legacy_pairs(cr):
    """Copy the rows behind the former stored ``text_element_ids``.

    The field of text.element.abstract becomes computed; the end script turns
    each copied pair into a document line. Other models may own an unrelated
    ``text_element_ids``: their tables are copied too but left untouched, and
    the end script ignores them (only then is the registry complete).
    """
    cr.execute(
        """
        SELECT model, relation_table, column1, column2
          FROM ir_model_fields
         WHERE name = 'text_element_ids'
           AND ttype = 'many2many'
           AND store
           AND relation_table IS NOT NULL
        """
    )
    rows = cr.fetchall()
    cr.execute(
        SQL(
            """
            CREATE TABLE IF NOT EXISTS %s (
                model varchar,
                relation_table varchar,
                res_id integer,
                element_id integer
            )
            """,
            SQL.identifier(LEGACY_PAIRS),
        )
    )
    # Odoo commits after each module of an upgrade: when a later module fails,
    # this script runs again on the next attempt. The source tables are never
    # modified, so start the copy over.
    cr.execute(SQL("TRUNCATE %s", SQL.identifier(LEGACY_PAIRS)))
    for model, table, col_record, col_element in rows:
        if not sql.table_exists(cr, table):
            continue
        cr.execute(
            SQL(
                """
                INSERT INTO %(pairs)s
                SELECT %(model)s, %(table_name)s, %(col_record)s, %(col_element)s
                  FROM %(table)s
                """,
                pairs=SQL.identifier(LEGACY_PAIRS),
                model=model,
                table_name=table,
                col_record=SQL.identifier(col_record),
                col_element=SQL.identifier(col_element),
                table=SQL.identifier(table),
            )
        )
        _logger.info("text_element: %s pairs copied from %s", cr.rowcount, table)


def _drop_former_views(cr):
    """Delete views whose structure changed.

    The former document views of text.element.custom extended the catalogue
    views, and the former simplified catalogue list called methods that are
    gone: reloading the catalogue views would validate those old extensions
    and fail. Children go with them (inherit_id
    cascades); the data files recreate what is still defined.
    """
    cr.execute(
        """
        DELETE FROM ir_ui_view
         WHERE id IN (
                SELECT res_id FROM ir_model_data
                 WHERE module = 'text_element_base'
                   AND model = 'ir.ui.view'
                   AND name IN (
                        'text_element_simplified_form_view',
                        'text_element_simplified_list_view',
                        'text_element_custom_form_view',
                        'text_element_custom_list_view',
                        'text_element_custom_simplified_form_view',
                        'text_element_custom_simplified_list_view',
                        'add_text_element_wizard_form_view'
                   )
               )
        """
    )
    _logger.info("text_element: %s former views deleted", cr.rowcount)
    cr.execute(
        """
        DELETE FROM ir_model_data imd
         WHERE imd.module = 'text_element_base'
           AND imd.model = 'ir.ui.view'
           AND NOT EXISTS (SELECT 1 FROM ir_ui_view v WHERE v.id = imd.res_id)
        """
    )


def _column_type(cr, table, column):
    cr.execute(
        """
        SELECT data_type FROM information_schema.columns
         WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    row = cr.fetchone()
    return row and row[0]


def _drop_archived_custom_texts(cr):
    """Document lines have no ``active`` field: archived ones would print."""
    if _column_type(cr, "text_element_custom", "active") is None:
        return
    cr.execute("DELETE FROM text_element_custom WHERE active IS FALSE")
    _logger.info("text_element: %s archived custom texts deleted", cr.rowcount)


def _collapse_translations(cr):
    """Keep the document partner's language in the custom texts.

    ``name`` and ``content`` of document lines stop being translatable, and
    Odoo then keeps the en_US value. A text adapted for one document is
    written in its customer's language: put that value under en_US first.

    Plain SQL: the models of the modules depending on this one are not in
    the registry yet when pre scripts run.
    """
    cr.execute("SELECT DISTINCT model FROM text_element_custom WHERE model IS NOT NULL")
    for (model,) in cr.fetchall():
        table = model.replace(".", "_")
        if not sql.column_exists(cr, table, "partner_id"):
            continue
        for column in ("name", "content"):
            if _column_type(cr, "text_element_custom", column) != "jsonb":
                continue
            cr.execute(
                SQL(
                    """
                    UPDATE text_element_custom line
                       SET %(col)s = jsonb_set(
                               line.%(col)s, '{en_US}', line.%(col)s -> partner.lang
                           )
                      FROM %(table)s doc
                      JOIN res_partner partner ON partner.id = doc.partner_id
                     WHERE line.model = %(model)s
                       AND line.res_id = doc.id
                       AND partner.lang IS NOT NULL
                       AND line.%(col)s ? partner.lang
                    """,
                    col=SQL.identifier(column),
                    table=SQL.identifier(table),
                    model=model,
                )
            )
            _logger.info(
                "text_element: %s custom %s kept in partner language for %s",
                cr.rowcount,
                column,
                model,
            )


def migrate(cr, version):
    if not version:
        return
    _snapshot_legacy_pairs(cr)
    _drop_former_views(cr)
    _drop_archived_custom_texts(cr)
    _collapse_translations(cr)
