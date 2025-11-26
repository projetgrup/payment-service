/** @odoo-module alias=paylox.page.agreement **/
'use strict';

import rpc from 'web.rpc';
import { _t } from 'web.core';
import dialog from 'web.Dialog';
import payloxPage from 'paylox.page';
import fields from 'paylox.fields';

payloxPage.include({
    init: function (parent, options) {
        this._super(parent, options);
        this.agreement = new fields.element({
            events: [['click', this._onClickAgreement]],
        });
    },

    start: function () {
        window.addEventListener('agreement-added', (ev) => {
            for (const agreement of ev.detail) {
                this.agreement.all[agreement.id] = false;
            }
        });
        return this._super.apply(this, arguments).then(() => {
            if (this.agreement.exist) {
                this.agreement.all = {};
                this.agreement.$.each((_, e) => {
                    const $e = $(e);
                    const id = Number($e.data('id'));
                    const input = $e.find('input');
                    const options = input.data('options');
                    this.agreement.all[id] = {
                        checked: input.is(':checked'),
                        required: input.prop('required'),
                        options: options && JSON.parse(atob(options)) || {},
                    };
                    input.data('options', undefined);
                    this._processOptions(id);
                });
                Object.defineProperty(this.agreement, 'confirmed', {
                    get () {
                        return Object.values(this.all).filter(v => v.required && !v.checked).length === 0;
                    },
                });
            }
        });
    },

    _getParams: function () {
        let params = this._super.apply(this, arguments);
        if (this.agreement.exist) {
            params['agreements'] = Object.entries(this.agreement.all).filter(([k, v]) => v.checked).map(x => Number(x[0]));
        }
        return params;
    },

    _checkData: function () {
        if (!this.agreement.exist) {
            return this._super.apply(this, arguments);
        }

        const type = this.type.selected;
        if (['virtualpos', 'softpos'].includes(type) && !this.agreement.confirmed) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please read and confirm necessary agreements'),
            });
            this._enableButton();
            return false;
        } else {
            return this._super.apply(this, arguments);
        }
    },

    _rejectAgreement: function (el, id) {
        el.find('input').prop('checked', false);
        this.agreement.all[id]['checked'] = false;
        this._processOptions(id);
    },

    _confirmAgreement: function (el, id) {
        el.find('input').prop('checked', true);
        this.agreement.all[id]['checked'] = true;
        this._processOptions(id);
    },

    _processOptions: function (id) {
        const checked = this.agreement.all[id]['checked'];
        const options = this.agreement.all[id]['options'];
        if (options.card_save) {
            if (!isNaN(Number(this.card.token.value))) {
                this.card.token.value = checked ? 0 : -1;
                this._onChangeCardToken();
            }
        }
    },

    _onClickAgreement: function (ev) {
        if (this.agreement.locked) return;

        const item = $(ev.currentTarget);
        const agreement_id = Number(item.data('id'));
        const agreement = this.agreement.all[agreement_id];
        if (ev.target.tagName === 'INPUT' && (agreement.read || !agreement.required)) {
            this.agreement.all[agreement_id]['checked'] = ev.target.checked;
            this._processOptions(agreement_id);
            return;
        };

        ev.stopPropagation();
        ev.preventDefault();

        //const buttons = $('button:not(:disabled)');
        this.agreement.locked = true;
        
        rpc.query({
            route: '/my/agreement',
            params: {
                agreement_id,
                partner_id: this.partner.value,
                currency_id: this.currency.id,
                amount: this.amount.value,
            }
        }).then((a) => {
            if (!a) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
            } else {
                const popup = new dialog(this, {
                    title: a.name,
                    $content: $('<div/>').html(a.body),
                    dialogClass: 'o_payment_agreement_popup',
                    technical: false,
                    buttons: [{
                        text: _t('I have read and confirmed'),
                        classes: 'btn-primary o_btn_preview m-1 flex-fill',
                    }, {
                        text: _t('Close'),
                        classes: 'btn-light m-1 flex-fill d-none',
                    }],
                });
                popup.opened(() => {
                    //const header = popup.$modal.find('.modal-header');
                    const footer = popup.$modal.find('.modal-footer');
                    const body = popup.$modal.find('.modal-body');
                    const confirm = popup.$modal.find('.modal-footer button.btn-primary');
                    const close = popup.$modal.find('.modal-footer button.btn-light');
                    const check = () => {
                        if (!agreement.read && body[0].scrollHeight - body[0].scrollTop - body[0].clientHeight < 10) {
                            agreement.read = true;
                            confirm.prop('disabled', false);
                        }
                    };

                    //header.find('button.close').remove();
                    footer.addClass('justify-content-center');
                    body.addClass('w-100');
                    body.scroll(check);
                    close.after(_.str.sprintf(
                        '<div class="font-italic text-600 mt16 mb-3 px-2 text-center">%s</div>',
                        _t('Please read the whole agreement content entirely to confirm it'),
                    ));
                    close.click(() => {
                        popup.close();
                    });
                    confirm.click(() => {
                        if (agreement.read) {
                            this._confirmAgreement(item, agreement_id);
                            popup.close();
                        } else {
                            this.displayNotification({
                                type: 'warning',
                                title: _t('Warning'),
                                message: _t('Please read the whole agreement content entirely.'),
                            });
                        }
                    });
                    if (!agreement.read) {
                        confirm.prop('disabled', 'disabled');
                    }
                    check();
                })
                popup.open();
            }
        }).guardedCatch(() => {
            this.displayNotification({
                type: 'danger',
                title: _t('Error'),
                message: _t('An error occured. Please contact with your system administrator.'),
            });
        }).finally(() => {
            this.agreement.locked = false;
        });
    },
});
