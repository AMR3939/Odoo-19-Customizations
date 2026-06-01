# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    jitsi_server_url = fields.Char(
        string="Jitsi Server URL",
        default="https://meet.jit.si",
        config_parameter="event_customizations.jitsi_server_url",
        help="The URL of the Jitsi server used for online events."
    )

    zoom_client_id = fields.Char(
        string="Zoom Client ID",
        config_parameter="event_customizations.zoom_client_id",
        help="Client ID for Zoom OAuth integration."
    )

    zoom_client_secret = fields.Char(
        string="Zoom Client Secret",
        config_parameter="event_customizations.zoom_client_secret",
        help="Client Secret for Zoom OAuth integration."
    )

    google_meet_client_id = fields.Char(
        string="Google Meet Client ID",
        config_parameter="event_customizations.google_meet_client_id",
        help="Client ID for Google Meet integration."
    )

    google_meet_client_secret = fields.Char(
        string="Google Meet Client Secret",
        config_parameter="event_customizations.google_meet_client_secret",
        help="Client Secret for Google Meet integration."
    )

    teams_client_id = fields.Char(
        string="Microsoft Teams Client ID",
        config_parameter="event_customizations.teams_client_id",
        help="Client ID for Microsoft Teams integration."
    )

    teams_client_secret = fields.Char(
        string="Microsoft Teams Client Secret",
        config_parameter="event_customizations.teams_client_secret",
        help="Client Secret for Microsoft Teams integration."
    )