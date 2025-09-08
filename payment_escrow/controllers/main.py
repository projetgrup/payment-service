# -*- coding: utf-8 -*-
import json
import base64
import logging
from urllib.parse import unquote, urlparse
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
    def get_transaction_data(self, product_id=None, **kwargs):
        try:
            if not product_id:
                return {'error': 'No product ID provided'}

            payment_item = request.env['payment.item'].sudo().search([('product_id', '=', int(product_id))], limit=1)
            if not payment_item.exists():
                return {'error': 'Payment item not found'}
            
            transactions = request.env['payment.transaction'].sudo().search([
                ('paylox_transaction_item_ids.item_id', '=', payment_item.id),
                ('state', '=', 'done')
            ], order='create_date desc')
            
            total_amount = payment_item.amount
            paid_amount = sum(tx.amount for tx in transactions)
            remaining_amount = total_amount - paid_amount

            transaction_list = []
            for tx in transactions:
                transaction_list.append({
                    'id': tx.id,
                    'reference': tx.reference,
                    'amount': tx.amount,
                    'date': tx.create_date.isoformat() if tx.create_date else '',
                    'status': tx.state,
                    'payment_method': tx.acquirer_id.name if tx.acquirer_id else 'Unknown'
                })
            
            return {
                'total_amount': total_amount,
                'previous_amount': paid_amount,
                'remaining_amount': remaining_amount,
                'paid': payment_item.paid,
                'transactions': transaction_list,
                'currency': 'TL'
            }
            
        except Exception as e:
            _logger.error("Error in get_transaction_data: %s", str(e))
            return {'error': str(e)}

    def _generate_hash_url(self, step=0, id=0, owner=None, status=None):
        import base64
        import json
        from urllib.parse import quote
        
        values = {
            'i': id,
            's': step,
        }
        
        if owner is not None:
            values['o'] = owner
        if status is not None:
            values['t'] = status
            
        hash_value = base64.b64encode(json.dumps(values).encode('utf-8')).decode('utf-8')
        return f'/my/ads?={quote(hash_value)}'

    def _process(self, **kwargs):
        url, tx, status = super()._process(**kwargs)
        system = kwargs.get('system') or (tx and tx.system) or request.env.company.system
        if system == 'escrow' and tx:
            if tx.state == 'done':
                payment_items_paid = True
                if tx.paylox_transaction_item_ids:
                    for item_line in tx.paylox_transaction_item_ids:
                        payment_item = item_line.item_id
                        if payment_item:
                            if not payment_item.paid:
                                payment_items_paid = False
                                break
                
                product_id = 0
                if tx.paylox_transaction_item_ids:
                    first_item = tx.paylox_transaction_item_ids[0]
                    if first_item.item_id and first_item.item_id.product_id:
                        product_id = first_item.item_id.product_id.id
                
                if payment_items_paid:
                    url = self._generate_hash_url(step=5, id=product_id)
                else:
                    url = self._generate_hash_url(step=5, id=product_id, status='partial')
            else:
                url = self._generate_hash_url(step=5, status='error')
        return url, tx, status

    def _get_tx_values(self, **kwargs):
        res = super()._get_tx_values(**kwargs)
        system = kwargs.get('system', request.env.company.system)
        if system == 'escrow':
            products = kwargs.get('products', [])
            payment_items = request.env['payment.item'].sudo().search([('product_id', 'in', products and [p['pid'] for p in products] or [])])
            res['paylox_transaction_item_ids'] = [(0, 0, {
                    'item_id': rec.id,
                    'amount': kwargs.get('amount', 0.0),
                    'ref': rec.ref,
                    'date': rec.date,
                    'desc': rec.description,
                    'advance': rec.advance,
                })
                for rec in payment_items
            ]
            res.update({
                'jetcheckout_approval_ok': True,
            })
        return res

    def _get_data_values(self, data, transaction, **kwargs):
        values = super()._get_data_values(data, transaction, **kwargs)
        if transaction and transaction.system == 'escrow':

            # if kwargs.get('file'):
            #     for f in kwargs['file']:
            #         if f['type'] == 'conveyance':
            #             attachment = request.env['ir.attachment'].sudo().create({
            #                 'name': _('%s - %s') % (transaction.reference, f['name'] or _('File.pdf')),
            #                 'res_model': transaction._name,
            #                 'res_id': transaction.id,
            #                 'mimetype': f['mimetype'] or 'application/pdf',
            #                 'datas': f['data'],
            #                 'type': 'binary',
            #             })
            #             body = _('User has been signed conveyance. User IP Address is %s') % (transaction.jetcheckout_ip_address or request.httprequest.remote_addr,)
            #             self.message_post(body=body, attachment_ids=attachment.ids)
            #             transaction.message_post()
            #             break
            product = transaction.paylox_product_ids[0]
            customer_basket = []

            partner = transaction.paylox_product_ids[0]['product_id']['escrow_owner_id']
            customers = transaction.paylox_product_ids[0]['product_id']['escrow_customer_ids']
            customer = next((customer for customer in customers if customer.is_escrow_customer), None)
            
            if not customer:
                raise ValidationError(_('No active escrow customer found for this transaction.'))
                
            reference_seller = partner.bank_ids and partner.bank_ids[0]['api_ref']
            if not reference_seller:
                raise ValidationError(_('%s must have at least one bank account which is verified.' % partner.name))

            platform_owner = request.env['res.partner'].sudo().search([('paylox_escrow_type', '=', 'platform_owner')], limit=1)
            infrastructure_provider = request.env['res.partner'].sudo().search([('paylox_escrow_type', '=', 'infrastructure_provider')], limit=1)

            def find_rate(rec, inst):
                if rec and rec.installment_rate_ids:
                    for r in rec.installment_rate_ids:
                        if int(r.installment_count) == inst:
                            return float(r.rate)
                return 0.0

            installment_count = int(transaction.jetcheckout_installment_count or 1)
            seller_net = float(transaction.jetcheckout_payment_amount or 0.0)
            paid = transaction.jetcheckout_payment_paid
            additional_rate = transaction.jetcheckout_additional_rate

            platform_rate = find_rate(platform_owner, installment_count)
            infra_rate = find_rate(infrastructure_provider, installment_count)

            infra_commission = paid * infra_rate
            platform_commission = (paid * additional_rate / 100) - infra_commission
            total_paid = seller_net + infra_commission + platform_commission

            customer_amount = paid * seller_net / total_paid
            customer_basket.append({
                "id": 24,
                "name": product['product_id']['name'],
                "description": product['name'],
                "qty": 1,
                "amount": customer_amount,
                "category": product['product_id']['categ_id']['name'],
                "is_physical": product['product_id']['type'] == 'product',
                "submerchant_external_id": reference_seller,
                "submerchant_price": seller_net
            })
            infra_amount = paid * infra_commission / total_paid
            #infra_commission = float_round(charged * (1 - (infra_rate / 100)), 4) if infra_rate else 0.0
            #platform_commission = float_round(charged * (1 - (platform_rate / 100)), 4) if platform_rate else 0.0
            if infra_commission > 0:
                ref_infra = (infrastructure_provider.bank_ids and infrastructure_provider.bank_ids[0]['api_ref']) or reference_seller
                customer_basket.append({
                    "id": 25,
                    "name": f"{product['product_id']['name']} - Altyapı Komisyonu",
                    "description": f"Altyapı Komisyonu (%{infra_rate})",
                    "qty": 1,
                    "amount": infra_amount,
                    "category": "Komisyon",
                    "is_physical": False,
                    "submerchant_external_id": ref_infra,
                    "submerchant_price": infra_commission
                })
            platform_amount = paid * platform_commission / total_paid
            if platform_commission > 0:
                ref_platform = (platform_owner.bank_ids and platform_owner.bank_ids[0]['api_ref']) or reference_seller
                customer_basket.append({
                    "id": 26,
                    "name": f"{product['product_id']['name']} - Platform Komisyonu",
                    "description": f"Platform Komisyonu (%{platform_rate})",
                    "qty": 1,
                    "amount": platform_amount,
                    "category": "Komisyon",
                    "is_physical": False,
                    "submerchant_external_id": ref_platform,
                    "submerchant_price": platform_commission
                })
            fullname = customer.name.split(' ', 1)
            address = []
            if customer.city:
                address.append(customer.city)
            if customer.state_id:
                address.append(customer.state_id.name)
            if customer.country_id:
                address.append(customer.country_id.name)
            values.update({
                'submerchant_external_id': reference_seller,
                # 'is_submerchant_payment': True,
                'customer_basket': customer_basket,
                'customer':{
                    "name": fullname[0],
                    "surname": fullname[-1],
                    "email": customer.email,
                    "id": str(customer.id),
                    "identity_number": customer.vat,
                    "phone": customer.phone,
                    "ip_address": transaction.jetcheckout_ip_address or request.httprequest.remote_addr,
                    "postal_code": customer.zip,
                    "company": customer.parent_id and customer.parent_id.name or "",
                    "address": ", ".join(address) if address else customer.street or "",
                    "city": customer.state_id and customer.state_id.name or "",
                    "country": customer.country_id and customer.country_id.name or "",
                }
            })
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
        ad = request.env['product.product'].sudo().with_context(system='escrow').search(domain, limit=1)
        if not ad.exists():
            return {'success': False, 'message': 'Ad not found'}

        image = ad.escrow_ad_sale_img
        if image:
            mime = guess_mimetype(base64.b64decode(image))
            image = 'data:%s;base64,%s' % (mime, image.decode('utf-8'))
        return {
            'success': True,
            'ad': {
                'id': ad.id,
                'name': ad.name,
                'description': ad.description,
                'price': ad.list_price,
                'image': image,
                'categ_id': ad.categ_id and {'id': ad.categ_id.id, 'name': ad.categ_id.name} or None,
                'brand_id': ad.escrow_car_brand_id.id,
                'model_id': ad.escrow_car_model_id.id,
                'year': ad.escrow_car_model_year,
                'vin': ad.escrow_car_vin,
                'plate': ad.escrow_car_plate,
                'owner_id': ad.escrow_owner_id.id,
                'customer_id': ad.escrow_customer_ids and [{'id': customer.id, 'name': customer.name} for customer in ad.escrow_customer_ids if customer.is_escrow_customer] or None,
                'broker_id': ad.broker_id.id,
                'item_id': ad.escrow_payment_item_id and ad.escrow_payment_item_id.id or None,
                'paid_amount': ad.escrow_payment_item_id.paid_amount or 0.0
            }
        }

    @route('/my/ads', type='http', auth='user', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True)
    def page_my_ads(self, **kwargs):
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
        domain = [('company_id', '=', company.id)]
        if user.share:
            domain.append(('broker_id', '=', partner.id))
        ads = request.env['product.product'].sudo().with_context(system='escrow').search(domain)

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
            'step': step,
        }
        return request.render('payment_escrow.page_ads', values, headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate, max-age=0',
            'Pragma': 'no-cache',
            'Expires': '-1'
        })

    @route(['/my/ad/<int:id>/image'], type='http', auth='user')
    def page_my_ad_image(self, id):
        return request.env['ir.http'].sudo()._content_image(xmlid=None, model='product.product', res_id=id, field='image_1920', filename_field='name', unique=None, filename=None, mimetype=None, download=None, width=0, height=0, crop=False, quality=0, access_token=None)

    @route(['/my/ad/save'], type='json', auth='user', website=True)
    def page_my_ad_save(self, **kwargs):
        company = request.env.company
        user = request.env.user
        partner = user.partner_id
        values = {}
        
        def generate_product_name():
            brand_name = ""
            model_name = ""
            year = kwargs.get('escrow_car_model_year', '')
            
            if kwargs.get('escrow_car_brand_id'):
                try:
                    brand = request.env['escrow.car.brand'].sudo().browse(int(kwargs['escrow_car_brand_id']))
                    if brand.exists():
                        brand_name = brand.name
                except:
                    pass
            
            if kwargs.get('escrow_car_model_id'):
                try:
                    model = request.env['escrow.car.model'].sudo().browse(int(kwargs['escrow_car_model_id']))
                    if model.exists():
                        model_name = model.name
                except:
                    pass

            name_parts = []
            if brand_name:
                name_parts.append(brand_name)
            if model_name:
                name_parts.append(model_name)
            if year:
                name_parts.append(str(year))
            return " / ".join(name_parts) if name_parts else "Araç İlanı"
        if kwargs.get('id'):
            product = request.env['product.product'].sudo().with_context(system='escrow').search([
                ('id', '=', kwargs['id']),
                ('broker_id', '=', request.env.user.partner_id.id),
                ('company_id', '=', request.env.company.id),
            ])
            if not product:
                return {'error': _('Product cannot be found, or you are not allowed to save it.')}

            values.update({'system': 'escrow', 'broker_id': partner.id, **kwargs})
            
            values['name'] = generate_product_name()
            item = request.env['payment.item'].sudo().search([('product_id', '=', product.id)])
            if item:
                item.write({'amount': kwargs.get('price')})
                values['escrow_payment_item_id'] = item.id
            else:
                values['escrow_payment_item_id'] = item.create({
                    'parent_id': product.escrow_owner_id.id,
                    'product_id': product.id,
                    'amount': kwargs.get('price'),
                    'currency_id': company.currency_id.id,
                })

            if values:
                product.write(values)
        else:
            values.update({
                'system': 'escrow',
                'broker_id': partner.id,
                **kwargs
            })
            
            values['name'] = generate_product_name()

            product = request.env['product.product'].sudo().create(values)
            item = request.env['payment.item'].sudo().create({
                'parent_id': product.escrow_owner_id.id,
                'product_id': product.id,
                'amount': kwargs.get('price'),
                'currency_id': company.currency_id.id,
            })
            product.escrow_payment_item_id = item.id
                
        return {
            'id': product.id,
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
        product = request.env['product.product'].sudo().with_context(system='escrow').search([
            ('id', '=', kwargs['id']),
            ('broker_id', '=', request.env.user.partner_id.id),
            ('company_id', '=', request.env.company.id),
        ])
        if not product:
            return {'error': _('Product cannot be found, or you are not allowed to save it.')}

        product.unlink()
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

            partner_field = company._get_payment_partner_unique_field()
            partner = request.env['res.partner'].sudo().search([(partner_field, '=', partner_data[partner_field]), ('company_id', '=', company.id), ('paylox_escrow_type', '=', 'owner')])
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
                    ('sanitized_acc_number', '=', iban_sanitized),
                    ('company_id', '=', request.env.company.id),
                ], limit=1)

                if not existing:
                    bank.create(bank_vals)
                    if not bank.api_state:
                        return {
                            'success': False,
                            'partner_id': partner.id,
                            'message': bank.api_message
                        }
                #else:
                #    existing.write(bank_vals)

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

    @route('/my/customer/lookup', type='json', auth='public', methods=['POST'], csrf=False)
    def lookup_customer_by_identity(self, **kwargs):
        try:
            identity = kwargs.get('identity', '').strip()
            customer_type = kwargs.get('customer_type', 'individual')
            
            if not identity:
                return {'success': False, 'message': 'Identity number is required'}
            
            company = request.env.company
            search_field = 'vat'
            partner = request.env['res.partner'].sudo().search([
                (search_field, '=', identity),
                ('company_id', '=', company.id),
                ('paylox_escrow_type', '=', 'customer'),
                ('is_company', '=', customer_type == 'corporate')
            ], limit=1)
            
            if partner:
                return {
                    'success': True,
                    'found': True,
                    'customer_data': {
                        'name': partner.name,
                        'email': partner.email,
                        'phone': partner.mobile or partner.phone,
                        'address': partner.street or '',
                        'is_otp_verified': partner.is_otp_verified,
                        'tax_office': getattr(partner, 'paylox_tax_office', '') if customer_type == 'corporate' else '',
                        'vat': partner.vat,
                        'contact_person': getattr(partner, 'contact_person', '') if customer_type == 'corporate' else '',
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

    @route('/my/customer/save', type='json', auth='public', methods=['POST'], csrf=False)
    def save_customer_info(self, **kwargs):
        company = request.env.company
        is_card_holder_different = kwargs.get('is_card_holder_different', False)
        escrow_customer_id = kwargs.get('escrow_customer_id')
        if is_card_holder_different:
            card_holder_data = {
                'name': kwargs.get('customer_name_surname', ''),
                'email': kwargs.get('customer_email', ''),
                'mobile': kwargs.get('customer_phone', ''),
                'vat': kwargs.get('customer_identity', ''),
                'street': kwargs.get('customer_address', ''),
                'is_company': False,
                'escrow_customer_id': escrow_customer_id,
                'paylox_escrow_type': 'card_holder',
                'system': 'escrow'
            }
            card_holder_partner = request.env['res.partner'].sudo().create(card_holder_data)
            return {
                'success': True,
                'partner_id': card_holder_partner.id,
                'message': 'Card holder information has been successfully saved.'
            }
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
                    'vat': kwargs.get('customer_tax_number', ''),
                    'street': kwargs.get('customer_address', ''),
                    'is_company': True,
                })
            else:
                partner_data.update({
                    'name': kwargs.get('customer_name_surname', ''),
                    'email': kwargs.get('customer_email', ''),
                    'mobile': kwargs.get('customer_phone', ''),
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
                    product = request.env['product.product'].sudo().browse(int(product_id))
                    if product.exists():
                        for customer in product.escrow_customer_ids:
                            if not customer.id == partner.id:
                                customer.write({'is_escrow_customer': False})
                        product.write({'escrow_customer_ids': [(4, partner.id)]})
                except:
                    pass 
            
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
