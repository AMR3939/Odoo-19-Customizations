# -*- coding: utf-8 -*-
from .registry import register_handler
from .share_base import BaseShareHandler


@register_handler
class EventShareHandler(BaseShareHandler):
    """Instant reward for clicking Share on a Website Event page.

    Kept separate from EventReferralHandler on purpose: sharing an event
    (this handler) and someone actually registering through that shared
    link (EventReferralHandler) are two independent, separately
    configurable rewards - exactly like Product/Blog sharing already
    works.
    """
    trigger_code = "event_share"
    content_type = "event"
