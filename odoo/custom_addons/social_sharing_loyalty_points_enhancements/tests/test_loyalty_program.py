# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestLoyaltyProgramRewardTriggerPoints(TransactionCase):
    """Covers the 'Points per Action' validation on loyalty.program:
    a program with an active Reward Trigger must always require at
    least 1 point, since 0 or negative points can never actually grant
    a reward in real-world use (see handlers/base_handler.py's
    'reward_not_configured' skip, which this now prevents at save time
    instead of only silently skipping at grant time).
    """

    def _make_program(self, points, trigger="product_share"):
        return self.env["loyalty.program"].create({
            "name": "Test Reward Trigger Program",
            "program_type": "loyalty",
            "reward_trigger": trigger,
            "reward_trigger_points": points,
            "trigger": "auto",
            "applies_on": "both",
        })

    def test_zero_points_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._make_program(0)

    def test_negative_points_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._make_program(-5)

    def test_positive_points_is_allowed(self):
        program = self._make_program(1)
        self.assertEqual(program.reward_trigger_points, 1)

    def test_zero_points_allowed_when_trigger_is_none(self):
        # The field is hidden/unused for a standard ('none') program,
        # so it is not blocked in that case.
        program = self._make_program(0, trigger="none")
        self.assertEqual(program.reward_trigger_points, 0)

    def test_existing_program_cannot_be_updated_to_zero(self):
        program = self._make_program(10)
        with self.assertRaises(ValidationError):
            program.write({"reward_trigger_points": 0})


@tagged("post_install", "-at_install")
class TestLoyaltyProgramAppliesOnGuard(TransactionCase):
    """Social-sharing/referral points are never linked to a sale order
    (see handlers/share_base.py, handlers/referral_base.py), so
    `applies_on = 'current'` has nothing to anchor the points to and
    they would never become redeemable. This module must never let that
    combination be saved - either by auto-correcting it (onchange, UI
    path) or by blocking it outright (constrains, every other path:
    imports, XML-RPC, scripts, migrations).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            "social_sharing_loyalty_points_enhancement.enable_blog_share_rewards",
            "True",
        )

    def _base_vals(self, **overrides):
        vals = {
            "name": "Blog Share Reward",
            "program_type": "loyalty",
            "trigger": "auto",
            "applies_on": "both",
            "reward_trigger": "blog_share",
            "reward_trigger_points": 10,
        }
        vals.update(overrides)
        return vals

    # -- constrains: server-side safety net (bypasses onchange) --------

    def test_create_blocks_current_order_with_social_trigger(self):
        with self.assertRaises(ValidationError):
            self.env["loyalty.program"].create(
                self._base_vals(applies_on="current")
            )

    def test_write_blocks_switching_to_current_order(self):
        program = self.env["loyalty.program"].create(
            self._base_vals(applies_on="future")
        )
        with self.assertRaises(ValidationError):
            program.write({"applies_on": "current"})

    def test_write_blocks_switching_to_social_trigger_while_current(self):
        # A plain, non-social program is allowed to use 'current' ...
        program = self.env["loyalty.program"].create(
            self._base_vals(reward_trigger="none", applies_on="current")
        )
        # ... but assigning it a social trigger afterwards must be
        # blocked too, not just the reverse order of edits.
        with self.assertRaises(ValidationError):
            program.write({"reward_trigger": "blog_share"})

    def test_future_and_both_are_allowed(self):
        for applies_on in ("future", "both"):
            program = self.env["loyalty.program"].create(
                self._base_vals(applies_on=applies_on, name="Test %s" % applies_on)
            )
            self.assertEqual(program.applies_on, applies_on)

    def test_current_order_still_allowed_for_non_social_program(self):
        program = self.env["loyalty.program"].create(
            self._base_vals(reward_trigger="none", applies_on="current")
        )
        self.assertEqual(program.applies_on, "current")

    # -- onchange: UI-path auto-correction ------------------------------

    def test_onchange_autocorrects_current_order_when_trigger_picked(self):
        program = self.env["loyalty.program"].new(
            self._base_vals(reward_trigger="none", applies_on="current")
        )
        program.reward_trigger = "blog_share"
        result = program._onchange_social_trigger_applies_on()

        self.assertEqual(program.applies_on, "future")
        self.assertIn("warning", result)

    def test_onchange_autocorrects_when_current_order_picked_second(self):
        program = self.env["loyalty.program"].new(
            self._base_vals(applies_on="both")
        )
        program.applies_on = "current"
        result = program._onchange_social_trigger_applies_on()

        self.assertEqual(program.applies_on, "future")
        self.assertIn("warning", result)

    def test_onchange_no_warning_when_combination_is_fine(self):
        program = self.env["loyalty.program"].new(
            self._base_vals(applies_on="future")
        )
        result = program._onchange_social_trigger_applies_on()
        self.assertIsNone(result)
