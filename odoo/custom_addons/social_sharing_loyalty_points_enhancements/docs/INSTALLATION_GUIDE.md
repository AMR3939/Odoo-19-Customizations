# Installation Guide

## Fresh install (Odoo 19 Community)

1. Copy `social_sharing_loyalty_points_enhancement/` into an addons
   path your Odoo instance actually loads (`--addons-path`).

   > If you have this module in **more than one** addons path (a common
   > cause of "my changes aren't showing up" bugs), remove or rename the
   > stale copy first — Odoo loads whichever one appears first on its
   > addons path, silently shadowing the other.

2. Update Apps List (Settings → General Settings → Activate developer
   mode → Apps → Update Apps List), then install **Social Sharing
   Loyalty Points Enhancement**.

3. Go to **Sales → Configuration → Social Media & Loyalty** and open **Social
   Sharing, Referral & Loyalty Points** section. Both master switches
   (Enable Social Sharing Rewards / Enable Referral Rewards) are ON by
   default.

4. Go to **Discount & Loyalty → Programs**, create (or reuse) a Loyalty
   Program per Reward Trigger you want active, and set its **Reward
   Trigger** + **Points per Action**. Remember: only one *active*
   program may be assigned to a given trigger at a time.

5. (Optional) A demo, inactive Event Referral program is shipped in
   `data/loyalty_program_data.xml` — activate it if you just want to
   see the flow working end-to-end before setting up your own.

## Upgrading from a pre-2.0 install

`migrations/19.0.2.0.0/` runs automatically the next time the module is
upgraded (Apps → search the module → Upgrade, or
`-u social_sharing_loyalty_points_enhancement` from the command line):

* `pre-migrate.py` snapshots the old
  `is_social_share_program` / `social_share_points` /
  `is_social_share_reward_program` / `social_share_reward_points`
  columns before Odoo's ORM drops them.
* `post-migrate.py` maps that snapshot onto the new `reward_trigger` /
  `reward_trigger_points` fields:
  * `is_social_share_program = True` → `reward_trigger = 'event_referral'`
  * `is_social_share_reward_program = True` → `reward_trigger = 'product_share'`

**After upgrading, review Discount & Loyalty → Programs once:**
if a program previously had "Use for Social Share Rewards" checked (it
used to cover both Product *and* Blog page shares from one program),
it is migrated to `product_share` only. Duplicate that program and set
the copy's Reward Trigger to `blog_share` if you also want Blog shares
rewarded.

Your old, separate "Referral Rewards" top-level Settings app is gone —
all the same settings (plus the new architecture-level toggles) now
live under **Sales → Configuration → Social Media & Loyalty**.

## Verifying the install

* Run the test suite: `--test-tags social_sharing_loyalty_points_enhancement`
  (or `-i social_sharing_loyalty_points_enhancement --test-enable` on a
  scratch database) — see `tests/`.
* Check **Sales → Configuration → Social Media & Loyalty → Social Sharing, Referral &
  Loyalty Points → Supported Reward Triggers** — every built-in trigger
  should show a ✅ Handler, confirming `handlers/__init__.py` imported
  correctly.
* As a logged-in portal user, click Share on a Product/Blog/Event page
  with a matching active program configured, and confirm a
  `social.share.record` was created (Settings → Technical → Database
  Structure, or add a menu action over that model for your own admin
  use).

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Reward Trigger dropdown missing on Loyalty Program form | Module not upgraded, or `views/loyalty_program_views.xml` failed to load — check the server log for the exact xpath error. |
| Points never granted, no errors | Check the master switch in Settings, then check "Supported Reward Triggers" for a ⚠️ (no handler) or "Not configured" (no active program) next to the trigger you expect. |
| Menu doesn't appear under Sales > Configuration | Confirm the logged-in user is in the Sales / Administration > Sales Manager group — the menu and its action are both restricted to `sales_team.group_sale_manager`. |
| Changes to the module don't show up in the running instance | You likely have a duplicate copy of this module on another addons path that is shadowing the one you're editing — see step 1 above. |
