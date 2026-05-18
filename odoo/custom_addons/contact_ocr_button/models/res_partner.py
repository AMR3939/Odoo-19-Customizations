# -*- coding: utf-8 -*-
import os
import base64
import logging
import io
import json
import numpy as np

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCR
    from PIL import Image
    import cv2
except ImportError:
    _logger.error("Missing dependency. Run: pip install paddleocr opencv-python-headless Pillow")
    PaddleOCR = None


# -------- Add “Scan Card” button on Contact form --------
class ResPartner(models.Model):
    _inherit = 'res.partner'

    def action_scan_via_ocr(self):
        """Open step 1 (Upload) view of the OCR wizard."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Business Card OCR',
            'res_model': 'ocr.wizard',
            'view_mode': 'form',
            'views': [(self.env.ref('contact_ocr_button.view_business_card_ocr_upload').id, 'form')],
            'target': 'new',
            'context': {'default_partner_id': self.id},
        }


# -------- OCR Wizard (two screens) --------
class OcrWizard(models.TransientModel):
    _name = 'ocr.wizard'
    _description = 'Business Card OCR Wizard'

    partner_id = fields.Many2one('res.partner', string="Contact", readonly=True)
    upload_image = fields.Binary(string="Upload Business Card")
    preview_image = fields.Binary(string="Processed Preview", readonly=True)
    ocr_line_ids = fields.One2many('ocr.wizard.line', 'wizard_id', string="Extracted Lines")

    # keep raw image + OCR result to avoid re-processing
    raw_image_data = fields.Binary("Raw Image Data")
    ocr_json_data = fields.Text("OCR JSON Data")

    # ---- Step 1 -> run OCR and go to Step 2
    def action_extract_data(self):
        self.ensure_one()

        if not self.upload_image:
            raise UserError("Please upload an image first.")

        if not PaddleOCR:
            raise UserError("OCR libraries are not installed.\n"
                            "Run: pip install paddleocr opencv-python-headless Pillow")

        # --- DYNAMIC PATH SETUP ---
        # Get the directory of the current file (models folder)
        current_dir = os.path.dirname(__file__)
        # Go up one level to the module root, then into ocr_models
        # This assumes your structure: contact_ocr_button/ocr_models/
        model_base_path = os.path.abspath(os.path.join(current_dir, '..', 'ocr_models'))

        det_model_dir = os.path.join(model_base_path, 'det')
        rec_model_dir = os.path.join(model_base_path, 'rec')
        cls_model_dir = os.path.join(model_base_path, 'cls')

        # Verify folders exist to prevent a crash
        if not os.path.exists(det_model_dir):
            raise UserError(f"Model folder not found at: {det_model_dir}. Please ensure you extracted the models there.")

        # --- IMAGE PROCESSING ---
        self.raw_image_data = self.upload_image
        image_data = base64.b64decode(self.raw_image_data)
        image_np = np.array(Image.open(io.BytesIO(image_data)).convert('RGB'))

        _logger.info("Starting OCR detection using LOCAL models...")
        
        # Initialize PaddleOCR with explicit local paths to skip internet check
        try:
            ocr_reader = PaddleOCR(
                use_angle_cls=True, 
                lang='en', 
                use_gpu=False, 
                show_log=False,
                det_model_dir=det_model_dir,
                rec_model_dir=rec_model_dir,
                cls_model_dir=cls_model_dir
            )
            ocr_results = ocr_reader.ocr(image_np, cls=True)
        except Exception as e:
            _logger.exception("OCR Processing Failed")
            raise UserError(f"OCR Error: {str(e)}")

        detected_objects = []
        if ocr_results and ocr_results[0]:
            for i, line in enumerate(ocr_results[0]):
                detected_objects.append({
                    'id': i,
                    'box': [int(p) for point in line[0] for p in point],  # flatten 4 points
                    'text': line[1][0],
                })

        self.ocr_json_data = json.dumps(detected_objects)
        self._update_lines_and_preview()

        # open Step 2 (Results) view
        return {
            'type': 'ir.actions.act_window',
            'name': 'Business Card OCR - Results',
            'res_model': 'ocr.wizard',
            'view_mode': 'form',
            'views': [(self.env.ref('contact_ocr_button.view_business_card_ocr_result').id, 'form')],
            'target': 'new',
            'res_id': self.id,
        }

    # ---- draw boxes + fill table
    def _update_lines_and_preview(self):
        if not self.ocr_json_data or not self.raw_image_data:
            return

        all_objects = json.loads(self.ocr_json_data)

        # refresh One2many
        self.write({'ocr_line_ids': [(5, 0, 0)] + [
            (0, 0, {'box_text': obj['text']}) for obj in all_objects
        ]})

        # draw polygon boxes on the preview
        image_data = base64.b64decode(self.raw_image_data)
        image_np = np.array(Image.open(io.BytesIO(image_data)).convert('RGB'))
        vis_image = image_np.copy()

        try:
            for obj in all_objects:
                points = np.array(obj['box']).reshape(-1, 2).astype(np.int32)
                cv2.polylines(vis_image, [points], isClosed=True, color=(0, 255, 0), thickness=2)

            _, buffer = cv2.imencode('.jpg', cv2.cvtColor(vis_image, cv2.COLOR_RGB2BGR))
            self.preview_image = base64.b64encode(buffer)
        except Exception as e:
            _logger.exception("Drawing boxes failed: %s", e)
            self.preview_image = self.raw_image_data

    # ---- Step 2: apply selections to partner, then close
    def action_apply_and_close(self):
        self.ensure_one()
        if not self.partner_id:
            return {'type': 'ir.actions.act_window_close'}

        partner_updates = {}
        company_name = None

        for line in self.ocr_line_ids:
            if line.label_id and line.label_id.target_field not in ['unassigned', 'other']:
                field_name = line.label_id.target_field
                if field_name == 'parent_id':
                    company_name = (line.box_text or '').strip()
                elif field_name:
                    if partner_updates.get(field_name):
                        partner_updates[field_name] += ' ' + (line.box_text or '')
                    else:
                        partner_updates[field_name] = (line.box_text or '')

        if company_name:
            company = self.env['res.partner'].search(
                [('is_company', '=', True), ('name', '=ilike', company_name)], limit=1
            )
            if not company:
                company = self.env['res.partner'].create({'name': company_name, 'is_company': True})
            partner_updates['parent_id'] = company.id

        if partner_updates:
            self.partner_id.write(partner_updates)

        return {'type': 'ir.actions.act_window_close'}

    # ---- Optional: go back to Step 1 (re-upload)
    def action_back_to_upload(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Business Card OCR',
            'res_model': 'ocr.wizard',
            'view_mode': 'form',
            'views': [(self.env.ref('contact_ocr_button.view_business_card_ocr_upload').id, 'form')],
            'target': 'new',
            'res_id': self.id,
        }


class OcrWizardLine(models.TransientModel):
    _name = 'ocr.wizard.line'
    _description = 'Line item in OCR Wizard'

    wizard_id = fields.Many2one('ocr.wizard', string="Wizard", ondelete='cascade')
    box_text = fields.Char(string="Detected Text")
    label_id = fields.Many2one('ocr.label', string="Label")