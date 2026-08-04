# -*- coding: utf-8 -*-
"""
Post-migration step for splitting the single "Enable Referral Rewards"
switch into three independent, per-type switches (Event / Product /
Blog Referral), mirroring the split already done for Social Sharing in
19.0.2.0.0.

Any existing install has exactly one
ir.config_parameter row:

    social_sharing_loyalty_points_enhancement.referral_rewards_enabled

Its value is copied forward to all three new keys so upgrading never
silently disables (or enables) a referral type an admin didn't
explicitly change - after upgrade, all three start out exactly where
the single switch left off, and can then be adjusted independently
from Sales -> Configuration -> Social Media & Loyalty.
"""

import logging

_logger = logging.getLogger(__name__)

OLD_KEY = "social_sharing_loyalty_points_enhancement.referral_rewards_enabled"
NEW_KEYS = (
    "social_sharing_loyalty_points_enhancement.enable_event_referral_rewards",
    "social_sharing_loyalty_points_enhancement.enable_product_referral_rewards",
    "social_sharing_loyalty_points_enhancement.enable_blog_referral_rewards",
)


def migrate(cr, version):
    cr.execute(
        "SELECT value FROM ir_config_parameter WHERE key = %s",
        (OLD_KEY,),
    )
    row = cr.fetchone()

    if not row:
        _logger.info(
            "social_sharing_loyalty_points_enhancement: no legacy "
            "'referral_rewards_enabled' parameter found - nothing to "
            "migrate, new installs already ship the three per-type "
            "keys via data/social_loyalty_config_data.xml."
        )
        return

    old_value = row[0]

    for key in NEW_KEYS:
        cr.execute(
            """
            INSERT INTO ir_config_parameter (key, value)
            VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """,
            (key, old_value),
        )

    cr.execute("DELETE FROM ir_config_parameter WHERE key = %s", (OLD_KEY,))

    _logger.info(
        "social_sharing_loyalty_points_enhancement: migrated legacy "
        "'referral_rewards_enabled' (%s) to the three new per-type "
        "switches (Event/Product/Blog Referral). Review Sales -> "
        "Configuration -> Social Media & Loyalty if any of the three "
        "should now differ from one another.",
        old_value,
    )
