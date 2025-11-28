# -*- coding: utf-8 -*-
import json
import base64
import logging
import re
import secrets
import string
import traceback
import time
import uuid
from collections import OrderedDict
from urllib.parse import unquote, urlparse, quote

from datetime import datetime
from odoo import _, fields
from odoo import http
from odoo.http import route, request
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round
from odoo.tools.mimetypes import guess_mimetype
from odoo.addons.portal.controllers import portal
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as Controller
from odoo.addons.base.models.res_bank import sanitize_account_number

_logger = logging.getLogger(__name__)


class CustomerPortal(portal.CustomerPortal):

    @route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kwargs):
        system = kwargs.get('system', request.env.company.system)
        if system == 'escrow':
            return request.redirect('/my/ads')
        return super().home(**kwargs)


class PayloxSystemEscrowController(Controller):

    @http.route('/payment/escrow/transaction-data', type='json', auth='user', methods=['POST'])
    def get_transaction_data(self, product_id=None, status=None, **kwargs):
        try:
            company = request.env.company
            if not product_id:
                return {'error': 'No ad ID provided'}

            if status == 'success':
                status = 'done'
            elif status == 'partial':
                status = 'done'
            payment_item = request.env['payment.item'].sudo().search([('ad_id', '=', int(product_id))], limit=1)
            if not payment_item.exists():
                return {'error': 'Payment item not found'}

            transactions = payment_item.transaction_ids.filtered(lambda tx: tx.state == status and tx.system == 'escrow').sorted(key='create_date', reverse=True)
            total_amount = payment_item.amount
            paid_amount = payment_item.paid_amount
            remaining_amount = payment_item.residual_amount

            transaction_list = []
            for tx in transactions:
                receipt_url = None
                if tx.conveyance_attachment_id and tx.jetcheckout_order_id:
                    receipt_url = f"/payment/escrow/attachment/{tx.conveyance_attachment_id.id}/download?token={tx.jetcheckout_order_id}"

                transaction_list.append({
                    'id': tx.id,
                    'reference': tx.reference,
                    'amount': tx.amount,
                    'date': tx.create_date.isoformat() if tx.create_date else '',
                    'status': tx.state,
                    'message': tx.state_message,
                    'payment_method': tx.acquirer_id.name if tx.acquirer_id else 'Unknown',
                    'different_holder': tx.jetcheckout_different_card_holder,
                    'order_id': tx.jetcheckout_order_id if company.conveyance_show_link else None,
                    'receipt_url': receipt_url,
                    'conveyance_attachment': {
                        'name': tx.conveyance_attachment_id.name or '',
                        'mimetype': tx.conveyance_attachment_id.mimetype if tx.conveyance_attachment_id else '',
                        'data': tx.conveyance_attachment_id.datas.decode('utf-8') if tx.conveyance_attachment_id else '',
                    } if tx.conveyance_attachment_id else None,
                    'conveyance_file_name': tx.conveyance_attachment_id.name if tx.conveyance_attachment_id else None,
                    'conveyance_upload_date': tx.conveyance_upload_date if tx.conveyance_upload_date else None,
                })
            different_holder_txs = payment_item.transaction_ids.filtered(lambda tx: tx.jetcheckout_different_card_holder).sorted('create_date', reverse=True)
            
            result = {
                'total_amount': total_amount,
                'previous_amount': paid_amount,
                'remaining_amount': remaining_amount,
                'paid': payment_item.paid,
                'transactions': transaction_list,
                'paid_date': payment_item.paid_date.strftime('%d.%m.%Y') if payment_item.paid_date else '',
                'currency': 'TL',
                'img': payment_item.ad_id.official_sale_document and 'data:%s;base64,%s' % (guess_mimetype(base64.b64decode(payment_item.ad_id.official_sale_document)), payment_item.ad_id.official_sale_document.decode('utf-8')) or '',
            }
            
            if different_holder_txs:
                latest_tx = different_holder_txs[0]
                result.update({
                    'different': latest_tx.jetcheckout_different_card_holder,
                    'different_holder': {
                        'name': latest_tx.jetcheckout_different_card_holder_id.name if latest_tx.jetcheckout_different_card_holder_id else '',
                        'vat': latest_tx.jetcheckout_different_card_holder_id.vat if latest_tx.jetcheckout_different_card_holder_id else '',
                        'phone': latest_tx.jetcheckout_different_card_holder_id.mobile if latest_tx.jetcheckout_different_card_holder_id else '',
                        'email': latest_tx.jetcheckout_different_card_holder_id.email if latest_tx.jetcheckout_different_card_holder_id else '',
                        'is_otp_verified': latest_tx.jetcheckout_different_card_holder_id.is_otp_verified if latest_tx.jetcheckout_different_card_holder_id else False,
                    }
                })
            else:
                result.update({
                    'different': False,
                    'different_holder': {
                        'name': '',
                        'vat': '',
                        'phone': '',
                        'email': '',
                    }
                })
            
            return result

        except Exception as e:
            _logger.error("Error in get_transaction_data: %s", str(e))
            return {'error': str(e)}

    def _generate_hash_url(self, step=0, id=0, owner=None, customer=None, status=None):
        values = {
            'i': id,
            's': step,
        }
        
        if owner is not None:
            values['o'] = owner
        if status is not None:
            values['t'] = status
        if customer is not None:
            values['c'] = customer
        _logger.error(values)
        hash_value = base64.b64encode(json.dumps(values).encode('utf-8')).decode('utf-8')
        return f'/my/ads?={quote(hash_value)}'

    def _process(self, **kwargs):
        url, tx, status = super()._process(**kwargs)
        #if status:
        #    return url, tx, status

        system = kwargs.get('system') or (tx and tx.system) or request.env.company.system
        if system == 'escrow':
            paylox_product_ids = request.env['payment.transaction.product'].sudo().browse(tx.paylox_product_ids.ids)
            ad_id = paylox_product_ids and paylox_product_ids.ad_id.id or 0
            owner = paylox_product_ids and paylox_product_ids.ad_id.owner_id.id or None
            escrow_customer_id = paylox_product_ids.ad_id.customer_ids
            customer = escrow_customer_id.filtered(lambda c: c.is_escrow_customer).id
            if tx.state == 'done':
                payment_items_paid = True
                if tx.paylox_transaction_item_ids:
                    for item_line in tx.paylox_transaction_item_ids:
                        payment_item = item_line.item_id
                        if payment_item:
                            if not payment_item.paid:
                                payment_items_paid = False
                                break

                ad_id = 0
                if tx.paylox_transaction_item_ids:
                    first_item = tx.paylox_transaction_item_ids[0]
                    if first_item.item_id and first_item.item_id.ad_id:
                        ad_id = first_item.item_id.ad_id.id

                if payment_items_paid:
                    url = self._generate_hash_url(step=5, id=ad_id, owner=owner, customer=customer, status='success')
                else:
                    url = self._generate_hash_url(step=5, id=ad_id, owner=owner, customer=customer, status='partial')
            else:
                url = self._generate_hash_url(step=5, id=ad_id, owner=owner, customer=customer, status='error')
        return url, tx, status

    def _get_tx_values(self, **kwargs):
        res = super()._get_tx_values(**kwargs)
        system = kwargs.get('system', request.env.company.system)
        if system == 'escrow':
            different = kwargs.get('different_holder', {}).get('different', False)
            if different:
                partner = request.env['res.partner'].sudo().search([('vat', '=', kwargs.get('different_holder', {}).get('vat', '')), ('paylox_escrow_type', '=', 'card_holder')], limit=1)
            products = kwargs.get('products', [])
            payment_items = request.env['payment.item'].sudo().search([('ad_id', 'in', products and [p['pid'] for p in products] or [])])
            res.update({
                'paylox_transaction_item_ids':[(0, 0, {
                        'item_id': rec.id,
                        'amount': kwargs.get('amount', 0.0),
                        'ref': rec.ref,
                        'date': rec.date,
                        'desc': rec.description,
                        'advance': rec.advance,
                    })
                    for rec in payment_items
                ],
                'jetcheckout_different_card_holder_id': partner.id if different and partner.exists() else None,
                'jetcheckout_different_card_holder': different,
                'jetcheckout_item_ids': [(6, 0, payment_items.ids)],
                'jetcheckout_approval_ok': True,
            })
            res.update({
                'paylox_product_ids': [(0, 0, {
                    'ad_id': product['pid'],
                    'qty': product['qty'],
                }) for product in products]})
        return res

    def _prepare_broker_installment_lines(self, partner, amount, currency, campaign=None):
        try:
            amount_value = float(amount or 0.0)
        except (TypeError, ValueError):
            return {'error': _('Invalid amount value.')}

        currency = currency or request.env.company.currency_id
        precision = currency.decimal_places or 2

        installment_data = self._prepare_installment(
            partner=partner.id,
            amount=amount_value,
            currency=currency.id,
            campaign=partner.campaign_id.name,
        )
        if not isinstance(installment_data, dict):
            return {'error': _('Unexpected response from installment service.')}

        if installment_data.get('error'):
            return {'error': installment_data['error']}

        additional_rates = {}
        if campaign:
            additional_rates = {
                int(line.installment_count): float(line.broker_additional_rate or 0.0)
                for line in campaign.line_ids
            }

        def _to_float(value):
            try:
                return float(value or 0.0)
            except (TypeError, ValueError):
                return 0.0

        def _to_int(value):
            try:
                return int(value or 0)
            except (TypeError, ValueError):
                return 0

        lines = []

        def _add_line(row, card_type='', card_family='', card_logo=''):
            row_id = _to_int(row.get('id'))
            plus = _to_int(row.get('plus'))
            count = _to_int(row.get('count')) or (row_id + plus if row_id else 0)
            
            crate = _to_float(row.get('crate'))
            
            corate = round((crate / (100 + crate)) * 100, 2) if crate > 0 else 0.0
            broker_rate = additional_rates.get(count, 0.0)
            
            customer_rate = round(crate, 4)
            customer_amount = float_round(amount_value * customer_rate / 100.0, precision_digits=precision)
            
            combined_rate = corate + broker_rate
            broker_impact_rate = round(((100 / (1 - (combined_rate / 100)) - 100) / 100) * 100, 4) if combined_rate < 100 else 0.0
            broker_impact_amount = float_round(amount_value * broker_impact_rate / 100.0, precision_digits=precision)
            
            total_amount = float_round(amount_value + broker_impact_amount, precision_digits=precision)

            bank_commission = round(total_amount * corate / 100.0, 4)
            broker_extra = round(amount_value * broker_rate / 100.0, 4)
            paylox_total_commission = round(total_amount - amount_value, 4)

            profit = round(total_amount * broker_rate / 100.0, 4)
            profit_rate = (profit / amount_value * 100) if amount_value > 0 else 0.0

            monthly_amount = count and round(total_amount / count, 4) or total_amount

            lines.append({
                'card_type': card_type or '',
                'card_family': card_family or '',
                'card_logo': card_logo or '',
                'installment_base': row_id,
                'installment_plus': plus,
                'installment_count': count,
                'installment_label': '%s%s' % (row_id or '', ('+' + str(plus)) if plus else ''),
                'customer_rate': customer_rate,
                'customer_amount': customer_amount,
                'bank_commission_rate': corate,
                'bank_commission': bank_commission,
                'paylox_commission': paylox_total_commission,
                'broker_rate': broker_rate,
                'broker_commission': broker_extra,
                'broker_impact_rate': broker_impact_rate,
                'broker_impact_amount': broker_impact_amount,
                'total_amount': total_amount,
                'monthly_amount': monthly_amount,
                'profit': profit,
                'profit_rate': profit_rate,
            })

        card_data = installment_data.get('card') or {}
        card_type = card_data.get('type')
        
        if card_type == 'Credit':
            for row in installment_data.get('rows', []):
                _add_line(row, card_type, card_data.get('family'), card_data.get('logo'))

        grids = installment_data.get('grids') or {}
        for card_type, card_grids in grids.items():
            if card_type != 'Credit':
                continue
                
            for grid in card_grids:
                family = grid.get('family') or card_type
                logo = grid.get('logo')
                for line in grid.get('lines', []):
                    _add_line(line, card_type, family, logo)

        if card_data.get('type') == 'Credit':
            for line in installment_data.get('lines', []):
                _add_line(line, card_data.get('type'), card_data.get('family'), card_data.get('logo'))

        lines.sort(key=lambda item: (item['card_family'], item['installment_count'], item['card_type']))

        def _slugify(value):
            value = (value or '').lower()
            value = re.sub(r'[^a-z0-9]+', '-', value)
            value = value.strip('-')
            return value or 'other'

        def _card_type_label(code):
            mapping = {
                'Credit': _('Credit Card'),
                'Debit': _('Debit Card'),
                'Credit-Business': _('Business Card'),
            }
            if not code:
                return _('Other Cards')
            return mapping.get(code, code)

        grouped_types = OrderedDict()
        for line in lines:
            type_code = line.get('card_type') or 'Other'
            family_name = line.get('card_family') or _('Other Cards')
            type_entry = grouped_types.setdefault(type_code, {
                'code': type_code,
                'slug': _slugify(type_code),
                'label': _card_type_label(type_code),
                'families': OrderedDict(),
            })
            families = type_entry['families']
            family_entry = families.setdefault(family_name, {
                'name': family_name,
                'code': _slugify(family_name),
                'logo': line.get('card_logo') or '',
                'lines': [],
            })
            if not family_entry['logo'] and line.get('card_logo'):
                family_entry['logo'] = line.get('card_logo')
            family_entry['lines'].append(line)

        card_types = []
        for type_entry in grouped_types.values():
            families = []
            for family_entry in type_entry['families'].values():
                family_entry['lines'].sort(key=lambda l: (l['installment_count'], l['installment_plus']))
                
                if family_entry['lines']:
                    max_profit = max(line.get('profit', 0) for line in family_entry['lines'])
                    if max_profit > 0:
                        for line in family_entry['lines']:
                            line['is_best_profit'] = (line.get('profit', 0) == max_profit)
                    else:
                        for line in family_entry['lines']:
                            line['is_best_profit'] = False
                
                families.append({
                    'name': family_entry['name'],
                    'code': family_entry['code'],
                    'logo': family_entry['logo'],
                    'lines': family_entry['lines'],
                })
            card_types.append({
                'code': type_entry['code'],
                'slug': type_entry['slug'],
                'label': type_entry['label'],
                'families': families,
            })

        return {
            'amount': float_round(amount_value, precision_digits=precision),
            'lines': lines,
            'card_types': card_types,
            'type': installment_data.get('type'),
        }

    def _prepare_installment(self, acquirer=None, partner=0, amount=0, rate=0, currency=None, campaign='', bin='', token='', **kwargs):
        result = super()._prepare_installment(
            acquirer=acquirer,
            partner=partner,
            amount=amount,
            rate=rate,
            currency=currency,
            campaign=campaign,
            bin=bin,
            token=token,
            **kwargs
        )
        if result.get('error') or not result.get('rows'):
            return result
        try:
            partner_obj = request.env['res.partner'].sudo().browse(int(partner)) if partner else request.env.user.partner_id
            if not partner_obj or partner_obj.paylox_escrow_type != 'broker':
                return result
            
            broker_campaign = partner_obj.broker_default_campaign_id
            if not broker_campaign or not broker_campaign.active:
                return result
            
            additional_rates = {
                int(line.installment_count): float(line.broker_additional_rate or 0.0)
                for line in broker_campaign.line_ids
            }
            
            if not additional_rates:
                return result
            
            currency_obj = request.env['res.currency'].sudo().browse(int(currency)) if currency else request.env.company.currency_id
            precision = currency_obj.decimal_places or 2
            amount_value = float(amount or 0.0)
            for row in result.get('rows', []):
                installment_count = int(row.get('count', 0))
                broker_rate = additional_rates.get(installment_count, 0.0)
                
                if broker_rate <= 0:
                    continue
                
                crate = float(row.get('crate', 0.0))
                corate = (crate / (100 + crate)) * 100 if crate > 0 else 0.0
                combined_rate = corate + broker_rate
                broker_impact_rate = ((100 / (1 - (combined_rate / 100)) - 100) / 100) * 100 if combined_rate < 100 else 0.0
                broker_impact_amount = float_round(amount_value * broker_impact_rate / 100.0, precision_digits=precision)
                total_amount = float_round(amount_value + broker_impact_amount, precision_digits=precision)

                row['amount'] = float_round(total_amount / installment_count, precision_digits=precision) if installment_count > 0 else total_amount
                row['crate'] = broker_impact_rate
                row['broker_rate'] = broker_rate
                row['total_amount'] = total_amount
            
            return result
            
        except Exception as e:
            _logger.error("Error applying broker rates in _prepare_installment: %s", str(e))
            return result
    
    @http.route(['/payment/escrow/card/validate'], type='json', auth='user', methods=['POST'], website=True)
    def validate_card(self, **kwargs):
        company = request.env.company
        user = request.env.user
        customer = request.env['res.partner'].sudo().search([('vat', '=', kwargs.get('vat'))], limit=1)
        if company.syncops_check_card:
            if customer and customer.is_card_verified:
                return {
                    'success': True,
                }
            else:
                try:
                    result, message = request.env['syncops.connector'].sudo()._execute(
                        'other_get_ozan_cardnumber', 
                        reference=str(user.partner_id.id), 
                        params={
                            'vat': kwargs.get('vat'),
                            'number': kwargs.get('card_number'),
                        }, 
                        company=company, 
                        message=True
                    )
                    
                    if result is None:
                        return {
                            'success': False,
                            'message': message or 'Card validation failed'
                        }
                    res = result[0]
                    if res.get('ok'):
                        customer.sudo().write({'is_card_verified': True})
                        return {
                            'success': True,
                            'data': res
                        }
                    else:
                        return {
                            'success': False,
                            'message': res.get('message') or 'Card validation failed'
                        }
                except Exception as e:
                    _logger.error("Error in validate_card: %s", str(e))
                    return {
                        'success': False,
                        'message': str(e)
                    }
        else:
            return {
                'success': True,
            }

    def _get_data_values(self, data, transaction, **kwargs):
        values = super()._get_data_values(data, transaction, **kwargs)
        if transaction and transaction.system == 'escrow':
            customer_basket = []

            ad = transaction.paylox_product_ids[0].ad_id
            partner = ad.owner_id
            customers = ad.customer_ids
            customer = customers.filtered(lambda c: c.is_escrow_customer)[:1]
            
            if not customer:
                raise ValidationError(_('No active escrow customer found for this transaction.'))
                
            verified_banks = partner.bank_ids.filtered(lambda b: b.api_ref)
            reference_seller = verified_banks[0].api_ref if verified_banks else False
            if not reference_seller:
                raise ValidationError(_('%s must have at least one bank account which is verified.' % partner.name))

            platform_owner = request.env['res.partner'].sudo().search([('paylox_escrow_type', '=', 'platform_owner')], limit=1)
            infrastructure_provider = request.env['res.partner'].sudo().search([('paylox_escrow_type', '=', 'infrastructure_provider')], limit=1)
            broker = transaction.partner_id

            dealer = broker.broker_dealer_id if broker else None

            def find_rate(rec, inst):
                if rec and rec.installment_rate_ids:
                    for r in rec.installment_rate_ids:
                        if int(r.installment_count) == inst:
                            return float(r.rate)
                return 0.0
            
            def find_broker_rate(rec, inst):
                if rec and rec.broker_default_campaign_id and rec.broker_default_campaign_id.line_ids:
                    for r in rec.broker_default_campaign_id.line_ids:
                        if int(r.installment_count) == inst:
                            return float(r.broker_additional_rate)
                return 0.0
            
            def find_dealer_rate(dealer_partner, campaign_id):
                if dealer_partner and campaign_id:
                    dealer_commission = dealer_partner.dealer_commission_rate_ids.filtered(lambda d: d.campaign_id.id == campaign_id and d.active)
                    if dealer_commission:
                        return dealer_commission.commission_rate or 0.0
                return 0.0

            installment_count = int(transaction.jetcheckout_installment_count or 1)
            seller_net = float(transaction.jetcheckout_payment_amount or 0.0)
            paid = transaction.jetcheckout_payment_paid
            additional_rate = transaction.jetcheckout_additional_rate

            infra_rate = find_rate(infrastructure_provider, installment_count)
            broker_rate = find_broker_rate(broker, installment_count)
            
            dealer_rate = 0.0
            if dealer and broker and broker.campaign_id:
                dealer_rate = find_dealer_rate(dealer, broker.campaign_id.id)

            infra_commission = paid * infra_rate
            dealer_commission = (paid * dealer_rate / 100)
            platform_commission = (paid * additional_rate / 100) - infra_commission - dealer_commission
            broker_commission = (paid * broker_rate / 100)

            total_paid = seller_net + infra_commission + platform_commission + broker_commission + dealer_commission

            seller_amount = paid * seller_net / total_paid
            if transaction.company_id.paylox_escrow_use_paid_price:
                seller_amount = transaction.jetcheckout_payment_paid
            customer_basket.append({
                "id": 24,
                "name": partner.name or '',
                "description": ad.name or 'Owner commission',
                "qty": 1,
                "amount": seller_amount,
                "category": ad.category_id.name if ad.category_id else '',
                "is_physical": False,
                "submerchant_external_id": reference_seller,
                "partner_id": partner.id,
                "submerchant_price": seller_net
            })
            infra_amount = paid * infra_commission / total_paid
            if infra_commission > 0:
                infra_banks = infrastructure_provider.bank_ids.filtered(lambda b: b.api_ref)
                ref_infra = infra_banks[0].api_ref if infra_banks else ''
                customer_basket.append({
                    "id": 25,
                    "name": infrastructure_provider.name or '',
                    "description": f"Infrastructure Commission (%{infra_rate})",
                    "qty": 1,
                    "amount": infra_amount,
                    "category": "Komisyon",
                    "is_physical": False,
                    "partner_id": infrastructure_provider.id,
                    "submerchant_external_id": ref_infra,
                    "submerchant_price": infra_commission
                })
            platform_amount = paid * platform_commission / total_paid
            if platform_commission > 0:
                platform_banks = platform_owner.bank_ids.filtered(lambda b: b.api_ref)
                ref_platform = platform_banks[0].api_ref if platform_banks else ''
                customer_basket.append({
                    "id": 26,
                    "name": platform_owner.name or '',
                    "description": _(f"Platform commission"),
                    "qty": 1,
                    "amount": platform_amount,
                    "category": "Commission",
                    "is_physical": False,
                    "partner_id": platform_owner.id,
                    "submerchant_external_id": ref_platform,
                    "submerchant_price": platform_commission
                })
            broker_amount = paid * broker_commission / total_paid
            if broker and broker.broker_default_campaign_id and broker_amount > 0:
                broker_banks = broker.bank_ids.filtered(lambda b: b.api_ref)
                ref_broker = broker_banks[0].api_ref if broker_banks else ''
                if broker_amount > 0:
                    customer_basket.append({
                        "id": 27,
                        "name": broker.name or '',
                        "description": _("Broker Commission"),
                        "qty": 1,
                        "amount": broker_amount,
                        "category": "Commission",
                        "is_physical": False,
                        "partner_id": broker.id,
                        "submerchant_external_id": ref_broker,
                        "submerchant_price": broker_commission
                    })
            
            dealer_amount = paid * dealer_commission / total_paid
            if dealer and dealer_commission > 0:
                dealer_banks = dealer.bank_ids.filtered(lambda b: b.api_ref)
                ref_dealer = dealer_banks[0].api_ref if dealer_banks else ''
                if dealer_amount > 0:
                    customer_basket.append({
                        "id": 28,
                        "name": dealer.name or '',
                        "description": _("Dealer Commission"),
                        "qty": 1,
                        "amount": dealer_amount,
                        "category": "Commission",
                        "is_physical": False,
                        "submerchant_external_id": ref_dealer,
                        "submerchant_price": dealer_commission,
                        "partner_id": dealer.id,
                    })
            fullname = customer.name.split(' ', 1) if customer.name else ['', '']
            address = []
            if customer.city:
                address.append(customer.city)
            if customer.state_id:
                address.append(customer.state_id.name)
            if customer.country_id:
                address.append(customer.country_id.name)
            values.update({
                'submerchant_external_id': reference_seller,
                'is_submerchant_payment': True,
                'customer_basket': customer_basket,
                'customer':{
                    "name": fullname[0] or '',
                    "surname": fullname[-1] if len(fullname) > 1 else '',
                    "email": customer.email or '',
                    "id": str(customer.id),
                    "identity_number": customer.vat or '',
                    "phone": customer.phone or '',
                    "ip_address": transaction.jetcheckout_ip_address or request.httprequest.remote_addr,
                    "postal_code": customer.zip or '',
                    "company": customer.parent_id.name if customer.parent_id else "",
                    "address": ", ".join(address) if address else customer.street or "",
                    "city": customer.state_id.name if customer.state_id else "",
                    "country": customer.country_id.name if customer.country_id else "",
                }
            })
            transaction.partner_id = customer.id
        return values

    @http.route(['/payment/escrow/get_items'], type='json', auth='user', methods=['POST'], website=True)
    def get_items(self, id,**kwargs):
        item = request.env['payment.item'].sudo().search([('product_id', '=', id)], limit=1)
        if not item:
            return {'error': 'Item not found'}
        return {'item': item.read()[0]}

    @http.route(['/my/iban/verify'], type='json', auth='user', methods=['POST'], website=True)
    def verify_iban(self, iban, vat, **kwargs):
        iban = sanitize_account_number(iban)
        bank_account = request.env['res.partner.bank'].sudo().search([
            ('api_state', '=', True),
            ('partner_id.vat', '=', vat),
            ('sanitized_acc_number', '=', iban),
            ('company_id', '=', request.env.company.id),
        ], limit=1)
        return bool(bank_account)

    @route('/my/otp/validate', type='json', auth='user', methods=['POST'], website=True)
    def validate_otp(self, otp, **kwargs):
        domain = [('mobile', 'like', '%%%s' % otp)]
        try:
            otp = '%s %s %s %s' % (otp[0:3], otp[3:6], otp[6:8], otp[8:10])
            domain = ['|'] + domain + [('mobile', 'like', '%%%s' % otp)]
        except:
            pass
        domain = [('is_otp_verified', '=', True)] + domain
        partner = request.env['res.partner'].sudo().search(domain, limit=1)
        return bool(partner)

    @route('/my/otp/start', type='json', auth='user', methods=['POST'], website=True)
    def start_otp(self, partner_id=None, **kwargs):
        try:
            if not partner_id:
                return {'success': False, 'message': 'Missing partner_id'}

            partner = request.env['res.partner'].sudo().browse(int(partner_id))
            if partner.is_otp_verified:
                return {'is_otp_verified': True, 'message': 'OTP already verified'}
            if not partner.exists():
                return {'success': False, 'message': 'Partner not found'}

            try:
                otp = request.env['res.partner.otp'].sudo().create({
                    'partner_id': partner.id,
                    'company_id': request.env.company.id,
                    'lang': request.env.lang or 'tr_TR',
                    'phone': partner.mobile
                })
                return {
                    'success': True,
                    'otp_id': otp.id,
                    'expires_in': 120,
                    'message': _('A verification code was sent to your phone')
                }
            except Exception as e:
                return {'success': False, 'message': 'OTP service unavailable: %s' % str(e)}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @route('/escrow/register/otp/start', type='json', auth='public', methods=['POST'], website=True)
    def escrow_register_otp_start(self, partner_id=None, **kwargs):
        try:
            if not partner_id:
                return {'success': False, 'message': 'Missing partner_id'}

            partner = request.env['res.partner'].sudo().browse(int(partner_id))
            if partner.is_otp_verified:
                return {'is_otp_verified': True, 'message': 'OTP already verified'}
            if not partner.exists():
                return {'success': False, 'message': 'Partner not found'}

            try:
                otp = request.env['res.partner.otp'].sudo().create({
                    'partner_id': partner.id,
                    'company_id': request.env.company.id,
                    'lang': request.env.lang or 'tr_TR',
                    'phone': partner.mobile
                })
                return {
                    'success': True,
                    'otp_id': otp.id,
                    'expires_in': 120,
                    'message': _('A verification code was sent to your phone')
                }
            except Exception as e:
                return {'success': False, 'message': 'OTP service unavailable: %s' % str(e)}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @route('/escrow/register/otp/verify', type='json', auth='public', methods=['POST'], website=True)
    def escrow_register_otp_verify(self, otp_id=None, code=None, **kwargs):
        try:
            if not otp_id or not code:
                return {'success': False, 'message': 'Missing parameters'}

            otp = request.env['res.partner.otp'].sudo().browse(int(otp_id))
            partner = request.env['res.partner'].sudo().browse(int(otp.partner_id))
            if not otp.exists():
                return {'success': False, 'message': _('Verification request not found or expired')}

            if otp.date and otp.date < fields.Datetime.now():
                return {'success': False, 'message': _('Verification code has expired')}

            if str(otp.code) != str(code):
                return {'success': False, 'message': _('Invalid verification code')}

            otp.unlink()
            partner.write({'is_otp_verified': True})
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @route('/my/otp/verify', type='json', auth='user', methods=['POST'], website=True)
    def verify_otp(self, otp_id=None, code=None, **kwargs):
        try:
            if not otp_id or not code:
                return {'success': False, 'message': 'Missing parameters'}

            otp = request.env['res.partner.otp'].sudo().browse(int(otp_id))
            partner = request.env['res.partner'].sudo().browse(int(otp.partner_id))
            if not otp.exists():
                return {'success': False, 'message': _('Verification request not found or expired')}

            if otp.date and otp.date < fields.Datetime.now():
                return {'success': False, 'message': _('Verification code has expired')}

            if str(otp.code) != str(code):
                return {'success': False, 'message': _('Invalid verification code')}

            otp.unlink()
            partner.write({'is_otp_verified': True})
            return {'success': True}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @route('/get/ad', type='json', auth='user', methods=['POST'], website=True)
    def get_ad(self, ad_id=None, **kwargs):
        company = request.env.company
        if not ad_id:
            return {'success': False, 'message': 'Missing ad_id'}
        domain = [('company_id', '=', company.id), ('id', '=', ad_id)]
        ad = request.env['escrow.ad'].sudo().search(domain, limit=1)
        if not ad.exists():
            return {'success': False, 'message': 'Ad not found'}

        image = ad.image_1920
        if image:
            mime = guess_mimetype(base64.b64decode(image))
            image = 'data:%s;base64,%s' % (mime, image.decode('utf-8'))
        acc_number = ad.owner_id.bank_ids.filtered(lambda b: b.api_state) and ad.owner_id.bank_ids.filtered(lambda b: b.api_state)[0]['acc_number'] or ''
        attributes = [{'name': v.attribute_id.name, 'value': v.display_value} for v in ad.attribute_value_ids]
        attribute_values = {}
        for value_rec in ad.attribute_value_ids:
            attr = value_rec.attribute_id
            key = attr.technical_name
            
            if attr.attribute_type == 'binary' and value_rec.value_binary:
                mime = guess_mimetype(base64.b64decode(value_rec.value_binary))
                image = 'data:%s;base64,%s' % (mime, value_rec.value_binary.decode('utf-8'))
                attribute_values[key] = image
            elif attr.attribute_type == 'many2one' and value_rec.value_many2one:
                attribute_values[key] = value_rec.value_many2one
            elif attr.attribute_type == 'boolean':
                attribute_values[key] = value_rec.value_boolean
            elif attr.attribute_type == 'integer':
                attribute_values[key] = value_rec.value_integer
            elif attr.attribute_type == 'float':
                attribute_values[key] = value_rec.value_float
            elif attr.attribute_type == 'date' and value_rec.value_date:
                attribute_values[key] = value_rec.value_date.strftime('%Y-%m-%d')
            elif attr.attribute_type == 'datetime' and value_rec.value_datetime:
                attribute_values[key] = value_rec.value_datetime.strftime('%Y-%m-%d %H:%M:%S')
            elif attr.attribute_type in ('char', 'text', 'selection'):
                attribute_values[key] = value_rec.value_char or value_rec.value_text or ''
        return {
            'success': True,
            'ad': {
                'id': ad.id,
                'name': ad.name,
                'description': ad.description,
                'price': ad.price,
                'image': image,
                'categ_id': ad.category_id and {'id': ad.category_id.id, 'name': ad.category_id.name} or None,
                'owner_id': ad.owner_id.id,
                'state': ad.state,
                'customer_id': ad.customer_ids and [{'id': customer.id, 'name': customer.name} for customer in ad.customer_ids if customer.is_escrow_customer] or None,
                'broker_id': None,
                'item_id': ad.payment_item_id and ad.payment_item_id.id or None,
                'paid_amount': ad.payment_item_id.paid_amount or 0.0 if ad.payment_item_id else 0.0,
                'iban': acc_number,
                'partner': ad.owner_id.name,
                'vat': ad.owner_id.vat,
                'sale_state': ad.sale_state,
                'attribute_values': attribute_values,
                'attributes': attributes,
            }
        }

    @route('/payment/escrow/ad/official_sale', type='json', auth='user', methods=['POST'], website=True)
    def upload_official_sale_image(self, ad_id=None, file=None, **kwargs):
        if not ad_id or not file:
            return {'success': False, 'message': 'Missing parameters'}
        company = request.env.company
        user = request.env.user
        partner = user.partner_id
        domain = [('company_id', '=', company.id), ('id', '=', ad_id)]
        ad = request.env['escrow.ad'].sudo().search(domain, limit=1)
        if not ad.exists():
            return {'success': False, 'message': 'Ad not found'}
        if ad.owner_id != partner:
            return {'success': False, 'message': 'You are not allowed to update this ad'}
        try:
            attachment = request.env['ir.attachment'].sudo().create({
                'name': _('%s - Official Sale Document') % (ad.title,),
                'res_model': ad._name,
                'res_id': ad.id,
                'mimetype': file['mimetype'] or 'application/pdf',
                'datas': file['data'],
                'type': 'binary',
            })
            ad.official_sale_document = file['data']
            ad.official_sale_document_name = attachment.name
            ad.official_sale_upload_date = fields.Datetime.now()
            ad.write({'sale_state': 'waiting_transfer'})
            body = _('User has uploaded official sale document. User IP Address is %s') % (request.httprequest.remote_addr,)
            ad.message_post(body=body, attachment_ids=attachment.ids)
            return {'success': True, 'message': 'Official sale document uploaded successfully'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @route('/my/ads/broker', type='http', auth='public', methods=['GET'], sitemap=False, csrf=False, website=True)
    def page_broker_payment_link(self, token=None, **kwargs):
        if not token:
            return request.render('payment_escrow.broker_link_error', {
                'error': _('Invalid link: No token provided')
            })
        
        try:
            decoded = base64.b64decode(token).decode()
            
            broker_id, expires_timestamp = decoded.split(':')
            broker_id = int(broker_id)
            expires_timestamp = int(expires_timestamp)
            
            if datetime.now().timestamp() > expires_timestamp:
                return request.render('payment_escrow.broker_link_error', {
                    'error': _('This payment link has expired')
                })
            
            broker = request.env['res.partner'].sudo().search([
                ('id', '=', broker_id),
                ('paylox_escrow_type', '=', 'broker'),
            ], limit=1)
            
            if not broker:
                return request.render('payment_escrow.broker_link_error', {
                    'error': _('Broker not found')
                })
            
            if not broker.user_ids:
                alphabet = string.ascii_letters + string.digits
                password = ''.join(secrets.choice(alphabet) for i in range(16))
                
                user_vals = {
                    'name': broker.name,
                    'login': f'broker_{broker.id}@system.local',
                    'partner_id': broker.id,
                    'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])],
                }
                broker_user = request.env['res.users'].sudo().with_context(no_reset_password=True).create(user_vals)
                broker_user.sudo().write({'password': password})
            else:
                broker_user = broker.user_ids[0]
            
            request.session.uid = broker_user.id
            request.session.login = broker_user.login
            request.session.session_token = broker_user._compute_session_token(request.session.sid)

            owner_param = kwargs.get('owner') or kwargs.get('owner_id')
            customer_param = kwargs.get('customer') or kwargs.get('customer_id')

            try:
                owner_id = int(owner_param) if owner_param is not None else None
            except (TypeError, ValueError):
                owner_id = None

            try:
                customer_id = int(customer_param) if customer_param is not None else None
            except (TypeError, ValueError):
                customer_id = None

            redirect_url = self._generate_hash_url(step=1, owner=owner_id, customer=customer_id)
            return request.redirect(redirect_url)
            
        except Exception as e:
            return request.render('payment_escrow.broker_link_error', {
                'error': _('Invalid or malformed token: %s') % str(e)
            })

    @route('/my/ads', type='http', auth='user', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True)
    def page_my_ads(self, **kwargs):
        user = request.env.user
        partner = user.partner_id
        
        if partner.paylox_escrow_type == 'dealer':
            return request.redirect('/my/dealer/transactions')

        hash = kwargs.get('')
        values = {}
        if hash:
            try:
                value = base64.b64decode(unquote(hash)).decode('utf-8')
                values = json.loads(value)
            except:
                pass

        company = request.env.company
        user = request.env.user
        partner = user.partner_id
        campaign = partner.campaign_id.name if partner and partner.campaign_id else ''
        domain = [('company_id', '=', company.id)]
        if user.share:
            domain.append(('broker_id', '=', partner.id))
        ads = request.env['escrow.ad'].sudo().search(domain)

        try:
            step = int(values['s'])
        except:
            step = 0

        values = {
            'ads': ads,
            'partner': partner,
            'company': company,
            'currency': company.currency_id,
            'agreements': self._get_agreements(),
            'campaign': campaign,
            'step': step,
        }
        return request.render('payment_escrow.page_ads', values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })

    @route('/my/broker/rates', type='http', auth='user', methods=['GET'], sitemap=False, website=True)
    def page_broker_rates(self, **kwargs):
        partner = request.env.user.partner_id
        if partner.paylox_escrow_type != 'broker':
            return request.redirect('/my')

        partner_sudo = partner.sudo()
        company = request.env.company
        campaigns = partner_sudo.broker_campaign_id.filtered(lambda c: c.active)

        campaign_param = kwargs.get('campaign_id')
        selected_campaign = request.env['escrow.broker.campaign']
        if campaign_param:
            try:
                campaign_param = int(campaign_param)
            except (TypeError, ValueError):
                campaign_param = False
        if campaign_param:
            selected_campaign = campaigns.filtered(lambda c: c.id == campaign_param)[:1]
        if not selected_campaign:
            if partner_sudo.broker_default_campaign_id and partner_sudo.broker_default_campaign_id in campaigns:
                selected_campaign = partner_sudo.broker_default_campaign_id
            elif campaigns:
                selected_campaign = campaigns.sorted(lambda c: (c.sequence, c.id))[:1]

        amount_param = kwargs.get('amount')
        try:
            default_amount = float(amount_param) if amount_param else 0.0
        except (TypeError, ValueError):
            default_amount = 0.0

        currency = company.currency_id
        values = {
            'company': company,
            'partner': partner_sudo,
            'currency': currency,
            'campaigns': campaigns,
            'selected_campaign': selected_campaign,
            'default_amount': default_amount,
        }
        return request.render('payment_escrow.page_broker_rates', values)

    @route('/payment/escrow/broker/rates/data', type='json', auth='user', methods=['POST'], website=True)
    def broker_rates_data(self, amount=0.0, campaign_id=None, **kwargs):
        partner = request.env.user.partner_id
        if partner.paylox_escrow_type != 'broker':
            return {'error': _('Only brokers can access broker rates.')}

        company = request.env.company
        currency = company.currency_id

        amount_param = kwargs.get('amount', amount)
        try:
            amount_value = float(amount_param or 0.0)
        except (TypeError, ValueError):
            return {'error': _('Invalid amount value.')}

        partner_sudo = partner.sudo()
        campaigns = partner_sudo.broker_campaign_id.filtered(lambda c: c.company_id.id == company.id and c.active)

        campaign_param = kwargs.get('campaign_id', campaign_id)
        if campaign_param:
            try:
                campaign_param = int(campaign_param)
            except (TypeError, ValueError):
                campaign_param = False

        selected_campaign = request.env['escrow.broker.campaign'].sudo().browse(campaign_param)
        # if campaign_param:
        #     selected_campaign = campaigns.filtered(lambda c: c.id == campaign_param)[:1]
        # if not selected_campaign and campaigns:
        #     selected_campaign = campaigns.sorted(lambda c: (c.sequence, c.id))[:1]
        # if not selected_campaign:
        #     return {'error': _('No active campaign has been assigned to your account.')}

        result = self._prepare_broker_installment_lines(
            partner=partner,
            amount=amount_value,
            currency=currency,
            campaign=selected_campaign,
        )
        if result.get('error'):
            return result

        campaign_info = {}
        if selected_campaign:
            campaign_info = {
                'id': selected_campaign.id,
                'name': selected_campaign.name,
            }
        
        result.update({
            'currency': {
                'id': currency.id,
                'name': currency.name,
                'symbol': currency.symbol,
                'position': currency.position,
                'decimal_places': currency.decimal_places,
            },
            'campaign': campaign_info,
            'campaigns': [{
                'id': campaign.id,
                'name': campaign.name,
                'active': selected_campaign and campaign.id == selected_campaign.id,
            } for campaign in campaigns],
        })
        return result

    @route('/my/broker/settings', type='http', auth='user', methods=['GET'], sitemap=False, website=True)
    def page_broker_settings(self, **kwargs):
        partner = request.env.user.partner_id
        if partner.paylox_escrow_type != 'broker':
            return request.redirect('/my')

        partner_sudo = partner.sudo()
        company = request.env.company
        campaigns = partner_sudo.broker_campaign_id.filtered(lambda c: c.active)
        default_campaign_id = partner_sudo.broker_default_campaign_id.id if partner_sudo.broker_default_campaign_id else None

        values = {
            'company': company,
            'partner': partner_sudo,
            'campaigns': campaigns,
            'default_campaign_id': default_campaign_id,
        }
        return request.render('payment_escrow.page_broker_settings', values)

    @route('/payment/escrow/broker/settings/save', type='json', auth='user', methods=['POST'], website=True)
    def broker_settings_save(self, default_campaign_id=None, sign_name=None, authorized_person=None, 
                           email=None, phone=None, mobile=None, **kwargs):
        partner = request.env.user.partner_id
        if partner.paylox_escrow_type != 'broker':
            return {'error': _('Only brokers can access settings.'), 'success': False}

        if not all([sign_name, authorized_person, email, phone]):
            return {'error': _('Please fill all required fields.'), 'success': False}

        partner_sudo = partner.sudo()
        values = {
            'sign_name': sign_name,
            'authorized_person': authorized_person,
            'email': email,
            'phone': phone,
        }

        if mobile:
            values['mobile'] = mobile

        if default_campaign_id:
            try:
                campaign_id = int(default_campaign_id)
                campaigns = partner_sudo.broker_campaign_id.filtered(lambda c: c.active)
                selected_campaign = campaigns.filtered(lambda c: c.id == campaign_id)
                if selected_campaign:
                    values['broker_default_campaign_id'] = campaign_id
            except (TypeError, ValueError):
                pass

        partner_sudo.write(values)
        return {'success': True}

    @route(['/my/ad/<int:id>/image'], type='http', auth='user')
    def page_my_ad_image(self, id):
        return request.env['ir.http'].sudo()._content_image(xmlid=None, model='escrow.ad', res_id=id, field='image_1920', filename_field='title', unique=None, filename=None, mimetype=None, download=None, width=0, height=0, crop=False, quality=0, access_token=None)

    @route(['/my/ad/category/attributes'], type='json', auth='user', methods=['POST'])
    def get_category_attributes(self, category_id=None, ad_id=None, **kwargs):
        if not category_id:
            return {'error': 'No category ID provided'}
        
        try:
            category = request.env['escrow.ad.category'].sudo().browse(int(category_id))
            if not category.exists():
                return {'error': 'Category not found'}
            
            attributes = []
            # Attribute'leri sequence'a göre sırala
            for attr in category.attribute_ids.sorted(lambda a: (a.sequence, a.name)):
                attr_data = {
                    'id': attr.id,
                    'name': attr.name,
                    'technical_name': attr.technical_name,
                    'attribute_type': attr.attribute_type,
                    'required': attr.required,
                    'help_text': attr.help_text or '',
                    'mask': attr.mask or '',
                    'sequence': attr.sequence,
                }
                
                if attr.attribute_type == 'selection':
                    # Selection option'ları da sequence'a göre sırala
                    attr_data['options'] = [
                        {'value': opt.value, 'name': opt.name}
                        for opt in attr.selection_option_ids.sorted(lambda o: (o.sequence, o.name))
                    ]
                elif attr.attribute_type == 'many2one' and attr.relation_model:
                    # Many2one için ilgili modelden kayıtları getir
                    try:
                        related_model = request.env[attr.relation_model].sudo()
                        if attr.relation_model == 'escrow.car.model':
                            # Model için sadece aktif olanları getir
                            records = related_model.search([('active', '=', True)], order='name')
                        else:
                            # Brand ve diğerleri için tüm kayıtları getir
                            records = related_model.search([], order='name')
                        
                        attr_data['options'] = [
                            {'value': str(rec.id), 'name': rec.name}
                            for rec in records
                        ]
                        attr_data['relation_model'] = attr.relation_model
                    except Exception as e:
                        _logger.warning(f"Could not load many2one options for {attr.relation_model}: {e}")
                        attr_data['options'] = []
                
                attributes.append(attr_data)
            
            result = {
                'success': True,
                'category_type': category.category_type,
                'attributes': attributes
            }
            
            if ad_id:
                _logger.info(f"Loading attribute values for ad_id: {ad_id}")
                try:
                    ad = request.env['escrow.ad'].sudo().browse(int(ad_id))
                    _logger.info(f"Ad found: {ad.exists()}, attribute_value_ids count: {len(ad.attribute_value_ids)}")
                    if ad.exists():
                        attribute_values = {}
                        for value_rec in ad.attribute_value_ids:
                            attr = value_rec.attribute_id
                            _logger.info(f"Processing attribute: {attr.technical_name}, categories: {attr.category_ids.ids}, current category: {category.id}")
                            if category.id in attr.category_ids.ids:
                                key = attr.technical_name
                                if attr.attribute_type == 'binary':
                                    if value_rec.value_binary:
                                        b64_data = base64.b64encode(value_rec.value_binary).decode('utf-8')
                                        attribute_values[key] = f'data:image/jpeg;base64,{b64_data}'
                                    elif attr.is_primary_image and ad.image_1920:
                                        attribute_values[key] = f'data:image/jpeg;base64,{ad.image_1920.decode("utf-8")}'
                                elif attr.attribute_type == 'many2one' and value_rec.value_many2one:
                                    # value_many2one artık integer (ID) - string'e çevir
                                    attribute_values[key] = str(value_rec.value_many2one)
                                elif attr.attribute_type == 'boolean':
                                    attribute_values[key] = value_rec.value_boolean
                                elif attr.attribute_type == 'integer':
                                    attribute_values[key] = value_rec.value_integer
                                elif attr.attribute_type == 'float':
                                    attribute_values[key] = value_rec.value_float
                                elif attr.attribute_type == 'date' and value_rec.value_date:
                                    attribute_values[key] = value_rec.value_date.strftime('%Y-%m-%d')
                                elif attr.attribute_type == 'datetime' and value_rec.value_datetime:
                                    attribute_values[key] = value_rec.value_datetime.strftime('%Y-%m-%d %H:%M:%S')
                                elif attr.attribute_type in ('char', 'text', 'selection'):
                                    attribute_values[key] = value_rec.value_char or value_rec.value_text or ''
                        
                        _logger.info(f"Collected attribute_values: {attribute_values}")
                        result['attribute_values'] = attribute_values
                except Exception as e:
                    _logger.warning(f"Could not load attribute values for ad {ad_id}: {e}")
                    _logger.error(traceback.format_exc())
            
            return result
        except Exception as e:
            _logger.error("Error in get_category_attributes: %s", str(e))
            return {'error': str(e)}

    @route(['/my/ad/brand/models'], type='json', auth='user', methods=['POST'])
    def get_brand_models(self, brand_id=None, **kwargs):
        """Brand seçildiğinde o brand'e ait modelleri döndür"""
        if not brand_id:
            return {'error': 'No brand ID provided'}
        
        try:
            brand = request.env['escrow.car.brand'].sudo().browse(int(brand_id))
            if not brand.exists():
                return {'error': 'Brand not found'}
            
            models = request.env['escrow.car.model'].sudo().search([
                ('brand_id', '=', brand.id),
                ('active', '=', True)
            ], order='name')
            
            return {
                'success': True,
                'models': [{'id': m.id, 'name': m.name} for m in models]
            }
        except Exception as e:
            _logger.error("Error in get_brand_models: %s", str(e))
            return {'error': str(e)}

    @route(['/my/ad/save'], type='json', auth='user', website=True)
    def page_my_ad_save(self, **kwargs):
        company = request.env.company
        user = request.env.user
        partner = user.partner_id
        values = {}
        
        category_id = kwargs.get('category_id')
        if not category_id:
            return {'error': _('Category is required.')}
        
        category = request.env['escrow.ad.category'].sudo().browse(int(category_id))
        if not category.exists():
            return {'error': _('Invalid category.')}
        
        ad_values = {
            'name': kwargs.get('name', ''),
            'description': kwargs.get('description', ''),
            'price': kwargs.get('price', 0.0),
            'category_id': category_id,
            'owner_id': kwargs.get('owner_id', partner.id),
            'broker_id': partner.id,
            'company_id': company.id,
        }
        
        if kwargs.get('image_1920'):
            ad_values['image_1920'] = kwargs['image_1920']
        
        if kwargs.get('id'):
            ad = request.env['escrow.ad'].sudo().search([
                ('id', '=', kwargs['id']),
                ('company_id', '=', company.id),
            ])
            if not ad:
                return {'error': _('Ad cannot be found, or you are not allowed to save it.')}
            
            ad.write(ad_values)
            
            item = request.env['payment.item'].sudo().search([('ad_id', '=', ad.id)])
            if item:
                item.write({'amount': kwargs.get('price')})
            else:
                item = request.env['payment.item'].sudo().create({
                    'parent_id': ad.owner_id.id,
                    'ad_id': ad.id,
                    'amount': kwargs.get('price'),
                    'currency_id': company.currency_id.id,
                })
                ad.payment_item_id = item.id
        else:
            ad = request.env['escrow.ad'].sudo().create(ad_values)
            item = request.env['payment.item'].sudo().create({
                'parent_id': ad.owner_id.id,
                'ad_id': ad.id,
                'amount': kwargs.get('price'),
                'currency_id': company.currency_id.id,
            })
            ad.payment_item_id = item.id
        
        if kwargs.get('attributes'):
            ad.attribute_value_ids.unlink()
            for attr_data in kwargs.get('attributes', []):
                attr_id = attr_data.get('attribute_id')
                if not attr_id:
                    continue
                
                attribute = request.env['escrow.ad.attribute'].sudo().browse(int(attr_id))
                if not attribute.exists():
                    continue
                
                value_data = {
                    'ad_id': ad.id,
                    'attribute_id': attribute.id,
                }
                
                if attribute.attribute_type == 'char':
                    value_data['value_char'] = attr_data.get('value', '')
                elif attribute.attribute_type == 'text':
                    value_data['value_text'] = attr_data.get('value', '')
                elif attribute.attribute_type == 'integer':
                    value_data['value_integer'] = int(attr_data.get('value', 0))
                elif attribute.attribute_type == 'float':
                    value_data['value_float'] = float(attr_data.get('value', 0.0))
                elif attribute.attribute_type == 'boolean':
                    value_data['value_boolean'] = bool(attr_data.get('value', False))
                elif attribute.attribute_type == 'date':
                    value_data['value_date'] = attr_data.get('value')
                elif attribute.attribute_type == 'datetime':
                    value_data['value_datetime'] = attr_data.get('value')
                elif attribute.attribute_type == 'selection':
                    value_data['value_selection'] = attr_data.get('value', '')
                elif attribute.attribute_type == 'many2one' and attr_data.get('value'):
                    many2one_id = int(attr_data.get('value'))
                    value_data['value_many2one'] = many2one_id
                elif attribute.attribute_type == 'binary' and attr_data.get('value'):
                    binary_value = attr_data.get('value')
                    if isinstance(binary_value, str) and 'base64,' in binary_value:
                        binary_value = binary_value.split('base64,')[1]
                    
                    value_data['value_binary'] = binary_value
                    value_data['value_binary_filename'] = attr_data.get('filename', 'image.jpg')
                    
                    if attribute.is_primary_image:
                        ad.write({'image_1920': binary_value})
                
                request.env['escrow.ad.attribute.value'].sudo().create(value_data)
        
        return {
            'id': ad.id,
            'item_id': item.id
        }
    
    @route(['/my/ad/vin/check'], type='json', auth='user', methods=['POST'], website=True)
    def page_my_ad_vin_check(self, **kwargs):
        vin = kwargs.get('vin')
        company = request.env.company
        if not vin:
            return {'error': _('VIN is required.')}

        result, message = request.env['syncops.connector'].sudo()._execute('other_get_vpic_vin_brand', reference=str(vin), params={
            'vin': vin
        },company=company,  message=True)
        if not result:
            return {'error': message}
        res = result[0]

        brand = request.env['escrow.car.brand'].sudo().search([('brand_id', '=', res.get('brand_id'))], limit=1)
        model = request.env['escrow.car.model'].sudo().search([('model_id', '=', res.get('model_id')), ('brand_id', '=', brand.id)], limit=1) if brand else None

        return {
            'success': True,
            'data': {
                'brand_id': brand.id if brand else None,
                'brand_name': brand.name if brand else None,
                'model_id': model.id if model else None,
                'model_name': model.name if model else None,
                'model_year': res.get('year') or None,
            }
        }

    @route(['/my/ad/delete'], type='json', auth='user', website=True)
    def page_my_ad_delete(self, **kwargs):
        ad = request.env['escrow.ad'].sudo().with_context(system='escrow').search([
            ('id', '=', kwargs['id']),
            ('broker_id', '=', request.env.user.partner_id.id),
            ('company_id', '=', request.env.company.id),
        ])
        if not ad:
            return {'error': _('Ad cannot be found, or you are not allowed to delete it.')}

        ad.unlink()
        return {}

    @route(['/my/iban/check'], type='json', auth='user', methods=['POST'], website=True)
    def check_iban(self, **kwargs):
        try:
            iban = kwargs.get('iban', '').replace(' ', '').upper()
            vat = kwargs.get('vat', '')
            
            if not iban:
                return {
                    'success': False,
                    'message': 'IBAN is required'
                }
            
            if not iban.startswith('TR') or len(iban) != 26:
                return {
                    'success': False,
                    'message': 'Invalid IBAN format'
                }

            company = request.env.company
            if hasattr(company, 'syncops_check_iban') and company.syncops_check_iban:
                user = request.env.user
                if user.has_group('payment_syncops.group_check_iban'):
                    cached_iban = request.env['syncops.partner.iban'].sudo().search([('name', '=', iban)])
                    if cached_iban:
                        return {
                            'success': True,
                            'message': 'IBAN doğrulandı (önbellekten)'
                        }
                    
                    try:
                        result, message = request.env['syncops.connector'].sudo()._execute(
                            'other_get_ozan_iban', 
                            reference=str(user.partner_id.id), 
                            params={
                                'vat': vat,
                                'iban': iban,
                            }, 
                            company=company, 
                            message=True
                        )
                        
                        if result is None:
                            return {
                                'success': False,
                                'message': message or 'IBAN doğrulama servisi kullanılamıyor'
                            }
                        elif not result[0]['ok']:
                            return {
                                'success': False,
                                'message': result[0]['message'] or 'IBAN doğrulanamadı'
                            }
                        else:
                            request.env['syncops.partner.iban'].sudo().create({'name': iban})
                            return {
                                'success': True,
                                'message': 'IBAN başarıyla doğrulandı'
                            }
                    except Exception as e:
                        return {
                            'success': False,
                            'message': 'IBAN doğrulama hatası: ' + str(e)
                        }
            return {
                'success': True,
                'message': 'IBAN formatı geçerli (temel doğrulama)'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': 'Beklenmeyen hata: ' + str(e)
            }

    @route(['/my/seller/save'], type='json', auth='user', methods=['POST'], website=True)
    def save_seller_info(self, **kwargs):
        company = request.env.company
        try:
            partner_data = {
                'paylox_escrow_type': 'owner',
                'is_company': kwargs.get('seller_type') == 'corporate',
                'system': 'escrow',
                'street': 'Merkez',
                'paylox_tax_office': 'Merkez'

            }
            iban = kwargs.get('seller_iban', '')
            vat = kwargs.get('seller_tax_number', '') if kwargs.get('seller_type') == 'corporate' else kwargs.get('seller_tc_number', '')

            if kwargs.get('seller_type') == 'corporate':
                partner_data.update({
                    'name': kwargs.get('seller_name', ''),
                    'email': kwargs.get('seller_email', ''),
                    'mobile': kwargs.get('seller_phone', ''),
                    'vat': kwargs.get('seller_tax_number', ''),
                    'comment': 'Yetkili Kişi: ' + kwargs.get('seller_contact_person', ''),
                    'is_company': True,
                })
            else:
                partner_data.update({
                    'name': kwargs.get('seller_name', ''),
                    'email': kwargs.get('seller_email', ''),
                    'mobile': kwargs.get('seller_phone', ''),
                    'vat': kwargs.get('seller_tc_number', ''),
                    'comment': 'Doğum Tarihi: ' + kwargs.get('seller_birthdate', ''),
                    'is_company': False,
                })
            
            if kwargs.get('seller_iban'):
                iban_info = f"IBAN: {kwargs.get('seller_iban', '')}"
                if kwargs.get('seller_iban_name'):
                    iban_info += f" - Hesap Adı: {kwargs.get('seller_iban_name', '')}"
                
                if partner_data.get('comment'):
                    partner_data['comment'] += f"\n{iban_info}"
                else:
                    partner_data['comment'] = iban_info

            if kwargs.get('seller_city'):
                partner_data['state_id'] = int(kwargs.get('seller_city'))

            partner_field = company._get_payment_partner_unique_field()
            partner = request.env['res.partner'].sudo().search([(partner_field, '=', partner_data[partner_field]), ('company_id', '=', company.id), ('paylox_escrow_type', '=', 'owner')], limit=1)
            if not partner:
                partner = request.env['res.partner'].sudo().create(partner_data)
            else:
                partner.write(partner_data)

            iban_verified = self.verify_iban(iban, vat)
            if kwargs.get('seller_iban') and not iban_verified:
                iban_raw = kwargs.get('seller_iban', '')
                iban_sanitized = sanitize_account_number(iban_raw)
                bank = request.env['res.partner.bank'].sudo()
                bank_vals = {
                    'partner_id': partner.id,

                    'acc_number': iban_raw.replace(' ', ''),
                    'api_merchant': kwargs.get('seller_iban_name', ''),
                    'currency_id': request.env.company.currency_id.id,
                    'acc_holder_name': kwargs.get('seller_iban_name', ''),
                }
                existing = bank.search([
                    ('partner_id.vat', '=', vat),
                    ('company_id', '=', request.env.company.id),
                    ('sanitized_acc_number', '=', iban_sanitized),
                ], limit=1)
                if existing:
                    existing.write(bank_vals)
                if not existing:
                    existing = bank.create(bank_vals)
                existing.action_api_query()
                if not existing.api_state:
                    return {
                        'success': False,
                        'state': existing.api_state,
                        'partner_id': partner.id,
                        'message': existing.api_message
                    }
            if kwargs.get('ad_id'):
                ad = request.env['escrow.ad'].sudo().with_context(system='escrow').search([('id', '=', int(kwargs.get('ad_id'))), ('company_id', '=', company.id)], limit=1)
                if ad:
                    ad.owner_id = partner.id
                    item = request.env['payment.item'].sudo().search([('ad_id', '=', ad.id)], limit=1)
                    if item:
                        item.parent_id = partner.id
            return {
                'success': True,
                'partner_id': partner.id,
                'message': 'Seller information has been successfully saved.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Seller information could not be saved.'
            }

    @route('/my/partner/lookup', type='json', auth='public', methods=['POST'], csrf=False)
    def lookup_partner_by_identity(self, **kwargs):
        try:
            identity = kwargs.get('identity', '').strip()
            customer_type = kwargs.get('seller_type', kwargs.get('customer_type', 'individual'))
            lookup_type = kwargs.get('type', 'owner') 

            if not identity:
                return {'success': False, 'message': 'Identity number is required'}
            
            company = request.env.company
            search_field = 'vat'
            partner = request.env['res.partner'].sudo().search([
                (search_field, '=', identity),
                ('company_id', '=', company.id),
                ('paylox_escrow_type', '=', lookup_type),
                ('is_company', '=', customer_type == 'corporate')
            ], limit=1)
            
            if partner:
                return {
                    'success': True,
                    'found': True,
                    'data': {
                        'name': partner.name,
                        'email': partner.email,
                        'phone': partner.mobile or partner.phone,
                        'address': partner.street or '',
                        'city': partner.state_id.id if partner.state_id else False,
                        'is_otp_verified': partner.is_otp_verified,
                        'tax_office': getattr(partner, 'paylox_tax_office', '') if customer_type == 'corporate' else '',
                        'vat': partner.vat,
                        'contact_person': getattr(partner, 'contact_person', '') if customer_type == 'corporate' else '',
                        'bank_ids': [{
                            'id': bank.id,
                            'acc_number': bank.acc_number,
                            'acc_holder_name': bank.acc_holder_name,
                            'api_merchant': bank.api_merchant,
                            'api_state': bank.api_state,
                            'api_message': bank.api_message,
                        } for bank in partner.bank_ids]
                    }
                }
            else:
                return {
                    'success': True,
                    'found': False,
                    'message': 'No existing customer found with this identity number'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error looking up customer: {str(e)}'
            }

    @route('/payment/escrow/customer/card-holder/update', type='json', auth='user', methods=['POST'], website=True)
    def update_card_holder_name(self, **kwargs):
        try:
            partner = request.env['res.partner'].sudo().browse(kwargs.get('partner_id'))
            if not partner.exists():
                return {'success': False, 'message': 'Partner not found'}
            card_holder_partner = request.env['res.partner'].sudo().search([('paylox_escrow_type', '=', 'card_holder'), ('vat', '=', kwargs.get('vat'))], limit=1)
            card_holder_data = {
                'name': kwargs.get('name', ''),
                'email': kwargs.get('email', ''),
                'mobile': kwargs.get('phone', ''),
                'vat': kwargs.get('vat', ''),
                'is_company': False,
                'escrow_customer_id': partner.id,
                'paylox_escrow_type': 'card_holder',
                'system': 'escrow'
            }
            if card_holder_partner:
                card_holder_partner.write(card_holder_data)
            else:
                card_holder_partner = request.env['res.partner'].sudo().create(card_holder_data)
            return {'success': True, 'partner': {
                'id': card_holder_partner.id,
                'name': card_holder_partner.name,
                'email': card_holder_partner.email,
                'phone': card_holder_partner.mobile,
                'vat': card_holder_partner.vat,
            }}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @route('/my/customer/save', type='json', auth='public', methods=['POST'], csrf=False)
    def save_customer_info(self, **kwargs):
        company = request.env.company
        try:
            partner_data = {
                'paylox_escrow_type': 'customer',
                'is_company': kwargs.get('customer_type') == 'corporate',
                "system": 'escrow'
            }

            if kwargs.get('customer_type') == 'corporate':
                partner_data.update({
                    'name': kwargs.get('customer_corporate_title', ''),
                    'email': kwargs.get('customer_email', ''),
                    'mobile': kwargs.get('customer_phone', ''),
                    'phone': kwargs.get('customer_phone', ''),
                    'vat': kwargs.get('customer_tax_number', ''),
                    'street': kwargs.get('customer_address', ''),
                    'paylox_tax_office': kwargs.get('customer_tax_office', ''),
                    'is_company': True,
                })
            else:
                partner_data.update({
                    'name': kwargs.get('customer_name_surname', ''),
                    'email': kwargs.get('customer_email', ''),
                    'mobile': kwargs.get('customer_phone', ''),
                    'phone': kwargs.get('customer_phone', ''),
                    'vat': kwargs.get('customer_identity', ''),
                    'street': kwargs.get('customer_address', ''),
                    'is_company': False,
                })
            partner_field = company._get_payment_partner_unique_field()
            partner = request.env['res.partner'].sudo().search([(partner_field, '=', partner_data[partner_field]), ('company_id', '=', company.id), ('paylox_escrow_type', '=', 'customer')])
            partner_data.update({
                'is_escrow_customer': True
            })
            if not partner:
                partner = request.env['res.partner'].sudo().create(partner_data)
            else:
                partner.write(partner_data)
            product_id = kwargs.get('product_id')
            if product_id:
                try:
                    product = request.env['escrow.ad'].sudo().browse(int(product_id))
                    _logger.error(f"Associating customer {partner.id} with product {product.id}")
                    if product.exists():
                        for customer in product.customer_ids:
                            if not customer.id == partner.id:
                                customer.write({'is_escrow_customer': False})
                        product.write({'customer_ids': [(4, partner.id)]})
                except Exception as e:
                    _logger.error(f"Error associating customer with product: {str(e)}")
            
            return {
                'success': True,
                'partner_id': partner.id,
                'message': 'Customer information has been successfully saved.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Customer information could not be saved.'
            }

    @route('/my/partner/get', type='json', auth='public', methods=['POST'], csrf=False)
    def get_partner_info(self, **kwargs):
        try:
            partner_id = kwargs.get('partner_id')
            if not partner_id:
                return {
                    'success': False,
                    'error': 'missing_partner_id',
                    'message': 'Partner ID is required.'
                }
            
            partner = request.env['res.partner'].sudo().browse(int(partner_id))
            if not partner.exists():
                return {
                    'success': False,
                    'error': 'partner_not_found',
                    'message': 'Partner could not be found.'
                }
            
            bank_accounts = []
            for bank in partner.bank_ids:
                bank_accounts.append({
                    'id': bank.id,
                    'acc_number': bank.acc_number,
                    'api_merchant': bank.acc_holder_name,
                    'bank_name': bank.bank_id.name if bank.bank_id else '',
                    'is_verified': bank.api_state,
                })
            
            partner_data = {
                'id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'phone': partner.mobile,
                'mobile': partner.mobile,
                'street': partner.street,
                'street2': partner.street2,
                'city': partner.city,
                'zip': partner.zip,
                'vat': partner.vat,
                'is_otp_verified': partner.is_otp_verified,
                'is_company': partner.is_company,
                'is_escrow_customer': partner.is_escrow_customer,
                'commercial_partner_id': {
                    'id': partner.commercial_partner_id.id,
                    'name': partner.commercial_partner_id.name
                } if partner.commercial_partner_id else None,
                'state_id': {
                    'id': partner.state_id.id,
                    'name': partner.state_id.name
                } if partner.state_id else None,
                'country_id': {
                    'id': partner.country_id.id,
                    'name': partner.country_id.name
                } if partner.country_id else None,
                'bank_ids': bank_accounts,
            }

            return {
                'success': True,
                'partner': partner_data
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'An error occurred while retrieving partner information.'
            }

    @http.route('/payment/escrow/attachment/<int:attachment_id>/download', type='http', auth='public', csrf=False)
    def download_attachment_with_token(self, attachment_id, token=None, **kwargs):
        try:
            if not token:
                return request.not_found()
            
            transaction = request.env['payment.transaction'].sudo().search([
                ('jetcheckout_order_id', '=', token),
                ('conveyance_attachment_id', '=', attachment_id),
                ('system', '=', 'escrow')
            ], limit=1)
            
            if not transaction.exists():
                return request.not_found()
            
            attachment = request.env['ir.attachment'].sudo().browse(attachment_id)
            if not attachment.exists():
                return request.not_found()
            
            return request.env['ir.http'].sudo()._get_content_common(
                xmlid=None,
                model='ir.attachment',
                res_id=attachment_id,
                field='datas',
                filename=attachment.name,
                filename_field='name',
                unique=None,
                mimetype=attachment.mimetype,
                download=True,
                token=None,
                access_token=None
            )
            
        except Exception as e:
            _logger.error(f"Error downloading attachment with token: {str(e)}")
            return request.not_found()

    @http.route('/payment/escrow/upload-conveyance', type='json', auth='user', methods=['POST'])
    def upload_conveyance_file(self, **kwargs):
        try:
            file_name = kwargs.get('file_name')
            file_data = kwargs.get('file_data')
            file_type = kwargs.get('file_type')
            payment_id = kwargs.get('payment_id')
            
            if not file_data or not payment_id or not file_name:
                return {
                    'success': False,
                    'error': 'Missing file data, file name, or payment_id parameter'
                }
            payment = request.env['payment.transaction'].sudo().browse(int(payment_id))
            if not payment.exists():
                return {
                    'success': False,
                    'error': 'Payment transaction not found'
                }
            try:
                file_content = base64.b64decode(file_data)
            except Exception as e:
                return {
                    'success': False,
                    'error': 'Invalid base64 file data'
                }
            
            if not file_content:
                return {
                    'success': False,
                    'error': 'Empty file uploaded'
                }
            if len(file_content) > 10 * 1024 * 1024:
                return {
                    'success': False,
                    'error': 'File too large. Maximum size is 10MB'
                }
            allowed_types = ['image/png', 'image/jpeg', 'image/gif', 'application/pdf']
            if file_type not in allowed_types:
                return {
                    'success': False,
                    'error': 'Invalid file type. Only PNG, JPEG, GIF, and PDF files are allowed'
                }
            attachment = request.env['ir.attachment'].sudo().create({
                'name': file_name,
                'datas': file_data,
                'mimetype': file_type,
                'res_model': 'payment.transaction',
                'res_id': payment.id,
                'description': 'Conveyance form for payment transaction'
            })
            payment.sudo().write({
                'conveyance_attachment_id': attachment.id,
                'conveyance_upload_date': fields.Datetime.now(),
            })

            body = _('Conveyance form has been sent. User IP Address is %s') % (request.httprequest.remote_addr,)
            attachment = payment.conveyance_attachment_id
            payment.sudo().message_post(body=body, attachment_ids=attachment.ids)
            
            return {
                'success': True,
                'attachment_id': attachment.id,
                'filename': file_name,
                'message': 'File uploaded successfully'
            }
            
        except Exception as e:
            _logger.error(f"Error uploading conveyance file: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'An error occurred while uploading the file'
            }

    @route('/escrow/register', type='json', auth='public', methods=['POST'], csrf=False)
    def escrow_register(self, **kwargs):
        try:
            company = request.env.company
            step = kwargs.get('step', 1)
            user_type = kwargs.get('user_type', 'corporate')
            base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
            dealer_referral_code = kwargs.get('dealer_referral_code')
            if dealer_referral_code:
                dealer = request.env['res.partner'].sudo().search([
                    ('paylox_escrow_type', '=', 'dealer'),
                    ('dealer_referral_code', '=', '%s/escrow/broker/register/%s' % (base_url, dealer_referral_code)),
                    ('company_id', '=', company.id),
                ], limit=1)
                if dealer:
                    kwargs['referred_by_id'] = dealer.id
            
            if step == 1:
                if user_type == 'individual':
                    required_fields = ['vat', 'name','sign_name', 'state_id', 'city', 'person', 'phone', 'email', 'iban', 'iban_name']
                else: 
                    required_fields = ['tax_number', 'company_title', 'sign_name', 'state_id', 'city', 'person', 'phone', 'email', 'iban', 'iban_name']
                
                for field in required_fields:
                    if not kwargs.get(field):
                        return {
                            'success': False,
                            'message': f'Missing required field: {field}'
                        }
                
                vat_number = kwargs.get('vat') if user_type == 'individual' else kwargs.get('tax_number')
                existing_broker = request.env['res.partner'].sudo().search([
                    ('vat', '=', vat_number),
                    ('paylox_escrow_type', '=', kwargs.get('user_register_type')),
                    ('company_id', '=', company.id),
                ], limit=1)
                if existing_broker and existing_broker.approval_state in ['pending', 'approved']:
                    return {
                        'success': True,
                        'registered': True,
                        'partner_id': existing_broker.id,
                        'message': _('Broker with this tax/identity number already exists. Please proceed to the next step.')
                    }
                if existing_broker and existing_broker.approval_state not in ['pending', 'approved']:
                    return {
                        'success': True,
                        'registered': False,
                        'partner_id': existing_broker.id,
                        'message': _('Broker with this tax/identity number already exists. Please proceed to the next step.')
                    }
                
                if user_type == 'individual':
                    partner_vals = {
                        'name': kwargs.get('name'),
                        'vat': kwargs.get('vat'),
                        'email': kwargs.get('email'),
                        'sign_name': kwargs.get('sign_name'),
                        'mobile': kwargs.get('phone'),
                        'state_id': int(kwargs.get('state_id')),
                        'authorized_person': kwargs.get('person'),
                        'paylox_tax_office': kwargs.get('tax_office', 'Merkez'),
                        'city': kwargs.get('city'),
                        'is_company': False,
                        'company_id': company.id,
                        'paylox_escrow_type': kwargs.get('user_register_type'),
                        'system': 'escrow',
                        'broker_dealer_id': kwargs.get('referred_by_id'),
                    }
                else:
                    partner_vals = {
                        'name': kwargs.get('company_title'),
                        'vat': kwargs.get('tax_number'),
                        'email': kwargs.get('email'),
                        'mobile': kwargs.get('phone'),
                        'state_id': int(kwargs.get('state_id')),
                        'sign_name': kwargs.get('sign_name'),
                        'authorized_person': kwargs.get('person'),
                        'paylox_tax_office': kwargs.get('tax_office', 'Merkez'),
                        'city': kwargs.get('city'),
                        'is_company': True,
                        'company_id': company.id,
                        'paylox_escrow_type': kwargs.get('user_register_type'),
                        'system': 'escrow',
                        'broker_dealer_id': kwargs.get('referred_by_id'),
                    }
                
                partner = request.env['res.partner'].sudo().create(partner_vals)
                try:
                    iban = kwargs.get('iban', '')
                    vat = kwargs.get('vat') if user_type == 'individual' else kwargs.get('tax_number', '')
                    iban_verified = self.verify_iban(iban, vat)
                    if iban and not iban_verified:
                        iban_raw = kwargs.get('iban', '')
                        iban_sanitized = sanitize_account_number(iban_raw)
                        bank = request.env['res.partner.bank'].sudo()
                        bank_vals = {
                            'partner_id': partner.id,
                            'acc_number': iban_raw.replace(' ', ''),
                            'api_merchant': kwargs.get('iban_name', ''),
                            'currency_id': company.currency_id.id,
                            'acc_holder_name': kwargs.get('iban_name', ''),
                        }
                        existing_bank = bank.search([
                            ('partner_id.vat', '=', vat),
                            ('company_id', '=', company.id),
                            ('sanitized_acc_number', '=', iban_sanitized),
                        ], limit=1)
                        if not existing_bank:
                            existing_bank = bank.create(bank_vals)
                        
                        if not existing_bank.api_state:
                            return {
                                'success': False,
                                'partner_id': partner.id,
                                'message': existing_bank.api_message or 'Bank account verification failed'
                            }
                except Exception as e:
                    return {
                        'success': False,
                        'partner_id': partner.id,
                        'message': 'Bank account verification error: ' + str(e)
                    }
                
                return {
                    'success': True,
                    'partner_id': partner.id,
                    'message': 'Company information saved successfully'
                }
            
            elif step == 2:
                partner_vals = {}
                broker = request.env['res.partner'].sudo().browse(int(kwargs.get('partner_id')))
                if not broker.exists():
                    return {
                        'success': False,
                        'message': 'Session expired. Please start over.'
                    }
                
                required_files = []
                user_register_type = kwargs.get('user_register_type', 'broker')
                user_type = kwargs.get('user_type', 'individual')
                
                if user_register_type == 'dealer':
                    if user_type == 'individual':
                        required_files = ['identity_doc', 'residence_doc', 'criminal_record_doc']
                    else:
                        required_files = ['identity_doc', 'tax_plate', 'signature_circular']
                else: 
                    required_files = ['tax_plate', 'signature_circular', 'identity_doc', 'authorization_doc']
                for file_field in required_files:
                    if not kwargs.get(file_field):
                        return {
                            'success': False,
                            'message': f'Missing required document: {file_field}'
                        }
                
                for file_field in required_files:
                    file_data = kwargs.get(file_field)
                    file_name = kwargs.get(f'{file_field}_filename')
                    
                    if not file_name:
                        if file_data and ',' in file_data:
                            mime_part = file_data.split(',')[0]
                            if 'image/jpeg' in mime_part or 'image/jpg' in mime_part:
                                file_name = f'{file_field}.jpg'
                            elif 'image/png' in mime_part:
                                file_name = f'{file_field}.png'
                            elif 'image/gif' in mime_part:
                                file_name = f'{file_field}.gif'
                            elif 'application/pdf' in mime_part:
                                file_name = f'{file_field}.pdf'
                            else:
                                file_name = f'{file_field}.pdf'
                        else:
                            file_name = f'{file_field}.pdf'
                    
                    if file_data:
                        if ',' in file_data:
                            file_data = file_data.split(',')[1]
                        
                        partner_vals[file_field] = file_data
                        partner_vals[f'{file_field}_filename'] = file_name
                
                broker.write(partner_vals)
                broker.action_set_to_pending()
                
                return {
                    'success': True,
                    'broker_id': broker.id,
                    'message': 'Your registration has been submitted successfully. You will be notified via email once it is reviewed.'
                }
            
        except Exception as e:
            _logger.error(f"Error in broker registration: {str(e)}")
            request.env.cr.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': 'An error occurred while processing your registration'
            }

    def _get_broker_agreements(self):
        company = request.env.company.sudo()
        if company.parent_id:
            company = company.parent_id
        if not company.system_agreement:
            return []

        domain = [
            ('active', '=', True),
            ('page_ids.path', 'like', '/escrow/broker/register%'),
            ('company_id', '=', company.id),
        ]

        today = fields.Date.today()
        domain += [
            '|', ('date_start', '=', False), ('date_start', '<=', today),
            '|', ('date_end', '=', False), ('date_end', '>=', today),
        ]
        return request.env['payment.agreement'].sudo().search(domain)
    
    def _get_dealer_agreements(self):
        company = request.env.company.sudo()
        if company.parent_id:
            company = company.parent_id
        if not company.system_agreement:
            return []

        domain = [
            ('active', '=', True),
            ('page_ids.path', 'like', '/escrow/dealer/register%'),
            ('company_id', '=', company.id),
        ]

        today = fields.Date.today()
        domain += [
            '|', ('date_start', '=', False), ('date_start', '<=', today),
            '|', ('date_end', '=', False), ('date_end', '>=', today),
        ]
        return request.env['payment.agreement'].sudo().search(domain)

    @route([
        '/escrow/<string:register_type>/register',
        '/escrow/<string:register_type>/register/<string:dealer_referral_code>'
    ], type='http', auth='public', website=True, csrf=False)
    def escrow_register_page(self, register_type, dealer_referral_code=None, **kwargs):
        company = request.env.company
        
        allowed_types = ['broker', 'dealer']
        if register_type not in allowed_types:
            return request.not_found()
        
        states = request.env['res.country.state'].sudo().search([
            ('country_id.code', '=', 'TR')
        ], order='name')
        
        agreements = getattr(self, '_get_' + register_type + '_agreements', lambda: [])()
        
        values = {
            'company': company,
            'website': request.website,
            'states': states,
            'agreements': agreements,
            'register_type': register_type,
            'dealer_referral_code': dealer_referral_code or '',
        }
        return request.render('payment_escrow.page_escrow_register', values)

    @route('/my/broker/transactions', type='http', auth='user', website=True)
    def broker_transactions_page(self, **kwargs):
        user = request.env.user
        partner = user.partner_id
        
        if partner.paylox_escrow_type != 'broker':
            return request.redirect('/my')

        baskets = request.env['payment.transaction.basket'].sudo().search([
            ('partner_id', '=', partner.id),
            ('transaction_id.state', '=', 'done'),
        ], order='transaction_date desc')

        values = {
            'baskets': baskets,
            'page_name': 'broker_transactions',
        }
        return request.render('payment_escrow.broker_transactions_page', values)

    @route('/my/broker/transaction/upload_invoice', type='json', auth='user', website=True, methods=['POST'], csrf=False)
    def broker_upload_invoice(self, **kwargs):
        basket_id = kwargs.get('basket_id')
        basket = request.env['payment.transaction.basket'].sudo().browse(int(basket_id))
        
        if not basket.exists():
            return {'success': False, 'message': 'Transaction basket not found'}
        
        invoice_file = kwargs.get('invoice_file')
        filename = kwargs.get('filename', 'invoice.pdf')
        mimetype = kwargs.get('mimetype', 'application/pdf')
        
        if invoice_file:
            attachment = request.env['ir.attachment'].sudo().create({
                'name': filename,
                'datas': invoice_file,
                'res_model': 'payment.transaction.basket',
                'res_id': basket.id,
                'mimetype': mimetype,
            })
            
            basket.sudo().write({
                'broker_invoice_id': attachment.id,
                'broker_invoice_upload_date': fields.Datetime.now(),
                'transfer_status': 'can_approve',
            })
            
            return {'success': True, 'message': 'Invoice uploaded successfully'}
        
        return {'success': False, 'message': 'No file provided'}

    @route('/my/broker/transaction/<int:basket_id>/submit_for_approval', type='http', auth='user', website=True, methods=['POST'], csrf=False)
    def broker_submit_for_approval(self, basket_id, **kwargs):
        basket = request.env['payment.transaction.basket'].sudo().browse(basket_id)
        basket.write({
            'broker_submitted_for_approval': True,
            'broker_submit_date': fields.Datetime.now(),
        })
        return request.redirect('/my/broker/transactions')

    @route('/escrow/insurance/brands', type='json', auth='user', website=True, methods=['POST'], csrf=False)
    def escrow_insurance_brands(self, **kwargs):
        try:
            company = request.env.company
            if not company.escrow_insurance_quote_enabled:
                return {
                    'success': False,
                    'message': _('Insurance quote feature is not enabled')
                }

            year = kwargs.get('year') or kwargs.get('model_year') or kwargs.get('modelYear')

            if not year:
                return {
                    'success': False,
                    'message': _('Model year is required')
                }

            payload = {
                'year': year,
                'usage': '1',
            }

            result, message = request.env['syncops.connector'].sudo()._execute(
                'insurance_get_vehicle_brands',
                reference=str(request.env.user.partner_id.id),
                params=payload,
                company=company,
                message=True
            )

            if result is None:
                return {
                    'success': False,
                    'message': message or _('Unable to fetch vehicle brands')
                }

            response = result[0] if result else {}
            success_flag = str(response.get('success', True)).lower() == 'true'
            if not success_flag:
                return {
                    'success': False,
                    'message': response.get('message') or message or _('Unable to fetch vehicle brands'),
                    'errors': response.get('errors') or []
                }

            result_block = response.get('result') or {}
            raw_brands = result_block.get('brands') or []
            options = []
            for item in raw_brands:
                code = item.get('brandId') or item.get('brand_id') or item.get('id')
                label = item.get('brand') or item.get('label') or item.get('name') or ''
                name = label
                if label and ' - ' in label:
                    name = label.split(' - ', 1)[1]
                if code:
                    options.append({
                        'code': code,
                        'label': label or name,
                        'name': (name or '').strip(),
                    })

            return {
                'success': True,
                'data': options,
            }
        except Exception as e:
            _logger.exception('Error fetching insurance brands: %s', str(e))
            return {
                'success': False,
                'message': _('Unable to fetch vehicle brands. %s') % str(e)
            }

    @route('/escrow/insurance/models', type='json', auth='user', website=True, methods=['POST'], csrf=False)
    def escrow_insurance_models(self, **kwargs):
        try:
            company = request.env.company
            if not company.escrow_insurance_quote_enabled:
                return {
                    'success': False,
                    'message': _('Insurance quote feature is not enabled')
                }

            year = kwargs.get('year') or kwargs.get('model_year') or kwargs.get('modelYear')
            brand_code = kwargs.get('brand_code') or kwargs.get('brandCode') or kwargs.get('brand_id')

            if not year or not brand_code:
                return {
                    'success': False,
                    'message': _('Model year and brand are required')
                }

            payload = {
                'year': year,
                'usage': '1',
                'brand_id': brand_code,
            }

            result, message = request.env['syncops.connector'].sudo()._execute(
                'insurance_get_vehicle_models',
                reference=str(request.env.user.partner_id.id),
                params=payload,
                company=company,
                message=True
            )

            if result is None:
                return {
                    'success': False,
                    'message': message or _('Unable to fetch vehicle models')
                }

            response = result[0] if result else {}
            success_flag = str(response.get('success', True)).lower() == 'true'
            if not success_flag:
                return {
                    'success': False,
                    'message': response.get('message') or message or _('Unable to fetch vehicle models'),
                    'errors': response.get('errors') or []
                }

            result_block = response.get('result') or {}
            raw_models = result_block.get('models') or []
            options = []
            for item in raw_models:
                code = item.get('makeId') or item.get('modelId') or item.get('model_id')
                label = item.get('model') or item.get('label') or item.get('name') or ''
                brand_name = item.get('brand') or ''
                if code:
                    options.append({
                        'code': code,
                        'label': (label or code).strip(),
                        'brand': (brand_name or '').strip(),
                    })

            return {
                'success': True,
                'data': options,
            }
        except Exception as e:
            _logger.exception('Error fetching insurance models: %s', str(e))
            return {
                'success': False,
                'message': _('Unable to fetch vehicle models. %s') % str(e)
            }
    
    @route('/escrow/insurance/quote', type='json', auth='user', website=True, methods=['POST'], csrf=False)
    def escrow_insurance_quote(self, **kwargs):
        """Handle insurance quote request from frontend"""
        try:
            company = request.env.company
            if not company.escrow_insurance_quote_enabled:
                return {
                    'success': False,
                    'message': _('Insurance quote feature is not enabled')
                }
            
            partner = request.env.user.partner_id

            birth_date_str = kwargs.get('birth_date')
            brand_code = kwargs.get('brand_code') or kwargs.get('brandCode') or kwargs.get('brand_id')
            model_code = kwargs.get('model_code') or kwargs.get('modelCode') or kwargs.get('model_id')
            model_name = kwargs.get('model_name') or kwargs.get('modelName') or kwargs.get('model')
            year = kwargs.get('year') or kwargs.get('model_year') or kwargs.get('modelYear')
            brand_name = kwargs.get('brand_name') or kwargs.get('brandName')
            birth_date = datetime.strptime(birth_date_str, '%d%m%Y').date().strftime('%Y-%m-%d')

            values = {
                'birth_date': birth_date,
                'vat': kwargs.get('vat'),
                'mobile': kwargs.get('gsmNo'),
                'email': kwargs.get('email'),
                'plate': kwargs.get('plate'),
                'license_no': kwargs.get('license_no'),
                'brand_id': brand_code,
                'brand_name': brand_name,
                'model_id': model_code,
                'model_name': model_name,
                'year': year,
                'person_name': partner.name,
                'partner_id': partner.id,
                'company_id': company.id,
                'state': 'draft',
                'notes': brand_name and _('Vehicle Brand: %s') % brand_name or False,
            }

            quotes = request.env['escrow.insurance.quote'].sudo().create_quotes(values)

            return {
                'success': True,
                'quotes': quotes
            }
        except Exception as e:
            _logger.exception('Error creating insurance quote: %s', str(e))
            return {
                'success': False,
                'message': _('An error occurred while processing your request. Please try again later. %s' % str(e))
            }


    @route('/my/dealer/transactions', type='http', auth='user', website=True)
    def dealer_transactions_page(self, **kwargs):
        user = request.env.user
        partner = user.partner_id
        
        if partner.paylox_escrow_type != 'dealer':
            return request.redirect('/my')
        
        brokers = request.env['res.partner'].sudo().search([
            ('broker_dealer_id', '=', partner.id),
            ('paylox_escrow_type', '=', 'broker'),
        ])
        
        dealer_baskets = request.env['payment.transaction.basket'].sudo().search([
            ('partner_id', '=', partner.id),
            ('transaction_id.state', '=', 'done'),
        ], order='transaction_date desc')
        
        broker_bank_map = {}
        broker_banks = request.env['res.partner.bank'].sudo().search([
            ('partner_id', 'in', brokers.ids),
        ])
        for bank in broker_banks:
            broker_bank_map[bank.api_ref] = bank.partner_id
        
        basket_broker_map = {}
        for dealer_basket in dealer_baskets:
            broker_basket = request.env['payment.transaction.basket'].sudo().search([
                ('transaction_id', '=', dealer_basket.transaction_id.id),
                ('partner_id', 'in', brokers.ids),
            ], limit=1)
            if broker_basket:
                broker = broker_basket.partner_id
                basket_broker_map[dealer_basket.id] = broker
        
        broker_transactions = {}
        broker_volumes = {}
        for basket in dealer_baskets:
            broker = basket_broker_map.get(basket.id, False)
            broker_id = broker.id if broker else 0
            broker_transactions[broker_id] = broker_transactions.get(broker_id, 0) + 1
            broker_volumes[broker_id] = broker_volumes.get(broker_id, 0.0) + basket.transfer_amount
        
        total_transactions = len(dealer_baskets)
        total_volume = sum(dealer_baskets.mapped('transfer_amount'))
        
        currency = request.env.company.currency_id
        
        dealer_referral_code = partner.dealer_referral_code if partner.dealer_referral_code else ''
        
        commission_rates = partner.dealer_commission_rate_ids.filtered('active')
        values = {
            'baskets': dealer_baskets,
            'brokers': brokers,
            'basket_broker_map': basket_broker_map,
            'broker_transactions': broker_transactions,
            'broker_volumes': broker_volumes,
            'broker_stats': {
                'total_brokers': len(brokers),
                'total_transactions': total_transactions,
                'total_volume': total_volume,
            },
            'currency': currency,
            'dealer_referral_code': dealer_referral_code,
            'commission_rates': commission_rates,
            'page_name': 'dealer_transactions',
        }
        return request.render('payment_escrow.dealer_transactions_page', values)

