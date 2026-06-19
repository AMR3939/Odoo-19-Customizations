import { BaseOptionComponent, useDomState } from "@html_builder/core/utils";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { SNIPPET_SPECIFIC } from "@html_builder/utils/option_sequence";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";

function readStyle(el, prop, fallback) {
    if (!el) return fallback;
    return el.style[prop] || fallback;
}

// ─────────────────────────────────────────────────────────────────────────────
// SINGLE OPTION: Full theming panel for the Event QR snippet & Sidebar QR
// ─────────────────────────────────────────────────────────────────────────────
export class WebsiteEventQrOption extends BaseOptionComponent {
    static template = "website_event_qr_theming.WebsiteEventQrOption";
    static selector = ".s_event_qr_block";

    setup() {
        super.setup();
        this.orm = useService("orm");

        const section = this._getSection();
        
        // Resolve event ID dynamically
        let eventId = section.getAttribute("data-event-id");
        if (!eventId || eventId === "false" || eventId === "False") {
            const otherQr = document.querySelector(".s_event_qr_block[data-event-id]:not([data-event-id='false']):not([data-event-id='False'])");
            if (otherQr) {
                eventId = otherQr.getAttribute("data-event-id");
            }
        }
        if (!eventId || eventId === "false" || eventId === "False") {
            const match = window.location.pathname.match(/\/event\/[^/]+?(\d+)(?:\/|$)/);
            if (match) {
                eventId = match[1];
            }
        }

        if (eventId && eventId !== "false" && eventId !== "False") {
            this.eventId = parseInt(eventId);
            section.setAttribute("data-event-id", this.eventId);
            
            // Sync placeholder image to the real event QR image
            const qrImg = section.querySelector(".s_event_qr_image");
            if (qrImg) {
                const src = qrImg.getAttribute("src") || "";
                if (src.includes("qr_placeholder.png")) {
                    qrImg.setAttribute("src", `/event_qr/generate?event_id=${this.eventId}&fg_color=%23000000&bg_color=%23ffffff`);
                }
            }
        } else {
            this.eventId = null;
        }

        this.state = useDomState((el) => {
            const sec = el.closest(".s_event_qr_block") || el;
            const qrImg = sec.querySelector(".s_event_qr_image");
            const innerBox = sec.querySelector(".s_event_qr_inner");
            const textCol = sec.querySelector(".s_event_qr_text_col");
            const qrWrapper = sec.querySelector(".s_event_qr_wrapper");
            const heading = sec.querySelector("h3, h4, h5");
            const para = sec.querySelector("p");
            const btn = sec.querySelector(".s_event_qr_btn");

            let fgColor = "#000000";
            let bgColor = "#ffffff";
            let qrText = "https://www.odoo.com/event";
            let eyeInnerColor = "#000000";
            let eyeOuterColor = "#000000";

            if (qrImg) {
                const src = qrImg.getAttribute("src") || "";
                try {
                    const url = new URL(src, window.location.origin);
                    fgColor = url.searchParams.get("fg_color") || "#000000";
                    bgColor = url.searchParams.get("bg_color") || "#ffffff";
                    qrText = url.searchParams.get("text") || "https://www.odoo.com/event";
                    eyeInnerColor = url.searchParams.get("eye_color") || fgColor;
                    eyeOuterColor = url.searchParams.get("eye_outer_color") || fgColor;
                } catch (e) { /* use fallbacks */ }
            }

            const hasSection = !!(sec.querySelector("h3, h4, h5") || sec.querySelector("p"));
            const hasButton = !!sec.querySelector(".s_event_qr_btn");
            const hasTextCol = !!textCol;
            const hasQrWrapper = !!qrWrapper;

            return {
                // Section
                sectionBg: readStyle(sec, "backgroundColor", "#ffffff"),
                headingColor: readStyle(heading, "color", "#212529"),
                textColor: readStyle(para, "color", "#6c757d"),
                // Text column layer
                textColBg: readStyle(textCol, "backgroundColor", ""),
                // QR Wrapper layer
                qrWrapperBg: readStyle(qrWrapper, "backgroundColor", ""),
                // QR API
                fgColor,
                bgColor,
                qrText,
                eyeInnerColor,
                eyeOuterColor,
                // QR box
                boxBg: readStyle(innerBox, "backgroundColor", "#f8f9fa"),
                boxBorderColor: readStyle(innerBox, "borderColor", "#dee2e6"),
                boxBorderWidth: parseInt(readStyle(innerBox, "borderWidth", "2px")) || 2,
                boxRadius: parseInt(readStyle(innerBox, "borderRadius", "8px")) || 8,
                // Button
                btnBg: readStyle(btn, "backgroundColor", "#0d6efd"),
                btnColor: readStyle(btn, "color", "#ffffff"),
                btnBorderColor: readStyle(btn, "borderColor", "#0d6efd"),
                // Display flags
                hasSection,
                hasButton,
                hasTextCol,
                hasQrWrapper,
            };
        });
    }

    _getSection() {
        const el = this.env.getEditingElement();
        return el.closest(".s_event_qr_block") || el;
    }

    // ── Section ──────────────────────────────────────────────────────────────
    updateSectionBg(color) {
        this._getSection().style.backgroundColor = color;
        this.state.sectionBg = color;
        this.config.onChange?.({ isPreviewing: false });
    }
    updateTextColBg(color) {
        const textCol = this._getSection().querySelector(".s_event_qr_text_col");
        if (textCol) textCol.style.backgroundColor = color;
        this.state.textColBg = color;
        this.config.onChange?.({ isPreviewing: false });
    }
    updateQrWrapperBg(color) {
        const qrWrapper = this._getSection().querySelector(".s_event_qr_wrapper");
        if (qrWrapper) qrWrapper.style.backgroundColor = color;
        this.state.qrWrapperBg = color;
        this.config.onChange?.({ isPreviewing: false });
    }
    updateHeadingColor(color) {
        this._getSection().querySelectorAll("h3,h4,h5").forEach((h) => { h.style.color = color; });
        this.state.headingColor = color;
        this.config.onChange?.({ isPreviewing: false });
    }
    updateTextColor(color) {
        this._getSection().querySelectorAll("p").forEach((p) => {
            p.style.setProperty('color', color, 'important');
            p.classList.remove('text-muted');
            p.querySelectorAll('font, span').forEach((child) => {
                child.style.setProperty('color', color, 'important');
            });
        });
        this.state.textColor = color;
        this.config.onChange?.({ isPreviewing: false });
    }

    // ── QR API ───────────────────────────────────────────────────────────────
    async updateFgColor(color) {
        this.state.fgColor = color;
        this._updateQrSrc();
    }
    async updateBgColor(color) {
        this.state.bgColor = color;
        // Sync visible box background
        const innerBox = this._getInnerBox();
        if (innerBox) innerBox.style.backgroundColor = color;
        this.state.boxBg = color;
        this._updateQrSrc();
    }
    async updateText(text) {
        this.state.qrText = text;
        this._updateQrSrc();
    }
    updateEyeColor(type, color) {
        if (type === 'inner') {
            this.state.eyeInnerColor = color;
        } else {
            this.state.eyeOuterColor = color;
        }
        this._updateQrSrc();
    }
    _updateQrSrc() {
        const section = this._getSection();
        const qrImg = section.querySelector(".s_event_qr_image");
        if (!qrImg) return;
        
        qrImg.setAttribute("src",
            `/event_qr/generate` +
            `?text=${encodeURIComponent(this.state.qrText)}` +
            `&fg_color=${encodeURIComponent(this.state.fgColor)}` +
            `&bg_color=${encodeURIComponent(this.state.bgColor)}` +
            `&eye_color=${encodeURIComponent(this.state.eyeInnerColor)}` +
            `&eye_outer_color=${encodeURIComponent(this.state.eyeOuterColor)}`
        );
        
        this.config.onChange?.({ isPreviewing: false });
    }

    // ── QR Box ───────────────────────────────────────────────────────────────
    _getInnerBox() { return this._getSection().querySelector(".s_event_qr_inner"); }

    async updateBoxBg(color) {
        const b = this._getInnerBox();
        if (b) b.style.backgroundColor = color;
        this.state.boxBg = color;
        this.state.bgColor = color;
        this._updateQrSrc();
    }
    updateBoxBorderColor(color) {
        const b = this._getInnerBox();
        if (b) b.style.borderColor = color;
        this.state.boxBorderColor = color;
        this.config.onChange?.({ isPreviewing: false });
    }
    updateBoxBorderWidth(value) {
        const px = parseInt(value) || 0;
        const b = this._getInnerBox();
        if (b) b.style.borderWidth = px + "px";
        this.state.boxBorderWidth = px;
        this.config.onChange?.({ isPreviewing: false });
    }
    updateBoxRadius(value) {
        const px = parseInt(value) || 0;
        const b = this._getInnerBox();
        if (b) b.style.setProperty('border-radius', px + 'px', 'important');
        this.state.boxRadius = px;
        this.config.onChange?.({ isPreviewing: false });
    }

    // ── Button ───────────────────────────────────────────────────────────────
    _getBtn() { return this._getSection().querySelector(".s_event_qr_btn"); }

    updateBtnBg(color) {
        const btn = this._getBtn();
        if (btn) btn.style.backgroundColor = color;
        this.state.btnBg = color;
        this.config.onChange?.({ isPreviewing: false });
    }
    updateBtnColor(color) {
        const btn = this._getBtn();
        if (btn) btn.style.color = color;
        this.state.btnColor = color;
        this.config.onChange?.({ isPreviewing: false });
    }
    updateBtnBorderColor(color) {
        const btn = this._getBtn();
        if (btn) { btn.style.borderColor = color; btn.style.borderStyle = "solid"; }
        this.state.btnBorderColor = color;
        this.config.onChange?.({ isPreviewing: false });
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// PLUGIN
// ─────────────────────────────────────────────────────────────────────────────
class WebsiteEventQrOptionPlugin extends Plugin {
    static id = "website_event_qr_theming.WebsiteEventQrOption";
    resources = {
        builder_options: [
            withSequence(SNIPPET_SPECIFIC, WebsiteEventQrOption),
        ],
    };
}

registry
    .category("website-plugins")
    .add(WebsiteEventQrOptionPlugin.id, WebsiteEventQrOptionPlugin);
