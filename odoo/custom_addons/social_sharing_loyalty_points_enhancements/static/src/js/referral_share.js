/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";

/**
 * Handles the website's native Share buttons (".s_share" - Facebook / X /
 * LinkedIn / Email / Copy Link) for TWO independent things:
 *
 * 1. Referral link tagging: attach "?ref=<partner_id>&ref_type=<event|
 *    product|blog>&ref_src=<record_id>" to the URL being shared.
 *
 * 2. Share Reward: an instant, separate reward just for clicking Share,
 *    granted via /social_share/reward - independent of whether the shared
 *    link ever converts into a referral.
 *
 * IMPORTANT - how the content TYPE is determined, and why: it is classified
 * straight from the current page's URL path (classifyReferralType() below),
 * NOT from a page-level marker set by a specific QWeb template. Content
 * pages have MULTIPLE templates a visitor can be on when they click Share -
 * e.g. an event's main description page (website_event.event_description_
 * full) vs its ticket-selection page (/event/<slug>/register, a completely
 * different template) - and putting a marker on only one of them meant
 * sharing from any other page under that same content silently mis-tagged
 * the referral (e.g. got "other" instead of "event"). Classifying by URL
 * path instead ("/event..." -> event, "/shop..." -> product, "/blog..." ->
 * blog) is correct on every page under that content, no matter which
 * specific template rendered it - and it mirrors exactly the same logic
 * social.share.record.classify_content_type() already uses server-side for
 * the instant Share Reward, so the two are always in sync.
 *
 * The exact source record id (event/product/blog.post id, used for precise
 * cancellation matching - see social.referral.record.
 * _reverse_matching_share_reward()) is a separate, best-effort concern: it's
 * only available when window.socialReferralContext was set by one of the
 * three content-page templates (website_event_templates.xml /
 * website_product_templates.xml / website_blog_templates.xml), and only
 * trusted when its type matches what the URL says. If it's missing (e.g.
 * shared from the register/cart page rather than the main content page),
 * cancellation falls back to the existing title-based best-effort match.
 *
 * The partner id is read via [data-referrer-id] set on #wrapwrap, present
 * on every page for any logged-in user - see website_layout_referral.xml.
 */
/**
 * Minimal, dependency-free validation-error toast for the Share Reward
 * call below. Deliberately plain DOM/CSS (Bootstrap classes only,
 * always present on website pages) rather than the backend web
 * client's OWL notification service - that service belongs to the
 * WebClient env and isn't reliably available on public website pages,
 * where this script also runs. Only shown for an actual validation
 * failure (feature disabled, no program configured, not eligible,
 * etc) - a successful reward, or the visitor simply not being logged
 * in and not caring, never shows anything.
 */
function showShareRewardToast(message) {
    if (!message) {
        return;
    }

    var container = document.getElementById("o_social_share_toast_container");
    if (!container) {
        container = document.createElement("div");
        container.id = "o_social_share_toast_container";
        container.style.position = "fixed";
        container.style.top = "16px";
        container.style.right = "16px";
        container.style.zIndex = "2000";
        container.style.maxWidth = "320px";
        document.body.appendChild(container);
    }

    var toast = document.createElement("div");
    toast.className = "alert alert-warning shadow-sm mb-2";
    toast.setAttribute("role", "alert");
    toast.style.opacity = "0";
    toast.style.transition = "opacity 0.2s ease-in-out";
    toast.textContent = message;
    container.appendChild(toast);

    // Fade in, then auto-dismiss - no user action required, and it
    // never blocks or steals focus from the native Share popup.
    window.requestAnimationFrame(function () {
        toast.style.opacity = "1";
    });

    window.setTimeout(function () {
        toast.style.opacity = "0";
        window.setTimeout(function () {
            toast.remove();
        }, 250);
    }, 5000);
}

function classifyReferralType(url) {
    let path = "";
    try {
        path = new URL(url, window.location.origin).pathname.toLowerCase();
    } catch (e) {
        path = String(url || "").toLowerCase();
    }

    if (path.startsWith("/event")) {
        return "event";
    }
    if (path.startsWith("/shop")) {
        return "product";
    }
    if (path.startsWith("/blog")) {
        return "blog";
    }
    return "other";
}

document.addEventListener(
    "click",
    (ev) => {
        const shareButton = ev.target.closest(".s_share a, .s_share button");

        if (!shareButton) {
            return;
        }

        const referralType = classifyReferralType(window.location.href);

        const context = window.socialReferralContext || {};
        // Only trust the page-level source id if it was set for the SAME
        // type we just derived from the URL - guards against a stale
        // global from a previous SPA-style navigation ever being applied
        // to the wrong content type.
        const referralSourceId =
            context.type === referralType && context.sourceId ? context.sourceId : "";

        // --- 1. Share Reward: fire-and-forget, never blocks the popup ---
        rpc("/social_share/reward", {
            url: window.location.href,
            content_name: document.title,
            source_id: referralSourceId || undefined,
        })
            .then((result) => {
                // A validation failure (feature disabled, no program
                // configured, not eligible, etc) now surfaces as a
                // small toast instead of failing completely silently -
                // it still never blocks or delays the native Share
                // action itself, which has already run by this point.
                if (result && result.success === false && result.message) {
                    showShareRewardToast(result.message);
                }
            })
            .catch(() => {
                // A genuine network/RPC failure (as opposed to a
                // validation rejection returned in the response body
                // above) stays silent - a transient connectivity issue
                // isn't something the visitor needs to see a popup
                // about.
            });

        // --- 2. Referral link tagging ---
        const referrerEl = shareButton.closest("[data-referrer-id]");
        const partnerId = referrerEl ? referrerEl.dataset.referrerId : false;

        if (!partnerId) {
            return;
        }

        // Temporarily attach the referral params to the page URL so the
        // native share logic (which reads window.location.href at click
        // time) picks them up, then restore the clean URL right after.
        // Since we're in the capture phase, this runs BEFORE the native
        // share handler's own (bubble-phase) click listener fires.
        const originalHref = window.location.href;
        const referralUrl = new URL(originalHref);
        referralUrl.searchParams.set("ref", partnerId);
        referralUrl.searchParams.set("ref_type", referralType);
        if (referralSourceId) {
            referralUrl.searchParams.set("ref_src", referralSourceId);
        }
        history.replaceState({}, "", referralUrl.toString());

        setTimeout(() => {
            history.replaceState({}, "", originalHref);
        }, 0);
    },
    true
);