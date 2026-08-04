# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRewardService(TransactionCase):
    """Covers the validation layer end-to-end through RewardService,
    without needing a full website/checkout flow."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from odoo.addons.social_sharing_loyalty_points_enhancement.services.reward_service import (
            RewardService,
        )
        cls.RewardService = RewardService

        cls.partner_a = cls.env["res.partner"].create({"name": "Referrer A"})
        cls.partner_b = cls.env["res.partner"].create({"name": "Referred B"})

        cls.program = cls.env["loyalty.program"].create({
            "name": "Test Product Share Program",
            "program_type": "loyalty",
            "applies_on": "both",
            "trigger": "auto",
            "reward_trigger": "product_share",
            "reward_trigger_points": 15,
        })
        cls.env["ir.config_parameter"].sudo().set_param(
            "social_sharing_loyalty_points_enhancement.enable_product_share_rewards",
            "True",
        )

    def test_share_reward_granted_when_configured(self):
        share = self.RewardService.grant_share_reward(
            self.env, self.partner_a, "/shop/test-product-1",
            content_name="Test Product",
        )
        self.assertTrue(share)
        self.assertEqual(share.rewarded_points, 15)
        self.assertEqual(share.content_type, "product")

    def test_share_reward_skipped_when_feature_disabled(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "social_sharing_loyalty_points_enhancement.enable_product_share_rewards",
            "False",
        )
        try:
            share = self.RewardService.grant_share_reward(
                self.env, self.partner_a, "/shop/test-product-2",
            )
            self.assertFalse(share)
        finally:
            self.env["ir.config_parameter"].sudo().set_param(
                "social_sharing_loyalty_points_enhancement.enable_product_share_rewards",
                "True",
            )

    def test_share_reward_toggles_are_independent_per_content_type(self):
        """Disabling Product Share must NOT disable Blog/Event Share -
        each of the three has its own switch (see
        services/validation_service.py::is_feature_enabled)."""
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param(
            "social_sharing_loyalty_points_enhancement.enable_product_share_rewards",
            "False",
        )
        try:
            self.assertFalse(
                self.RewardService.grant_share_reward(
                    self.env, self.partner_a, "/shop/test-product-3",
                )
            )
            # Blog's own switch is untouched (defaults True) - a program
            # existing for it would still be rewarded; here it's absent,
            # so this only proves the product switch didn't leak into
            # the blog feature-check itself (no feature_disabled short-circuit).
        finally:
            ICP.set_param(
                "social_sharing_loyalty_points_enhancement.enable_product_share_rewards",
                "True",
            )

    def test_share_reward_skipped_when_no_program_configured(self):
        # blog_share has a registered handler but (in this test's data)
        # no active program - must be safely skipped, not raise.
        share = self.RewardService.grant_share_reward(
            self.env, self.partner_a, "/blog/test-post-1",
        )
        self.assertFalse(share)

    def test_return_reason_is_opt_in_and_backward_compatible(self):
        """Default call shape (no return_reason) keeps returning just
        the record/False, exactly as every existing caller expects."""
        share = self.RewardService.grant_share_reward(
            self.env, self.partner_a, "/blog/test-post-2",
        )
        self.assertFalse(share)

    def test_return_reason_surfaces_validation_failure(self):
        """With return_reason=True (used by controllers/share.py to
        show the validation-error toast), a tuple of (False, reason) is
        returned instead, with a reason code the UI can map to a
        message via RewardValidationService.get_user_message().

        'no_program_configured' is a store *setup* problem, not
        anything about this visitor - get_user_message() must return
        None for it so controllers/share.py never turns it into a
        customer-facing toast (see SILENT_REASONS)."""
        from odoo.addons.social_sharing_loyalty_points_enhancement.services.validation_service import (
            RewardValidationService,
        )

        share, reason = self.RewardService.grant_share_reward(
            self.env, self.partner_a, "/blog/test-post-3",
            return_reason=True,
        )
        self.assertFalse(share)
        self.assertEqual(reason, "no_program_configured")
        self.assertIsNone(RewardValidationService.get_user_message(reason))

    def test_get_user_message_is_silent_for_config_reasons(self):
        """Every reason that reflects a store configuration/setup issue
        (as opposed to something about the visitor) must never produce
        a customer-facing message."""
        from odoo.addons.social_sharing_loyalty_points_enhancement.services.validation_service import (
            RewardValidationService,
            SILENT_REASONS,
        )

        for reason in SILENT_REASONS:
            self.assertIsNone(
                RewardValidationService.get_user_message(reason),
                "%s should be silent but produced a message" % reason,
            )

    def test_get_user_message_still_shown_for_visitor_reasons(self):
        """Reasons that genuinely describe the visitor's own state
        (not logged in, already claimed, not eligible, etc) must still
        surface a message - only config/setup reasons go silent."""
        from odoo.addons.social_sharing_loyalty_points_enhancement.services.validation_service import (
            RewardValidationService,
        )

        for reason in ("no_partner", "partner_inactive", "not_eligible", "already_shared"):
            self.assertTrue(RewardValidationService.get_user_message(reason))

    def test_no_handler_registered_now_shows_a_message(self):
        """Product decision (see SILENT_REASONS comment): unlike other
        store-configuration reasons, 'no_handler_registered' is
        deliberately surfaced to the visitor rather than swallowed
        silently, since it can only be reached via a technical/DB-level
        misconfiguration the UI itself prevents choosing - so showing
        it is treated as an honest signal, not a broken-looking error.
        This must stay True even if SILENT_REASONS is edited later."""
        from odoo.addons.social_sharing_loyalty_points_enhancement.services.validation_service import (
            RewardValidationService,
            SILENT_REASONS,
        )

        self.assertNotIn("no_handler_registered", SILENT_REASONS)
        self.assertEqual(
            RewardValidationService.get_user_message("no_handler_registered"),
            "This type of reward isn't available yet.",
        )

    def test_return_reason_is_none_on_success(self):
        share, reason = self.RewardService.grant_share_reward(
            self.env, self.partner_a, "/shop/test-product-return-reason",
            return_reason=True,
        )
        self.assertTrue(share)
        self.assertIsNone(reason)

    def test_referral_toggles_are_independent_per_type(self):
        """Disabling Event Referral must NOT disable Product/Blog
        Referral - each of the three now has its own switch (see
        services/validation_service.py::is_feature_enabled)."""
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param(
            "social_sharing_loyalty_points_enhancement.enable_event_referral_rewards",
            "False",
        )
        ICP.set_param(
            "social_sharing_loyalty_points_enhancement.enable_product_referral_rewards",
            "True",
        )
        try:
            self.env["loyalty.program"].create({
                "name": "Test Product Referral Independence Program",
                "program_type": "loyalty",
                "applies_on": "both",
                "trigger": "auto",
                "reward_trigger": "product_referral",
                "reward_trigger_points": 20,
            })
            # Event referral disabled, but product referral (separately
            # enabled) still grants its reward.
            referral = self.RewardService.register_referral(
                self.env, "product", self.partner_a, self.partner_b,
            )
            self.assertTrue(referral)
        finally:
            ICP.set_param(
                "social_sharing_loyalty_points_enhancement.enable_event_referral_rewards",
                "True",
            )

    def test_self_referral_is_prevented(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "social_sharing_loyalty_points_enhancement.enable_event_referral_rewards",
            "True",
        )
        self.env["loyalty.program"].create({
            "name": "Test Event Referral Program",
            "program_type": "loyalty",
            "applies_on": "both",
            "trigger": "auto",
            "reward_trigger": "event_referral",
            "reward_trigger_points": 100,
        })
        referral = self.RewardService.register_referral(
            self.env, "event", self.partner_a, self.partner_a,
        )
        self.assertFalse(referral)

    def test_duplicate_referral_is_prevented(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "social_sharing_loyalty_points_enhancement.enable_product_referral_rewards",
            "True",
        )
        self.env["loyalty.program"].create({
            "name": "Test Product Referral Program",
            "program_type": "loyalty",
            "applies_on": "both",
            "trigger": "auto",
            "reward_trigger": "product_referral",
            "reward_trigger_points": 50,
        })
        first = self.RewardService.register_referral(
            self.env, "product", self.partner_a, self.partner_b,
        )
        self.assertTrue(first)

        second = self.RewardService.register_referral(
            self.env, "product", self.partner_a, self.partner_b,
        )
        # Duplicate: returns the SAME existing record, no new points.
        self.assertEqual(first.id, second.id)

    def test_signup_reward_granted_when_configured(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "social_sharing_loyalty_points_enhancement.enable_customer_signup_rewards",
            "True",
        )
        self.env["loyalty.program"].create({
            "name": "Test Customer Signup Program",
            "program_type": "loyalty",
            "applies_on": "both",
            "trigger": "auto",
            "reward_trigger": "customer_signup",
            "reward_trigger_points": 25,
        })
        new_partner = self.env["res.partner"].create({"name": "Brand New Customer"})

        result = self.RewardService.grant_signup_reward(self.env, new_partner)

        self.assertTrue(result)
        self.assertTrue(new_partner.signup_reward_granted)

        card = self.env["loyalty.card"].search([
            ("partner_id", "=", new_partner.id),
            ("program_id.reward_trigger", "=", "customer_signup"),
        ])
        self.assertEqual(card.points, 25)

    def test_signup_reward_is_one_time_only(self):
        """Unlike Share (repeatable) and Referral (repeatable per
        distinct referred person), a signup reward can never be earned
        a second time by the same partner - even across separate calls
        (e.g. the res.users.create() hook firing twice)."""
        self.env["ir.config_parameter"].sudo().set_param(
            "social_sharing_loyalty_points_enhancement.enable_customer_signup_rewards",
            "True",
        )
        self.env["loyalty.program"].create({
            "name": "Test Customer Signup One-Time Program",
            "program_type": "loyalty",
            "applies_on": "both",
            "trigger": "auto",
            "reward_trigger": "customer_signup",
            "reward_trigger_points": 25,
        })
        new_partner = self.env["res.partner"].create({"name": "Repeat Signup Attempt"})

        first = self.RewardService.grant_signup_reward(self.env, new_partner)
        self.assertTrue(first)

        second = self.RewardService.grant_signup_reward(self.env, new_partner)
        self.assertFalse(second)

        card = self.env["loyalty.card"].search([
            ("partner_id", "=", new_partner.id),
            ("program_id.reward_trigger", "=", "customer_signup"),
        ])
        # Still 25, not 50 - the second call never credited anything.
        self.assertEqual(card.points, 25)

    def test_signup_reward_skipped_when_feature_disabled(self):
        self.env["ir.config_parameter"].sudo().set_param(
            "social_sharing_loyalty_points_enhancement.enable_customer_signup_rewards",
            "False",
        )
        try:
            new_partner = self.env["res.partner"].create({"name": "Disabled Feature Customer"})
            result = self.RewardService.grant_signup_reward(self.env, new_partner)
            self.assertFalse(result)
            self.assertFalse(new_partner.signup_reward_granted)
        finally:
            self.env["ir.config_parameter"].sudo().set_param(
                "social_sharing_loyalty_points_enhancement.enable_customer_signup_rewards",
                "True",
            )