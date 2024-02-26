/** @odoo-module alias=paylox.system.page.flow.agreement **/
'use strict';

import rpc from 'web.rpc';
import { _t, qweb } from 'web.core';
import payloxPage from 'paylox.page';
import systemFlow from 'paylox.system.page.flow';

systemFlow.dynamic.include({
    xmlDependencies: (systemFlow.dynamic.xmlDependencies || []).concat(
        ['/payment_system_agreement/static/src/xml/page.xml']
    ),
 
    _onClickAmountNext: async function () {
        const _super = this._super;

        let ready = true;
        if (this.wizard.button.product.exist) {
            ready = false;
            try {
                const agreements = await rpc.query({
                    route: '/my/agreement',
                    params: {
                        product_id: this.wizard.button.product.selected,
                    }
                });
                if (agreements) {
                    const $agreements = $('[field=agreements]');
                    for (const agreement of agreements) {
                        const $agreement = qweb.render('paylox.agreement.product', { agreement });
                        $agreements.append($agreement);
                    }

                    window.dispatchEvent(new CustomEvent('agreement-added', {'detail': agreements}));
                    window.dispatchEvent(new CustomEvent('field-updated', {'detail': ['agreement']}));
                }
                ready = true;
            } catch {
                this.displayNotification({
                    type: 'danger',
                    title: _t('Error'),
                    message: _t('An error occured. Please try again.'),
                });
            }
        }

        if (!ready) return;
        return _super.apply(this, arguments);
    }
});