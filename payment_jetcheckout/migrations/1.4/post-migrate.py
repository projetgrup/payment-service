# -*- coding: utf-8 -*-
def migrate(cr, version):
    cr.execute(
        """
        UPDATE payment_transaction AS pt SET
        jetcheckout_installment_description = vals.installment
        FROM (
            SELECT id, jetcheckout_installment_count::text AS installment
            FROM payment_transaction
        ) vals
        WHERE vals.id = pt.id
        """,
    )
