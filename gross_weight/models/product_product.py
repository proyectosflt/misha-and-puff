from odoo import _, api, fields, models

class ProductProduct(models.Model):
    _inherit = 'product.product'
    _description = 'Product Product'
    
    gross_weight = fields.Float('Peso bruto', compute='_compute_cone_quantity_gross_weight', compute_sudo=True)
    cone_quantity = fields.Float('Cantidad de conos', compute='_compute_cone_quantity_gross_weight', compute_sudo=True)

    quantity_svl = fields.Float(compute='_compute_value_svl', compute_sudo=True)

    @api.depends('stock_quant_ids')
    @api.depends_context('to_date', 'company')
    def _compute_cone_quantity_gross_weight(self):
        """Compute `value_svl` and `quantity_svl`."""
        company_id = self.env.company.id
        domain = [
            ('product_id', 'in', self.ids),
            ('company_id', '=', company_id),
        ]
        if self.env.context.get('to_date'):
            to_date = fields.Datetime.to_datetime(self.env.context['to_date'])
            domain.append(('create_date', '<=', to_date))
        groups = self.env['stock.quant'].read_group(domain, ['cone_quantity:sum', 'gross_weight:sum'], ['product_id'], orderby='id')
        products = self.browse()
        for group in groups:
            product = self.browse(group['product_id'][0])
            # product.value_svl = self.env.company.currency_id.round(group['value'])
            product.cone_quantity = group['cone_quantity']
            product.gross_weight = group['gross_weight']
            products |= product
        remaining = (self - products)
        remaining.cone_quantity = 0
        remaining.gross_weight = 0