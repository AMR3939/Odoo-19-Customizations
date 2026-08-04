# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSocialLoyaltyConfig(TransactionCase):
    """Covers the singleton behaviour of the dedicated configuration
    screen (Sales -> Configuration -> Social Media & Loyalty), and that
    its fields transparently read/write the same ir.config_parameter
    keys the reward engine already reads directly.
    """

    def test_get_singleton_returns_same_record_every_time(self):
        Config = self.env["social.loyalty.config"]
        first = Config.get_singleton()
        second = Config.get_singleton()
        self.assertEqual(first.id, second.id)

    def test_create_never_produces_a_second_row(self):
        Config = self.env["social.loyalty.config"]
        Config.get_singleton()
        before_count = Config.search_count([])
        Config.create({"name": "Attempted Duplicate"})
        after_count = Config.search_count([])
        self.assertEqual(before_count, after_count)

    def test_unlink_is_blocked(self):
        record = self.env["social.loyalty.config"].get_singleton()
        with self.assertRaises(UserError):
            record.unlink()

    def test_fields_round_trip_through_config_parameter(self):
        record = self.env["social.loyalty.config"].get_singleton()
        record.write({
            "enable_product_share_rewards": False,
            "referral_cookie_days": 45,
        })

        ICP = self.env["ir.config_parameter"].sudo()
        self.assertEqual(
            ICP.get_param("social_sharing_loyalty_points_enhancement.enable_product_share_rewards"),
            "False",
        )
        self.assertEqual(
            ICP.get_param("social_sharing_loyalty_points_enhancement.referral_cookie_days"),
            "45",
        )

        # And reading it back through the model reflects the same value.
        record.invalidate_recordset()
        self.assertFalse(record.enable_product_share_rewards)
        self.assertEqual(record.referral_cookie_days, 45)
