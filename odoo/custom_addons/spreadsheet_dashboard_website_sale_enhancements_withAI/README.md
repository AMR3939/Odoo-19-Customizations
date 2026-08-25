# spreadsheet_dashboard_website_sale_enhancements_withAI

Custom Odoo 19 addon that updates the standard eCommerce Spreadsheet Dashboard.

## Changes
- Adds **Average Order Value** KPI: confirmed website revenue / confirmed website orders.
- Adds **Customer Acquisition** KPI: unique customers with a linked Odoo user whose first confirmed website order occurs in the selected period. The website public user is excluded.
- Adds **% of Revenue** to the Top Products table: product revenue / total website product revenue * 100.
- Expands the Top Products table from 3 to 4 columns and shifts Top Categories to keep the two tables separated.

## Dependencies
- spreadsheet_dashboard_website_sale
- spreadsheet_dashboard
- website_sale

## Install
1. Copy this folder into the Odoo custom addons path.
2. Restart Odoo.
3. Update the Apps list.
4. Install `eCommerce Dashboard Enhancements withAI`.
5. Upgrade the addon after any JSON changes.

The addon updates the existing `spreadsheet_dashboard_website_sale.spreadsheet_dashboard_ecommerce` record, so the standard eCommerce dashboard remains the dashboard being customized.
