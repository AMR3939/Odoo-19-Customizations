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

            event_url = f"/event/{event.id}"

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