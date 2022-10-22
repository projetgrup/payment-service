��    ,      |  ;   �      �  ]   �  �   '  B   �  �  0  
     	   '     1     B     P     X     a     q      �  	   �     �     �     �     �     �     �     �  &   
     1     C     T     h     q          �     �     �     �     �     �     �     �     �     �                     /  6   8  ;  o  V   �  �     ?   �  �       �'  
   �'     �'     (     (  
   '(     2(     D(  (   `(     �(     �(     �(     �(     �(  	   �(     �(     �(  %   �(     %)     9)     J)  	   ])     g)     {)     �)     �)     �)  &   �)  
   �)     �)     �)     �)     �)     �)     *     -*     5*  
   G*  0   R*                              ,   
      &      #      "       !                          %               (                             +      '   $      	         *                              )              <strong class="h4">Thank You!</strong><br/>There is not any unpaid transaction related to you <strong class="text-primary font-weight-bold z-index-1 flex-fill">Payment</strong>
                                <strong class="text-primary font-weight-bold text-right z-index-1">Amount</strong> <strong class="text-primary font-weight-bold">Information</strong> <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">
<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">
<tbody>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="top" style="font-size: 13px;">
                    <div>
                        Hello <t t-out="object.name or ''">Marc Demo</t>,<br/><br/>
                        Successful transaction information as follows.<br/><br/>
                        Transaction Owner Company : <t t-esc="ctx['partner'].name or ''"/><br/>
                        Transaction Date : <t t-out="ctx['tx'].last_state_change.strftime('%d.%m.%Y %H:%M:%S')">01.01.2022 00:00:00</t><br/><br/>
                        Transaction Amount : <t t-esc="format_amount(ctx['tx'].jetcheckout_payment_amount, ctx['tx'].currency_id) or ''"/><br/>
                        Installment Count : <t t-esc="ctx['tx'].jetcheckout_installment_description or ''"/><br/><br/>
                        <div style="margin: 16px 0px 16px 0px; text-align: center;">
                            <a t-att-href="'%s/report/html/payment_jetcheckout.payment_receipt/%s' % (ctx['url'], ctx['tx'].id)" style="display: inline-block; padding: 10px; text-decoration: none; font-size: 12px; background-color: #875A7B; color: #fff; border-radius: 5px;">
                                <strong>Receipt</strong>
                            </a>
                            <a t-att-href="'%s/report/html/payment_jetcheckout.payment_conveyance/%s' % (ctx['url'], ctx['tx'].id)" style="display: inline-block; padding: 10px; text-decoration: none; font-size: 12px; background-color: #875A7B; color: #fff; border-radius: 5px;">
                                <strong>Conveyance</strong>
                            </a>
                        </div>
                    </div>
                </td></tr>
                <tr><td style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle" align="left">
                    <t t-out="ctx['company'].name or ''">YourCompany</t>
                </td></tr>
                <tr><td valign="middle" align="left" style="opacity: 0.7;">
                    <t t-out="ctx['company'].phone or ''">+1 650-123-4567</t>
                    <t t-if="ctx['company'].email">
                        | <a t-attf-href="'mailto:%s' % {{ ctx['company'].email }}" style="text-decoration:none; color: #454748;" t-out="ctx['company'].email or ''">info@yourcompany.com</a>
                    </t>
                    <t t-if="ctx['company'].website">
                        | <a t-attf-href="'%s' % {{ ctx['company'].website }}" style="text-decoration:none; color: #454748;" t-out="ctx['company'].website or ''">http://www.example.com</a>
                    </t>
                </td></tr>
            </table>
        </td>
    </tr>
</tbody>
</table>
</td></tr>
</table> Authorized Companies Company Settings Configuration Contact Contacts Create a vendor Create a vendor contact Created payments are listed here Dashboard Email Settings Email Templates HTTP Routing Mail Servers Manager Menu No payments yet Payment - {{ object.company_id.name }} Payment Acquirers Payment Settings Payment Transaction Payments SMS Providers SMS Settings SMS Templates Settings System Transaction: Successful Email Transactions User Users VPS Vendor Vendor Payment Email Vendor Payment System Vendors Website Settings Websites {{ ctx['url'] }} | Successful Transaction Notification Project-Id-Version: Odoo Server 15.0-20220110
Report-Msgid-Bugs-To: 
PO-Revision-Date: 2022-10-22 18:00+0300
Last-Translator: 
Language-Team: 
Language: tr
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=2; plural=(n != 1);
X-Generator: Poedit 3.1.1
 <strong class="h4">Teşekkür Ederiz!</strong><br/>Size ait ödenmemiş bir işlem yok <strong class="text-primary font-weight-bold z-index-1 flex-fill">Ödeme</strong>
                                <strong class="text-primary font-weight-bold text-right z-index-1">Tutar</strong> <strong class="text-primary font-weight-bold">Bilgiler</strong> <table border="0" cellpadding="0" cellspacing="0" style="padding-top: 16px; background-color: #F1F1F1; font-family:Verdana, Arial,sans-serif; color: #454748; width: 100%; border-collapse:separate;"><tr><td align="center">
<table border="0" cellpadding="0" cellspacing="0" width="590" style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">
<tbody>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="top" style="font-size: 13px;">
                    <div>
                        Merhaba <t t-out="object.name or ''">Marc Demo</t>,<br/><br/>
                        Başarılı işlem bilgileri aşağıdaki gibidir.<br/><br/>
                        İşlem Geçen Firma : <t t-esc="ctx['partner'].name or ''"/><br/>
                        İşlem Tarihi : <t t-out="ctx['tx'].last_state_change.strftime('%d.%m.%Y %H:%M:%S')">01.01.2022 00:00:00</t><br/><br/>
                        İşlem Tutarı : <t t-esc="format_amount(ctx['tx'].jetcheckout_payment_amount, ctx['tx'].currency_id) or ''"/><br/>
                        Taksit Sayısı : <t t-esc="ctx['tx'].jetcheckout_installment_description or ''"/><br/><br/>
                        <div style="margin: 16px 0px 16px 0px; text-align: center;">
                            <a t-att-href="'%s/report/html/payment_jetcheckout.payment_receipt/%s' % (ctx['url'], ctx['tx'].id)" style="display: inline-block; padding: 10px; text-decoration: none; font-size: 12px; background-color: #875A7B; color: #fff; border-radius: 5px;">
                                <strong>Makbuz</strong>
                            </a>
                            <a t-att-href="'%s/report/html/payment_jetcheckout.payment_conveyance/%s' % (ctx['url'], ctx['tx'].id)" style="display: inline-block; padding: 10px; text-decoration: none; font-size: 12px; background-color: #875A7B; color: #fff; border-radius: 5px;">
                                <strong>Temlikname</strong>
                            </a>
                        </div>
                    </div>
                </td></tr>
                <tr><td style="text-align:center;">
                  <hr width="100%" style="background-color:rgb(204,204,204);border:medium none;clear:both;display:block;font-size:0px;min-height:1px;line-height:0; margin: 16px 0px 16px 0px;"/>
                </td></tr>
            </table>
        </td>
    </tr>
    <tr>
        <td align="center" style="min-width: 590px;">
            <table border="0" cellpadding="0" cellspacing="0" width="590" style="min-width: 590px; background-color: white; font-size: 11px; padding: 0px 8px 0px 8px; border-collapse:separate;">
                <tr><td valign="middle" align="left">
                    <t t-out="ctx['company'].name or ''">YourCompany</t>
                </td></tr>
                <tr><td valign="middle" align="left" style="opacity: 0.7;">
                    <t t-out="ctx['company'].phone or ''">+1 650-123-4567</t>
                    <t t-if="ctx['company'].email">
                        | <a t-attf-href="'mailto:%s' % {{ ctx['company'].email }}" style="text-decoration:none; color: #454748;" t-out="ctx['company'].email or ''">info@yourcompany.com</a>
                    </t>
                    <t t-if="ctx['company'].website">
                        | <a t-attf-href="'%s' % {{ ctx['company'].website }}" style="text-decoration:none; color: #454748;" t-out="ctx['company'].website or ''">http://www.example.com</a>
                    </t>
                </td></tr>
            </table>
        </td>
    </tr>
</tbody>
</table>
</td></tr>
</table> Yetkili Şirketler Şirket Ayarları Yapılandırma Yetkili Yetkililer Bir bayi oluştur Bir bayi yetkilisi oluştur Oluşturulan ödemeler burada listelenir Panel Eposta Ayarları Eposta Şablonları HTTP Yönlendirme Eposta Sunucuları Yönetici Menü Henüz bir ödeme yok Ödeme - {{ object.company_id.name }} Ödeme Alıcıları Ödeme Ayarları Ödeme İşlemleri Ödemeler SMS Sağlayıcılar SMS Ayarları SMS Şablonları Ayarlar Sistem Ödeme İşlemi: Başarılı Epostası İşlemler Kullanıcı Kullanıcılar BTS Bayi Bayi Tahsilat Epostası Bayi Tahsilat Sistemi Bayiler Website Ayarları Websiteler {{ ctx['url'] }} | Başarılı İşlem Bildirimi 