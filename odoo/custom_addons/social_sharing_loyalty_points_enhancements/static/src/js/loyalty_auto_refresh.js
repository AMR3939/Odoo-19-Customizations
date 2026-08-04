/**
 * Auto-refresh for the "My Loyalty Points" portal page (/my/loyalty).
 *
 * Points can be earned/claimed by processes the user themselves didn't
 * just click through on this page - e.g. a payment provider confirming
 * an order a few seconds after checkout, or a second user registering
 * through this user's referral link while this page sits open. Rather
 * than requiring a manual browser refresh to see that reflected, this
 * polls the read-only /my/loyalty/data JSON endpoint (see
 * controllers/portal.py) every few seconds and patches the total points
 * + history table in place.
 *
 * Deliberately plain vanilla JS (no Odoo JS module framework) - this
 * page is a simple server-rendered portal page, not part of the web
 * client/OWL app, so it only needs to run after DOMContentLoaded.
 */
(function () {
    "use strict";

    var POLL_INTERVAL_MS = 8000;
    var pollTimer = null;

    function escapeHtml(value) {
        var div = document.createElement("div");
        div.textContent = value === null || value === undefined ? "" : String(value);
        return div.innerHTML;
    }

    function renderRows(tbody, rows) {
        if (!rows || !rows.length) {
            tbody.innerHTML =
                '<tr><td colspan="4" class="text-center text-muted py-4">' +
                "No loyalty points earned yet.</td></tr>";
            return;
        }

        var html = "";

        rows.forEach(function (row) {
            var isNegative = row.points < 0;
            var badgeClass = isNegative ? "bg-danger" : "bg-success";
            var sign = isNegative ? "" : "+";

            html += "<tr>";
            html += "<td>" + escapeHtml(row.description) + "</td>";
            html +=
                '<td><span class="badge rounded-pill" ' +
                'style="background-color:#f5d5a8; color:#7a4a12;">' +
                escapeHtml(row.category) +
                "</span></td>";
            html += "<td>" + escapeHtml(row.timestamp) + "</td>";
            html +=
                '<td><span class="badge ' +
                badgeClass +
                '">' +
                sign +
                escapeHtml(row.points) +
                "</span></td>";
            html += "</tr>";
        });

        tbody.innerHTML = html;
    }

    function refreshLoyaltyData() {
        var page = document.getElementById("o_loyalty_page");
        if (!page) {
            return;
        }

        fetch("/my/loyalty/data", {
            method: "GET",
            headers: { Accept: "application/json" },
            credentials: "same-origin",
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error("Bad response: " + response.status);
                }
                return response.json();
            })
            .then(function (data) {
                var totalEl = document.getElementById("o_loyalty_total_points");
                var tbody = document.getElementById("o_loyalty_history_tbody");

                if (totalEl && typeof data.total_points !== "undefined") {
                    totalEl.textContent = data.total_points;
                }

                if (tbody) {
                    renderRows(tbody, data.rows || []);
                }
            })
            .catch(function () {
                // Silently skip this cycle - transient network hiccups
                // shouldn't surface an error to the user; the next poll
                // will simply try again.
            });
    }

    function startPolling() {
        if (!pollTimer) {
            pollTimer = window.setInterval(refreshLoyaltyData, POLL_INTERVAL_MS);
        }
    }

    function stopPolling() {
        if (pollTimer) {
            window.clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        var page = document.getElementById("o_loyalty_page");
        if (!page) {
            return;
        }

        // Pause polling while the tab isn't visible so a page left open
        // in a background tab doesn't keep hitting the server, and do
        // one immediate refresh when the user comes back to it.
        document.addEventListener("visibilitychange", function () {
            if (document.hidden) {
                stopPolling();
            } else {
                refreshLoyaltyData();
                startPolling();
            }
        });

        startPolling();
    });
})();