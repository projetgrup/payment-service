# -*- coding: utf-8 -*-
import logging
from odoo import _
from odoo.http import route, request
from odoo.exceptions import ValidationError, AccessError, UserError
from odoo.tools.float_utils import float_round
from odoo.addons.portal.controllers import portal
from odoo.addons.payment_jetcheckout_system.controllers.main import PayloxSystemController as Controller
import werkzeug

_logger = logging.getLogger(__name__)


class CustomerPortal(portal.CustomerPortal):

    @route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kwargs):
        system = kwargs.get('system', request.env.company.system)
        if system == 'escrow':
            return request.redirect('/my/ads')
        return super().home(**kwargs)


class PayloxSystemEscrowController(Controller):

    def _get_tx_values(self, **kwargs):
        return {
            'paylox_description': kwargs.get('description', False),
            'jetcheckout_payment_ok': kwargs.get('payment_ok', True),
        }

    def _get_tx_values(self, **kwargs):
        res = super()._get_tx_values(**kwargs)
        system = kwargs.get('system', request.env.company.system)
        if system == 'escrow':
            res.update({
                'jetcheckout_approval_ok': True,
            })
        return res

    def _get_data_values(self, data, transaction, **kwargs):
        values = super()._get_data_values(data, transaction, **kwargs)
        if transaction and transaction.system == 'escrow':
            partner = request.env['res.partner'].sudo().browse(16444) #transaction.paylox_product_ids[0]['product_id']['owner_id'] 
            reference = partner.bank_ids and partner.bank_ids[0]['api_ref']
            if not reference:
                raise ValidationError(_('%s must have at least one bank account which is verified.' % partner.name))

            if transaction.company_id.payment_page_token_wo_commission:
                amount = float_round(transaction.amount * (1 - (transaction.jetcheckout_commission_rate / 100)), 4)
            else:
                amount = float(kwargs['amount'])

            values.update({
                'is_submerchant_payment': True,
                'submerchant_external_id': reference,
                'submerchant_price': amount,
            })
        return values

    @route('/my/ads', type='http', auth='user', methods=['GET', 'POST'], sitemap=False, csrf=False, website=True)
    def page_my_ads(self, **kwargs):
        company = request.env.company
        user = request.env.user
        partner = user.partner_id
        domain = [('company_id', '=', company.id)]
        if user.share:
            domain.append(('broker_id', '=', partner.id))
        ads = request.env['product.product'].sudo().with_context(system='escrow').search(domain)
        values = {
            'ads': ads,
            'partner': partner,
            'company': company,
            'currency': company.currency_id,
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

        return {
            'id': product.id,
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
        """Check IBAN validity using syncOPS if available"""
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
            
            # Check if syncOPS is available and IBAN check is enabled
            # if hasattr(company, 'syncops_check_iban') and company.syncops_check_iban:
            #     user = request.env.user
            #     if user.has_group('payment_syncops.group_check_iban'):
            #         # Check if IBAN was already validated
            #         cached_iban = request.env['syncops.partner.iban'].sudo().search([('name', '=', iban)])
            #         if cached_iban:
            #             return {
            #                 'success': True,
            #                 'message': 'IBAN doğrulandı (önbellekten)'
            #             }
                    
            #         # Use syncOPS to validate IBAN
            #         try:
            #             result, message = request.env['syncops.connector'].sudo()._execute(
            #                 'other_get_ozan_iban', 
            #                 reference=str(user.partner_id.id), 
            #                 params={
            #                     'vat': vat,
            #                     'iban': iban,
            #                 }, 
            #                 company=company, 
            #                 message=True
            #             )
                        
            #             if result is None:
            #                 return {
            #                     'success': False,
            #                     'message': message or 'IBAN doğrulama servisi kullanılamıyor'
            #                 }
            #             elif not result[0]['ok']:
            #                 return {
            #                     'success': False,
            #                     'message': result[0]['message'] or 'IBAN doğrulanamadı'
            #                 }
            #             else:
            #                 # Cache the validated IBAN
            #                 request.env['syncops.partner.iban'].sudo().create({'name': iban})
            #                 return {
            #                     'success': True,
            #                     'message': 'IBAN başarıyla doğrulandı'
            #                 }
            #         except Exception as e:
            #             return {
            #                 'success': False,
            #                 'message': 'IBAN doğrulama hatası: ' + str(e)
            #             }
            
            # If syncOPS is not available, do basic validation only
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
            
            # Validate IBAN if provided
            if iban:
                iban_check = self.check_iban(iban=iban, vat=vat)
                if not iban_check.get('success', False):
                    return {
                        'success': False,
                        'message': 'IBAN Doğrulama Hatası: ' + iban_check.get('message', 'Bilinmeyen hata')
                    }

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
            
            partner = request.env['res.partner'].sudo().create(partner_data)
            
            if kwargs.get('seller_iban'):
                bank_data = {
                    'partner_id': partner.id,
                    'acc_number': kwargs.get('seller_iban', '').replace(' ', ''),
                    'api_merchant': kwargs.get('seller_iban_name', ''),
                    'currency_id': request.env.company.currency_id.id,
                }
                request.env['res.partner.bank'].sudo().create(bank_data)
            
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

    @route('/my/customer/save', type='json', auth='public', methods=['POST'], csrf=False)
    def save_customer_info(self, **kwargs):
        try:
            # Common fields for both individual and corporate
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
            
            partner = request.env['res.partner'].sudo().create(partner_data)
            
            product_id = kwargs.get('product_id')
            if product_id:
                try:
                    product = request.env['product.product'].sudo().browse(int(product_id))
                    if product.exists():
                        product.write({'escrow_customer_id': partner.id})
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
                    'api_merchant': bank.api_merchant,
                    'bank_name': bank.bank_id.name if bank.bank_id else '',
                })
            
            partner_data = {
                'id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'phone': partner.phone,
                'mobile': partner.mobile,
                'street': partner.street,
                'street2': partner.street2,
                'city': partner.city,
                'zip': partner.zip,
                'vat': partner.vat,
                'is_company': partner.is_company,
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


class EscrowPaymentController(Controller):
    
    @route(['/payment/status/<int:tx_id>'], type='json', auth='public', methods=['POST'], sitemap=False, csrf=False)
    def payment_status(self, tx_id, **kwargs):
        """Check payment transaction status"""
        try:
            tx = request.env['payment.transaction'].sudo().browse(tx_id)
            if tx.exists():
                return {'status': tx.state}
            return {'status': 'not_found'}
        except Exception as e:
            _logger.error("Error checking payment status: %s", e)
            return {'status': 'error'}

    @route(['/escrow/assignment/form/download'], type='http', auth='public', methods=['GET'], sitemap=False)
    def download_assignment_form(self, **kwargs):
        """Download blank assignment form template"""
        try:
            # Serve the HTML form template that can be printed as PDF
            return request.render('payment_escrow.assignment_form_template')
        except Exception as e:
            _logger.error("Error downloading assignment form: %s", e)
            return request.render('website.404')

    @route(['/escrow/assignment/form/upload'], type='json', auth='public', methods=['POST'], sitemap=False, csrf=False)
    def upload_assignment_form(self, **kwargs):
        """Upload signed assignment form"""
        try:
            assignment_form = request.httprequest.files.get('assignment_form')
            
            if not assignment_form:
                return {'success': False, 'error': 'No file provided'}

            # Validate file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
            if assignment_form.content_type not in allowed_types:
                return {'success': False, 'error': 'Invalid file type. Only PDF, JPG, and PNG files are allowed.'}

            # Validate file size (max 5MB)
            max_size = 5 * 1024 * 1024
            assignment_form.seek(0, 2)  # Seek to end to get file size
            file_size = assignment_form.tell()
            assignment_form.seek(0)  # Reset to beginning
            
            if file_size > max_size:
                return {'success': False, 'error': 'File size exceeds 5MB limit.'}

            # Read file content
            file_content = assignment_form.read()
            
            # Here you can save the file to database or file system
            # For example, save to ir.attachment
            attachment = request.env['ir.attachment'].sudo().create({
                'name': assignment_form.filename,
                'type': 'binary',
                'datas': file_content,
                'mimetype': assignment_form.content_type,
                'res_model': 'payment.transaction',
                'public': False,
                'description': 'Assignment Form Upload'
            })

            if attachment:
                return {'success': True, 'attachment_id': attachment.id, 'message': 'File uploaded successfully'}
            else:
                return {'success': False, 'error': 'Failed to save file'}

        except Exception as e:
            _logger.error("Error uploading assignment form: %s", e)
            return {'success': False, 'error': 'Upload failed. Please try again.'}