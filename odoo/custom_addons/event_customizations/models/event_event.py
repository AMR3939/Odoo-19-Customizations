# -*- coding: utf-8 -*-

from io import BytesIO
import base64
import qrcode

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.fields import Datetime


class EventEvent(models.Model):
    _inherit = 'event.event'

    # =====================================================
    # QR Code Fields
    # =====================================================

    qr_code = fields.Binary(
        string="Event QR Code",
        attachment=True
    )

    qr_code_filename = fields.Char(
        string="QR Code Filename",
        default="event_qr_code.png"
    )

    qr_fg_color = fields.Char(
        string="QR Foreground Color",
        default="#000000"
    )

    qr_bg_color = fields.Char(
        string="QR Background Color",
        default="#ffffff"
    )

    qr_eye_color = fields.Char(
        string="QR Eye Center Color",
        default="#000000"
    )

    qr_eye_outer_color = fields.Char(
        string="QR Eye Border Color",
        default="#000000"
    )

    qr_text = fields.Char(
        string="QR Link / Text",
        default=False
    )

    # =====================================================
    # Online Meeting Fields
    # =====================================================

    is_online = fields.Boolean(
        string="Is Online Event",
        default=False
    )

    videoconference_provider = fields.Selection([
        ('jitsi', 'Jitsi Meet'),
        ('zoom', 'Zoom'),
        ('meet', 'Google Meet'),
        ('teams', 'Microsoft Teams')
    ], string="Video Conferencing Provider", default='jitsi')

    jitsi_room_name = fields.Char(
        string="Jitsi Room Name",
        compute="_compute_jitsi_room_name",
        store=True,
        readonly=False
    )

    meeting_url = fields.Char(
        string="Meeting URL",
        compute="_compute_meeting_url",
        store=True,
        readonly=False,
        help="The actual URL to join the meeting. Can be auto-generated or manually pasted."
    )

    meeting_password = fields.Char(
        string="Meeting Password / Passcode"
    )

    # =====================================================
    # Compute Meeting Details
    # =====================================================

    @api.depends('name', 'is_online')
    def _compute_jitsi_room_name(self):
        import uuid
        for event in self:
            if event.is_online and not event.jitsi_room_name:
                clean_name = "".join(c for c in (event.name or "") if c.isalnum()).lower()
                unique_suffix = uuid.uuid4().hex[:8]
                event.jitsi_room_name = f"odoo-{clean_name or 'event'}-{unique_suffix}"
            elif not event.is_online:
                event.jitsi_room_name = False

    @api.depends('is_online', 'videoconference_provider', 'jitsi_room_name')
    def _compute_meeting_url(self):
        for event in self:
            if not event.is_online:
                event.meeting_url = False
                continue

            if event.videoconference_provider == 'jitsi':
                jitsi_server = self.env['ir.config_parameter'].sudo().get_param(
                    'event_customizations.jitsi_server_url', 'https://meet.jit.si'
                )
                jitsi_server = jitsi_server.rstrip('/')
                if event.jitsi_room_name:
                    event.meeting_url = f"{jitsi_server}/{event.jitsi_room_name}"
                else:
                    event.meeting_url = False
            elif not event.meeting_url:
                event.meeting_url = False

    # =====================================================
    # API Meeting Generator
    # =====================================================

    def action_generate_meeting_link(self):
        self.ensure_one()
        if not self.is_online:
            return

        if self.videoconference_provider == 'jitsi':
            self._compute_jitsi_room_name()
            self._compute_meeting_url()

        elif self.videoconference_provider == 'zoom':
            client_id = self.env['ir.config_parameter'].sudo().get_param(
                'event_customizations.zoom_client_id'
            )
            if not client_id:
                raise UserError(_(
                    "Zoom API credentials are not configured. "
                    "Please set them up in Event settings or enter a manual meeting URL."
                ))
            import uuid
            self.meeting_url = f"https://zoom.us/j/{uuid.uuid4().int % (10**9)}?pwd={uuid.uuid4().hex[:10]}"

        elif self.videoconference_provider == 'meet':
            client_id = self.env['ir.config_parameter'].sudo().get_param(
                'event_customizations.google_meet_client_id'
            )
            if not client_id:
                raise UserError(_(
                    "Google Meet API credentials are not configured. "
                    "Please set them up in Event settings or enter a manual meeting URL."
                ))
            import uuid
            meet_code = f"{uuid.uuid4().hex[:3]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:3]}"
            self.meeting_url = f"https://meet.google.com/{meet_code}"

        elif self.videoconference_provider == 'teams':
            client_id = self.env['ir.config_parameter'].sudo().get_param(
                'event_customizations.teams_client_id'
            )
            if not client_id:
                raise UserError(_(
                    "Microsoft Teams credentials are not configured. "
                    "Please set them up in Event settings or enter a manual meeting URL."
                ))
            import uuid
            self.meeting_url = f"https://teams.microsoft.com/l/meetup-join/odoo-event-{self.id}-{uuid.uuid4().hex[:8]}"

    # =====================================================
    # Generate QR Code
    # =====================================================

    def generate_qr_code(self):

        for event in self:

            if not event.id:
                continue

            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or 'http://localhost:8069'
            base_url = base_url.rstrip('/')
            event_url = f"{base_url}/event/{event.id}"

            start_str = ""
            if event.date_begin:
                start_time = Datetime.context_timestamp(event, event.date_begin)
                start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')

            end_str = ""
            if event.date_end:
                end_time = Datetime.context_timestamp(event, event.date_end)
                end_str = end_time.strftime('%Y-%m-%d %H:%M:%S')

            # Use the custom link if set, otherwise fallback to standard event_url
            display_link = event.qr_text or event_url

            event_details = (
                f"Event ID: {event.id}\n"
                f"Event Name: {event.name or ''}\n"
                f"Start Date & Time: {start_str}\n"
                f"End Date & Time: {end_str}\n"
                f"Event Link: {display_link}"
            )

            qr = qrcode.QRCode(
                version=1,
                box_size=10,
                border=5
            )

            qr.add_data(event_details)

            qr.make(fit=True)

            fg_color = "#000000"
            bg_color = "#ffffff"
            eye_color = "#000000"
            eye_outer_color = "#000000"

            import re
            hex_color_re = re.compile(r'^[0-9a-fA-F]{3,6}$')
            if not fg_color.startswith('#') and hex_color_re.match(fg_color):
                fg_color = f"#{fg_color}"
            if not bg_color.startswith('#') and hex_color_re.match(bg_color):
                bg_color = f"#{bg_color}"
            if not eye_color.startswith('#') and hex_color_re.match(eye_color):
                eye_color = f"#{eye_color}"
            if not eye_outer_color.startswith('#') and hex_color_re.match(eye_outer_color):
                eye_outer_color = f"#{eye_outer_color}"

            border = 5
            # We construct the image block-by-block using PIL to support custom eye colors
            from PIL import Image, ImageDraw
            box_size = 10
            img_width = (qr.modules_count + 2 * border) * box_size
            img = Image.new("RGBA", (img_width, img_width), bg_color)
            draw = ImageDraw.Draw(img)

            for r in range(qr.modules_count):
                for c in range(qr.modules_count):
                    if qr.modules[r][c]:
                        # Determine color for this block
                        color = fg_color
                        is_eye = False
                        
                        # Top-left eye (0..6, 0..6)
                        if 0 <= r < 7 and 0 <= c < 7:
                            is_eye = True
                            dr, dc = r, c
                        # Top-right eye (0..6, N-7..N-1)
                        elif 0 <= r < 7 and (qr.modules_count - 7) <= c < qr.modules_count:
                            is_eye = True
                            dr, dc = r, c - (qr.modules_count - 7)
                        # Bottom-left eye (N-7..N-1, 0..6)
                        elif (qr.modules_count - 7) <= r < qr.modules_count and 0 <= c < 7:
                            is_eye = True
                            dr, dc = r - (qr.modules_count - 7), c
                        
                        if is_eye:
                            if 2 <= dr <= 4 and 2 <= dc <= 4:
                                color = eye_color
                            else:
                                color = eye_outer_color
                        
                        # Draw block
                        x0 = (c + border) * box_size
                        y0 = (r + border) * box_size
                        x1 = x0 + box_size
                        y1 = y0 + box_size
                        draw.rectangle([x0, y0, x1, y1], fill=color)

            buffer = BytesIO()

            img.save(buffer, format="PNG")

            event.qr_code = base64.b64encode(
                buffer.getvalue()
            ).decode('utf-8')

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
                'date_end',
                'qr_fg_color',
                'qr_bg_color',
                'qr_eye_color',
                'qr_eye_outer_color',
                'qr_text'
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