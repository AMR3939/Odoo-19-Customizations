import { BaseOptionComponent, useDomState } from "@html_builder/core/utils";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";

// ─────────────────────────────────────────────────────────────────────────────
// OPTION 0: Section-level background options — shown when the section or any
// non-specific child is selected.
// Provides: Section BG, Text Area BG, Heading Color, Text Color
// ─────────────────────────────────────────────────────────────────────────────
export class EventQrSectionOption extends BaseOptionComponent {
    static template = "emailmarketing_event_qr_theming.EventQrSectionOption";
    static selector = ".s_event_qr_block";

    setup() {
        super.setup();
        this.state = useDomState((el) => {
            const sec = el.closest(".s_event_qr_block") || el;
            const textCol = sec.querySelector(".s_event_qr_text_col");
            const qrWrapper = sec.querySelector(".s_event_qr_wrapper");
            const heading = sec.querySelector("h3, h4, h5");
            const para = sec.querySelector("p");

            function readStyle(node, prop, fallback) {
                if (!node) return fallback;
                return node.style[prop] || fallback;
            }

            return {
                sectionBg: readStyle(sec, "backgroundColor", "#ffffff"),
                textColBg: readStyle(textCol, "backgroundColor", ""),
                qrWrapperBg: readStyle(qrWrapper, "backgroundColor", ""),
                headingColor: readStyle(heading, "color", "#212529"),
                textColor: readStyle(para, "color", "#6c757d"),
                hasTextCol: !!textCol,
                hasQrWrapper: !!qrWrapper,
            };
        });
    }

    _getSection() {
        const el = this.env.getEditingElement();
        return el.closest(".s_event_qr_block") || el;
    }

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
}

// ─────────────────────────────────────────────────────────────────────────────
// OPTION 1: QR Code options — shown ONLY when the QR wrapper column is selected
// Selector targets .s_event_qr_wrapper so these options NEVER appear when the
// user clicks on text, heading, or the button.
// ─────────────────────────────────────────────────────────────────────────────
export class EventQrOption extends BaseOptionComponent {
    static template = "emailmarketing_event_qr_theming.EventQrOption";
    static selector = ".s_event_qr_block .s_event_qr_wrapper";

    // Internal color/text state — independent of useDomState
    // so changes are preserved even when image src is a placeholder
    _fgColor = '#000000';
    _bgColor = '#f8f9fa';
    _qrText = 'https://www.odoo.com/event';
    _eyeColor = '#000000';
    _eyeOuterColor = '#000000';

    setup() {
        super.setup();
        this.state = useDomState((editingElement) => {
            // editingElement is the .s_event_qr_wrapper div
            const section = editingElement.closest('.s_event_qr_block');
            const qrImg = section ? section.querySelector('.s_event_qr_image') : null;
            const innerBox = section ? section.querySelector('.s_event_qr_inner') : null;

            let fgColor = '#000000';
            let bgColor = '#f8f9fa';
            let qrText = 'https://www.odoo.com/event';
            let eyeInnerColor = '#000000';
            let eyeOuterColor = '#000000';
            if (qrImg) {
                const src = qrImg.getAttribute('src') || '';
                try {
                    const url = new URL(src, window.location.origin);
                    fgColor = url.searchParams.get('fg_color') || '#000000';
                    bgColor = url.searchParams.get('bg_color') || '#f8f9fa';
                    qrText = url.searchParams.get('text') || 'https://www.odoo.com/event';
                    eyeInnerColor = url.searchParams.get('eye_color') || fgColor;
                    eyeOuterColor = url.searchParams.get('eye_outer_color') || fgColor;
                } catch (e) { /* use fallbacks */ }
            }
            // Sync internal tracking variables with DOM-read values
            this._fgColor = fgColor;
            this._bgColor = bgColor;
            this._qrText = qrText;
            this._eyeColor = eyeInnerColor;
            this._eyeOuterColor = eyeOuterColor;

            function readStyle(node, prop, fallback) {
                if (!node) return fallback;
                return node.style[prop] || fallback;
            }

            function toHex(color) {
                if (!color || color === 'transparent') return '#ffffff';
                if (color.startsWith('#')) return color;
                const matches = color.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*(\d+(?:\.\d+)?))?\)$/);
                if (!matches) return '#ffffff';
                if (matches[4] !== undefined && parseFloat(matches[4]) === 0) {
                    return '#ffffff';
                }
                const r = parseInt(matches[1]).toString(16).padStart(2, '0');
                const g = parseInt(matches[2]).toString(16).padStart(2, '0');
                const b = parseInt(matches[3]).toString(16).padStart(2, '0');
                return `#${r}${g}${b}`;
            }

            const borderCol = readStyle(innerBox, "borderColor", "#dee2e6");
            const borderW = parseInt(readStyle(innerBox, "borderWidth", "2px")) || 2;
            const borderRad = parseInt(readStyle(innerBox, "borderRadius", "8px")) || 8;

            return {
                fgColor,
                bgColor,
                qrText,
                eyeInnerColor,
                eyeOuterColor,
                boxBorderColor: toHex(borderCol),
                boxBorderWidth: borderW,
                boxRadius: borderRad,
            };
        });
    }

    _getInnerBox() {
        const editingElement = this.env.getEditingElement();
        const section = editingElement ? editingElement.closest('.s_event_qr_block') : null;
        return section ? section.querySelector('.s_event_qr_inner') : null;
    }

    updateColor(type, color) {
        const editingElement = this.env.getEditingElement();
        const section = editingElement.closest('.s_event_qr_block');
        if (type === 'fg') {
            this._fgColor = color;
            this.state.fgColor = color;
        } else {
            this._bgColor = color;
            this.state.bgColor = color;
            // Also update the visible CSS background of the QR inner box
            const innerBox = section ? section.querySelector('.s_event_qr_inner') : null;
            if (innerBox) innerBox.style.backgroundColor = color;
        }
        this._updateQrSrc(section);
    }

    updateText(text) {
        this._qrText = text;
        this.state.qrText = text;
        const editingElement = this.env.getEditingElement();
        const section = editingElement.closest('.s_event_qr_block');
        this._updateQrSrc(section);
    }

    updateEyeColor(type, color) {
        const editingElement = this.env.getEditingElement();
        const section = editingElement.closest('.s_event_qr_block');
        if (type === 'inner') {
            this._eyeColor = color;
            this.state.eyeInnerColor = color;
        } else {
            this._eyeOuterColor = color;
            this.state.eyeOuterColor = color;
        }
        this._updateQrSrc(section);
    }

    updateBoxBorderColor(color) {
        const b = this._getInnerBox();
        if (b) {
            b.style.borderColor = color;
            b.style.borderStyle = "solid";
        }
        this.state.boxBorderColor = color;
        this.config.onChange?.({ isPreviewing: false });
    }

    updateBoxBorderWidth(value) {
        const px = parseInt(value) || 0;
        const b = this._getInnerBox();
        if (b) {
            b.style.borderWidth = px + "px";
            b.style.borderStyle = "solid";
        }
        this.state.boxBorderWidth = px;
        this.config.onChange?.({ isPreviewing: false });
    }

    updateBoxRadius(value) {
        const px = parseInt(value) || 0;
        const b = this._getInnerBox();
        if (b) {
            b.style.setProperty('border-radius', px + 'px', 'important');
        }
        this.state.boxRadius = px;
        this.config.onChange?.({ isPreviewing: false });
    }

    _updateQrSrc(section) {
        const qrImg = section ? section.querySelector('.s_event_qr_image') : null;
        if (!qrImg) return;
        // Use internal tracking variables so values are always correct
        // even when the image src is still a placeholder PNG
        const newSrc = `/event_qr/generate?text=${encodeURIComponent(this._qrText)}&fg_color=${encodeURIComponent(this._fgColor)}&bg_color=${encodeURIComponent(this._bgColor)}&eye_color=${encodeURIComponent(this._eyeColor)}&eye_outer_color=${encodeURIComponent(this._eyeOuterColor)}`;
        qrImg.setAttribute('src', newSrc);
        this.config.onChange?.({ isPreviewing: false });
    }
}

export class EventQrButtonOption extends BaseOptionComponent {
    static template = "emailmarketing_event_qr_theming.EventQrButtonOption";
    static selector = ".s_event_qr_block .s_event_qr_btn";

    setup() {
        super.setup();
        this.state = useDomState((editingElement) => {
            const style = editingElement.style;
            const computedStyle = window.getComputedStyle(editingElement);

            function toHex(color) {
                if (!color || color === 'transparent') return '#ffffff';
                if (color.startsWith('#')) return color;
                const matches = color.match(/^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*(\d+(?:\.\d+)?))?\)$/);
                if (!matches) return '#ffffff';
                if (matches[4] !== undefined && parseFloat(matches[4]) === 0) {
                    return '#ffffff';
                }
                const r = parseInt(matches[1]).toString(16).padStart(2, '0');
                const g = parseInt(matches[2]).toString(16).padStart(2, '0');
                const b = parseInt(matches[3]).toString(16).padStart(2, '0');
                return `#${r}${g}${b}`;
            }

            return {
                buttonColor: toHex(style.backgroundColor || computedStyle.backgroundColor),
                textColor: toHex(style.color || computedStyle.color),
                borderColor: toHex(style.borderColor || computedStyle.borderColor),
            };
        });
    }

    updateButtonColor(color) {
        this.state.buttonColor = color;
        const editingElement = this.env.getEditingElement();
        if (editingElement) {
            editingElement.style.setProperty('background-color', color, 'important');
            this.config.onChange?.({ isPreviewing: false });
        }
    }

    updateTextColor(color) {
        this.state.textColor = color;
        const editingElement = this.env.getEditingElement();
        if (editingElement) {
            editingElement.style.setProperty('color', color, 'important');
            this.config.onChange?.({ isPreviewing: false });
        }
    }

    updateBorderColor(color) {
        this.state.borderColor = color;
        const editingElement = this.env.getEditingElement();
        if (editingElement) {
            editingElement.style.setProperty('border', `1px solid ${color}`, 'important');
            this.config.onChange?.({ isPreviewing: false });
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// PLUGIN: Register all 3 option classes into the mass_mailing builder
// ─────────────────────────────────────────────────────────────────────────────
class EventQrOptionPlugin extends Plugin {
    static id = "emailmarketing_event_qr_theming.EventQrOption";
    resources = {
        builder_options: [
            withSequence(0, EventQrSectionOption),
            withSequence(1, EventQrOption),
            withSequence(2, EventQrButtonOption),
        ],
    };
}

registry.category("mass_mailing-plugins").add(EventQrOptionPlugin.id, EventQrOptionPlugin);
