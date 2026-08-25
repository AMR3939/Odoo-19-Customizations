from odoo import fields, models, tools


class WebsiteSaleCustomerAcquisition(models.Model):
    _name = 'website.sale.customer.acquisition'
    _description = 'Website Customer Acquisition'
    _auto = False
    _rec_name = 'partner_id'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        readonly=True,
    )
    website_id = fields.Many2one(
        'website',
        string='Website',
        readonly=True,
    )
    order_id = fields.Many2one(
        'sale.order',
        string='First Website Order',
        readonly=True,
    )
    date = fields.Datetime(
        string='Acquisition Date',
        readonly=True,
    )
    customer_count = fields.Integer(
        string='New Customers',
        readonly=True,
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(f'''
            CREATE OR REPLACE VIEW {self._table} AS (
                SELECT DISTINCT ON (so.partner_id)
                    so.id AS id,
                    so.partner_id AS partner_id,
                    so.website_id AS website_id,
                    so.id AS order_id,
                    so.date_order AS date,
                    1 AS customer_count
                FROM sale_order so
                JOIN website w
                    ON w.id = so.website_id
                JOIN res_users customer_user
                    ON customer_user.partner_id = so.partner_id
                WHERE so.website_id IS NOT NULL
                  AND so.state IN ('sale', 'done')
                  AND so.partner_id IS NOT NULL
                  AND so.partner_id != w.user_id
                ORDER BY so.partner_id, so.date_order, so.id
            )
        ''')
