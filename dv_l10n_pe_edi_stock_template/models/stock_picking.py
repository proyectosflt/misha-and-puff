from odoo import api, fields, models, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    orden_compra = fields.Char(string="Orden de Compra", store=True)
    sale_order_id = fields.Many2one('sale.order', string="Orden de Venta Relacionada", compute="_compute_sale_order", store=True)
    cliente = fields.Char(string="Cliente", compute="_compute_sale_order", store=True)
    cliente_ruc = fields.Char(string="RUC del Cliente", compute="_compute_sale_order", store=True)
    vendedor = fields.Char(string="Vendedor", compute="_compute_sale_order", store=True)

    sale_order_notes = fields.Text(string="Notas de la Orden de Venta",compute="_compute_sale_order", store=True)

    @api.depends('origin')
    def _compute_sale_order(self):
        for picking in self:
            # Limpiar valores por defecto
            picking.sale_order_id = False
            picking.cliente = False
            picking.cliente_ruc = False
            picking.vendedor = False 
            picking.sale_order_notes = ""  # Asignar valor predeterminado
            # Verificar si el campo origin está vinculado a una orden de venta
            if picking.origin:
                sale_order = self.env['sale.order'].search([('name', '=', picking.origin)], limit=1)
                if sale_order:
                    picking.sale_order_id = sale_order
                    picking.cliente = sale_order.partner_id.name
                    picking.cliente_ruc = sale_order.partner_id.vat  # Asegúrate de que el campo VAT sea el RUC
                    picking.vendedor = sale_order.user_id.name
                    picking.sale_order_notes = sale_order.note or ""  # Asegurarse de asignar siempre un valor

    def get_transport_type_label(self):
        self.ensure_one()
        # Diccionario de traducciones manuales
        translations = {
            '01': 'Transporte Público',
            '02': 'Transporte Privado'
        }
        # Obtener la traducción correspondiente al valor seleccionado
        return translations.get(self.l10n_pe_edi_transport_type, '')
    
    def get_reason_for_transfer_label(self):
        self.ensure_one()
        # Diccionario de traducciones manuales
        translations = {
            '01': 'Venta',
            '03': 'Venta con entrega a terceros',
            '04': 'Transferencia entre establecimientos de la misma empresa',
            '05': 'Envíos',
            '13': 'Otros',
            '14': 'Venta sujeta a confirmación del comprador',
            '17': 'Transferencia de bienes para transformación',
            '18': 'Emisor ambulante traslado CP',
        }
        # Obtener la traducción correspondiente al valor seleccionado
        return translations.get(self.l10n_pe_edi_reason_for_transfer, '')
