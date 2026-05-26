# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class SurveyProductImagesController(http.Controller):

    def _make_json(self, data):
        return request.make_response(
            json.dumps(data),
            headers=[('Content-Type', 'application/json')]
        )

    # ── Route 1: question already saved ──────────────────────────────────────
    @http.route(
        '/survey/product_images/question/<int:question_id>',
        type='http', auth='user', methods=['GET'], csrf=False,
    )
    def get_images_by_question(self, question_id, **kwargs):
        """
        Reads from saved survey.question.selected.image records.
        Falls back to the product if no saved records exist yet.
        """
        question = request.env['survey.question'].sudo().browse(question_id)
        if not question.exists():
            return self._make_json([])

        saved = request.env['survey.question.selected.image'].sudo().search([
            ('question_id', '=', question_id),
            ('image', '!=', False),
        ])

        if saved:
            return self._make_json([{
                'id': img.id,
                'name': img.name or '',
                'image_type': img.image_type or '',
                'url': f'/web/image/survey.question.selected.image/{img.id}/image',
            } for img in saved])

        # No saved records yet — fall back to product
        return self._make_json(
            self._collect_from_product(
                question.selected_product_id,
                question.show_product_images,
                question.show_variant_images,
                question.show_ecommerce_media,
            )
        )

    # ── Route 2: question not yet saved — read from product directly ─────────
    @http.route(
        '/survey/product_images/product/<int:product_id>/<string:flags>',
        type='http', auth='user', methods=['GET'], csrf=False,
    )
    def get_images_by_product(self, product_id, flags='0,0,0', **kwargs):
        """
        Reads images directly from the product record.
        flags = "show_product,show_variant,show_ecommerce"  (e.g. "1,0,1")
        Used by the JS widget before the question is saved.
        """
        parts = flags.split(',')
        show_product   = len(parts) > 0 and parts[0] == '1'
        show_variant   = len(parts) > 1 and parts[1] == '1'
        show_ecommerce = len(parts) > 2 and parts[2] == '1'

        product = request.env['product.template'].sudo().browse(product_id)
        if not product.exists():
            return self._make_json([])

        return self._make_json(
            self._collect_from_product(product, show_product, show_variant, show_ecommerce)
        )

    # ── shared helper ─────────────────────────────────────────────────────────
    def _collect_from_product(self, product, show_product, show_variant, show_ecommerce):
        if not product:
            return []

        result = []
        fake_id = -1  # negative IDs mark preview-only entries

        if show_product and product.image_1920:
            result.append({
                'id': fake_id,
                'name': product.name or '',
                'image_type': 'product',
                'url': f'/web/image/product.template/{product.id}/image_1920',
            })
            fake_id -= 1

        if show_variant:
            for variant in product.product_variant_ids:
                if variant.image_variant_1920:
                    result.append({
                        'id': fake_id,
                        'name': variant.display_name or '',
                        'image_type': 'variant',
                        'url': f'/web/image/product.product/{variant.id}/image_variant_1920',
                    })
                    fake_id -= 1

        if show_ecommerce:
            for media in product.product_template_image_ids:
                if media.image_1920:
                    result.append({
                        'id': fake_id,
                        'name': media.name or '',
                        'image_type': 'ecommerce',
                        'url': f'/web/image/product.image/{media.id}/image_1920',
                    })
                    fake_id -= 1

        return result