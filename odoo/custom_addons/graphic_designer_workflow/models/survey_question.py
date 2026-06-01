# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    show_product_images = fields.Boolean(string="Product Images", default=False)
    show_variant_images = fields.Boolean(string="Product Variant Images", default=False)
    show_ecommerce_media = fields.Boolean(string="E-commerce Media", default=False)

    selected_product_id = fields.Many2one(
        'product.template',
        string="Approved Product",
        domain="[('approval_state', '=', 'approved')]",
        help="Select an approved product to pull images from."
    )

    selected_image_ids = fields.One2many(
        'survey.question.selected.image',
        'question_id',
        string="Available Product Images"
    )

    description_with_images = fields.Html(
        string="Description with Images",
        compute='_compute_description_with_images',
        store=True,
        sanitize=False
    )

    TRIGGER_FIELDS = frozenset({
        'selected_product_id',
        'show_product_images',
        'show_variant_images',
        'show_ecommerce_media',
    })

    # ── image collection ──────────────────────────────────────────────────────

    def _collect_image_vals(self, include_url=False):
        """
        Collect image values from the selected product.

        include_url=True  → also populate image_url with a product /web/image/
                            URL so the list column shows the image immediately
                            (used by onchange and _sync).
        """
        self.ensure_one()
        image_vals = []
        product = self.selected_product_id
        if not product:
            return image_vals

        if self.show_product_images and product.image_1920:
            val = {
                'image': product.image_1920,
                'image_type': 'product',
                'name': product.name,
                'selected': True,
            }
            if include_url:
                val['image_url'] = f'/web/image/product.template/{product.id}/image_1920'
            image_vals.append(val)

        if self.show_variant_images:
            for variant in product.product_variant_ids:
                if variant.image_variant_1920:
                    val = {
                        'image': variant.image_variant_1920,
                        'image_type': 'variant',
                        'name': variant.display_name,
                        'selected': True,
                    }
                    if include_url:
                        val['image_url'] = f'/web/image/product.product/{variant.id}/image_variant_1920'
                    image_vals.append(val)

        if self.show_ecommerce_media:
            for media in product.product_template_image_ids:
                if media.image_1920:
                    val = {
                        'image': media.image_1920,
                        'image_type': 'ecommerce',
                        'name': media.name,
                        'selected': True,
                    }
                    if include_url:
                        val['image_url'] = f'/web/image/product.image/{media.id}/image_1920'
                    image_vals.append(val)

        return image_vals

    def _sync_selected_images(self, pre_selected_by_index=None):
        """
        Delete stale image rows and recreate with binary + proper image_url.
        pre_selected_by_index: dict of {position_index: bool} from create() commands.
        Falls back to reading existing DB rows keyed by (image_type, name).
        """
        for rec in self:
            rec.invalidate_recordset()
            question = self.env['survey.question'].browse(rec.id)

            # Build selected map from DB (for write/update scenarios)
            existing_selected = {
                (img.image_type, img.name): img.selected
                for img in question.selected_image_ids
                if img.image_type and img.name
            }

            question.selected_image_ids.unlink()

            if not question.selected_product_id:
                continue

            image_vals = question._collect_image_vals(include_url=False)
            for i, val in enumerate(image_vals):
                if pre_selected_by_index is not None:
                    # Use positional index from create() commands
                    val['selected'] = pre_selected_by_index.get(i, True)
                else:
                    # Use name+type key from existing DB rows (write scenario)
                    key = (val.get('image_type'), val.get('name'))
                    val['selected'] = existing_selected.get(key, True)
                val['question_id'] = question.id
                created = self.env['survey.question.selected.image'].create(val)
                created.image_url = (
                    f'/web/image/survey.question.selected.image/{created.id}/image'
                )

    # ── onchange ──────────────────────────────────────────────────────────────

    @api.onchange('selected_product_id', 'show_product_images',
                  'show_variant_images', 'show_ecommerce_media')
    def _onchange_selected_product_images(self):
        """
        Populate rows with binary + product-based image_url for immediate
        preview.  The image_url here points at the product record so it's
        visible before save.  write() will replace these with permanent rows
        pointing at survey.question.selected.image records.
        """
        self.selected_image_ids = [(5, 0, 0)]
        if not self.selected_product_id:
            return
        # include_url=True so the Image URL column shows immediately
        image_vals = self._collect_image_vals(include_url=True)
        self.selected_image_ids = [(0, 0, val) for val in image_vals]

    # ── write / create ────────────────────────────────────────────────────────

    def write(self, vals):
        affected_ids = self.ids if self.TRIGGER_FIELDS.intersection(vals.keys()) else []
        res = super().write(vals)
        if affected_ids:
            self.env['survey.question'].browse(affected_ids)._sync_selected_images()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        # Extract selected state per image index from one2many create commands
        # BEFORE super().create(), keyed by position since image_type/name
        # are not set on virtual records yet.
        pre_selected_by_index = []
        for vals in vals_list:
            selected_by_index = {}
            for i, cmd in enumerate(vals.get('selected_image_ids') or []):
                if isinstance(cmd, (list, tuple)) and len(cmd) >= 3 and cmd[0] == 0:
                    cv = cmd[2] if isinstance(cmd[2], dict) else {}
                    selected_by_index[i] = cv.get('selected', True)
            pre_selected_by_index.append(selected_by_index)

        records = super().create(vals_list)

        for rec, vals, sel_by_idx in zip(records, vals_list, pre_selected_by_index):
            if not rec.selected_product_id:
                continue
            if not self.TRIGGER_FIELDS.intersection(vals.keys()):
                continue
            rec._sync_selected_images(pre_selected_by_index=sel_by_idx)
        return records

    # ── description HTML ──────────────────────────────────────────────────────

    @api.depends('selected_image_ids.selected', 'selected_image_ids.image',
                 'selected_image_ids.image_type', 'selected_image_ids.name')
    def _compute_description_with_images(self):
        for rec in self:
            selected_images = rec.selected_image_ids.filtered(
                lambda img: img.selected and img.image
            )
            if not selected_images:
                rec.description_with_images = ""
                continue

            cards = []
            for img in selected_images:
                if img.id:
                    img_src = f"/web/image/survey.question.selected.image/{img.id}/image"
                else:
                    try:
                        img_data = img.image
                        img_b64 = img_data.decode('utf-8') if isinstance(img_data, bytes) else str(img_data)
                        img_src = f"data:image/png;base64,{img_b64}"
                    except Exception:
                        continue

                label = "Product Image"
                if img.image_type == 'variant':
                    label = "Variant"
                elif img.image_type == 'ecommerce':
                    label = "E-com Media"

                cards.append(rec._generate_image_card_html(img_src, label, img.name or ""))

            if cards:
                rec.description_with_images = f"""
                <style>
                    .product-image-card:hover {{
                        transform: translateY(-4px) scale(1.02);
                        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.08) !important;
                        border-color: rgba(99, 102, 241, 0.4) !important;
                    }}
                </style>
                <div class="o_survey_product_carousel_container mt-3" style="width: 100%;">
                    <h5 style="margin-bottom: 12px; font-weight: 600; color: #495057; font-size: 14px; letter-spacing: 0.3px;">Lifestyle Images</h5>
                    <div style="display: flex; flex-direction: row; gap: 16px; overflow-x: auto; padding: 12px 4px; scrollbar-width: thin; scroll-behavior: smooth;">
                        {''.join(cards)}
                    </div>
                </div>
                """
            else:
                rec.description_with_images = ""

    def _generate_image_card_html(self, img_src, label, subtitle):
        badge_bg = "#eff6ff"
        badge_color = "#2563eb"
        if label == "Variant":
            badge_bg = "#faf5ff"
            badge_color = "#7c3aed"
        elif label == "E-com Media":
            badge_bg = "#ecfdf5"
            badge_color = "#059669"

        return f"""
        <div class="product-image-card" style="flex: 0 0 170px; width: 170px; display: flex; flex-direction: column; border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 12px; padding: 12px; background-color: #ffffff; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03), 0 2px 4px -1px rgba(0,0,0,0.02); transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1); cursor: default;">
            <div style="position: relative; width: 100%; height: 140px; display: flex; align-items: center; justify-content: center; overflow: hidden; border-radius: 8px; background-color: #f8f9fa;">
                <span style="position: absolute; top: 6px; left: 6px; padding: 2px 7px; font-size: 8px; font-weight: 700; border-radius: 12px; background-color: {badge_bg}; color: {badge_color}; text-transform: uppercase; letter-spacing: 0.5px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">{label}</span>
                <img src="{img_src}" alt="{label}" style="max-width: 90%; max-height: 90%; object-fit: contain;"/>
            </div>
            <div style="margin-top: 10px; width: 100%; text-align: center;">
                <span title="{subtitle}" style="display: block; font-size: 12px; color: #374151; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; line-height: 1.4;">{subtitle}</span>
            </div>
        </div>
        """