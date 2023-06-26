odoo.define('payment_jetcheckout_system_otp.otp_page', function (require) {
"use strict";

var config = require('web.config');
var publicWidget = require('web.public.widget');
var core = require('web.core');
var rpc = require('web.rpc');
var framework = require('payment_jetcheckout.framework');

var _t = core._t;

publicWidget.registry.JetcheckoutOtpForm = publicWidget.Widget.extend({
    selector: '.oe_otp_form',
    events: {},
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self.page = 0;
            self.duration = 0;
            self.interval = undefined;
            self.$next = document.getElementById('next');
            self.$previous = document.getElementById('previous');
            self.$card0 = document.getElementById('card0');
            self.$card1 = document.getElementById('card1');
            self.$validate = document.getElementById('submit');
            self.$resend = document.getElementById('resend');
            self.$login = document.getElementById('login');
            self.$code = document.getElementById('code');
            self.$id = document.getElementById('id');
            self.$email = document.getElementById('email');
            self.$phone = document.getElementById('phone');
            self.$vat= document.getElementById('vat');
            self.$ref= document.getElementById('ref');
            self.$countdown = document.getElementById('countdown');
            self.$next.addEventListener('click', self._onSend.bind(self));
            self.$previous.addEventListener('click', self._onPrevious.bind(self));
            self.$validate.addEventListener('click', self._onValidate.bind(self));
            self.$resend.addEventListener('click', self._onResend.bind(self));
            self.$code.addEventListener('change', self._onChangeField.bind(self));
        });
    },

    _onPrevious: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();        
        window.location.reload();    
    },

    _onSend: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();        
        if (!this.$login.value) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please enter your email address or phone number or reference code'),
            });
            this.$login.focus();
            return;
        }

        framework.showLoading();
        var self = this;
        rpc.query({
            route: '/otp/prepare',
            params: this._getParams(),
        }).then(function (result) {
            self.$previous.classList.remove('d-none');
            self.$validate.classList.remove('d-none');
            self.$resend.classList.add('d-none');
            self.duration = 120;
            self.$countdown.innerHTML = self.duration + ' ' + _t('seconds');
            self.interval = setInterval(function() {
                if (self.duration === 0) {
                    clearInterval(self.interval);
                    self.$countdown.innerHTML = _t('expired');
                    self.$validate.classList.add('d-none');
                    self.$resend.classList.remove('d-none');
                    return;
                }
                self.duration -= 1;
                self.$countdown.innerHTML = self.duration + ' ' + _t('seconds');
            }, 1000);
            self.$id.value = result.id;
            self.$email.innerHTML = result.email;
            self.$phone.innerHTML = result.phone;
            self.$vat.innerHTML = result.vat;
            self.$ref.innerHTML = result.ref;
            if (self.page !== 1) {
                self.page = 1;
                self.$next.classList.add('d-none');
                self.$validate.classList.remove('d-none');
                self.$card0.classList.add('fly-left');
                self.$card1.classList.remove('fly-right');
            }
            framework.hideLoading();
        }).guardedCatch(function (error) {
            self.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occured. Please contact with your system administrator.'),
            });
            if (config.isDebug()) {
                console.error(error);
            }
            framework.hideLoading();
        });
    },

    _onResend: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        if (this.duration <= 0) {
            this._onSend(ev)
        }
    },

    _onValidate: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        
        const codeRegex = /^[0-9]\d{3}$/;
        if (!codeRegex.test(this.$code.value)) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Code must be 4 digits'),
            });
            this.$code.focus();
            return;
        }

        var self = this;
        framework.showLoading();
        rpc.query({
            route: '/otp/validate',
            params: this._getParams(),
        }).then(function (result) {
            if ('error' in result) {
                self.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: result.error,
                });
                framework.hideLoading();
                self.$code.focus();
            } else {
                window.location = result.url;
            }
        }).guardedCatch(function (error) {
            self.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occured. Please contact with your system administrator.'),
            });
            if (config.isDebug()) {
                console.error(error);
            }
            framework.hideLoading();
        });
    },

    _getParams: function () {
        return {
            login: this.$login.value,
            code: this.$code.value,
            id: this.$id.value,
        }
    },

    _onChangeField: function (ev) {
        ev.target.classList.remove('border-danger');
        const $label = document.querySelector('label[for=' + ev.target.attributes.id.value + ']');
        $label.classList.remove('text-danger');
    },
});
});