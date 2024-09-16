odoo.define('web_multitenant.switchWebsiteMenu', function (require) {
    'use strict';
    
    const Widget = require('web.Widget'); 
    const { qweb } = require('web.core');
    const { registry } = require("@web/core/registry");

    const switchWebsiteMenu = Widget.extend({
        xmlDependencies: ['/web_multitenant/static/src/xml/website_menu.xml'],
        events: {
            'input .filter-input': '_onSearch',
            'click #website_switcher': '_onWebsiteClick',
        },

        start: function () {
            const data = $('.oe_filter_website').attr('data');
            const websites = JSON.parse(data.replace(/'/g, '"'));
            const $filter = $(qweb.render('web_multitenant.switch_website_menu', { websites }));
            this.$el.append($filter);
            return this._super.apply(this, arguments);
        },

        _onSearch: function (ev) {
            const $input = $(ev.currentTarget);
            const value = $input.val().toLowerCase();
            const $websites = $('.oe_website_filter');
            $websites.each(function () {
                const $names = $(this).find('.oe_website_name');
                $names.each(function () {
                    const $name = $(this);
                    const name = $name.text().toLowerCase();
                    if (name.indexOf(value) > -1) {
                        $name.parent().show();
                    } else {
                        $name.parent().hide();
                    }
                });
            });
        },
    });
    
    registry.category("website_navbar_widgets").add("switchWebsiteMenu", {
        Widget: switchWebsiteMenu,
        selector: '.oe_filter_website',
    });
    
    return switchWebsiteMenu;
});