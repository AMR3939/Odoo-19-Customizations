# -*- coding: utf-8 -*-
"""
Post-migration step for the 19.0.2.0.0 architecture refactor.

Reads the snapshot created by pre-migrate.py and sets the new
reward_trigger / reward_trigger_points fields accordingly, so existing
installs keep working exactly as before after the upgrade, with no
manual reconfiguration required for the common cases:

    is_social_share_program = True        -> reward_trigger = 'event_referral'
    is_social_share_reward_program = True -> reward_trigger = 'product_share'

NOTE on the second mapping: the OLD "Social Share Rewards" flag granted
instant points for BOTH Product and Blog page shares off a single
program (Event pages were never covered by it - see the removed
docstring in the old loyalty_program.py). The new architecture rewards
each content type through its own trigger (product_share / blog_share
/ event_share), so a program that had this flag set is migrated to
'product_share' by default; if that program was actually meant to also
(or only) cover Blog shares, duplicate the program after upgrading and
set the copy's Reward Trigger to 'blog_share'.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("SELECT to_regclass('_social_sharing_legacy_program_flags')")
    if not cr.fetchone()[0]:
        _logger.info(
            "social_sharing_loyalty_points_enhancement: no legacy flag "
            "snapshot found - nothing to migrate."
        )
        return

    cr.execute(
        """
        SELECT id, is_social_share_program, social_share_points,
               is_social_share_reward_program, social_share_reward_points
        FROM _social_sharing_legacy_program_flags
        """
    )
    rows = cr.fetchall()

    migrated = 0
    for program_id, is_referral, referral_points, is_share, share_points in rows:
        if is_referral:
            cr.execute(
                """
                UPDATE loyalty_program
                SET reward_trigger = %s, reward_trigger_points = %s
                WHERE id = %s
                """,
                ("event_referral", referral_points or 10, program_id),
            )
            migrated += 1
        elif is_share:
            cr.execute(
                """
                UPDATE loyalty_program
                SET reward_trigger = %s, reward_trigger_points = %s
                WHERE id = %s
                """,
                ("product_share", share_points or 10, program_id),
            )
            migrated += 1

    cr.execute("DROP TABLE IF EXISTS _social_sharing_legacy_program_flags")

    _logger.info(
        "social_sharing_loyalty_points_enhancement: migrated %s "
        "loyalty.program record(s) from legacy boolean flags to "
        "reward_trigger. Review Discount & Loyalty -> Programs after "
        "upgrading, especially any program that previously had "
        "'Use for Social Share Rewards' checked (now defaulted to "
        "'Product Share' - duplicate it with 'Blog Share' if it should "
        "also cover blog posts).",
        migrated,
    )
