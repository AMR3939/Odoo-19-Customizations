/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

// Hides QR snippets that belong to a different event (sweeper)
publicWidget.registry.EventQrSnippetFrontend = publicWidget.Widget.extend({
    selector: '.s_event_qr_block',

    start: function () {
        const snippetEventId = this.$el.attr("data-event-id");

        if (!snippetEventId || snippetEventId === "false" || snippetEventId === "False") {
            return this._super.apply(this, arguments);
        }

        const eventMatch = window.location.pathname.match(/\/event\/[^\/]*?(\d+)(?:\/|$)/);
        if (eventMatch) {
            const currentEventId = eventMatch[1];
            if (snippetEventId !== currentEventId) {
                this.$el.addClass("d-none");
                this.$el.empty();
                this.$el.hide();
            }
        } else {
            this.$el.addClass("d-none");
            this.$el.hide();
        }

        return this._super.apply(this, arguments);
    },
});
