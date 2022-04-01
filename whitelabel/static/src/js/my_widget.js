odoo.define('whitelabel.my_widget', function (require) {
    "use strict";

    
    var Widget = require('web.Widget');
    var widget_registry = require('web.widget_registry');
    var session = require ('web.session');

    var ResConfigEdition = Widget.extend({
        template: 'res_config_edition',
       /**
        * @override
        */
        init: function () {
            this._super.apply(this, arguments);
            this.server_version = session.server_version;
            if(odoo && odoo.debranding_settings && odoo.debranding_settings.odoo_text_replacement)
                this.odoo_text_replacement = odoo.debranding_settings.odoo_text_replacement;
            else
                this.odoo_text_replacement = "Software"
        },
   });

   widget_registry.add('res_config_edition', ResConfigEdition);

});