/** @odoo-module **/

import { FormRenderer } from "@web/views/form/form_renderer";
import { patch } from "@web/core/utils/patch";

let graphObserver = null;

function redrawCommissionGraph() {
    if (window.drawCommissionGraph) {
        window.drawCommissionGraph();
    }
}

function observeCommissionTable() {
    const container = document.querySelector("div[name='commission_ids']");

    if (!container) {
        return;
    }

    if (graphObserver) {
        graphObserver.disconnect();
    }

    graphObserver = new MutationObserver(() => {
        redrawCommissionGraph();
    });

    graphObserver.observe(container, {
        childList: true,
        subtree: true,
    });

    // Draw immediately too, in case rows are already present.
    redrawCommissionGraph();
}

patch(FormRenderer.prototype, {

    mounted() {
        if (super.mounted) {
            super.mounted();
        }
        observeCommissionTable();
    },

    patched() {
        if (super.patched) {
            super.patched();
        }
        observeCommissionTable();
    },

    willUnmount() {
        if (graphObserver) {
            graphObserver.disconnect();
            graphObserver = null;
        }
        if (super.willUnmount) {
            super.willUnmount();
        }
    },

});