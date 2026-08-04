# -*- coding: utf-8 -*-
from .registry import register_handler
from .share_base import BaseShareHandler


@register_handler
class ProductShareHandler(BaseShareHandler):
    """Instant reward for clicking Share on an eCommerce Product page."""
    trigger_code = "product_share"
    content_type = "product"
