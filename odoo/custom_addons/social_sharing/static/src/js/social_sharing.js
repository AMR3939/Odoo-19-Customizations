/** @odoo-module **/

// Social Sharing
// Since we are leveraging Odoo's core 'oe_share' class and JS interaction
// (defined in website/static/src/snippets/s_share/share.js),
// we don't need any custom javascript runtime handlers for URL popup logic.
// The core Odoo handler will automatically intercept clicks, bind the share URLs,
// and open them in the Event-style popup window.
export default {};
