# -*- coding: utf-8 -*-

import logging

from odoo import models
from odoo.http import request

_logger = logging.getLogger(__name__)

# Cookie names (must also match models/event_registration.py and
# models/sale_order.py)
REFERRAL_COOKIE_PARTNER = "social_share_ref"
REFERRAL_COOKIE_TYPE = "social_share_ref_type"
REFERRAL_COOKIE_SOURCE = "social_share_ref_source_id"

VALID_REFERRAL_TYPES = ("event", "product", "blog")


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls, endpoint):
        """
        Capture referral query parameters on ANY website page request, not
        just the page being shared.

        Why this is needed: paid/ticketed events send the visitor first to
        `/event/<event>/register` (a ticket-selection page), not to
        `/event/<event>`; a shared product or blog link may likewise be
        followed by clicks to other pages before the visitor buys or signs
        up. Hooking into the global dispatch means it no longer matters
        which page the referral link points to, or which page the visitor
        is on when the rewarded action happens - the cookies get set as
        long as `ref` is present anywhere in the URL, once, and persist
        for the configured duration.

        Three cookies are stored:
        - `social_share_ref`: id of the referrer's res.partner.
        - `social_share_ref_type`: 'event' | 'product' | 'blog' - which
          kind of content was shared. Defaults to 'event' when a `ref`
          param is present without a `ref_type` (keeps already-shared
          event links, generated before this module supported product/
          blog referrals, working unchanged).
        - `social_share_ref_source_id`: id of the specific record shared
          (event id / product id / blog post id), used for reporting only
          - never used to decide whether/how much to reward.
        """
        response = super()._dispatch(endpoint)

        try:
            ref = request.httprequest.args.get("ref")
        except Exception:
            ref = None

        if not ref:
            return response

        # Only relevant for actual website (frontend) requests.
        if not getattr(request, "website", False):
            return response

        try:
            partner = request.env["res.partner"].sudo().browse(int(ref)).exists()
        except (ValueError, TypeError):
            partner = False

        if not partner:
            return response

        # Prevent logged-in users from referring themselves.
        if (
            not request.env.user._is_public()
            and request.env.user.partner_id == partner
        ):
            return response

        ref_type = request.httprequest.args.get("ref_type") or "event"
        if ref_type not in VALID_REFERRAL_TYPES:
            ref_type = "event"

        ref_source = request.httprequest.args.get("ref_src")

        try:
            cookie_days = int(
                request.env["ir.config_parameter"]
                .sudo()
                .get_param(
                    "social_sharing_loyalty_points_enhancement.referral_cookie_days",
                    default=30,
                )
            )
        except (ValueError, TypeError):
            cookie_days = 30

        max_age = cookie_days * 24 * 60 * 60

        try:
            response.set_cookie(
                REFERRAL_COOKIE_PARTNER,
                str(partner.id),
                max_age=max_age,
                httponly=True,
                samesite="Lax",
            )
            response.set_cookie(
                REFERRAL_COOKIE_TYPE,
                ref_type,
                max_age=max_age,
                httponly=True,
                samesite="Lax",
            )
            if ref_source:
                response.set_cookie(
                    REFERRAL_COOKIE_SOURCE,
                    str(ref_source),
                    max_age=max_age,
                    httponly=True,
                    samesite="Lax",
                )
        except AttributeError:
            # Not every response object supports cookies
            # (e.g. some JSON-RPC responses) - safe to skip.
            return response

        _logger.info(
            "Referral cookie set (global dispatch) for partner %s, type=%s",
            partner.display_name,
            ref_type,
        )

        return response