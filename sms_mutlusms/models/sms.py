# -*- coding: utf-8 -*-
import requests

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.sms_api.models.sms import InsufficientCreditError

SENDURL = 'https://smsgw.mutlucell.com/smsgw-ws/sndblkex'
CREDITURL = 'https://smsgw.mutlucell.com/smsgw-ws/gtcrdtex'
HEADERS = {'content-type': 'text/xml; charset=utf-8'}
ERRORS = {
    None: ValidationError('Bir hata meydana geldi'),
    '20': ValidationError('Post edilen xml eksik veya hatalı'),
    '21': AccessError('Kullanılan originatöre sahip değilsiniz'),
    '22': InsufficientCreditError('Kontörünüz yetersiz'),
    '23': AccessError('Kullanıcı adı ya da parolanız hatalı'),
    '24': ValidationError('Şu anda size ait başka bir işlem aktif'),
    '25': ValidationError('SMSC Stopped (Bu hatayı alırsanız, işlemi 1-2 dk sonra tekrar deneyin)'),
    '30': AccessError('Hesap Aktivasyonu sağlanmamış'),
}

class ResCompany(models.Model):
    _inherit = 'res.company'

    sms_provider = fields.Selection(selection_add=[('mutlusms', 'MutluSMS')])
    sms_mutlusms_username = fields.Char('MutluSMS Username')
    sms_mutlusms_password = fields.Char('MutluSMS Password')
    sms_mutlusms_originator = fields.Char('MutluSMS Originator')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sms_mutlusms_username = fields.Char(related='company_id.sms_mutlusms_username', readonly=False)
    sms_mutlusms_password = fields.Char(related='company_id.sms_mutlusms_password', readonly=False)
    sms_mutlusms_originator = fields.Char(related='company_id.sms_mutlusms_originator', readonly=False)

class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'

    @api.model
    def _send_mutlusms_sms(self, messages):
        company = self.env.company
        username = company.sms_mutlusms_username
        password = company.sms_mutlusms_password
        originator = company.sms_mutlusms_originator

        numbers = [message['number'] for message in messages]
        message = messages[0] if messages else ''

        data = f"""<?xml version="1.0" encoding="UTF-8"?>
            <smspack ka="{username}" pwd="{password}" org="{originator}" charset="turkish">
                <mesaj>
                    <metin>{message}</metin>
                    <nums>{",".join(numbers)}</nums>
                </mesaj>
            </smspack>"""

        response = requests.post(SENDURL, data=data.encode('utf-8'), headers=HEADERS)
        code = response.text
        if code.startswith('$'):
            return [{'res_id': message['res_id'], 'state': 'success'} for message in messages]
        else:
            raise ERRORS.get(code, ERRORS[None])

    @api.model
    def _get_mutlusms_credit(self):
        company = self.env.company
        username = company.sms_mutlusms_username
        password = company.sms_mutlusms_password
        data = f"""<?xml version="1.0" encoding="UTF-8"?><smskredi ka="{username}" pwd="{password}"/>"""
        response = requests.post(CREDITURL, data=data.encode('utf-8'), headers=HEADERS)
        code = response.text
        if code.startswith('$'):
            return _('%s SMS credit(s) left') % int(float(code[1:]))
        else:
            raise ERRORS.get(code, ERRORS[None])
