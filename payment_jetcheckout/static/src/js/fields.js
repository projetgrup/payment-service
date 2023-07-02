/** @odoo-module alias=paylox.fields **/
'use strict';

export default class {
    constructor(options) {
        Object.assign(this, options);
        this.$ = $();
        this._ = undefined;
    }

    async start(self) {
        if (this.mask) {
            if (this.mask instanceof Function) {
                this.mask = this.mask.apply(self);
            }
            this._ = new IMask(this.$[0], this.mask);
        }
        if (this.events) {
            for (const [e, f] of this.events) {
                if (this._ && e === 'accept') {
                    this._.on(e, f.bind(self));
                } else {
                    this.$.on(e, f.bind(self));
                }
            }
        }
        //this.$.removeClass('p_fields');
    }
 
    get value() {
        if (this._) {
            return this._.typedValue;
        } else {
            return this.$ && this.$.val() || this.default;
        }
    }

    set value(v) {
        this.$.val(v);
    }

    get checked() {
        return this.$.is(':checked');
    }
 
    set checked(v) {
        return this.$.prop('checked', v);
    }

    set html(v) {
        this.$.html(v);
    }

    get html() {
        this.$.html();
    }

    get exist() {
        return !!this.$.length;
    }
}