# -*- coding: utf-8 -*-
import requests

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

SENDURL = 'https://api.netgsm.com.tr/sms/send/xml'
CREDITURL = 'https://api.netgsm.com.tr/balance/list/xml'
REPORTURL = 'https://api.netgsm.com.tr/sms/report'
HEADERS = {'content-type': 'application/xml'}
ERRORS = {
    None: ValidationError('Bir hata meydana geldi'),
    '20': UserError('Mesaj metni hatalı veya standart maksimum mesaj sayısını aşıyor'),
    '30': AccessError('Geçersiz kullanıcı adı veya şifre'),
    '40': ValidationError('Kullanılan başlık sistemde tanımlı değil'),
    '50': ValidationError('Abone hesabı ile İYS kontrollü gönderimler yapılamaz'),
    '51': ValidationError('Aboneliğinize tanımlı İYS marka bilgisi bulunamadı'),
    '60': ValidationError('Kayıt Bulunamadı'),
    '70': ValidationError('Hatalı sorgulama'),
    '80': ValidationError('Gönderim sınır aşımı'),
    '85': ValidationError('Mükerrer Gönderim sınır aşımı'),
    '100': ValidationError('Sistem hatası'),
    '101': ValidationError('Sistem hatası'),
}


class ResCompany(models.Model):
    _inherit = 'res.company'

    sms_provider = fields.Selection(selection_add=[('netgsm', 'Netgsm')])
    sms_netgsm_username = fields.Char('Netgsm Username')
    sms_netgsm_password = fields.Char('Netgsm Password')
    sms_netgsm_originator = fields.Char('Netgsm Originator')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sms_netgsm_username = fields.Char(related='company_id.sms_netgsm_username', readonly=False)
    sms_netgsm_password = fields.Char(related='company_id.sms_netgsm_password', readonly=False)
    sms_netgsm_originator = fields.Char(related='company_id.sms_netgsm_originator', readonly=False)

class SmsApi(models.AbstractModel):
    _inherit = 'sms.api'

    @api.model
    def _process_netgsm_sms(self, text):
        if ' ' in text:
            return text.split(' ')
        return text, '0'

    @api.model
    def _send_netgsm_sms(self, messages):
        company = self.env.company
        username = company.sms_netgsm_username
        password = company.sms_netgsm_password
        originator = company.sms_netgsm_originator

        numbers = ['<no>%s</no>' % message['number'] for message in messages]
        message = messages[0]['content'] if messages else ''

        data = f"""<?xml version="1.0" encoding="UTF-8"?>
            <mainbody>
                <header>
                    <company dil="TR">Netgsm</company>       
                    <usercode>{username}</usercode>
                    <password>{password}</password>
                    <type>1:n</type>
                    <msgheader>{originator}</msgheader>
                </header>
                <body>
                    <msg>
                        <![CDATA[{message}]]>
                    </msg>
                    {"".join(numbers)}
                </body>
            </mainbody>"""

        response = requests.post(SENDURL, data=data, headers=HEADERS)
        code, id, *args = self._process_netgsm_sms(response.text)
        if code.startswith('0'):
            return [{'res_id': message['res_id'], 'state': 'success'} for message in messages]
        else:
            raise ERRORS.get(code, ERRORS[None])

    @api.model
    def _get_netgsm_credit(self):
        company = self.env.company
        username = company.sms_netgsm_username
        password = company.sms_netgsm_password
        data = f"""<?xml version='1.0'?>
            <mainbody>
                <header>
                    <usercode>{username}</usercode>
                    <password>{password}</password>
                    <stip>2</stip>
                </header>
            </mainbody>"""

        response = requests.post(CREDITURL, data, headers=HEADERS)
        code, credit, *args = self._process_netgsm_sms(response.text)
        if code.startswith('0'):
            return _('%s SMS credit(s) left') % int(float(credit))
        else:
            raise ERRORS.get(code, ERRORS[None])
