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
    fecha_planificada = fields.Date(string='Fecha planificada', required=True)
    pri_tp = fields.Char(string='Pri T/P')
    temporada = fields.Char(string='Temporada')
    programa = fields.Char(string='Programa')
    pri_cp = fields.Char(string='Pri C/P')
    partner_id = fields.Many2one('res.partner', string='Clte/Prov', required=True)
    pri_prod = fields.Char(string='Pri Prod')
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    cantidad_requerida = fields.Float(string='Cantidad Requerida', required=True)
    
    sale_order_id = fields.Many2one('sale.order', string='Venta', readonly=True)
    # Definimos la tabla relacional explícitamente para el M2M
    picking_ids = fields.Many2many(
        'stock.picking', 
        'flt_planificador_picking_rel', 
        'line_id', 
        'picking_id', 
        string='Despachos', 
        readonly=True
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

    def action_procesar(self):
        # Filtramos solo las líneas que aún están pendientes
        lineas_pendientes = self.filtered(lambda l: l.state == 'pendiente')
        if not lineas_pendientes:
            return

        grupos = {}
        # Agrupar por Fecha, Temporada, Programa y Cliente
        for linea in lineas_pendientes:
            key = (linea.fecha_planificada, linea.temporada, linea.programa, linea.partner_id.id)
            if key not in grupos:
                grupos[key] = self.env['flt.planificador.line']
            grupos[key] |= linea

        for key, lineas in grupos.items():
            fecha, temporada, programa, partner_id = key
            
            # 1. Crear el Pedido de Venta (Sale Order)
            so_vals = {
                'partner_id': partner_id,
                'commitment_date': fecha,  # Fecha de entrega esperada
                'temporada': temporada,
                'programa': programa,
                'order_line': [],
            }
            
            for linea in lineas:
                so_vals['order_line'].append((0, 0, {
                    'product_id': linea.product_id.id,
                    'product_uom_qty': linea.cantidad_requerida,
                }))

            sale_order = self.env['sale.order'].create(so_vals)
            
            # 2. Confirmar el Pedido (esto genera el Stock Picking automáticamente)
            sale_order.action_confirm()

            # 3. Actualizar los pickings generados con los campos custom y enlazar M2M
            for picking in sale_order.picking_ids:
                picking.write({
                    'temporada': temporada,
                    'programa': programa,
                    'planificador_line_ids': [(6, 0, lineas.ids)]
                })

            # 4. Actualizar las líneas de planificación con el SO, los pickings y el estado
            lineas.write({
                'sale_order_id': sale_order.id,
                'picking_ids': [(6, 0, sale_order.picking_ids.ids)],
                'state': 'procesada',
            })