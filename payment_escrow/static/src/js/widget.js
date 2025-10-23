/** @odoo-module alias=paylox.system.escrow **/
'use strict';

import rpc from 'web.rpc';
import { _t, qweb } from 'web.core';
import publicWidget from 'web.public.widget';
import framework from 'paylox.framework';
import payloxPage from 'paylox.page';
import fields from 'paylox.fields';
import { format } from 'paylox.tools';

publicWidget.registry.payloxSystemEscrowBrokerRates = publicWidget.Widget.extend({
    selector: '.payment-escrow #wrapwrap',
    jsLibs: [
        '/payment_jetcheckout/static/src/lib/imask/imask.js',
        '/payment_jetcheckout/static/src/lib/filepond/filepond.js',
    ],
    xmlDependencies: ['/payment_escrow/static/src/xml/templates.xml'],

    init: function (parent, options) {
        this._super(parent, options);
        this.state = {
            broker: {
                activeType: null,
                requestToken: null,
            },
        };
        this.currency = {
            id: 0,
            decimal: 2,
            name: '',
            separator: '.',
            thousand: ',', 
            position: 'after',
            symbol: '', 
        };
        this.broker = {
            amount: new fields.float({
                events: [
                    ['input', this._onBrokerAmountInput],
                ],
                mask: payloxPage.prototype._maskAmount.bind(this),
                validate: () => {
                    const field = this.broker.amount;
                    let valid = true;
                    let message = null;
                    
                    if (field.value <= 0) {
                        message = _t('Please enter a positive amount to calculate rates.');
                        valid = false;
                    }
                    
                    this._onFieldValid(field, valid, message);
                    return valid;
                }
            }),
            campaign: new fields.selection({
                events: [['change', this._onBrokerCampaignChange]],
                default: '',
                validate: () => {
                    const field = this.broker.campaign;
                    let valid = true;
                    let message = null;
                    
                    if (!field.value) {
                        message = _t('No active campaign is linked to your account yet.');
                        valid = false;
                    }
                    
                    this._onFieldValid(field, valid, message);
                    return valid;
                }
            }),
            viewMode: new fields.element({
                events: [['change', this._onBrokerViewModeChange]]
            }),
            button: {
                refresh: new fields.element({
                    events: [['click', this._onBrokerRefresh]]
                })
            },
            container: new fields.element(),
            wrapper: new fields.element(),
            tabs: new fields.element(),
            tables: new fields.element(),
            summary: new fields.element(),
            loading: new fields.element(),
            empty: new fields.element(),
            error: new fields.element(),
        };

        this.settings = {
            campaign: new fields.selection({
                events: [['change', this._onSettingsFieldChange]],
                default: ''
            }),
            signName: new fields.string({
                events: [['input', this._onSettingsFieldChange]],
                default: ''
            }),
            authorizedPerson: new fields.string({
                events: [['input', this._onSettingsFieldChange]],
                default: ''
            }),
            email: new fields.string({
                events: [['input', this._onSettingsFieldChange]],
                mask: /^[\w-\.]+@{0,1}[\w-\.]*$/,
                default: ''
            }),
            phone: new fields.string({
                events: [['input', this._onSettingsFieldChange]],
                mask: '000 000 0000',
                default: ''
            }),
            mobile: new fields.string({
                events: [['input', this._onSettingsFieldChange]],
                mask: '000 000 0000',
                default: ''
            }),
            button: {
                save: new fields.element({
                    events: [['click', this._onSettingsSave]]
                })
            },
            success: new fields.element(),
            error: new fields.element(),
            errorMessage: new fields.element()
        };
    },

    start: function () {
        return this._super.apply(this, arguments).then(() => {
            payloxPage.prototype._setCurrency.apply(this);
            payloxPage.prototype._start.apply(this);
            
            const isBrokerPage = this.$('.broker-rates-container').length > 0;
            const isSettingsPage = this.$('.broker-settings-container').length > 0;
            
            if (isBrokerPage) {
                this._initBroker();
            } else if (isSettingsPage) {
                this._initSettings();
            }
            framework.hideLoading();
            setTimeout(() => $('div.o_loading').addClass('transparent'), 2000);
        });
    },

    _initBroker: function () {
        const $container = this.$('.broker-rates-container');
        if (!$container.length) return;

        const dataset = $container[0].dataset || {};
        this.currency.decimal = parseInt(dataset.currencyDecimals || this.currency.decimal, 10);
        this.currency.symbol = dataset.currencySymbol || this.currency.symbol;
        this.currency.position = dataset.currencyPosition || this.currency.position;

        this.broker.container.$ = $container;
        this.broker.wrapper.$ = $container.find('[data-role="table-wrapper"]');
        this.broker.tabs.$ = $container.find('[data-role="type-tabs"]');
        this.broker.tables.$ = $container.find('[data-role="tables"]');
        this.broker.loading.$ = $container.find('[data-role="loading"]');
        this.broker.empty.$ = $container.find('[data-role="empty"]');
        this.broker.error.$ = $container.find('[data-role="error"]');
        this.broker.summary.$ = $container.find('[data-role="summary"]');
        this.broker.amount.$ = $container.find('[data-role="amount"]');
        this.broker.campaign.$ = $container.find('[data-role="campaign"]');
        this.broker.viewMode.$ = $('[data-role="view-mode"]'); // Search in entire page (including header)
        this.broker.button.refresh.$ = $container.find('[data-role="refresh"]');

        // Manually bind change event for viewMode since it's in header
        if (this.broker.viewMode.$) {
            this.broker.viewMode.$.on('change', this._onBrokerViewModeChange.bind(this));
        }

        if (dataset.defaultCampaign) {
            this.broker.campaign.$.val(dataset.defaultCampaign);
        }

        const hasCampaign = this.broker.campaign.$.find('option[value!=""]').length > 0;
        if (hasCampaign && this.broker.campaign.$.val()) {
            this._fetchBrokerRates();
        } else {
            this._showBrokerError(_t('No active campaign is linked to your account yet.'));
        }
    },

    _initSettings: function () {
        const $container = this.$('.broker-settings-container');
        if (!$container.length) return;

        this.settings.campaign.$ = $container.find('[data-role="campaign"]');
        this.settings.signName.$ = $container.find('[data-role="sign-name"]');
        this.settings.authorizedPerson.$ = $container.find('[data-role="authorized-person"]');
        this.settings.email.$ = $container.find('[data-role="email"]');
        this.settings.phone.$ = $container.find('[data-role="phone"]');
        this.settings.mobile.$ = $container.find('[data-role="mobile"]');
        this.settings.button.save.$ = $container.find('[data-role="save"]');
        this.settings.success.$ = $container.find('[data-role="success"]');
        this.settings.error.$ = $container.find('[data-role="error"]');
        this.settings.errorMessage.$ = $container.find('[data-role="error-message"]');
    },

    _onSettingsFieldChange: function () {
        this.settings.success.$.addClass('d-none');
        this.settings.error.$.addClass('d-none');
    },

    _onSettingsSave: function () {
        console.log('Saving broker settings...');
        const campaignId = parseInt(this.settings.campaign.$.val(), 10) || null;
        const signName = this.settings.signName.$.val().trim();
        const authorizedPerson = this.settings.authorizedPerson.$.val().trim();
        const email = this.settings.email.$.val().trim();
        const phone = this.settings.phone.value || this.settings.phone.$.val().trim();
        const mobile = this.settings.mobile.value || this.settings.mobile.$.val().trim();

        if (!signName || !authorizedPerson || !email || !phone) {
            this.settings.errorMessage.$.text('Please fill all required fields');
            this.settings.error.$.removeClass('d-none');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            this.settings.errorMessage.$.text('Please enter a valid email address');
            this.settings.error.$.removeClass('d-none');
            return;
        }

        this.settings.button.save.$.prop('disabled', true);
        this.settings.success.$.addClass('d-none');
        this.settings.error.$.addClass('d-none');

        rpc.query({
            route: '/payment/escrow/broker/settings/save',
            params: { 
                default_campaign_id: campaignId,
                sign_name: signName,
                authorized_person: authorizedPerson,
                email: email,
                phone: phone.replace(/\s/g, ''),
                mobile: mobile.replace(/\s/g, '')
            }
        }).then(result => {
            if (result && result.success) {
                this.settings.success.$.removeClass('d-none');
                setTimeout(() => this.settings.success.$.addClass('d-none'), 3000);
            } else {
                this.settings.errorMessage.$.text(result.error || 'Failed to save settings');
                this.settings.error.$.removeClass('d-none');
            }
        }).guardedCatch(() => {
            this.settings.errorMessage.$.text('Unable to save settings. Please try again later.');
            this.settings.error.$.removeClass('d-none');
        }).then(() => {
            this.settings.button.save.$.prop('disabled', false);
        });
    },

    _onBrokerAmountInput: function () {
        if (!this._brokerDebounce) {
            this._brokerDebounce = this._debounce(() => this._fetchBrokerRates(), 400);
        }
        this._brokerDebounce();
    },

    _onBrokerAmountChange: function () {
        this._fetchBrokerRates();
    },

    _onBrokerCampaignChange: function () {
        this._fetchBrokerRates();
    },

    _onBrokerViewModeChange: function () {
        if (this._lastBrokerData) {
            this._renderBrokerRates(this._lastBrokerData);
        }
    },

    _onBrokerRefresh: function () {
        this._fetchBrokerRates();
    },

    _parseBrokerAmount: function (value) {
        if (typeof value === 'number') return value;
        if (!value) return 0;
        
        const normalized = String(value).replace(/\s/g, '').replace(',', '.');
        const parsed = parseFloat(normalized);
        return Number.isNaN(parsed) ? 0 : parsed;
    },

    _getBrokerFormatHelpers: function () {
        return {
            currency: (value, pos, sym, dec) => format.currency(
                value, 
                pos || this.currency.position, 
                sym || this.currency.symbol, 
                dec !== undefined ? dec : this.currency.decimal
            ),
            percent: (value) => {
                const rate = typeof value === 'number' ? value : parseFloat(value || 0);
                const percent = Number.isNaN(rate) ? 0 : rate;
                const numStr = percent.toString();
                const decimalPart = numStr.split('.')[1] || '';
                const decimals = Math.min(6, decimalPart.length);
                return (decimals > 0 ? percent.toFixed(decimals) : percent.toFixed(2)) + '%';
            },
        };
    },

    _getCardTypeLabel: function (type) {
        const labels = {
            'Credit': _t('Credit Card'),
            'Debit': _t('Debit Card'),
            'Credit-Business': _t('Business Card'),
        };
        return labels[type] || _t('Other Cards');
    },

    _toggleBrokerLoading: function (loading) {
        this.broker.loading.$.toggleClass('d-none', !loading);
        this.broker.button.refresh.$.prop('disabled', loading || !this.broker.campaign.value);
        
        if (loading) {
            this.broker.wrapper.$.addClass('d-none');
            this.broker.summary.$.addClass('d-none');
            this.broker.empty.$.addClass('d-none');
        }
    },

    _showBrokerError: function (message) {
        if (message) {
            this.broker.error.$.text(message).removeClass('d-none');
        } else {
            this.broker.error.$.addClass('d-none').empty();
        }
    },

    _renderBrokerRates: function (data = {}) {
        this._lastBrokerData = data;
        
        if (data.currency) {
            if (data.currency.symbol) this.currency.symbol = data.currency.symbol;
            if (data.currency.position) this.currency.position = data.currency.position;
            if (data.currency.decimal_places !== undefined) this.currency.decimal = data.currency.decimal_places;
        }

        const amount = typeof data.amount === 'number' ? data.amount : this._parseBrokerAmount(data.amount || 0);
        const lines = data.lines || [];
        const cardTypes = this._prepareBrokerCardTypes(data.card_types, lines);

        this.broker.tables.$.empty();
        if (this.broker.tabs.$) this.broker.tabs.$.empty();

        if (!cardTypes.length) {
            this.state.broker.activeType = null;
            this.broker.wrapper.$.addClass('d-none');
            this.broker.empty.$.toggleClass('d-none', !!data.error);
            this.broker.summary.$.addClass('d-none').empty();
            if (this.broker.tabs.$) this.broker.tabs.$.addClass('d-none');
            return;
        }

        this.broker.empty.$.addClass('d-none');
        this.broker.wrapper.$.removeClass('d-none');

        const availableSlugs = cardTypes.map(ct => ct.slug);
        if (!this.state.broker.activeType || !availableSlugs.includes(this.state.broker.activeType)) {
            this.state.broker.activeType = availableSlugs[0];
        }

        const showTabs = this.broker.tabs.$ && cardTypes.length > 1;
        if (this.broker.tabs.$) this.broker.tabs.$.toggleClass('d-none', !showTabs);

        cardTypes.forEach(cardType => {
            this._renderBrokerPanel(cardType, amount);
        });

        if (!showTabs) {
            this.broker.tables.$.children('[data-type]').removeClass('d-none');
        }
    },

    _prepareBrokerCardTypes: function (rawTypes, lines) {
        const slugify = (value, fallback) => {
            const slug = (value || '').toString().toLowerCase()
                .replace(/[^a-z0-9]+/g, '-')
                .replace(/(^-|-$)/g, '');
            return slug || fallback || 'other';
        };

        if (rawTypes && rawTypes.length) {
            return rawTypes.map((ct, i) => ({
                ...ct,
                slug: ct.slug || slugify(ct.code, `type-${i}`),
            }));
        }

        if (lines.length) {
            return [{
                code: 'Other',
                slug: 'other',
                label: _t('All Cards'),
                families: [{
                    name: _t('All Cards'),
                    code: 'all',
                    logo: '',
                    lines: lines,
                }],
            }];
        }

        return [];
    },

    _renderBrokerPanel: function (cardType, amount) {
        const isActive = cardType.slug === this.state.broker.activeType;
        const $panel = $('<div/>')
            .addClass('broker-card-type-panel')
            .attr('data-type', cardType.slug)
            .toggleClass('d-none', !isActive);

        const $header = $('<div/>')
            .addClass('d-flex align-items-center justify-content-between broker-card-type-header mb-4')
            .append($('<h4/>')
                .addClass('h5 text-uppercase text-primary mb-0 font-weight-bold')
                .text(cardType.label || this._getCardTypeLabel(cardType.code))
            );

        $panel.append($header);

        const $grid = $('<div/>').addClass('row');
        const families = cardType.families || [];

        if (!families.length) {
            $grid.append($('<div/>')
                .addClass('col-12 text-center text-muted py-5')
                .text(_t('No installment data found.'))
            );
        } else {
            const formatHelpers = this._getBrokerFormatHelpers();
            const detailedMode = this.broker.viewMode.$ ? this.broker.viewMode.$.is(':checked') : true;
            families.forEach(family => {
                const $col = $('<div/>').addClass('col-12 mb-4');
                const html = qweb.render('paylox.broker.rates.table', {
                    family: family,
                    baseAmount: amount,
                    format: formatHelpers,
                    position: this.currency.position,
                    symbol: this.currency.symbol,
                    decimal: this.currency.decimal,
                    detailedMode: detailedMode,
                    Number: Number,
                    _t: _t,
                });
                $col.html(html);
                $grid.append($col);
            });
        }

        $panel.append($grid);
        this.broker.tables.$.append($panel);
    },

    _fetchBrokerRates: function () {
        const campaignValue = this.broker.campaign.$.val();
        if (!campaignValue) {
            this._showBrokerError(_t('No active campaign is linked to your account yet.'));
            this._renderBrokerRates({ lines: [], error: true });
            return;
        }

        const amount = this._parseBrokerAmount(this.broker.amount.$.val());

        if (amount <= 0) {
            this._showBrokerError(_t('Please enter a positive amount to calculate rates.'));
            this._renderBrokerRates({ lines: [], error: true });
            return;
        }

        const token = Date.now();
        this.state.broker.requestToken = token;
        this._showBrokerError();
        this._toggleBrokerLoading(true);

        rpc.query({
            route: '/payment/escrow/broker/rates/data',
            params: {
                amount: amount,
                campaign_id: parseInt(campaignValue, 10) || null,
            },
        }).then(result => {
            if (this.state.broker.requestToken !== token) return;

            if (result && result.error) {
                this._showBrokerError(result.error);
                this._renderBrokerRates({ lines: [], error: true });
            } else {
                this._renderBrokerRates(result || { lines: [] });
            }
        }).guardedCatch(() => {
            if (this.state.broker.requestToken !== token) return;
            
            this._showBrokerError(_t('Unable to fetch broker rates. Please try again later.'));
            this._renderBrokerRates({ lines: [], error: true });
        }).then(() => {
            if (this.state.broker.requestToken === token) {
                this._toggleBrokerLoading(false);
            }
        });
    },

    _debounce: function (func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    },

    _onFieldValid: function(field, valid, message='') {
        field.$.closest('.form__group').find('.form__error-label, .just-validate-error-label').remove();
        if (valid) {
            field.$.removeClass('is-invalid -error just-validate-error-field').addClass('is-valid');
        } else {
            field.$.addClass('is-invalid -error just-validate-error-field').removeClass('is-valid');
            field.$.closest('.form__group').append($(`<div class="form__error-label just-validate-error-label">${message}</div>`));
        }
    },
});
