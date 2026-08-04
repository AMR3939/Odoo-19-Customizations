# Social Sharing Loyalty Points Enhancement

Enterprise-grade, extensible loyalty rewards for social sharing and
referrals across Website Events, eCommerce Products, and Blog posts —
built on top of Odoo 19's native Loyalty app, and on top of a
**Registry / Handler (Strategy Pattern)** architecture.

> Full design write-up: [`Architecture.md`](./Architecture.md)
> Step-by-step "add a new reward type" guide: [`docs/DEVELOPER_GUIDE.md`](./docs/DEVELOPER_GUIDE.md)
> Install/upgrade instructions: [`docs/INSTALLATION_GUIDE.md`](./docs/INSTALLATION_GUIDE.md)

## What it does

* Logged-in portal users earn an **instant Share Reward** the moment
  they click Share on an Event, Product, or Blog page.
* A larger **Referral Reward** is granted only when a second visitor
  actually converts through that shared link (registers for the Event,
  buys the Product, or signs up after reading the Blog post).
* If a share later converts into a referral, the earlier Share Reward
  for that exact piece of content is automatically reversed, so a
  sharer only ever keeps the larger Referral Reward.
* Self-referrals and duplicate rewards are always prevented.
* Redemption, coupons, discounts, and activation remain 100% native
  Odoo Loyalty — this module is only ever responsible for **earning**
  points.

## What changed in this release (19.0.2.0.0)

The previous release hardcoded four boolean flags on `loyalty.program`
(`is_social_share_program`, `is_social_share_reward_program`, plus a
points field each) and large if/elif blocks scattered across
`event_registration.py`, `sale_order.py`, and `res_users.py` to decide
how/whether to grant a reward.

This release replaces that with:

1. A single **Reward Trigger** selection field on `loyalty.program`.
2. A **Handler** class per trigger, each in its own file under
   `handlers/`, registered once in `handlers/registry.py`.
3. A **Validation Layer** (`services/validation_service.py`) that runs
   Program Active / Reward Trigger Exists / Registered Handler Exists /
   Reward Configured / Customer Eligible / Duplicate Prevention /
   Self-Referral Prevention checks before every reward, in that order.
4. A **Reward Service** (`services/reward_service.py`) that is the only
   public entry point for granting a reward — nothing else creates a
   `social.share.record` or `social.referral.record` directly, or reads
   the module's `ir.config_parameter` keys directly.
5. All configuration centralized under **Sales → Configuration →
   Settings → "Social Sharing, Referral & Loyalty Points"**, replacing
   the previous separate top-level "Referral Rewards" Settings app.

Existing installs are migrated automatically (see
`migrations/19.0.2.0.0/`) — see
[`docs/INSTALLATION_GUIDE.md`](./docs/INSTALLATION_GUIDE.md) for what to
double-check after upgrading.

## Supported reward triggers out of the box

| Reward Trigger      | Fires when...                                              | Handler                            |
|----------------------|-------------------------------------------------------------|-------------------------------------|
| `product_share`      | A logged-in user clicks Share on a Product page              | `handlers/product_share.py`         |
| `blog_share`         | A logged-in user clicks Share on a Blog post             | `handlers/blog_share.py`            |
| `event_share`        | A logged-in user clicks Share on an Event page                | `handlers/event_share.py`           |
| `event_referral`     | A referred visitor registers for the shared Event             | `handlers/event_referral.py`        |
| `product_referral`   | A referred visitor's first order for the shared Product is confirmed | `handlers/product_referral.py` |
| `blog_referral`      | A referred visitor creates an account after a shared Blog link | `handlers/blog_referral.py`         |
| `customer_signup`    | A new customer creates a website account — a flat, one-time, non-shareable welcome bonus (not tied to any share or referral) | `handlers/customer_signup.py` |

Adding a new one (Instagram Share, VIP Campaign, ...) never requires
touching any of the above — see the Developer Guide.

## Folder structure

```
social_sharing_loyalty_points_enhancement/
├── controllers/       # HTTP endpoints (thin - delegate to services/)
├── models/            # Odoo ORM models
├── handlers/          # One file per Reward Trigger (Strategy Pattern)
├── services/          # RewardService + RewardValidationService
├── security/
├── data/
├── views/
├── static/src/js/
├── migrations/
├── tests/
├── docs/
├── README.md
└── Architecture.md
```

## Installation

See [`docs/INSTALLATION_GUIDE.md`](./docs/INSTALLATION_GUIDE.md).

## License

LGPL-3
