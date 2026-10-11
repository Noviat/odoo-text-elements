# Copyright 2026 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api
from odoo.tools import SQL, sql

_logger = logging.getLogger(__name__)

LEGACY_PAIRS = "text_element_legacy_pairs"
BATCH = 1000


def _mark_personalized(cr):
    """Former custom texts copied from the catalogue are personalised lines."""
    cr.execute(
        """
        UPDATE text_element_custom
           SET is_personalized = TRUE, origin = 'manual'
         WHERE text_element_id IS NOT NULL
        """
    )
    _logger.info("text_element: %s custom texts marked as personalised", cr.rowcount)


def _text_element_models(env):
    abstract = env.registry["text.element.abstract"]
    return {
        name
        for name, model in env.registry.items()
        if not model._abstract and issubclass(model, abstract)
    }


def _legacy_pairs(env, model):
    """(record id, element id, element is automatic) not yet a line.

    Archived catalogue texts were hidden by the former Many2many: skipped.
    """
    env.cr.execute(
        SQL(
            """
            SELECT DISTINCT pair.res_id, pair.element_id, element."default"
              FROM %(pairs)s pair
              JOIN text_element element
                ON element.id = pair.element_id AND element.active
              JOIN %(doc_table)s doc ON doc.id = pair.res_id
             WHERE pair.model = %(model)s
               AND NOT EXISTS (
                    SELECT 1 FROM text_element_custom line
                     WHERE line.model = %(model)s
                       AND line.res_id = pair.res_id
                       AND line.text_element_id = pair.element_id
                   )
             ORDER BY pair.res_id
            """,
            pairs=SQL.identifier(LEGACY_PAIRS),
            doc_table=SQL.identifier(env[model]._table),
            model=model,
        )
    )
    return env.cr.fetchall()


def _create_lines(env, values):
    """Create a batch of lines; a line refused (e.g. company mismatch) is
    logged and skipped instead of aborting the upgrade.

    :return: number of skipped lines
    """
    Line = env["text.element.custom"]
    try:
        with env.cr.savepoint():
            Line.create(values)
            env.flush_all()
        return 0
    except Exception:  # pylint: disable=broad-except
        env.invalidate_all()
    skipped = 0
    for vals in values:
        try:
            with env.cr.savepoint():
                Line.create(vals)
                env.flush_all()
        except Exception as error:  # pylint: disable=broad-except
            env.invalidate_all()
            skipped += 1
            _logger.warning("text_element: line %s not migrated: %s", vals, error)
    return skipped


def _create_catalogue_lines(env):
    cr = env.cr
    if not sql.table_exists(cr, LEGACY_PAIRS):
        return
    cr.execute(
        SQL(
            "SELECT DISTINCT model, relation_table FROM %s",
            SQL.identifier(LEGACY_PAIRS),
        )
    )
    targets = _text_element_models(env)
    for model, relation_table in cr.fetchall():
        if model not in targets:
            continue
        values = [
            {
                "model": model,
                "res_id": res_id,
                "text_element_id": element_id,
                "origin": "auto" if is_default else "manual",
            }
            for res_id, element_id, is_default in _legacy_pairs(env, model)
        ]
        skipped = 0
        for start in range(0, len(values), BATCH):
            skipped += _create_lines(env, values[start : start + BATCH])
            env.invalidate_all()
        _logger.info(
            "text_element: %s catalogue lines created on %s, %s skipped",
            len(values) - skipped,
            model,
            skipped,
        )
        # The field is computed now; its former table is an orphan.
        if not env[model]._fields["text_element_ids"].store:
            cr.execute(SQL("DROP TABLE IF EXISTS %s", SQL.identifier(relation_table)))
    cr.execute(SQL("DROP TABLE %s", SQL.identifier(LEGACY_PAIRS)))


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    _mark_personalized(cr)
    _create_catalogue_lines(env)
