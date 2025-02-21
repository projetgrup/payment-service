/** @odoo-module alias=paylox.fields **/
'use strict';

class fields {
    constructor(options) {
        Object.assign(this, options);
        this.$ = $();
        this._ = undefined;
        this._name = undefined;
        this.options = options || {};
    }

    async start(self, name, force=false) {
        if (this._name && !force) {
            return;
        }

        this._name = name;
        if (this.mask) {
            if (this.mask instanceof Function) {
                this.mask = this.mask.apply(self);
            }
            try {
                this._ = new IMask(this.$[0], this.mask);
            } catch (error) {
                console.error(error);
            }
        }

        if (force) {
            this.$.off();
        }

        if (this.events) {
            for (const [e, f] of this.events) {
                if (this._ && e === 'accept') {
                    this._.on(e, f.bind(self));
                } else if (e === 'start') {
                    f.apply(self);
                } else {
                    this.$.on(e, f.bind(self));
                }
            }
        }

        //this.$.prop('field', undefined);
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

    set text(v) {
        this.$.text(v);
    }

    get text() {
        this.$.text();
    }

    get json() {
        try {
            return JSON.parse(this.$.val());
        } catch {
            return {};
        }
    }

    get exist() {
        return !!this.$.length;
    }
}

class string extends fields {}

class boolean extends fields {}

class element extends fields {}

class selection extends fields {
    async start() {
        super.start(...arguments);

        if (typeof this.options.data === 'function') {
            this.options.data = this.options.data();
        }

        const defaults = {
            placeholder: this.$.attr('placeholder'),
            ...this.options,
        }
        console.log(defaults);
        this.$.select2(defaults);
        if (this.options.data) {
            const placeholder = this.options.data.find(d => d.selected)
            if (placeholder) {
                this.value = placeholder.id;
            }
        }
    }

    get value() {
        let value = this.$.val();
        if ($.isNumeric(value)) return parseFloat(value);
        return value;
    }

    set value(v) {
        this.$.val(v);
        this.$.trigger('change');
    }
}

class float extends fields {
    get value() {
        if (this._) {
            return this._.typedValue;
        } else {
            return parseFloat(this.$ && this.$.val() || this.default || 0);
        }
    }

    set value(v) {
        this.$.val(v);
    }
}

class integer extends float {
    get value() {
        if (this._) {
            return this._.typedValue;
        } else {
            return parseInt(this.$ && this.$.val() || this.default || 0);
        }
    }

    set value(v) {
        this.$.val(v);
    }
}

export default {
    field: fields,
    string: string,
    boolean: boolean,
    integer: integer,
    float: float,
    selection: selection,
    element: element,
}