# -*- coding: utf-8 -*-
from .registry import register_handler
from .referral_base import BaseReferralHandler


@register_handler
class EventReferralHandler(BaseReferralHandler):
    """Referral reward granted when a visitor who followed a shared Event
    link actually registers for that event (free or paid ticket)."""
    trigger_code = "event_referral"
    referral_type = "event"
    unique_key_field = "registration_id"
