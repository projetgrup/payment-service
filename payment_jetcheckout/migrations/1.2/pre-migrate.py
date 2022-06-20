# -*- coding: utf-8 -*-
import logging
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not column_exists(cr, "payment_acquirer_jetcheckout_journal", "name"):
        cr.execute(
            """
            ALTER TABLE payment_acquirer_jetcheckout_journal
            ADD COLUMN name varchar
            """,
        )

    try:
        cr.execute(
            """
            SELECT journal.id, pos.name
            FROM payment_acquirer_jetcheckout_journal journal
            LEFT JOIN payment_acquirer_jetcheckout_pos pos ON pos.id = journal.pos_id
            """
        )
        result = cr.dictfetchall()
        values = []
        for res in result:
            values.append(f"""({res['id']}, '{res['name']}'""")
        if values:
            query = [
                """
                UPDATE payment_acquirer_jetcheckout_journal AS journal SET
                name = vals.name
                FROM (VALUES 
                """
            ]
            query.append(",".join(values))
            query.append(""") AS vals(id, name) WHERE vals.id = journal.id""")
            cr.execute("".join(query))

    except Exception as e:
        _logger.error(str(e))
        raise
