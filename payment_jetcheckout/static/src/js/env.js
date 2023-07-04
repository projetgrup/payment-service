/** @odoo-module alias=paylox.component **/
'use strict';

import { _t } from 'web.core';
import session from 'web.session';
import page from 'paylox.page';

const {Component, mount, QWeb} = owl;
const {whenReady} = owl.utils;

async function makeEnvironment() {
    const env = {};
    const services = Component.env.services;
    await session.is_bound;
    const qweb = new QWeb({translateFn: _t});
    const templates = await owl.utils.loadFile('/payment_jetcheckout/static/src/xml/page.xml');
    qweb.addTemplates(templates);
    return Object.assign(env, {qweb, services});
}

async function setup() {
    const env = await makeEnvironment();
    mount(
        page,
        {
            env: env,
            target: document.getElementById('payment'),
            props: {}
        }
    )
}

whenReady(setup);
