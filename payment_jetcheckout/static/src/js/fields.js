/** @odoo-module alias=paylox.fields **/
'use strict';

import wysiwygLoader from 'web_editor.loader';
import { _t } from 'web.core';

try {
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
        const callbacks = {};
        const props = {
            ...callbacks,
            credits: false,
            captureMethod: 'environment',
            allowFileSizeValidation: false,
            allowMultiple: this.options.allowMultiple || false,

            labelIdle: _t('Drag & Drop your picture or <span class="filepond--label-action">Browse</span>'),
            imagePreviewHeight: 170,
            imageCropAspectRatio: '1:1',
            imageResizeTargetWidth: 200,
            imageResizeTargetHeight: 200,
            stylePanelLayout: 'compact circle',
            styleLoadIndicatorPosition: 'center bottom',
            styleButtonRemoveItemPosition: 'center bottom',
            
            files: ['data:image/png;base64,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']
        }
        if (this.options.maxFileSize) {
            Object.assign(props, {
                maxFileSize: this.options.maxFileSize,
                allowFileSizeValidation: true,
                labelMaxFileSizeExceeded: _t('File is too large'),
                labelMaxFileSize: _t('Maximum file size is {filesize}'),
                labelMaxTotalFileSizeExceeded: _t('Maximum total size exceeded'),
                labelMaxTotalFileSize: _t('Maximum total file size is {filesize}'),
            })
        }

        FilePond.registerPlugin(
            FilePondPluginFileEncode,
            FilePondPluginFileValidateType,
            FilePondPluginFileValidateSize,
            FilePondPluginImageExifOrientation,
            FilePondPluginImagePreview,
            FilePondPluginImageCrop,
            FilePondPluginImageResize,
            FilePondPluginImageTransform,
            FilePondPluginImageEdit
        );
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
