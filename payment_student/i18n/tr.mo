��    o      �  �         `	     a	  ]   u	    �	     �     �     �          &     -  	   ;     E     M     ^     g     m     u  	   z     �     �     �     �     �  3   �     �  =     
   F  
   Q      \     }  	   �  �   �  :   0  E   k     �     �  ,   �  	   �                    /     8     E     H  $   T     y     �     �     �     �     �     �     �  	   �     �     �     �               )  &   1     X     j     z     �     �     �     �     �     �     �  ?   �  O   :     �     �     �     �     �     �     �     �     �     �  c        o     x     �     �  T   �  
     )        B  &   J     q     �     �     �     �     �     �  2   �  8   �     1     7     D     I     O     `     i  �   q  2  �     2  V   J  e  �                    6     Q     W     g     o     t  	   �     �  
   �     �  
   �     �     �     �  
   �     �  4   �     *  O   A  
   �     �  (   �     �     �  �   �  D   �  C   �            .   /     ^     j     w     �     �     �     �     �  ,   �     �               ,  	   ?     I     O  
   R     ]     i          �     �     �     �  %   �     �     �           "      3      D      S      g      w      �   I   �   G   �   	   '!     1!     I!     ]!     k!     |!     �!     �!     �!     �!  f   �!     "     #"     5"     P"  g   i"     �"  3   �"  	   #  (   ##     L#     g#     �#  
   �#     �#     �#  	   �#  6   �#  >   �#     '$  
   4$     ?$     K$     Z$  
   l$     w$  �   �$     "   A   [   %   -   M      8   Z   B   \   l       '   H       I      R         )          ]   $      Q   k          K   g          &      5   D   o   !   b       ,                 m           `       9       0       f      #       n       6             7   a          2       L   ?   T   (       S           V           *   /              e          Y   @      h      d       U   =           1             C       >   N   P   ^   :   E   3   ;   j   G           i   c   F      X   4   
      _   O   .          <       	              W      +              J       <em>Select All</em> <strong class="h4">Thank You!</strong><br/>There is not any unpaid transaction related to you <t t-set="line" t-value="object._get_setting_line()"/>
<p>
    <strong>Dear <i t-out="object.name"/></strong>,
    <br/><br/>
    You can pay register fee of students, who has been already registered at school, for our <t t-out="object._get_payment_terms()"/> services with your credit online
    <t t-if="line"> for <t t-out="line['month']"/> term by choosing either <t t-out="line['installment']"/> installments or single payment with <t t-out="line['percentage']"/>% discount.</t>
    <t t-else="">.</t>
    <br/>
    If you want to view and pay online, <a t-att-href="object._get_payment_url()" style="color:#3079ed;">click here.</a>
    <br/><br/>
    Have a nice day.
    <br/><br/>
    Sincerely...
    <br/><br/>
    <span t-out="object._get_payment_company()"/>
</p> Active Advance Discount Advance Payment Discount Advance Payment Discounts Amount Amount To Pay Bursaries Bursary Bursary Discount Children Class Classes Code Companies Company Company Settings Configuration Contact Create a parent Create a parent and link it to any student you want Create a student Create a student with its parent and start to record payments Created by Created on Created payments are listed here Currency Dashboard Dear {{ object.name }}, for viewing and paying register fee of students, who has been already registered at school, {{ object._get_payment_url(shorten=True) }} Define discounts when processing payment items of siblings Define discounts when processing payment items with straight payments Discount (%) Discount Rate Discount percentage must be higher than zero Discounts Display Name Email Settings Email Templates End Date HTTP Routing ID Installment Installment must be higher than zero Last Modified on Last Updated by Last Updated on Mail Servers Manager Menu Name No email No mobile No payments yet Notifications Parent Parent Payment Email Parent Payment SMS Parents Payment - {{ object.company_id.name }} Payment Acquirers Payment Details Payment Discounts Payment Items Payment Settings Payment Table Payment Templates Payment Transaction Payment Type Payment Types Payment table can be calculated only for non paid payment items Payment table will be displayed here after you select at least one payment item Payments Prepayment Discount SMS Providers SMS Settings SMS Templates SPS School School Settings Schools Select Maximum Discount Select maximum rate between <strong>Sibling Discount</strong> and <strong>Bursary Discount</strong> Settings Sibling Discount Sibling Discount Maximum Sibling Discount Rate Specify Webhook URL Addresses to notify when a successful payment transaction occurs Start Date Start date cannot be higher than end date Student Student Name<br/>School | Class | Type Student Payment System Student Payment Template Students Subtotal System Term Terms There is already a parent with the same email - %s There is already a student with the same Vat Number - %s Total Transactions User Users Website Settings Websites Welcome You can get payment amounts and applied discounts, which is calculated dynamically, with choosing student(s) of yours in the following table. Project-Id-Version: Odoo Server 13.0
Report-Msgid-Bugs-To: 
PO-Revision-Date: 2022-12-24 17:59+0300
Last-Translator: 
Language-Team: 
Language: tr
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Plural-Forms: nplurals=2; plural=(n != 1);
X-Generator: Poedit 3.1.1
 <em>Tümünü Seç</em> <strong class="h4">Teşekkür Ederiz!</strong><br/>Size ait ödenmemiş bir işlem yok <t t-set="line" t-value="object._get_setting_line()"/>
<p>
    <strong>Sayın <i t-out="object.name"/></strong>,
    <br/><br/>
    Okulda kayıtlı bulunan öğrenci veya öğrencileriniz için <t t-out="object._get_payment_terms()"/> hizmetlerimizle ilgili kayıt ücretini 
    <t t-if="line"><t t-out="line['month']"/> dönemi içerisinde kredi kartınız ile online olarak <t t-out="line['installment']"/> taksitle yada tek çekimde %<t t-out="line['percentage']"/> indirim ile ödeyebilirsiniz.</t>
    <t t-else="">kredi kartınız ile online olarak ödeyebilirsiniz.</t>
    <br/>
    İncelemek ve Online Ödeme için <a t-att-href="object._get_payment_url()" style="color:#3079ed;">tıklayınız.</a>
    <br/><br/>
    Sağlıklı bir yıl dileriz.
    <br/><br/>
    Saygılarımızla...
    <br/><br/>
    <span t-out="object._get_payment_company()"/>
</p> Aktif Peşin İndirimi Peşin Ödeme İndirimi Peşin Ödeme İndirimleri Tutar Ödenecek Tutar Burslar Burs Burs İndirimi Çocuklar Sınıf Sınıflar Kod Şirketler Şirket Şirket Ayarları Yapılandırma İletişim Bir veli oluştur Bir veli oluşturun ve bir öğrenciye bağlayınız Bir öğrenci oluştur Velisi ile beraber bir öğrenci oluşturun ve ödemeleri kaydetmeye başlayın Oluşturan Oluşturma Tarihi Oluşturulan ödemeler burada listelenir Para Birimi Panel Sayın {{ object.name }}, öğrencileriniz için hizmetlerimizle ilgili kayıt ücretini incelemek ve ödemek için {{ object._get_payment_url(shorten=True) }} Kardeşlere ait ödeme kalemlerini işlerken indirimler tanımlayın Peşin ödenen ödeme kalemlerini işlerken indirimler tanımlayın İndirim (%) İndirim Oranı İndirim oranı sıfırdan büyük olmalıdır İndirimler Görünen Ad Eposta Ayarları Eposta Şablonları Bitiş Tarihi HTTP Routing ID Taksit Taksit oranı sıfırdan büyük olmalıdır Son Düzenleme Tarihi Son Güncelleyen Son Güncelleme Tarihi Eposta Sunucuları Yönetici Menü Ad Eposta Yok Telefon Yok Henüz bir ödeme yok Bildirimler Veli Veli Tahsilat Epostası Veli Tahsilat SMS Veliler Ödeme - {{ object.company_id.name }} Ödeme Alıcıları Ödeme Detayları Ödeme İndirimleri Ödeme Kalemleri Ödeme Ayarları Ödeme Tablosu Ödeme Şablonları Ödeme İşlemi Ödeme Türü Ödeme Türleri Ödeme tablosu sadece ödenmemiş ödeme satırları için hesaplanabilir Bir ödeme satırı seçtiğinizde ödeme tablosu burada görünecektir Ödemeler Peşin Ödeme İndirimi SMS Sağlayıcılar SMS Ayarları SMS Şablonları ÖTS Okul Okul Ayarları Okullar Maksimum İndirim Seç <strong>Kardeş İndirimi</strong> ve <strong>Burs İndirimi</strong> arasındaki maksimum oranı seç Ayarlar Kardeş İndirimi Maksimum Kardeş İndirimi Kardeş İndirimi Oranı Başarılı bir ödeme işlemi gerçekleştiğinde bildirim yapılacak Webhook URL adreslerini belirtin Başlangıç Tarihi Başlangıç tarihi, bitiş tarihinden sonra olamaz Öğrenci Öğrenci Adı<br/>Okul | Sınıf | Tür Öğrenci Tahsilat Sistemi Öğrenci Ödeme Şablonu Öğrenciler Ara Toplam Sistem Dönem Dönemler Aynı eposta adresine sahip bir veli zaten mevcut - %s Aynı kimlik numarasına sahip bir öğrenci zaten mevcut - %s Genel Toplam İşlemler Kullanıcı Kullanıcılar Website Ayarları Websiteler Hoşgeldiniz Aşağıdaki listelenmiş olan velisi olduğunuz öğrenci veya öğrencilerin seçimlerini yaparak dinamik olarak hesaplanmış olan ödenecek tutar ve uygulanan indirimleri görebilirsiniz. 