# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class EventMeetingController(http.Controller):

    @http.route('/event/meeting/join/<string:token>',
                type='http', auth='public', website=True)
    def join_meeting(self, token, **kwargs):
        """Route to securely join video conferencing meeting."""

        registration = request.env['event.registration'].sudo().search(
            [('access_token', '=', token)], limit=1
        )

        if not registration:
            return request.render('website.404')

        if not registration._is_paid_and_registered():
            sale_status = getattr(registration, 'sale_status', None)
            return request.render('event_customizations.meeting_access_denied', {
                'registration': registration,
                'event': registration.event_id,
                'sale_status': sale_status,
            })

        event = registration.event_id

        if not event.is_online or not event.meeting_url:
            return request.render('event_customizations.meeting_not_ready', {
                'registration': registration,
                'event': event,
            })

        if event.videoconference_provider == 'jitsi':
            jitsi_server = 'https://meet.jit.si'
            if event.meeting_url:
                parts = event.meeting_url.rsplit('/', 1)
                if len(parts) == 2:
                    jitsi_server = parts[0]

            return request.render('event_customizations.portal_meeting_jitsi', {
                'registration': registration,
                'event': event,
                'jitsi_room_name': event.jitsi_room_name,
                'jitsi_server_domain': jitsi_server.replace(
                    'https://', '').replace('http://', ''),
                'meeting_password': event.meeting_password or '',
            })

        return request.redirect(event.meeting_url, local=False)


class EventQRUpdateController(http.Controller):

    @http.route('/event/update_qr_colors', type='json', auth='user', website=True)
    def update_qr_colors(self, event_id, fg_color=None, bg_color=None, qr_text=None, eye_color=None, eye_outer_color=None):
        """Endpoint to update event QR code colors and link from frontend editor."""
        event = request.env['event.event'].browse(int(event_id))
        if not event.exists():
            return {'success': False, 'error': 'Event not found'}
        vals = {}
        if fg_color is not None:
            vals['qr_fg_color'] = fg_color
        if bg_color is not None:
            vals['qr_bg_color'] = bg_color
        if qr_text is not None:
            vals['qr_text'] = qr_text or False
        if eye_color is not None:
            vals['qr_eye_color'] = eye_color
        if eye_outer_color is not None:
            vals['qr_eye_outer_color'] = eye_outer_color
        if vals:
            event.write(vals)
            event.generate_qr_code()
        return {'success': True}