import { BaseOptionComponent, useDomState } from "@html_builder/core/utils";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";

// ─────────────────────────────────────────────────────────────────────────────
// Event QR Page Option
// Adds QR dot color, background color, and link inputs to the "Event Page"
// style panel (same panel as Fixed Sidebar, Sidebar Blocks).
// Auto-saves and regenerates the QR image on every change — no button needed.
// ─────────────────────────────────────────────────────────────────────────────
export class EventQrPageOption extends BaseOptionComponent {
    static template = "website_event_qr_theming.EventQrPageOption";
    static selector = "main:has(#o_wevent_event_main)";
    static editableOnly = false;

    setup() {
        super.setup();
        this.orm = useService("orm");

        // Extract event ID from the current URL
        const match = window.location.pathname.match(/\/event\/[^/]+?(\d+)(?:\/|$)/);
        this.eventId = match ? parseInt(match[1]) : null;

        this.state = useDomState((el) => ({
            fgColor: "#000000",
            bgColor: "#ffffff",
            qrText: "",
            eyeInnerColor: "#000000",
            eyeOuterColor: "#000000",
            // True when Fixed Sidebar is ON — Odoo adds sticky-top class to the sidebar
            sidebarFixed: !!el.ownerDocument.querySelector(
                "#o_wevent_event_main_sidebar.sticky-top"
            ),
        }));

        onWillStart(async () => {
            if (!this.eventId) return;
            try {
                const result = await this.orm.read(
                    "event.event",
                    [this.eventId],
                    ["qr_fg_color", "qr_bg_color", "qr_text", "qr_eye_color", "qr_eye_outer_color"]
                );
                if (result && result.length > 0) {
                    this.state.fgColor = result[0].qr_fg_color || "#000000";
                    this.state.bgColor = result[0].qr_bg_color || "#ffffff";
                    this.state.qrText = result[0].qr_text || "";
                    this.state.eyeInnerColor = result[0].qr_eye_color || this.state.fgColor;
                    this.state.eyeOuterColor = result[0].qr_eye_outer_color || this.state.fgColor;
                }
            } catch (e) {
                console.error("Failed to load QR colors:", e);
            }
        });
    }

    // Save to backend and refresh ONLY the sidebar QR image (not drag-and-drop snippets)
    async _saveAndRefresh(vals) {
        if (!this.eventId) return;
        try {
            await this.orm.write("event.event", [this.eventId], vals);
            await this.orm.call("event.event", "generate_qr_code", [[this.eventId]]);

            // Only refresh the sidebar QR image — snippets are independent
            const sidebarBlock = document.querySelector(
                "#o_wevent_event_main_sidebar .s_event_qr_block"
            );
            if (sidebarBlock) {
                const img = sidebarBlock.querySelector(".s_event_qr_image");
                if (img) {
                    img.src = `/event_qr/generate?event_id=${this.eventId}&fg_color=${encodeURIComponent(this.state.fgColor)}&bg_color=${encodeURIComponent(this.state.bgColor)}&eye_color=${encodeURIComponent(this.state.eyeInnerColor)}&eye_outer_color=${encodeURIComponent(this.state.eyeOuterColor)}&ts=${Date.now()}`;
                }
                // Update sidebar QR box background color live
                if (vals.qr_bg_color) {
                    const box = sidebarBlock.querySelector(".s_event_qr_inner");
                    if (box) box.style.backgroundColor = vals.qr_bg_color;
                }
            }
        } catch (e) {
            console.error("Failed to save QR settings:", e);
        }
    }

    async saveFgColor(color) {
        this.state.fgColor = color;
        await this._saveAndRefresh({ qr_fg_color: color });
    }

    async saveBgColor(color) {
        this.state.bgColor = color;
        await this._saveAndRefresh({ qr_bg_color: color });
    }

    async saveQrText(text) {
        this.state.qrText = text;
        await this._saveAndRefresh({ qr_text: text || false });
    }

    async saveEyeColor(type, color) {
        if (type === 'inner') {
            this.state.eyeInnerColor = color;
            await this._saveAndRefresh({ qr_eye_color: color });
        } else {
            this.state.eyeOuterColor = color;
            await this._saveAndRefresh({ qr_eye_outer_color: color });
        }
    }
}

class EventQrPageOptionPlugin extends Plugin {
    static id = "website_event_qr_theming.EventQrPageOption";
    resources = {
        builder_options: [
            withSequence(1000, EventQrPageOption),
        ],
    };
}

registry
    .category("website-plugins")
    .add(EventQrPageOptionPlugin.id, EventQrPageOptionPlugin);
