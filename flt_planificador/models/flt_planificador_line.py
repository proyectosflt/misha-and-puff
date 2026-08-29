from odoo import models, fields

class FltPlanificadorLine(models.Model):
    _name = 'flt.planificador.line'
    _description = 'Línea de Planificación'
    _order = 'planificador_id, sequence, id'

    sequence = fields.Integer(string='Secuencia', default=10)

    planificador_id = fields.Many2one(
        'flt.planificador',
        string='Planificación',
        ondelete='cascade',
        required=True
    )
    fecha_planificada = fields.Date(string='Fecha planificada', required=True)
    temporada = fields.Char(string='Temporada')
    programa = fields.Char(string='Programa')
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

    # Cambiar de Char a Integer
    pri_tp = fields.Integer(string='Pri T/P')
    pri_cp = fields.Integer(string='Pri C/P')

    def action_copy_line(self):
        self.ensure_one()

        pri_prod_value = self.pri_prod
        try:
            if pri_prod_value is not None and pri_prod_value != '':
                numeric_value = float(pri_prod_value)
                pri_prod_value = str(int(numeric_value + 1) if numeric_value.is_integer() else numeric_value + 1)
        except (TypeError, ValueError):
            pri_prod_value = self.pri_prod

        current_sequence = self.sequence or 0
        following_lines = self.search([
            ('planificador_id', '=', self.planificador_id.id),
            ('id', '!=', self.id),
            ('sequence', '>', current_sequence),
        ], order='sequence, id')

        for line in following_lines:
            line.sequence += 1

        new_line = self.copy(default={
            'planificador_id': self.planificador_id.id,
            'sequence': current_sequence + 1,
            'state': 'pendiente',
            'sale_order_id': False,
            'picking_ids': [(5, 0, 0)],
            'pri_prod': pri_prod_value,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'flt.planificador.line',
            'view_mode': 'list,form',
            'res_id': new_line.id,
            'target': 'current',
        }

    @staticmethod
    def _pri_prod_sort_value(pri_prod):
        if pri_prod in (None, ''):
            return (1, 0.0)
        try:
            return (0, float(pri_prod))
        except (TypeError, ValueError):
            return (1, 0.0)

    def action_procesar(self):
        lineas_pendientes = self.filtered(lambda l: l.state == 'pendiente')
        if not lineas_pendientes:
            return

        grupos = {}
        for linea in lineas_pendientes:
            key = (linea.fecha_planificada, linea.temporada, linea.programa, linea.partner_id.id)
            if key not in grupos:
                grupos[key] = self.env['flt.planificador.line']
            grupos[key] |= linea

        for key, lineas in grupos.items():
            fecha, temporada, programa, partner_id = key

            lineas_ordenadas = sorted(
                lineas,
                key=lambda linea: self._pri_prod_sort_value(linea.pri_prod)
            )

            # Obtener el número más bajo (mayor prioridad) del grupo
            min_pri_tp = min([p for p in lineas.mapped('pri_tp') if p] or [0])
            min_pri_cp = min([p for p in lineas.mapped('pri_cp') if p] or [0])

            so_vals = {
                'partner_id': partner_id,
                'commitment_date': fecha,
                'temporada': temporada,
                'programa': programa,
                'pri_tp': min_pri_tp,
                'pri_cp': min_pri_cp,
                'order_line': [],
            }

            for linea in lineas_ordenadas:
                so_vals['order_line'].append((0, 0, {
                    'product_id': linea.product_id.id,
                    'product_uom_qty': linea.cantidad_requerida,
                }))

            sale_order = self.env['sale.order'].create(so_vals)
            sale_order.action_confirm()

            for picking in sale_order.picking_ids:
                picking.write({
                    'temporada': temporada,
                    'programa': programa,
                    'pri_tp': min_pri_tp,
                    'pri_cp': min_pri_cp,
                    'scheduled_date': fecha, # Forzamos la fecha programada
                    'planificador_line_ids': [(6, 0, lineas.ids)]
                })

            lineas.write({
                'sale_order_id': sale_order.id,
                'picking_ids': [(6, 0, sale_order.picking_ids.ids)],
                'state': 'procesada',
            })