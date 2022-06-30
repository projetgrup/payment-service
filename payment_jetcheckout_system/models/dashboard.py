# -*- coding: utf-8 -*-
import json
import random
import ast

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools.misc import formatLang


class PaymentDasboard(models.Model):
    _name = 'payment.dashboard'
    _description = 'Payment Dashboard'
    _order = 'sequence'

    def _compute_data(self):
        for dashboard in self:
            dashboard.data = json.dumps(dashboard._get_data())

    def _compute_graph(self):
        for dashboard in self:
            dashboard.graph = json.dumps(dashboard._get_graph())

    name = fields.Char(translate=True, required=True)
    code = fields.Char(required=True)
    period = fields.Selection([('hours', 'Hour'), ('days', 'Day'), ('weeks', 'Week'), ('months', 'Month'), ('years', 'Year')], required=True)
    offset = fields.Integer()
    limit = fields.Integer(default=1)
    sequence = fields.Integer(default=16)
    data = fields.Text(compute='_compute_data')
    graph = fields.Text(compute='_compute_graph')
    graph_type = fields.Selection([('bar', 'Bar'), ('line', 'Line')], default='bar', required=True)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        raise UserError(_('You cannot group dashboard items'))

    def _get_data(self):
        currencies = self.env['res.currency'].sudo().browse
        is_sample_data = self.graph and any(data.get('is_sample_data', False) for data in json.loads(self.graph))
        lines = self._get_domain_query()

        success_count = 0
        total_count = 0
        advance_count = 0

        for line in lines:
            success_count += line['success_count']
            advance_count += line['advance_count']
            total_count += line['total_count']
            average_amount = line['success_amount'] / line['success_count'] if line['success_count'] > 0 else 0
            currency = currencies(line['currency_id'])
            line['total_amount'] = formatLang(self.env, line['total_amount'], currency_obj=currency)
            line['success_amount'] = formatLang(self.env, line['success_amount'], currency_obj=currency)
            line['average_amount'] = formatLang(self.env, average_amount, currency_obj=currency)

        success_rate = int(100 * success_count / total_count) if total_count > 0 else 0
        advance_rate = int(100 * advance_count / success_count) if success_count > 0 else 0

        return {
            'lines': lines,
            'graph_type': self.graph_type,
            'success_rate': f'%{success_rate}',
            'advance_rate': f'%{advance_rate}',
            'is_sample_data': is_sample_data,
        }

    def _get_graph(self):
        now = fields.Datetime.now()
        if self.period == 'days':
            datas = [
                {'label': '00:00 - 03:59', 'value': 0.0, 'type': 'past'},
                {'label': '04:00 - 07:59', 'value': 0.0, 'type': 'past'},
                {'label': '08:00 - 11:59', 'value': 0.0, 'type': 'past'},
                {'label': '12:00 - 15:59', 'value': 0.0, 'type': 'past'},
                {'label': '16:00 - 19:59', 'value': 0.0, 'type': 'past'},
                {'label': '20:00 - 23:59', 'value': 0.0, 'type': 'past'},
            ]
            period = 'hours'
            interval = 4
            format = DTF
        elif self.period == 'weeks':
            datas = [
                {'label': _('Monday'), 'value': 0.0, 'type': 'past'},
                {'label': _('Tuesday'), 'value': 0.0, 'type': 'past'},
                {'label': _('Wednesday'), 'value': 0.0, 'type': 'past'},
                {'label': _('Thursday'), 'value': 0.0, 'type': 'past'},
                {'label': _('Friday'), 'value': 0.0, 'type': 'past'},
                {'label': _('Saturday'), 'value': 0.0, 'type': 'past'},
                {'label': _('Sunday'), 'value': 0.0, 'type': 'past'},
            ]
            period = 'days'
            interval = 1
            format = DF
        elif self.period == 'months':
            datas = [
                {'label': _('Week 1'), 'value': 0.0, 'type': 'past'},
                {'label': _('Week 2'), 'value': 0.0, 'type': 'past'},
                {'label': _('Week 3'), 'value': 0.0, 'type': 'past'},
                {'label': _('Week 4'), 'value': 0.0, 'type': 'past'},
                {'label': _('Week 5'), 'value': 0.0, 'type': 'past'},
            ]
            period = 'days'
            interval = 7
            format = DF
        elif self.period == 'years':
            datas = [
                {'label': _('January'), 'value': 0.0, 'type': 'past'},
                {'label': _('February'), 'value': 0.0, 'type': 'past'},
                {'label': _('March'), 'value': 0.0, 'type': 'past'},
                {'label': _('April'), 'value': 0.0, 'type': 'past'},
                {'label': _('May'), 'value': 0.0, 'type': 'past'},
                {'label': _('June'), 'value': 0.0, 'type': 'past'},
                {'label': _('July'), 'value': 0.0, 'type': 'past'},
                {'label': _('August'), 'value': 0.0, 'type': 'past'},
                {'label': _('September'), 'value': 0.0, 'type': 'past'},
                {'label': _('October'), 'value': 0.0, 'type': 'past'},
                {'label': _('November'), 'value': 0.0, 'type': 'past'},
                {'label': _('December'), 'value': 0.0, 'type': 'past'},
            ]
            period = 'months'
            interval = 1
            format = DF
        else:
            raise UserError(_('This time period is not implemented'))
            
        template = """
            SELECT %s AS line, COUNT(id) AS count, SUM(amount) AS amount
            FROM payment_transaction
            WHERE state = 'done'
            AND company_id = %s
        """
        query = []
        index = 0
        length = len(datas)
        company = self.env.company.id
        date_first, date_last = self._get_dates()
        date_first = datetime.combine(date_first, datetime.min.time())
        date_last = datetime.combine(date_last, datetime.min.time())
        for i in range(0, length):
            date_start = date_first + relativedelta(**{period: i * interval})
            if i == length - 1:
                date_end = date_last
            else:
                date_end = date_start + relativedelta(**{period: interval})

            if date_start <= now < date_end:
                index = i

            query.append("(" + template % (i, company) + " AND create_date >= '" + date_start.strftime(format) + "' AND create_date < '" + date_end.strftime(format) + "')")

        self.env.cr.execute(" UNION ALL ".join(query))
        result = self.env.cr.dictfetchall()

        count = 0
        for i in range(0, length):
            count += result[i]['count']
            datas[i]['value'] = result[i]['amount']
            if index == i:
                datas[i]['type'] = 'future'

        graph_key = _('Amount')
        is_sample_data = count == 0
        if is_sample_data:
            graph_key = _('Sample Amount')
            for i in range(0, length):
                datas[i]['type'] = 'o_sample_data'
                datas[i]['value'] = random.randint(0, 20)

        return [{'values': datas, 'title': _('Transactions'), 'key': graph_key, 'is_sample_data': is_sample_data}]

    def _get_dates(self):
        today = fields.Date.today()
        start = self.offset
        end = start - self.limit
        if self.period == 'days':
            vals_start = {'days': start}
            vals_end = {'days': end}
        elif self.period == 'weeks':
            vals_start = {'weekday': 0, 'weeks': start + 1}
            vals_end = {'weekday':0, 'weeks': end + 1}
        elif self.period == 'months':
            vals_start = {'day': 1, 'months': start}
            vals_end = {'day': 1, 'months': end}
        elif self.period == 'years':
            vals_start = {'day': 1, 'month': 1, 'years': start}
            vals_end = {'day': 1, 'month': 1, 'years': end}
        else:
            raise UserError(_('This time period is not implemented'))
        date_start = today - relativedelta(**vals_start)
        date_end = today - relativedelta(**vals_end)
        return date_start, date_end

    def _get_domain(self):
        date_start, date_end = self._get_dates()
        company = self.env.company.id
        return [('company_id', '=', company), ('create_date', '>=', date_start), ('create_date', '<', date_end), ('state', 'in', ('done', 'pending', 'error'))]

    def _get_domain_query(self):
        date_start, date_end = self._get_dates()
        company = self.env.company.id
        query = """
            SELECT
                COUNT(*) AS total_count,
                SUM(t.amount) AS total_amount,
                AVG(t.amount) AS average_amount,
                SUM(CASE WHEN t.state = 'done' THEN 1 ELSE 0 END) AS success_count,
                SUM(CASE WHEN t.state = 'done' THEN t.amount ELSE 0 END) AS success_amount,
                SUM(CASE WHEN t.jetcheckout_installment_count = 1 AND t.state = 'done' THEN 1 ELSE 0 END) AS advance_count,
                c.name AS currency_name,
                c.id AS currency_id
            FROM payment_transaction t
            LEFT JOIN res_currency c ON t.currency_id = c.id
            WHERE t.state IN ('done', 'pending', 'error')
            AND t.create_date >= %s
            AND t.create_date < %s
            AND t.company_id = %s
            GROUP BY c.name, c.id
        """
        self.env.cr.execute(query, (date_start, date_end, company))
        return self.env.cr.dictfetchall()

    def action_transactions(self):
        action = self.env.ref('payment_jetcheckout_system.action_transaction').sudo().read()[0]
        action['domain'] = self._get_domain()
        return action

    def action_success_transactions(self):
        action = self.action_transactions()
        action['domain'].append(('state', '=', 'done'))
        return action

    def action_failed_transactions(self):
        action = self.action_transactions()
        action['domain'].append(('state', 'in', ('pending', 'error')))
        return action

    def action_pos_distribution(self):
        action = self.action_transactions()
        action['domain'].append(('state', '=', 'done'))
        action['view_mode'] = 'pivot,list,graph,kanban,form'
        action['views'] = []
        context = ast.literal_eval(action['context']) if action['context'] else {}
        context['group_by'] = 'jetcheckout_vpos_name'
        action['context'] = context
        return action
