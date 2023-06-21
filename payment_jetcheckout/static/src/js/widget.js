/** @odoo-module alias=paylox.page.widget **/
'use strict';

export default class {
    constructor (options) {
        this.events = options.events || [];
        this.mask = options.mask;
        this.$ = undefined;
        this._ = undefined;
    }

    async start (self) {
        for (const [e, f] of this.events) {
            this.$.on(e, f.bind(self));
        }
        if (this.mask) {
            this._ = new IMask(this.$[0], this.mask);
        }
    }
}