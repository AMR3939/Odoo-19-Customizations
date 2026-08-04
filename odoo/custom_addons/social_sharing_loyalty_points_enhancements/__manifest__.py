# -*- coding: utf-8 -*-

{
    "name": "Social Sharing Loyalty Points Enhancements",
    "version": "19.0.2.3.0",
    "summary": "Enterprise-grade, Registry/Handler-based loyalty rewards for social sharing and referrals across Events, Shop products, and Blog posts.",
    "description": """
Social Sharing Loyalty Points Enhancement
=========================================

This module adds an extensible loyalty rewards system for social sharing
and referrals across Website Events, eCommerce Products, and Blog posts,
built on top of Odoo's native Loyalty app - and on top of a Registry /
Handler (Strategy Pattern) architecture that lets new reward types be
added without touching any existing business logic.

See Architecture.md (in the module folder) for the full design write-up,
and Developer Guide.md for a step-by-step "how to add a new reward type"
walkthrough.

Architecture highlights
------------------------
* Every reward trigger (Product Share, Blog Share, Event Share, Event
  Referral, Product Referral, Blog Referral, ...) has its own Handler
  class under handlers/, registered once in handlers/registry.py.
* A Loyalty Program picks its Reward Trigger from a single, clean
  Selection field - no more one boolean+integer pair per reward type.
* An unsupported/unconfigured Reward Trigger is ALWAYS safely ignored -
  logged and skipped, never crashed, never guessed at, never silently
  rewarded.
* A full validation layer runs before every reward: Program Active,
  Reward Trigger Exists, Registered Handler Exists, Reward Configured,
  Customer Eligible, Duplicate Prevention, Self Referral Prevention.
* The module never touches Odoo's native Loyalty Engine beyond earning
  points onto a loyalty.card - redemption, coupons, discounts, and
  activation all remain 100% standard Odoo.
* All configuration is centralized in one place: Sales -> Configuration
  -> Social Media & Loyalty -> "Social Sharing, Referral & Loyalty
  Points" (a dedicated screen, not res.config.settings).

Feature-level behaviour (unchanged from the previous release)
---------------------------------------------------------------
* Logged-in portal users can share Event, Product, and Blog pages using the
  website's existing native Share widget (Facebook, X, LinkedIn, Email, Copy
  Link) - no separate share button needed.
* Share Reward: an instant, smaller reward is granted the moment someone
  clicks Share, regardless of whether it ever converts.
* Referral Reward: a larger reward is granted only when a second visitor
  actually converts through that shared link:
    - registers for the shared Event (free or paid),
    - purchases the shared Product (order confirmed), or
    - creates an account after visiting the shared Blog post.
* Automatic cancellation: if a share DOES convert into a referral, the
  earlier Share Reward for that exact record is automatically reversed and
  logged, so the sharer only ever keeps the larger Referral Reward - never
  both.
* Exact-match reversal: cancellation is matched by the precise shared
  record's ID (not by guessing from a page title), so it stays reliable even
  across content with very similar names.
* Referral links carry the referrer's partner ID, content type, and source
  record ID as URL parameters, tracked afterwards via a browser cookie so
  the conversion can be attributed even several page-visits later.
* Every reward and reversal is logged as a normal Odoo loyalty.history entry
  and viewable by the user on their own portal loyalty page.
* Prevents self-referrals.
* Prevents duplicate rewards on repeated confirmation/visits.
* Supports multiple successful referrals per user.
""",
    "author": "ABAT MATHEW RAJESH",
    "website": "",
    "category": "Website/Event",
    "license": "LGPL-3",

    "depends": [
        "website",
        "website_blog",
        "website_event",
        "website_event_sale",
        "website_sale",
        "sale",
        "sales_team",
        "portal",
        "loyalty",
    ],

    "data": [
        "security/ir.model.access.csv",

        "data/social_loyalty_config_data.xml",
        "data/loyalty_program_data.xml",

        "views/website_share_templates.xml",
        "views/website_event_templates.xml",
        "views/website_product_templates.xml",
        "views/website_blog_templates.xml",
        "views/website_layout_referral.xml",

        "views/loyalty_program_views.xml",
        "views/referral_record_views.xml",
        "views/share_record_views.xml",
        "views/social_loyalty_config_views.xml",

        "views/portal_templates.xml",
    ],

    "assets": {
        "web.assets_frontend": [
            "social_sharing_loyalty_points_enhancements/static/src/js/referral_share.js",
        ],
    },

    "installable": True,
    "application": False,
    "auto_install": False,
}