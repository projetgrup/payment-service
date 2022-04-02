JetCheckout
-----------

JetCheckout is an online payment platform designed for corporate businesses.


Payment Service
---------------

Payment Service is an open source part of JetCheckout Platform that offers whitelabel functionality. You can create your own online payment brand.
You can join and follow the news and announcements from Telegram group below.

.. image:: https://jetcheckout.com/web/image/2999-550dbdfc/telegram_channel2.jpg
   :alt: Telegram Announcement Channel Link
   :target: https://t.me/+U6V29rMrOZNkYTk8

.. image:: https://jetcheckout.com/web/image/3003-1d5e6046/telegram_qrcode.png
   :alt: Telegram Announcement Channel QR Link
   :target: https://t.me/+U6V29rMrOZNkYTk8

Functions & Scope
-----------------

**1. Integrated Payment Systems in Turkey**

Paynet | PayTR | Iyzico | OzanPAY

**2. Integrated Virtual POS Systems in Turkey**

Akbank |Alternatifbank | Fibabanka | Halkbank | INGBank | Odeabank | Şekerbank | HSBC | TEB | İş Bankası | Ziraat | Garanti BBVA | Yapı Kredi QNB Finansbank | Vakıfbank | Denizbank | Albaraka | Anadolu Bank | Kuveyt Türk | Türkiye Finans

**3. Independent and Login-Free Payment Page**

**4. Dynamic Lowest Cost Transaction Routing Between Integrated Systems**

**5. Focused Vertical Solutions Specially Produced For Sectoral Needs**

Customer Payments | Dealer Payments | Field Sales Payments | Student Payments


Installation & Configuration Guide
----------------------------------

You can run “JetCheckout Payment Service Platform” on your own server.

**1. Step : Install Odoo as a Business Platform**

Here is the guide that you need to install Odoo as a business platform.

.. image:: https://jetcheckout.com/web/image/3006-b887144a/odoo_install.png
   :alt: Install Odoo as a Business Platform
   :target: https://www.odoo.com/documentation/15.0/administration/install.html
   

**2. Step : Add Payment Service Modules To The Business Platform**

**Git**: The following requires https://git-scm.com to be installed on your machine and that you have basic knowledge of git commands.

* git clone git@github.com:projetgrup/payment-service.git

Navigate to the path of your  payment-service addons path and run **pip3** on the requirements file in a terminal **with root privileges**:

* pip3 install setuptools wheel
* pip3 install -r requirements.txt

Now you have to add the "payment-service" path in the "odoo config" file and restart odoo service.

* nano /etc/odoo/odoo.conf
* addons_path = /../../odoo/addons, <payment-service-path>

Once you finished the process restart the server to configure the file.
You can use the following command to restart the server to configure the file.

* sudo service odoo restart

**3. Step : Install Payment Service Modules and Run Your Own Business**

.. image:: https://jetcheckout.com/web/image/3007-ee096a74/install_addons.gif
   :alt: Install Payment Service Modules


**4. Step : Create Your JetCheckout Account and Connect It To Your Own Business**

Create a JetCheckout account from the link below.

.. image:: https://jetcheckout.com/web/image/2992-01e9d133/jetcheckout_logo.png
   :alt: Create a JetCheckout account
   :target: https://www.jetcheckout.com/web/signup

If you have any problems, please report it to : jetcheckout@projetgrup.com


Developer Tutorials
-------------------

Don't limit your imagination!

* Create your own brand
* Develop your own modules on a stable platform
* Develop vertical solutions, create new markets for yourself

Here is the guide that you need to develop your own modules as addons

.. image:: https://jetcheckout.com/web/image/3005-17af4671/odoo_development.jpg
   :alt: Odoo Addon Development Tutorials
   :target: https://www.odoo.com/documentation/15.0/developer/howtos.html
   
