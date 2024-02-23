/** @odoo-module alias=paylox.system.agreement **/
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
        return this._super.apply(this, arguments).then(() => {
            if (this.agreement.exist) {
                this.agreement.all = {};
                this.agreement.ids = [];
                this.agreement.total = this.agreement.$.length;
                this.agreement.$.each((_, e) => {
                    const $e = $(e);
                    const id = Number($e.data('id'));
                    this.agreement.all[id] = $e.find('input').is(':checked');
                    this.agreement.ids.push(id);
                });
                Object.defineProperty(this.agreement, 'count', {
                    get () {
                        return Object.values(this.all).filter(v => v).length;
                    },
                });
                Object.defineProperty(this.agreement, 'confirmed', {
                    get () {
                        return this.total === this.count;
                    },
                });
            }
        });
    },

    _getParams: function () {
        let params = this._super.apply(this, arguments);
        if (this.agreement.exist) {
            params['agreements'] = this.agreement.ids;
        }
        return params;
    },

    _checkData: function () {
        if (!this.agreement.exist) {
            return this._super.apply(this, arguments);
        }

        if (!this.agreement.confirmed) {
            this.displayNotification({
                type: 'warning',
                title: _t('Warning'),
                message: _t('Please read and confirm all agreements'),
            });
            this._enableButton();
            return false;
        } else {
            return this._super.apply(this, arguments);
        }
    },

    _onClickAgreement: function (ev) {
        if(this.agreement.locked) return;
        ev.stopPropagation();
        ev.preventDefault();

        const item = $(ev.currentTarget);
        const agreement_id = Number(item.data('id'));
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
        }).then((agreement) => {
            if (!agreement) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Warning'),
                    message: _t('An error occured. Please contact with your system administrator.'),
                });
            } else {
                const popup = new dialog(this, {
                    title: agreement.name,
                    $content: $('<div/>').html(agreement.body),
                    buttons: [{
                        text: _t('I have read and confirmed'),
                        classes: 'btn-primary',
                    }],
                });
                popup.opened(() => {
                    let read = this.agreement.all[agreement_id];
                    const header = popup.$modal.find('.modal-header');
                    const body = popup.$modal.find('.modal-body');
                    const button = popup.$modal.find('.modal-footer button');
                    const check = () => {
                        if (!read && body[0].scrollHeight - body[0].scrollTop - body[0].clientHeight < 10) {
                            read = true;
                            button.prop('disabled', false);
                        }
                    };

                    header.find('button.close').remove();
                    body.addClass('w-100');
                    body.scroll(check);
                    button.after(_t('<em class="ml8 text-700">Please read the whole agreement content entirely to confirm it</em>'));
                    button.click(() => {
                        if (read) {
                            item.find('input').prop('checked', true);
                            this.agreement.all[agreement_id] = true;
                            popup.close();
                        } else {
                            this.displayNotification({
                                type: 'warning',
                                title: _t('Warning'),
                                message: _t('Please read the whole agreement content entirely.'),
                            });
                        }
                    });
                    if (!read) {
                        button.prop('disabled', 'disabled');
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