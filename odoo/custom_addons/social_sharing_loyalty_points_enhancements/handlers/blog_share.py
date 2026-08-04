# -*- coding: utf-8 -*-
from .registry import register_handler
from .share_base import BaseShareHandler


@register_handler
class BlogShareHandler(BaseShareHandler):
    """Instant reward for clicking Share on a Blog post page."""
    trigger_code = "blog_share"
    content_type = "blog"
