/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillUpdateProps, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class ProductImagePickerWidget extends Component {
    static template = "graphic_designer_workflow.ProductImagePicker";
    static props = ["*"];

    setup() {
        this.notification = useService("notification");
        this.fileInputRef = useRef("fileInput");

        this.state = useState({
            pickerOpen: false,
            loading: false,
            images: [],
            selectedId: null,
            currentImageUrl: this._resolveImageUrl(this.props),
        });

        onWillUpdateProps((nextProps) => {
            const next = this._resolveImageUrl(nextProps);
            if (next) {
                this.state.currentImageUrl = next;
            }
        });
    }

    // ── helpers ────────────────────────────────────────────────────────────

    _mimeFromBase64(b64) {
        try {
            const bin = atob(b64.substring(0, 16));
            const b = (i) => bin.charCodeAt(i);
            if (b(0) === 0xFF && b(1) === 0xD8) return "image/jpeg";
            if (b(0) === 0x89 && b(1) === 0x50) return "image/png";
            if (b(0) === 0x47 && b(1) === 0x49) return "image/gif";
            if (b(0) === 0x52 && b(1) === 0x49) return "image/webp";
        } catch (_) { }
        return "image/png";
    }

    _b64ToDataUrl(b64) {
        return `data:${this._mimeFromBase64(b64)};base64,${b64}`;
    }

    /**
     * Resolve the current image URL from every possible location Odoo
     * might store the binary value — props, record.data, _changes, _values.
     * Returns a displayable URL string or null.
     */
    _resolveImageUrl(p) {
        const recId = p.record?.resId;
        const fieldName = p.name || "value_image";

        // Gather every candidate value Odoo might have put the binary in
        const candidates = [
            p.value,
            p.record?.data?.[fieldName],
            p.record?._changes?.[fieldName],
            p.record?._values?.[fieldName],
        ];

        for (const val of candidates) {
            if (!val) continue;

            // Already a usable URL path
            if (typeof val === "string" && val.startsWith("/")) return val;

            // Base64 string — build inline data URI with correct MIME
            if (typeof val === "string" && val.length > 100) {
                return this._b64ToDataUrl(val);
            }

            // Odoo passes `true` for saved non-empty binary — use /web/image/
            if (val === true && recId) {
                return `/web/image/survey.question.answer/${recId}/${fieldName}`;
            }
        }

        // Last resort: saved record — always works after save
        if (recId) {
            // Only return if the field is actually set on the record
            const saved = p.record?.data?.[fieldName];
            if (saved) {
                return `/web/image/survey.question.answer/${recId}/${fieldName}`;
            }
        }

        return null;
    }

    _getParentRecord() {
        try {
            const rec = this.props.record;
            if (!rec) return null;

            const candidates = [];
            if (rec._parentRecord) candidates.push(rec._parentRecord);

            const list = rec._parentList || rec.__parentList;
            if (list?._parentRecord) candidates.push(list._parentRecord);
            if (list?.record) candidates.push(list.record);

            const root = rec.model?.root;
            if (root) candidates.push(root);

            for (const c of candidates) {
                if ("selected_product_id" in (c?.data || {})) return c;
            }

            return root || null;
        } catch (e) {
            console.error("[ImagePicker] _getParentRecord error:", e);
            return null;
        }
    }

    _getQuestionId() {
        try {
            const ctx = this.props.record?.context || {};
            if (ctx.default_question_id) return ctx.default_question_id;
            const parent = this._getParentRecord();
            if (parent?.resId) return parent.resId;
        } catch (_) { }
        return null;
    }

    _getProductInfo() {
        try {
            const parent = this._getParentRecord();
            if (!parent) return null;

            const data = parent.data || {};
            const changes = parent._changes || {};
            const values = parent._values || {};

            const resolveM2o = (f) => {
                if (!f && f !== 0) return null;
                if (typeof f === "number") return f;
                if (Array.isArray(f)) return f[0] || null;
                if (typeof f === "object") return f.id || f.resId || null;
                return null;
            };

            const productId =
                resolveM2o(data.selected_product_id) ||
                resolveM2o(changes.selected_product_id) ||
                resolveM2o(values.selected_product_id);

            const getBool = (key) => !!(data[key] ?? changes[key] ?? values[key]);

            if (!productId) return null;

            return {
                productId,
                showProduct: getBool("show_product_images"),
                showVariant: getBool("show_variant_images"),
                showEcommerce: getBool("show_ecommerce_media"),
            };
        } catch (e) {
            console.error("[ImagePicker] _getProductInfo error:", e);
            return null;
        }
    }

    // ── actions ────────────────────────────────────────────────────────────

    async openPicker() {
        this.state.pickerOpen = true;
        this.state.loading = true;
        this.state.images = [];
        this.state.selectedId = null;

        try {
            const info = this._getProductInfo();
            let url;

            if (info) {
                const flags = [
                    info.showProduct ? "1" : "0",
                    info.showVariant ? "1" : "0",
                    info.showEcommerce ? "1" : "0",
                ].join(",");
                url = `/survey/product_images/product/${info.productId}/${flags}`;
            } else {
                const questionId = this._getQuestionId();
                if (questionId) {
                    url = `/survey/product_images/question/${questionId}`;
                } else {
                    this.notification.add(
                        "Please select an approved product and enable at least one image type first.",
                        { type: "warning" }
                    );
                    this.state.pickerOpen = false;
                    this.state.loading = false;
                    return;
                }
            }

            const res = await fetch(url, { method: "GET" });
            const data = await res.json();
            this.state.images = data || [];

            if (this.state.images.length === 0) {
                this.notification.add(
                    "No images found. Make sure an approved product is selected and image toggles are enabled.",
                    { type: "warning" }
                );
            }
        } catch (e) {
            console.error("[ImagePicker] fetch error:", e);
            this.notification.add("Could not load product images.", { type: "danger" });
            this.state.images = [];
        } finally {
            this.state.loading = false;
        }
    }

    closePicker() {
        this.state.pickerOpen = false;
        this.state.selectedId = null;
    }

    selectImage(img) {
        this.state.selectedId = img.id;
    }

    async confirmSelection() {
        const img = this.state.images.find((i) => i.id === this.state.selectedId);
        if (!img) return;

        try {
            const res = await fetch(img.url);
            const blob = await res.blob();
            const mime = blob.type || "image/jpeg";
            const base64 = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result.split(",")[1]);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });

            await this.props.record.update({ value_image: base64 });
            // Set inline data URI immediately — survives re-render since
            // onWillUpdateProps will re-read the base64 from record.data
            this.state.currentImageUrl = `data:${mime};base64,${base64}`;
            this.closePicker();
            this.notification.add("Image selected successfully.", { type: "success" });
        } catch (e) {
            this.notification.add("Failed to apply the selected image.", { type: "danger" });
        }
    }

    async clearImage() {
        await this.props.record.update({ value_image: false });
        this.state.currentImageUrl = null;
    }

    // ── local file upload ──────────────────────────────────────────────────

    triggerFileUpload() {
        const input = this.fileInputRef.el;
        if (input) {
            input.value = "";
            input.click();
        }
    }

    async onFileSelected(ev) {
        const file = ev.target.files && ev.target.files[0];
        if (!file) return;

        try {
            const mime = file.type || "image/png";
            const base64 = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result.split(",")[1]);
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });

            await this.props.record.update({ value_image: base64 });
            this.state.currentImageUrl = `data:${mime};base64,${base64}`;
            this.notification.add("Image uploaded successfully.", { type: "success" });
        } catch (e) {
            console.error("[ImagePicker] file upload error:", e);
            this.notification.add("Failed to upload the image.", { type: "danger" });
        }
    }
}

registry.category("fields").add("product_image_picker", {
    component: ProductImagePickerWidget,
    supportedTypes: ["binary"],
});