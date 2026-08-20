from odoo import models, fields


class FltPlanificadorLine(models.Model):
    _name = 'flt.planificador.line'
    _description = 'Línea de Planificación'

    planificador_id = fields.Many2one(
        'flt.planificador',
        string='Planificación',
        ondelete='cascade',
        required=True
    )
    state = fields.Selection(
        [
            ('pendiente', 'Pendiente'),
            ('procesada', 'Procesada'),
        ],
        string='Estado',
        default='pendiente',
        required=True
    )
    fecha_planificada = fields.Date(string='Fecha planificada')
    pri_tp = fields.Char(string='Pri T/P')
    temporada = fields.Char(string='Temporada')
    programa = fields.Char(string='Programa')
    pri_cp = fields.Char(string='Pri C/P')
    partner_id = fields.Many2one('res.partner', string='Clte/Prov')
    pri_prod = fields.Char(string='Pri Prod')
    product_id = fields.Many2one('product.product', string='Producto')
    cantidad_requerida = fields.Float(string='Cantidad Requerida')
    sale_order_id = fields.Many2one('sale.order', string='Venta')
    picking_ids = fields.Many2many('stock.picking', string='Despachos')