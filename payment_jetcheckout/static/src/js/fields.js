/** @odoo-module alias=paylox.fields **/
'use strict';

import wysiwygLoader from 'web_editor.loader';

try {
    FilePond.registerPlugin(FilePondPluginImagePreview);
    FilePond.registerPlugin(FilePondPluginFileValidateSize);
    FilePond.registerPlugin(FilePondPluginFileValidateType);
} catch {}

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

class file extends fields {
    async start() {
        super.start(...arguments);
        this.$.prop('accept', this.options.accept || '*');
        const callbacks = {};
        if (this.el) {
            Object.assign(callbacks, {
                onaddfile: async (error, file) => {
                    const bytes = await file.file.bytes();
                    const array = Array.from(bytes).map(byte => String.fromCharCode(byte)).join('');
                    this.el.src = `data:${file.fileType};base64,${btoa(array)}`;
                },
            });
        }
        const props = {
            ...callbacks,
            credits: false,
            captureMethod: 'environment',
            allowFileSizeValidation: false,
            allowMultiple: this.options.allowMultiple || false,
        }
        if (this.options.size) {
            Object.assign(props, {
                maxFileSize: this.options.size,
                allowFileSizeValidation: true,
                labelMaxFileSizeExceeded: _t('File is too large'),
                labelMaxFileSize: _t('Maximum file size is {filesize}'),
                labelMaxTotalFileSizeExceeded: _t('Maximum total size exceeded'),
                labelMaxTotalFileSize: _t('Maximum total file size is {filesize}'),
            })
        }
        FilePond.create(this.$[0], props);
    }
}

class html extends fields {
    async start() {
        super.start(...arguments);
        const wysiwyg = await wysiwygLoader.loadFromTextarea(this.options.parent, this.$[0], {
            resizable: true,
            userGeneratedContent: true,
        });
        this.$ = wysiwyg.$editable;
    }

    get value() {
        return this.$.html();
    }

    set value(v) {
        this.$.html(v);
        this.$.trigger('change');
    }
}

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
    file: file,
    html: html,
    boolean: boolean,
    integer: integer,
    float: float,
    selection: selection,
    element: element,
}
