# -*- coding: utf-8 -*-

from io import BytesIO
import base64
import qrcode

from odoo import models, fields, api
from odoo.fields import Datetime


class EventEvent(models.Model):
    _inherit = 'event.event'

    # =====================================================
    # Fields
    # =====================================================

    qr_code = fields.Binary(
        string="Event QR Code",
        attachment=True
    )

    qr_code_filename = fields.Char(
        string="QR Code Filename",
        default="event_qr_code.png"
    )

    # =====================================================
    # Generate QR Code
    # =====================================================

    def generate_qr_code(self):

        for event in self:

            if not event.id:
                continue

            # Odoo 19 compatible URL
            event_url = (
                f"/event/{event.id}"
            )

            start_time = Datetime.context_timestamp(
                event,
                event.date_begin
            )

            end_time = Datetime.context_timestamp(
                event,
                event.date_end
            )

            event_details = (
                f"Event ID: {event.id}\n"
                f"Event Name: {event.name}\n"
                f"Start Date & Time: "
                f"{start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"End Date & Time: "
                f"{end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Event Link: {event_url}"
            )

            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=5
            )

            qr.add_data(event_details)

            qr.make(fit=True)

            img = qr.make_image(
                fill_color="black",
                back_color="white"
            )

            buffer = BytesIO()

            img.save(buffer, format="PNG")

            event.qr_code = base64.b64encode(
                buffer.getvalue()
            )

            event.qr_code_filename = (
                f"event_{event.id}_qr.png"
            )

    # =====================================================
    # Auto Generate on Create
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):

        events = super().create(vals_list)

        events.generate_qr_code()

        return events

    # =====================================================
    # Auto Regenerate on Update
    # =====================================================

    def write(self, vals):

        res = super().write(vals)

        if any(
            field in vals
            for field in [
                'name',
                'date_begin',
                'date_end'
            ]
        ):
            self.generate_qr_code()

        return res

    # =====================================================
    # Download QR Action
    # =====================================================

    def action_download_qr(self):

        self.ensure_one()

        if not self.qr_code:
            return False

        return {
            'type': 'ir.actions.act_url',
            'url': (
                f"/web/content/"
                f"{self._name}/"
                f"{self.id}/"
                f"qr_code"
                f"?download=true"
                f"&filename={self.qr_code_filename}"
            ),
            'target': 'self',
        }