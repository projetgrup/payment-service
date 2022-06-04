odoo.define('payment_jetcheckout.signup_page', function (require) {
"use strict";

var config = require('web.config');
var publicWidget = require('web.public.widget');
var {Markup} = require('web.utils');
var core = require('web.core');
var rpc = require('web.rpc');
var framework = require('payment_jetcheckout.framework');

var signup = publicWidget.registry.SignUpForm;
var _t = core._t;

signup.include({
    events: {},
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self.page = 0;
            self.$next = document.getElementById('next');
            self.$previous = document.getElementById('previous');
            self.$card0 = document.getElementById('card0');
            self.$card1 = document.getElementById('card1');
            self.$card2 = document.getElementById('card2');
            self.$button = document.getElementById('submit');
            self.$login = document.getElementById('login');
            self.$name = document.getElementById('name');
            self.$phone = document.getElementById('phone');
            self.$password = document.getElementById('password');
            self.$password2 = document.getElementById('confirm_password');
            self.$company = document.getElementById('company');
            self.$vat = document.getElementById('vat');
            self.$tax = document.getElementById('tax');
            self.$type = document.querySelector('input[name="type"]:checked');
            self.$domain = document.getElementById('domain');
            self.$button = document.getElementById('submit');
            self.$alert = document.getElementById('alert');
            self.domain_state = false;
            self.$domain_info = document.getElementById('domain_info');
            self.$next.addEventListener('click', self._onNextPage.bind(self));
            self.$previous.addEventListener('click', self._onPreviousPage.bind(self));
            self.$button.addEventListener('click', self._onSubmit.bind(self));
            self.$login.addEventListener('change', self._onChangeField.bind(self));
            self.$name.addEventListener('change', self._onChangeField.bind(self));
            self.$phone.addEventListener('change', self._onChangeField.bind(self));
            self.$password.addEventListener('change', self._onChangeField.bind(self));
            self.$password2.addEventListener('change', self._onChangeField.bind(self));
            self.$company.addEventListener('change', self._onChangeField.bind(self));
            self.$vat.addEventListener('change', self._onChangeField.bind(self));
            self.$tax.addEventListener('change', self._onChangeField.bind(self));
            self.$domain.addEventListener('change', self._onChangeDomain.bind(self));
        });
    },

    _onNextPage: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        if (this._checkCards()) {
            if (this.page >= 2) {
                this.page = 2;
            } else {
                this.page += 1;
            }
            this._toggleButtons();
        }
    },

    _onPreviousPage: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const page = this.page;
        if (this.page <= 0) {
            this.page = 0;
        } else {
            this.page -= 1;
        }
        this._toggleButtons(page > this.page);
    },

    _onSubmit: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        var self = this;
        if (this._checkCards()) {
            framework.showLoading();
            rpc.query({
                route: '/web/signup/prepare',
                params: this._getParams(),
            }).then(function (result) {
                if ('error' in result) {
                    self.$alert.classList.remove('d-none');
                    self.$alert.innerHTML = _t('An error occured.') + ' ' + result.error;
                    framework.hideLoading();
                    if (result.element) {
                        if (result.page !== 2) {
                            self.page = result.page;
                            self._toggleButtons(true);
                        }
                        let $el = document.getElementById(result.element);
                        let $label = document.querySelector('label[for=' + result.element + ']');
                        $el.classList.add('border-danger');
                        $label.classList.add('text-danger');
                        //$el.focus();
                    }
                } else {
                    window.location = result.redirect_url;
                }
            }).guardedCatch(function (error) {
                self.$alert.innerHTML = _t('An error occured. Please contact with your system administrator.');
                if (config.isDebug()) {
                    console.error(error);
                }
                framework.hideLoading();
            });
        }
    },

    _getParams: function () {
        return {
            login: this.$login.value,
            name: this.$name.value,
            phone: this.$phone.value,
            password: this.$password.value,
            confirm_password: this.$password2.value,
            company: this.$company.value,
            vat: this.$vat.value,
            tax: this.$tax.value,
            domain: this.$domain.value,
            type: this.$type.value,
        }
    },

    _onChangeField: function (ev) {
        ev.target.classList.remove('border-danger');
        const $label = document.querySelector('label[for=' + ev.target.attributes.id.value + ']');
        $label.classList.remove('text-danger');
    },

    _onChangeDomain: function (ev) {
        var self = this;
        this.domain_state = false;
        let $info = this.$domain_info;
        this._onChangeField(ev);
        $info.innerHTML = '<i class="fa fa-spin fa-circle-o-notch mr-2"></i>' + _t('Loading...');
        $info.classList.remove('d-none');
        $info.classList.remove('bg-100');
        $info.classList.remove('text-primary');
        $info.classList.add('alert-warning');
        rpc.query({
            route: '/web/signup/domain',
            params: {domain: this.$domain.value},
        }).then(function (result) {
            if ('error' in result) {
                $info.innerHTML = result.error;
                self.domain_state = false;
            } else {
                $info.classList.add('bg-100');
                $info.classList.add('text-primary');
                $info.classList.remove('alert-warning');
                $info.innerHTML = result.success;
                self.domain_state = true;
            }
        }).guardedCatch(function (error) {
            $info.innerHtml = _t('An error occured. Please contact with your system administrator.');
            self.domain_state = false;
            if (config.isDebug()) {
                console.error(error);
            }
        });
    },

    _checkCards: function () {
        switch (this.page) {
            case 0:
                const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
                const phoneRegex = /^[+]*[0-9]+$/;
                const passwordRegex = /(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.{8,})/;
                if (!this.$login.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter your email address'),
                    });
                    this.$login.focus();
                    return false;
                } else if (!emailRegex.test(this.$login.value)) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter a valid email address'),
                    });
                    this.$login.focus();
                    return false;
                } else if (!this.$name.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter your name'),
                    });
                    this.$name.focus();
                    return false;
                }  else if (this.$name.value.length < 3) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter a valid name'),
                    });
                    this.$name.focus();
                    return false;
                } else if (!this.$phone.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter your phone'),
                    });
                    this.$phone.focus();
                    return false;
                } else if (!phoneRegex.test(this.$phone.value)) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter a valid phone number'),
                    });
                    this.$phone.focus();
                    return false;
                } else if (!passwordRegex.test(this.$password.value)) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: Markup(_t('Please enter a strong password<br/><br/><small><ul style="padding-inline-start: 20px;"><li>Password must contain at least one lowercase character</li><li>Password must contain at least one uppercase character</li><li>Password must contain at least one numeric character</li><li>Password must be 8 characters or longer</li></ul></small>')),
                    });
                    this.$password.focus();
                    return false;
                } else if (this.$password.value !== this.$password2.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Passwords are not match'),
                    });
                    this.$password2.focus();
                    return false;
                }
                break;
            case 1:
                if (!this.$company.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter your company name'),
                    });
                    this.$company.focus();
                    return false;
                } else if (!this.$vat.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter VAT number'),
                    });
                    this.$vat.focus();
                    return false;
                } else if (!this.$tax.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter tax office'),
                    });
                    this.$tax.focus();
                    return false;
                }
                break;
            case 2:
                const domainRegex = /[a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$/;
                if (!this.$domain.value) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter your domain name'),
                    });
                    this.$domain.focus();
                    return false;
                } else if (!domainRegex.test(this.$domain.value)) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Please enter a valid domain name'),
                    });
                    this.$domain.focus();
                    return false;
                } else if (!this.domain_state) {
                    this.displayNotification({
                        type: 'warning',
                        title: _t('Warning'),
                        message: _t('Your domain is not pointing the correct IP'),
                    });
                    this.$domain.focus();
                    return false;
                }
                break;
            default:
                return false;
        }
        return true;
    },

    _toggleButtons: function (state) {
        switch (this.page) {
            case 0:
                this.$previous.classList.add('d-none');
                this.$next.classList.remove('d-none');
                this.$button.classList.add('d-none');
                this.$card0.classList.remove('fly-left');
                this.$card1.classList.remove('fly-left');
                this.$card1.classList.add('fly-right');
                this.$card2.classList.add('fly-right');
                break;
            case 1:
                this.$previous.classList.remove('d-none');
                this.$next.classList.remove('d-none');
                this.$button.classList.add('d-none');
                if (state) {
                    this.$card1.classList.remove('fly-left');
                    this.$card2.classList.add('fly-right');
                } else {
                    this.$card0.classList.add('fly-left');
                    this.$card1.classList.remove('fly-right');
                }
                break;
            case 2:
                this.$previous.classList.remove('d-none');
                this.$next.classList.add('d-none');
                this.$button.classList.remove('d-none');
                this.$card1.classList.add('fly-left');
                this.$card2.classList.remove('fly-right');
                break;
            default:
                this.$previous.classList.add('d-none');
                this.$button.classList.add('d-none');
                this.$card0.classList.add('d-none');
                this.$card1.classList.add('d-none');
                this.$card2.classList.add('d-none');
        }
    },
});
});