# -*- coding: utf-8 -*-
from .registry import register_handler
from .referral_base import BaseReferralHandler


@register_handler
class ProductReferralHandler(BaseReferralHandler):
    """Referral reward granted when a visitor who followed a shared
    Product link places their first confirmed order."""
    trigger_code = "product_referral"
    referral_type = "product"
