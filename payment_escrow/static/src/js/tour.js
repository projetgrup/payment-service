/** @odoo-module alias=paylox.system.escrow.tour **/
'use strict';

import publicWidget from 'web.public.widget';
import { _t } from 'web.core';

publicWidget.registry.payloxSystemEscrowTour = publicWidget.Widget.extend({
    selector: '.payment-escrow #wrapwrap',
    events: {
        'click [field="ad.button.tour.start"]': '_startTour',
        'click .tour-popover-close': '_endTour',
        'click .tour-prev': '_prevTourStep',
        'click .tour-next': '_nextTourStep',
        'click .tour-finish': '_endTour',
    },

    init: function (parent, options) {
        this._super(parent, options);
        console.log('Tour Widget Initialized');
        
        // Bind resize event to update overlay
        var self = this;
        $(window).on('resize.paylox_tour scroll.paylox_tour', function() {
            if (self.currentTourStep >= 0 && $('.tour-overlay-part').is(':visible')) {
                const step = self.tourSteps[self.currentTourStep];
                if (step) {
                    self._highlightElement(step.target, step.position, { skipScroll: true });
                }
            }
        });

        this.tourSteps = [
            {
                target: 'body',
                title: _t('Welcome to Escrow v2'),
                content: _t('Welcome to the new Escrow Payment System interface! Let\'s take a quick tour to show you around the new features.'),
                position: 'center'
            },
            {
                target: 'input[field="ad.search"]',
                title: _t('Quick Search'),
                content: _t('Easily find your ads by searching for keywords here.'),
                position: 'bottom'
            },
            {
                target: '[field="ad.category.filter"]',
                title: _t('Categories'),
                content: _t('Filter your ads by category to quickly find what you are looking for.'),
                position: 'right'
            },
            {
                target: '.price-range-wrapper',
                title: _t('Price Range'),
                content: _t('Set a price range to filter ads within your budget.'),
                position: 'right'
            },
            {
                target: '[field="ad.state.filter"]',
                title: _t('Status Tracking'),
                content: _t('Track the status of your transactions from "Published" to "Sold".'),
                position: 'right'
            },
            {
                target: '[field="ad.button.create"]',
                title: _t('Create New Transaction'),
                content: _t('Start a new secure payment transaction by clicking here.'),
                position: 'left'
            },
            {
                target: '[field="insurance.button.open"]',
                title: _t('Insurance Services'),
                content: _t('Get insurance quotes for your vehicles directly from here.'),
                position: 'bottom'
            },
            {
                target: '.btn-group',
                title: _t('View Options'),
                content: _t('Switch between List and Grid views to suit your preference.'),
                position: 'bottom'
            },
            {
                target: '[field="ad.button.sidebar.toggle"]',
                title: _t('Settings & Help'),
                content: _t('Access settings, theme options, and helpdesk from the sidebar.'),
                position: 'left'
            }
        ];
        this.currentTourStep = 0;
    },

    start: function () {
        var self = this;
        console.log('Tour Widget Started');
        
        // Manual binding to ensure events are caught
        $(document).on('click', '[field="ad.button.tour.start"]', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Start Tour Clicked');
            self._startTour();
        });

        return this._super.apply(this, arguments).then(function () {
            // Check if tour should run automatically
            if (!localStorage.getItem('escrow_tour_v2_completed')) {
                setTimeout(() => self._startTour(), 1000);
            }
        });
    },

    destroy: function () {
        $(window).off('resize.paylox_tour scroll.paylox_tour');
        this._super.apply(this, arguments);
    },

    _startTour: function () {
        console.log('Starting Tour...');
        this.currentTourStep = 0;
        this._createTourOverlay();
        this._showTourStep(this.currentTourStep);
    },

    _createTourOverlay: function () {
        if ($('.tour-overlay-backdrop').length === 0) {
            $('body').append(`
                <div class="tour-overlay-backdrop" style="display:none;">
                    <div class="tour-overlay-part top"></div>
                    <div class="tour-overlay-part bottom"></div>
                    <div class="tour-overlay-part left"></div>
                    <div class="tour-overlay-part right"></div>
                </div>
                <div class="tour-popover" style="display:none;">
                    <div class="tour-popover-header">
                        <div class="tour-popover-title"></div>
                        <div class="tour-popover-close"><i class="fa fa-times"></i></div>
                    </div>
                    <div class="tour-popover-body"></div>
                    <div class="tour-popover-footer">
                        <div class="tour-steps-count"></div>
                        <div class="tour-buttons">
                            <button class="btn btn-secondary btn-sm tour-prev">Prev</button>
                            <button class="btn btn-primary btn-sm tour-next">Next</button>
                            <button class="btn btn-primary btn-sm tour-finish" style="display:none">Finish</button>
                        </div>
                    </div>
                </div>
            `);
            
            var self = this;
            $(document).on('click', '.tour-popover-close', function() { self._endTour(); });
            $(document).on('click', '.tour-prev', function() { self._prevTourStep(); });
            $(document).on('click', '.tour-next', function() { self._nextTourStep(); });
            $(document).on('click', '.tour-finish', function() { self._endTour(); });
        }
        
        $('.tour-overlay-backdrop').fadeIn(200);
        $('.tour-popover').fadeIn(200);
    },

    _showTourStep: function (stepIndex) {
        const step = this.tourSteps[stepIndex];
        if (!step) return;

        // Update Content
        $('.tour-popover-title').text(step.title);
        $('.tour-popover-body').text(step.content);
        $('.tour-steps-count').text(`${stepIndex + 1} / ${this.tourSteps.length}`);

        // Update Buttons
        if (stepIndex === 0) {
            $('.tour-prev').hide();
        } else {
            $('.tour-prev').show();
        }

        if (stepIndex === this.tourSteps.length - 1) {
            $('.tour-next').hide();
            $('.tour-finish').show();
        } else {
            $('.tour-next').show();
            $('.tour-finish').hide();
        }

        // Highlight Target
        this._highlightElement(step.target, step.position);
    },

    _highlightElement: function (selector, position, options) {
        options = options || {};
        $('.tour-highlight-element').removeClass('tour-highlight-element');

        let target = $(selector);
        if (selector === 'body' || target.length === 0 || !target.is(':visible')) {
            this._resetOverlay();
            this._positionPopoverCenter();
            return;
        }

        if (target.parent().hasClass('input-group')) {
            target = target.parent();
        }

        if (!options.skipScroll) {
            const desiredScroll = Math.max(target.offset().top - 120, 0);
            const self = this;
            $('html, body').stop(true).animate({
                scrollTop: desiredScroll
            }, 300, function () {
                self._highlightElement(selector, position, { skipScroll: true });
            });
            return;
        }

        target.addClass('tour-highlight-element');

        const rect = target[0].getBoundingClientRect();
        const padding = 8;
        const viewportHeight = $(window).height();
        const viewportWidth = $(window).width();

        const top = Math.max(rect.top - padding, 0);
        const left = Math.max(rect.left - padding, 0);
        const width = Math.min(rect.width + (padding * 2), viewportWidth - left);
        const height = Math.min(rect.height + (padding * 2), viewportHeight - top);

        $('.tour-overlay-part.top').css({ top: 0, left: 0, width: '100%', height: top });
        $('.tour-overlay-part.bottom').css({ top: top + height, left: 0, width: '100%', height: Math.max(viewportHeight - (top + height), 0) });
        $('.tour-overlay-part.left').css({ top: top, left: 0, width: left, height: height });
        $('.tour-overlay-part.right').css({ top: top, left: left + width, width: Math.max(viewportWidth - (left + width), 0), height: height });

        this._positionPopover(target, position);
    },

    _resetOverlay: function () {
        $('.tour-overlay-part').css({ width: '100%', height: '100%', top: 0, left: 0 });
        $('.tour-overlay-part.top').css({ height: '100%' });
        $('.tour-overlay-part.bottom, .tour-overlay-part.left, .tour-overlay-part.right').css({ height: 0 });
    },

    _positionPopoverCenter: function () {
        const popover = $('.tour-popover');
        popover.css({
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)'
        }).addClass('visible');
    },

    _positionPopover: function (target, position) {
        const popover = $('.tour-popover');
        const rect = target[0].getBoundingClientRect();
        const scrollTop = $(window).scrollTop();
        const scrollLeft = $(window).scrollLeft();
        
        let top, left;
        const margin = 15;

        if (position === 'right') {
            top = rect.top + scrollTop + (rect.height / 2) - (popover.outerHeight() / 2);
            left = rect.right + scrollLeft + margin;
        } else if (position === 'left') {
            top = rect.top + scrollTop + (rect.height / 2) - (popover.outerHeight() / 2);
            left = rect.left + scrollLeft - popover.outerWidth() - margin;
        } else if (position === 'bottom') {
            top = rect.bottom + scrollTop + margin;
            left = rect.left + scrollLeft + (rect.width / 2) - (popover.outerWidth() / 2);
        } else { // top
            top = rect.top + scrollTop - popover.outerHeight() - margin;
            left = rect.left + scrollLeft + (rect.width / 2) - (popover.outerWidth() / 2);
        }

        if (left < 10) left = 10;
        if (left + popover.outerWidth() > $(window).width()) left = $(window).width() - popover.outerWidth() - 10;

        popover.css({
            top: top,
            left: left,
            transform: 'none'
        }).addClass('visible');
    },

    _nextTourStep: function () {
        if (this.currentTourStep < this.tourSteps.length - 1) {
            this.currentTourStep++;
            this._showTourStep(this.currentTourStep);
        }
    },

    _prevTourStep: function () {
        if (this.currentTourStep > 0) {
            this.currentTourStep--;
            this._showTourStep(this.currentTourStep);
        }
    },

    _endTour: function () {
        $('.tour-overlay-backdrop').hide();
        $('.tour-popover').hide();
        $('.tour-highlight-element').removeClass('tour-highlight-element');
        localStorage.setItem('escrow_tour_v2_completed', 'true');
    },
});
