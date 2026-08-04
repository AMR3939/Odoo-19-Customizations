# Developer Guide — Adding a New Reward Trigger

This module was built so that a brand-new reward type — Instagram
Share, Customer Signup, a VIP Campaign, a Bundle Share, an Age-Based
Campaign, Website Activity, etc. — can be added by **creating and
registering one handler file**. Nothing else needs to change.

## Step-by-step

### 1. Pick a `trigger_code`

Short, lowercase, snake_case, unique. Example: `instagram_share`.

### 2. Add it to the Reward Trigger selection

In `models/loyalty_program.py`:

```python
REWARD_TRIGGER_SELECTION = [
    ("none", "Standard Odoo (No Automatic Reward)"),
    ("product_share", "Product Share"),
    # ...
    ("instagram_share", "Instagram Share"),   # <-- add this line
]
```

That's the only change needed in `models/`.

### 3. Create the handler

For a "click something -> get instant points" trigger, subclass
`BaseShareHandler` (in `handlers/share_base.py`) — it already implements
`is_eligible()`/`execute()` generically:

```python
# handlers/instagram_share.py
# -*- coding: utf-8 -*-
from .registry import register_handler
from .share_base import BaseShareHandler


@register_handler
class InstagramShareHandler(BaseShareHandler):
    trigger_code = "instagram_share"
    content_type = "instagram"   # only meaningful if you also extend
                                  # social.share.record's content_type
                                  # selection to include "instagram"
```

For a "referral converted -> get points" trigger, subclass
`BaseReferralHandler` (in `handlers/referral_base.py`) the same way —
see `handlers/product_referral.py` for the smallest possible example.

For something that fits neither shape (e.g. **Customer Signup**, which
per the spec is "Not Shareable" and has no referrer at all), subclass
`BaseRewardHandler` directly and implement `is_eligible()`/`execute()`
yourself:

```python
# handlers/customer_signup.py
# -*- coding: utf-8 -*-
from odoo import _
from .base_handler import BaseRewardHandler
from .registry import register_handler


@register_handler
class CustomerSignupHandler(BaseRewardHandler):
    trigger_code = "customer_signup"

    def is_eligible(self, program, partner=None, **context):
        if not partner or not partner.id:
            return False, "no_partner"
        # Duplicate prevention: only reward the FIRST signup ever.
        already_rewarded = self.env["social.share.record"].sudo().search_count([
            ("sharer_partner_id", "=", partner.id),
            ("content_type", "=", "customer_signup"),
        ])
        if already_rewarded:
            return False, "duplicate_signup_reward"
        return True, None

    def execute(self, program, partner=None, points_override=None, **context):
        points = points_override if points_override is not None else program.reward_trigger_points
        card, history = self.env["social.loyalty.reward.mixin"]._credit_loyalty_points(
            partner, program, points, _("Customer Signup Reward"),
        )
        return history
```

### 4. Register the import

In `handlers/__init__.py`:

```python
from . import instagram_share
```

That's it. The `@register_handler` decorator runs at import time and
adds the class to `HANDLER_REGISTRY` — `handlers.registry.get_handler()`
will find it immediately, the Settings screen's "Supported Reward
Triggers" table will show it as having a Handler available, and any
admin can now pick "Instagram Share" from any Loyalty Program's Reward
Trigger field.

### 5. Call it from wherever the action actually happens

Add ONE call to `RewardService` at the point in your code where the
action occurs — e.g. in a controller handling an Instagram webhook:

```python
from odoo.addons.social_sharing_loyalty_points_enhancement.services.reward_service import RewardService

RewardService.grant_share_reward(request.env, partner, url, content_name=name)
```

(For a brand-new *family* of reward that doesn't fit `grant_share_reward`
/ `register_referral`'s signatures at all, add a third public method to
`RewardService` that calls `RewardValidationService.resolve()` the same
way the existing two do — the pattern is copy-paste simple.)

## Design rules to keep the architecture intact

* **Never** create a `social.share.record` / `social.referral.record`
  (or any future reward-ledger model) outside of `handlers/`.
* **Never** read a `social_sharing_loyalty_points_enhancement.*`
  `ir.config_parameter` key outside of `services/`.
* **Never** add an if/elif branch anywhere that switches on
  `reward_trigger` — if you find yourself doing that, you need a new
  handler instead.
* A handler's `execute()` must be idempotent — check for an existing
  record before creating one (see `BaseReferralHandler._find_existing()`
  for the pattern).
