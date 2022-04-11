odoo.define('payment_student.payment_page', function (require) {
"use strict";

var core = require('web.core');
var publicWidget = require('web.public.widget');
var utils = require('web.utils');
var rpc = require('web.rpc');
var dialog = require('web.Dialog');

var round_di = utils.round_decimals;
var qweb = core.qweb;
var _t = core._t;

publicWidget.registry.StudentPaymentPage = publicWidget.Widget.extend({
    selector: '.payment-student #wrapwrap',
    xmlDependencies: ['/payment_student/static/src/xml/templates.xml'],

    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self.$pivot = $('.payment-student div.payment-pivot');
            self.$items = $('.payment-student input.payment-items');
            self.$items_all = $('.payment-student input.payment-all-items');
            self.$tags = $('.payment-student button.btn-payments');
            self.$currency = $('#currency');
            self.precision = parseInt(self.$currency.data('decimal')) || 2;
            self.$amount = $('#amount');
            self.$amount_installment = $('#amount_installment');
            self.$advance_discount = $('#advance_discount');
            self.$maximum_discount = $('#maximum_discount').val();
            self.$sibling_discount = $('#sibling_discount');
            self.$privacy = $('#student_privacy_policy');
            self.$agreement = $('#student_distant_sale_agreement');
            self.$membership = $('#student_membership_agreement');
            self.$contact = $('#student_contact');

            self.$pivot.html($(qweb.render('payment_student.pivot', {'table': false})));
            self.$items.on('change', self.onChangePaid.bind(self));
            self.$items_all.on('change', self.onChangePaidAll.bind(self));
            self.$tags.on('click', self.onClickTag.bind(self));
            self.$privacy.on('click', self.onClickPrivacy.bind(self));
            self.$agreement.on('click', self.onClickAgreement.bind(self));
            self.$membership.on('click', self.onClickMembership.bind(self));
            self.$contact.on('click', self.onClickContact.bind(self));

            self.onChangePaid();
        });
    },

    onChangePaidAll: function (ev) {
        if (this.$items_all.prop('checked')) {
            this.$items.prop('checked', true);
        } else {
            this.$items.prop('checked', false);
        }
        this.onChangePaid();
    },

    onClickTag: function (ev) {
        const $button = $(ev.currentTarget);
        const pid = $button.data('id');
        $button.toggleClass('btn-light');

        _.each(this.$items, function(item) {
            var $el = $(item);
            if ($el.data('type-id') === pid) {
                if ($button.hasClass('btn-light')) {
                    $el.prop('checked', false);
                    $el.closest('tr').addClass('d-none');
                } else {
                    $el.prop('checked', true);
                    $el.closest('tr').removeClass('d-none');
                }
            }
        });
        this.onChangePaid();
    },

    onChangePaid: function (ev) {
        const $items = $('.payment-student input.payment-items:checked');
        if ($items.length) {
            this.$items_all.prop('checked', true);
        } else {
            this.$items_all.prop('checked', false);
        }

        var self = this;
        var student_ids = [];
        var payment_ids = [];
        var bursary_ids = [];
        var students = [];
        var payments = [];
        var bursaries = [];
        var siblings = [];
        var discounts = [];
        var subpayments = [];
        var subsiblings = [];
        var subbursaries = [];
        var totals = [];

        $items.each(function () {
            const $el = $(this);
            const student_id = parseInt($el.data('student-id')) || 0;
            const bursary_id = parseInt($el.data('bursary-id')) || 0;
            const term_id = parseInt($el.data('term-id')) || 0;
            const type_id = parseInt($el.data('type-id')) || 0;

            if (!payment_ids.filter(x => x[0] === term_id && x[1] === type_id).length) {
                payment_ids.push([term_id, type_id]);
                payments.push({
                    'term_id': term_id,
                    'type_id': type_id,
                    'name': $el.data('term-name') + ' | ' + $el.data('type-name'),
                    'amount': [],
                });
            }

            if (!bursary_ids.includes(bursary_id)) {
                bursary_ids.push(bursary_id);
                bursaries.push({
                    'id': bursary_id,
                    'name': $el.data('bursary-name'),
                    'amount': [],
                });
            }

            if (!student_ids.includes(student_id)) {
                student_ids.push(student_id);
                students.push({
                    'id': student_id,
                    'name': $el.data('student-name'),
                });
            }
        });

        student_ids.sort();
        payment_ids.sort((x, y) => x[0] - y[0]);
        bursary_ids.sort();
        students.sort((x, y) => x.id - y.id);
        payments.sort((x, y) => x.term_id - y.term_id);
        payments.sort((x, y) => x.type_id - y.type_id);
        bursaries.sort((x, y) => x.id - y.id);

        student_ids.forEach(function (student) {
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

        let advance_discount = parseFloat(this.$advance_discount.val()) || 0;
        let sibling_discount = 0;
        if (siblings.length > 1 || siblings.length === 1 && $items.filter('[data-sibling-paid="True"]').length) {
            sibling_discount = parseFloat(this.$sibling_discount.val()) || 0;
        }

        $items.each(function () {
            const $el = $(this);
            const student_id = parseInt($el.data('student-id')) || 0;
            const bursary_id = parseInt($el.data('bursary-id')) || 0;
            const term_id = parseInt($el.data('term-id')) || 0;
            const type_id = parseInt($el.data('type-id')) || 0;
            const amount = parseFloat($el.data('amount')) || 0;
            const discount_amount = advance_discount / -100;

            let sibling_amount = sibling_discount / -100;
            let bursary_amount = parseFloat($el.data('bursary-amount')) || 0;

            if (self.$maximum_discount === '1') {
                if (sibling_amount > bursary_amount) {
                    sibling_amount = 0
                } else {
                    bursary_amount = 0
                }
            }

            const payment = payments.filter(t => t.term_id === term_id && t.type_id === type_id)[0];
            const payment_item = payment.amount.filter(t => t.id === student_id)[0];
            payment_item.amount += round_di(amount, self.precision);

            const subpayment_item = subpayments.filter(s => s.id === student_id)[0];
            subpayment_item.amount += round_di(amount, self.precision);

            const sibling_item = siblings.filter(s => s.id === student_id)[0];
            sibling_item.amount = round_di(subpayment_item.amount * sibling_amount, self.precision);

            const subsibling_item = subsiblings.filter(s => s.id === student_id)[0];
            subsibling_item.amount = round_di(sibling_item.amount + subpayment_item.amount, self.precision);

            const bursary = bursaries.filter(b => b.id === bursary_id)[0];
            const bursary_item = bursary.amount.filter(b => b.id === student_id)[0];
            bursary_item.amount = round_di(subsibling_item.amount * bursary_amount, self.precision);

            const subbursary_item = subbursaries.filter(s => s.id === student_id)[0];
            subbursary_item.amount = round_di(bursary_item.amount + subsibling_item.amount, self.precision);

            const discount_item = discounts.filter(s => s.id === student_id)[0];
            discount_item.amount = round_di(subbursary_item.amount * discount_amount, self.precision);

            const total_item = totals.filter(s => s.id === student_id)[0];
            total_item.amount = round_di(discount_item.amount + subbursary_item.amount, self.precision);
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
        const amount_installment = amount;

        amount = 0
        totals.forEach(function (e) {
            amount += e.amount;
        });
        totals.push({id: 0, amount: amount});
        const amount_straight = amount;

        if (student_ids.length) {
            this.$pivot.html($(qweb.render('payment_student.pivot', {
                'table': true,
                'widget': this,
                'students': students,
                'payments': payments,
                'bursaries': bursaries,
                'siblings': siblings,
                'discounts': discounts,
                'subpayments': subpayments,
                'subbursaries': subbursaries,
                'subsiblings': subsiblings,
                'totals': totals,
                'advance_discount': advance_discount,
                'sibling_discount': sibling_discount,
                'has_payment': payment_ids.filter(s => s !== 0).length > 1,
                'has_bursary': bursary_ids.filter(s => s !== 0).length,
            })));
        } else {
            this.$pivot.html($(qweb.render('payment_student.pivot', {'table': false})));
        };

        const event = new Event('change');
        this.$amount_installment.val(amount_installment);
        this.$amount_installment[0].dispatchEvent(event);
        this.$amount.val(amount_straight);
        this.$amount[0].dispatchEvent(event);
    },

    format_currency: function(value) {
        const l10n = core._t.database.parameters;
        const formatted = _.str.sprintf('%.' + this.precision + 'f', round_di(value, this.precision) || 0).split('.');
        formatted[0] = utils.insert_thousand_seps(formatted[0]);
        const amount = formatted.join(l10n.decimal_point);
        if (this.$currency.data('position') === 'after') {
            return amount + ' ' + this.$currency.data('symbol');
        } else {
            return this.$currency.data('symbol') + ' ' + amount;
        }
    },

    onClickPrivacy: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        rpc.query({route: '/p/privacy'}).then(function (content) {
            new dialog(this, {
                title: _t('Privacy Policy'),
                $content: $(qweb.render('payment_student.page', {content: content})),
            }).open();
        });
    },

    onClickAgreement: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        rpc.query({route: '/p/agreement'}).then(function (content) {
            new dialog(this, {
                title: _t('Distant Sale Agreement'),
                $content: $(qweb.render('payment_student.page', {content: content})),
            }).open();
        });
    },

    onClickMembership: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        rpc.query({route: '/p/membership'}).then(function (content) {
            new dialog(this, {
                title: _t('Membership Agreement'),
                $content: $(qweb.render('payment_student.page', {content: content})),
            }).open();
        });
    },

    onClickContact: function (ev) {
        ev.stopPropagation();
        ev.preventDefault();
        rpc.query({route: '/p/contact'}).then(function (content) {
            new dialog(this, {
                title: _t('Contact'),
                $content: $(qweb.render('payment_student.page', {content: content})),
            }).open();
        });
    },

});

publicWidget.registry.JetcheckoutPaymentPage.include({
    _getParams: function () {
        const params = this._super.apply(this, arguments);
        const payment_ids = [];
        const $payable_items = $('input[type="checkbox"].payment-items:checked');
        $payable_items.each(function() { payment_ids.push(parseInt($(this).prop('name'))); });
        params['payment_ids'] = payment_ids;
        return params;
    },
});

});