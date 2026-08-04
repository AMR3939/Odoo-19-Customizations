# -*- coding: utf-8 -*-
"""
Pre-migration step for the 19.0.2.0.0 architecture refactor.

Snapshots the OLD boolean/points columns on loyalty_program (from before
the Reward Trigger redesign) into a temporary table, before the ORM
drops those columns while loading the new model definition. The
post-migrate.py script in this same folder reads that snapshot back and
maps it onto the new reward_trigger / reward_trigger_points fields.

Safe to run against a database that never had the old columns at all
(e.g. a fresh install being upgraded through this version): every
lookup is guarded by an information_schema check first.
"""

import logging

_logger = logging.getLogger(__name__)

OLD_COLUMNS = (
    "is_social_share_program",
    "social_share_points",
    "is_social_share_reward_program",
    "social_share_reward_points",
)


def migrate(cr, version):
    cr.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'loyalty_program'
          AND column_name = ANY(%s)
        """,
        (list(OLD_COLUMNS),),
    )
    existing_cols = {row[0] for row in cr.fetchall()}

    if not existing_cols:
        _logger.info(
            "social_sharing_loyalty_points_enhancement: no legacy "
            "reward-flag columns found on loyalty_program - nothing to "
            "snapshot, skipping."
        )
        return

    def col_or_default(name, default_sql):
        return name if name in existing_cols else default_sql

    cr.execute(
        """
        DROP TABLE IF EXISTS _social_sharing_legacy_program_flags;
        CREATE TABLE _social_sharing_legacy_program_flags AS
        SELECT id,
               {is_ref}   AS is_social_share_program,
               {ref_pts}  AS social_share_points,
               {is_share} AS is_social_share_reward_program,
               {share_pts} AS social_share_reward_points
        FROM loyalty_program
        """.format(
            is_ref=col_or_default("is_social_share_program", "FALSE"),
            ref_pts=col_or_default("social_share_points", "0"),
            is_share=col_or_default("is_social_share_reward_program", "FALSE"),
            share_pts=col_or_default("social_share_reward_points", "0"),
        )
    )

    _logger.info(
        "social_sharing_loyalty_points_enhancement: snapshotted legacy "
        "reward flags for migration to reward_trigger."
    )
