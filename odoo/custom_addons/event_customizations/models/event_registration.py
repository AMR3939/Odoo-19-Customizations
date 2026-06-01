# -*- coding: utf-8 -*-

import uuid
from odoo import api, fields, models


class EventRegistration(models.Model):
    _inherit = 'event.registration'

    access_token = fields.Char(
        string="Access Token",
        default=lambda self: uuid.uuid4().hex,
        copy=False,
        readonly=True,
        help="Secure token to authorize access to the event's meeting URL."
    )

    event_is_online = fields.Boolean(
        string="Event Is Online",
        related="event_id.is_online",
        store=False
    )

    secure_join_url = fields.Char(
        string="Secure Meeting Link",
        compute="_compute_secure_join_url",
        store=False
    )

    # =====================================================
    # Compute Secure URL
    # =====================================================

    @api.depends('access_token', 'event_id.is_online')
    def _compute_secure_join_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8019')
        base_url = base_url.rstrip('/')
        for reg in self:
            if reg.event_id.is_online and reg.access_token:
                reg.secure_join_url = f"{base_url}/event/meeting/join/{reg.access_token}"
            else:
                reg.secure_join_url = False

    # =====================================================
    # Helpers
    # =====================================================

    def get_secure_join_url(self):
        """Helper to generate the secure redirect URL sent to attendees."""
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', 'http://localhost:8019')
        return f"{base_url.rstrip('/')}/event/meeting/join/{self.access_token}"

    def _is_paid_and_registered(self):
        """Validates if the attendee is registered and has paid for the ticket."""
        self.ensure_one()
        # 1. State must be 'open' (Confirmed) or 'done' (Attended)
        is_registered = self.state in ('open', 'done')

        # 2. Payment check: If event_sale is installed, verify the ticket is paid ('sold' or 'free')
        is_paid = True
        if hasattr(self, 'sale_status'):
            is_paid = self.sale_status in ('sold', 'free')

        return is_registered and is_paid

    # =====================================================
    # Button Action
    # =====================================================

    def action_open_meeting_link(self):
        """Open the secure join URL in a new browser tab from the backend."""
        self.ensure_one()
        url = self.get_secure_join_url()
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

