odoo.define('point_of_sale.TransactionListScreen', function(require) {
'use strict';

const PosComponent = require('point_of_sale.PosComponent');
const Registries = require('point_of_sale.Registries');
const { useListener } = require('web.custom_hooks');
const { isConnectionError } = require('point_of_sale.utils');

class TransactionListScreen extends PosComponent {
    constructor() {
        super(...arguments);
        useListener('deselect-transaction', () => this._deselectTransaction());
        useListener('select-transaction', () => this._selectTransaction());
        this.state = {
            partner: this.props.partner,
            line: this.props.line,
            id: false,
            amount: 0,
            transactions: [],
        }
    }

    async willStart() {
        await this._getTransactions();
    }

    async _getTransactions() {
        const domain = [
            ['partner_id', '=', this.state.partner.id],
            ['pos_payment_id', '=', false],
            ['pos_method_id', '=', this.state.line.payment_method.id],
            ['state', '=', 'done'],
        ];
        const fields = ['id', 'reference', 'last_state_change', 'amount'];
        this.state.transactions = await this.rpc({
            model: 'payment.transaction',
            method: 'search_read',
            args: [domain, fields],
        },{
            timeout: 5000,
            shadow: true,
        });
    }

    getDate(date) {
        return moment(date).format('DD-MM-YYYY HH:mm:ss');
    }

    async refreshTransactions() {
        await this._getTransactions();
        this.state.transaction = false;
        this.render();
    }

    clickTransaction(id, amount) {
        if (this.state.id === id) {
            this.state.id = false;
            this.state.amount = 0;
        } else {
            this.state.id = id;
            this.state.amount = amount;
        }
        this.render();
    }

    back() {
        this.props.resolve({ confirmed: false, payload: false });
        this.trigger('close-temp-screen');
    }

    confirm() {
        this.props.resolve({ confirmed: true, payload: {id: this.state.id, amount: this.state.amount} });
        this.trigger('close-temp-screen');
    }
}

TransactionListScreen.template = 'TransactionListScreen';

Registries.Component.add(TransactionListScreen);

return TransactionListScreen;
});
