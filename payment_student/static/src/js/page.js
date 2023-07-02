/** @odoo-module alias=paylox.system.student **/
'use strict';

import core from 'web.core';
import utils from 'web.utils';
import publicWidget from 'web.public.widget';
import systemPage from 'paylox.system.page';
import { format } from 'paylox.tools';

const round_di = utils.round_decimals;
const qweb = core.qweb;

publicWidget.registry.payloxSystemStudent = systemPage.extend({
    selector: '.payment-student #wrapwrap',
    xmlDependencies: (systemPage.prototype.xmlDependencies || []).concat(
        ['/payment_student/static/src/xml/templates.xml']
    ),

    init: function() {
        this._super.apply(this, arguments);
        this.discount = {
            single: new fields({
                default: 0,
            }),
            maximum: new fields({
                default: 0,
            }),
            sibling: new fields({
                default: 0,
            }),
        };
    },

    start: function () {
        const self = this;
        return this._super.apply(this, arguments).then(function () {
            self.pivot.html = $(qweb.render('paylox.student.table', {'table': false}));
        });
    },

    _onChangePaid: function () {
        const $item = $('input[type="checkbox"].payment-items:checked');
        this.items.checked = !!$item.length;

        if (!this.amount.exist) {
            return
        }

        const self = this;
        const studentIds = [];
        const paymentIds = [];
        const bursaryIds = [];
        const students = [];
        const payments = [];
        const bursaries = [];
        const siblings = [];
        const discounts = [];
        const subpayments = [];
        const subsiblings = [];
        const subbursaries = [];
        const totals = [];

        $item.each(function () {
            const $el = $(this);
            const studentId = parseInt($el.data('student-id')) || 0;
            const bursaryId = parseInt($el.data('bursary-id')) || 0;
            const termId = parseInt($el.data('term-id')) || 0;
            const typeId = parseInt($el.data('type-id')) || 0;

            if (!paymentIds.filter(x => x[0] === termId && x[1] === typeId).length) {
                paymentIds.push([termId, typeId]);
                payments.push({
                    'term_id': termId,
                    'type_id': typeId,
                    'name': $el.data('term-name') + ' | ' + $el.data('type-name'),
                    'amount': [],
                });
            }

            if (!bursaryIds.includes(bursaryId)) {
                bursaryIds.push(bursaryId);
                bursaries.push({
                    'id': bursaryId,
                    'name': $el.data('bursary-name'),
                    'amount': [],
                });
            }

            if (!studentIds.includes(studentId)) {
                studentIds.push(studentId);
                students.push({
                    'id': studentId,
                    'name': $el.data('student-name'),
                });
            }
        });

        studentIds.sort();
        paymentIds.sort((x, y) => x[0] - y[0]);
        bursaryIds.sort();
        students.sort((x, y) => x.id - y.id);
        payments.sort((x, y) => x.termId - y.termId);
        payments.sort((x, y) => x.typeId - y.typeId);
        bursaries.sort((x, y) => x.id - y.id);

        studentIds.forEach(function (student) {
            payments.forEach(function (payment) {
                payment.amount.push({id: student, amount: 0});
            });
            bursaries.forEach(function (bursary) {
                bursary.amount.push({id: student, amount: 0});
            });
            siblings.push({id: student, amount: 0});
            discounts.push({id: student, amount: 0});
            subpayments.push({id: student, amount: 0});
            subsiblings.push({id: student, amount: 0});
            subbursaries.push({id: student, amount: 0});
            totals.push({id: student, amount: 0});
        });

        let discountSingle = self.discount.single.value;
        let discountSibling = 0;
        if (siblings.length > 1 || siblings.length === 1 && $item.filter('[data-sibling-paid="True"]').length) {
            discountSibling = self.discount.sibling.value;
        }

        $item.each(function () {
            const $el = $(this);
            const studentId = parseInt($el.data('student-id')) || 0;
            const bursaryId = parseInt($el.data('bursary-id')) || 0;
            const termId = parseInt($el.data('term-id')) || 0;
            const typeId = parseInt($el.data('type-id')) || 0;
            const amount = parseFloat($el.data('amount')) || 0;
            const amountDiscount = discountSingle / -100;

            let amountSibling = discountSibling / -100;
            let amountBursary = parseFloat($el.data('bursary-amount')) || 0;

            if (self.discount.maximum.value == '1') {
                if (amountSibling > amountBursary) {
                    amountSibling = 0
                } else {
                    amountBursary = 0
                }
            }

            const payment = payments.filter(t => t.termId === termId && t.typeId === typeId)[0];
            const itemPayment = payment.amount.filter(t => t.id === studentId)[0];
            itemPayment.amount += round_di(amount, self.currency.decimal);

            const itemSubpayment = subpayments.filter(s => s.id === studentId)[0];
            itemSubpayment.amount += round_di(amount, self.currency.decimal);

            const itemSibling = siblings.filter(s => s.id === studentId)[0];
            itemSibling.amount = round_di(itemSubpayment.amount * amountSibling, self.currency.decimal);

            const itemSubsibling = subsiblings.filter(s => s.id === studentId)[0];
            itemSubsibling.amount = round_di(itemSibling.amount + itemSubpayment.amount, self.currency.decimal);

            const bursary = bursaries.filter(b => b.id === bursaryId)[0];
            const itemBursary = bursary.amount.filter(b => b.id === studentId)[0];
            itemBursary.amount = round_di(itemSubsibling.amount * amountBursary, self.currency.decimal);

            const itemSubbursary = subbursaries.filter(s => s.id === studentId)[0];
            itemSubbursary.amount = round_di(itemBursary.amount + itemSubsibling.amount, self.currency.decimal);

            const itemDiscount = discounts.filter(s => s.id === studentId)[0];
            itemDiscount.amount = round_di(itemSubbursary.amount * amountDiscount, self.currency.decimal);

            const itemTotal = totals.filter(s => s.id === studentId)[0];
            itemTotal.amount = round_di(itemDiscount.amount + itemSubbursary.amount, self.currency.decimal);
        });

        let amount = 0
        payments.forEach(function (payment) {
            payment.amount.forEach(function (e) {
                amount += e.amount;
            });
            payment.amount.push({id: 0, amount: amount});
            amount = 0;
        });

        amount = 0
        bursaries.forEach(function (bursary) {
            bursary.amount.forEach(function (e) {
                amount += e.amount;
            });
            bursary.amount.push({id: 0, amount: amount});
        });
        if (amount === 0) {
            bursaries = false;
        } 

        amount = 0
        siblings.forEach(function (e) {
            amount += e.amount;
        });
        siblings.push({id: 0, amount: amount});
        if (amount === 0) {
            siblings = false;
        }

        amount = 0
        discounts.forEach(function (e) {
            amount += e.amount;
        });
        discounts.push({id: 0, amount: amount});

        amount = 0
        subpayments.forEach(function (e) {
            amount += e.amount;
        });
        subpayments.push({id: 0, amount: amount});

        amount = 0
        subsiblings.forEach(function (e) {
            amount += e.amount;
        });
        subsiblings.push({id: 0, amount: amount});

        amount = 0
        subbursaries.forEach(function (e) {
            amount += e.amount;
        });
        subbursaries.push({id: 0, amount: amount});

        amount = 0
        totals.forEach(function (e) {
            amount += e.amount;
        });
        totals.push({id: 0, amount: amount});
        const amount_straight = amount;

        if (studentIds.length) {
            this.pivot.html = $(qweb.render('paylox.student.table', {
                table: true,
                format: format,
                students: students,
                payments: payments,
                bursaries: bursaries,
                siblings: siblings,
                discounts: discounts,
                subpayments: subpayments,
                subbursaries: subbursaries,
                subsiblings: subsiblings,
                totals: totals,
                discountSingle: discountSingle,
                discountSibling: discountSibling,
                hasPayment: paymentIds.filter(s => s !== 0).length > 1,
                hasBursary: bursaryIds.filter(s => s !== 0).length,
            }));
        } else {
            this.pivot.html = $(qweb.render('paylox.student.table', {'table': false}));
        };

        const event = new Event('change');
        this.amount.value = amount_straight;
        this.amount.$[0].dispatchEvent(event);
    },

});
