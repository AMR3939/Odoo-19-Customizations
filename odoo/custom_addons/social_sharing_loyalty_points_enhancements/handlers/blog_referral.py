# -*- coding: utf-8 -*-
from .registry import register_handler
from .referral_base import BaseReferralHandler


@register_handler
class BlogReferralHandler(BaseReferralHandler):
    """Referral reward granted when a visitor who followed a shared
    Blog link creates a website account."""
    trigger_code = "blog_referral"
    referral_type = "blog"
