# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHandlerRegistry(TransactionCase):
    """Covers the core safety guarantee of the Registry/Handler pattern:
    an unsupported or unconfigured reward trigger must NEVER raise and
    must NEVER grant points."""

    def setUp(self):
        super().setUp()
        from odoo.addons.social_sharing_loyalty_points_enhancement.handlers.registry import (
            HANDLER_REGISTRY, get_handler, get_supported_triggers,
        )
        self.HANDLER_REGISTRY = HANDLER_REGISTRY
        self.get_handler = get_handler
        self.get_supported_triggers = get_supported_triggers

    def test_all_expected_handlers_registered(self):
        expected = {
            "product_share", "blog_share", "event_share",
            "event_referral", "product_referral", "blog_referral",
        }
        self.assertTrue(expected.issubset(set(self.get_supported_triggers())))

    def test_unknown_trigger_returns_none_not_error(self):
        handler = self.get_handler("totally_unregistered_trigger", self.env)
        self.assertIsNone(handler)

    def test_none_trigger_returns_none(self):
        handler = self.get_handler("none", self.env)
        self.assertIsNone(handler)

    def test_each_handler_reports_its_trigger_code(self):
        for trigger_code, handler_cls in self.HANDLER_REGISTRY.items():
            handler = handler_cls(self.env)
            self.assertEqual(handler.trigger_code, trigger_code)
