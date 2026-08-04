# Adding a new Referral trigger (low-code, no redeploy)

The Page Type Registry (`social.reward.page.type`, Configuration >
Social Sharing, Referral & Loyalty Points > Page Types) makes the
**Share** half of a brand-new page type fully UI-configurable - no code,
no module upgrade.

The **Referral** half can't be made equally generic, for an honest
structural reason: a referral is only ever "confirmed" when a *specific
business event* happens on a *specific Odoo model* -

| Built-in trigger   | Conversion event                          | Model              |
|---------------------|--------------------------------------------|---------------------|
| Event Referral       | registration confirmed (paid or free)     | `event.registration` |
| Product Referral     | order confirmed                            | `sale.order`         |
| Blog Referral        | account created after visiting a blog post | `res.users`          |

There's no generic Odoo field meaning "this record's creation is a
conversion" - so recognizing a new one always needs *some* logic tied to
*that* model. The good news: Odoo's built-in **Automation Rules** let an
admin add that logic entirely from the UI - no new Python file, no
module upgrade, no server restart.

## Step-by-step: reward a referral when an `hr.applicant` is created

(Swap `hr.applicant` and the field names for whatever model represents
"someone converted" for your new page type.)

1. **Settings > Technical > Automation Rules** (enable developer mode
   first if you don't see "Technical" in Settings).
2. **New** rule:
   - **Model**: Job Application (`hr.applicant`)
   - **Trigger**: "On Creation"
3. In the **Action To Do** section, add a **Python Code** action with
   roughly:

   ```python
   # Reads the referral cookie the same way models/res_users.py already
   # does for blog signups - adjust the cookie/field names to match
   # whatever your recruitment page actually sets.
   referrer_id = request.httprequest.cookies.get("social_referral_partner_id")
   if referrer_id:
       from odoo.addons.social_sharing_loyalty_points_enhancement.services.reward_service import RewardService
       referrer = env["res.partner"].sudo().browse(int(referrer_id))
       RewardService.register_referral(
           env, "recruitment",  # must match a REFERRAL_TRIGGER_MAP key - see step 4 below
           referrer_partner=referrer,
           referred_partner=record.partner_id,  # or whatever partner the applicant maps to
       )
   ```

4. Back in code (one-time setup per NEW referral type, same as any
   other trigger): add the trigger to
   `REWARD_TRIGGER_SELECTION` in `models/loyalty_program.py`, register a
   handler under `handlers/`, and add its map entry in
   `services/reward_service.py::REFERRAL_TRIGGER_MAP` - exactly the
   Step 1/2 pattern already used for Event/Product/Blog Referral. This
   part still needs a module upgrade, but it's a one-time, ~20-line
   addition per new referral type, not per page.

5. Add the matching master switch to `social_loyalty_config.py` +
   its view (optional but recommended, keeps every switch in one
   screen) - same pattern as the 6 existing ones.

## Why this is the right trade-off

- **Share** rewards are pure "did someone click this button" - no
  business-specific state to interpret, so it really can be 100%
  data-driven (the Page Type Registry).
- **Referral** rewards are "did a specific business process complete
  successfully" - order confirmed, registration paid, application
  submitted - and that always needs a little bit of model-specific
  logic somewhere. Automation Rules keep that logic in the UI/admin
  layer instead of a new module file, which is the closest thing to
  "no-code" this half can honestly offer.
