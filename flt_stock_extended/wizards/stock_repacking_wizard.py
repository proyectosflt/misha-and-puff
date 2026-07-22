from odoo import models, fields, api

class StockRepackWizard(models.TransientModel):
    _name = 'stock.repack.wizard'
    _description = 'Empacado por conteo con corrección de inventario'

    product_id = fields.Many2one('product.product', required=True)
    location_id = fields.Many2one('stock.location', required=True,
                                   domain=[('usage', '=', 'internal')])
    theoretical_qty = fields.Float(compute='_compute_theoretical_qty',
                                   digits='Stock Weight')
    line_ids = fields.One2many('stock.repack.wizard.line', 'wizard_id')
    remaining_qty = fields.Float(compute='_compute_remaining_qty',
                                  digits='Stock Weight')

    @api.depends('product_id', 'location_id')
    def _compute_theoretical_qty(self):
        for w in self:
            w.theoretical_qty = 0.0
            if w.product_id and w.location_id:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', w.product_id.id),
                    ('location_id', '=', w.location_id.id),
                ])
                w.theoretical_qty = sum(quants.mapped('quantity'))

    @api.depends('theoretical_qty', 'line_ids.peso_neto')
    def _compute_remaining_qty(self):
        for w in self:
            w.remaining_qty = w.theoretical_qty - sum(w.line_ids.mapped('peso_neto'))
            
    def action_apply(self):
        self.ensure_one()
        # Usamos inventory_mode=True para habilitar la edición de conteo de inventario
        Quant = self.env['stock.quant'].with_context(inventory_mode=True)
        quants_to_apply = self.env['stock.quant']

        # 1. Crear paquetes y asignar cantidad contada a cada uno
        for line in self.line_ids:
            package = self.env['stock.quant.package'].create({
                'package_type_id': line.package_type_id.id,
            })

            quant = Quant.search([
                ('product_id', '=', self.product_id.id),
                ('location_id', '=', self.location_id.id),
                ('package_id', '=', package.id),
                ('lot_id', '=', False),
                ('owner_id', '=', False),
            ], limit=1)

            if not quant:
                quant = Quant.create({
                    'product_id': self.product_id.id,
                    'location_id': self.location_id.id,
                    'package_id': package.id,
                })

            quant.inventory_quantity = line.peso_neto
            quants_to_apply |= quant

        # 2. Quant "suelto" (sin paquete) — asignamos lo que sobra/falta
        loose_quant = Quant.search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.location_id.id),
            ('package_id', '=', False),
            ('lot_id', '=', False),
            ('owner_id', '=', False),
        ], limit=1)

        if not loose_quant:
            loose_quant = Quant.create({
                'product_id': self.product_id.id,
                'location_id': self.location_id.id,
                'package_id': False,
            })

        loose_quant.inventory_quantity = self.remaining_qty
        quants_to_apply |= loose_quant

        # 3. Aplicar el ajuste únicamente en los quants modificados
        if quants_to_apply:
            quants_to_apply.action_apply_inventory()
            
class StockRepackWizardLine(models.TransientModel):
    _name = 'stock.repack.wizard.line'

    wizard_id = fields.Many2one('stock.repack.wizard')
    package_type_id = fields.Many2one('stock.package.type', string="Tipo de paquete", required=True)
    cono_id = fields.Many2one('tipo.cono', string="Tipo de cono")
    cantidad_conos = fields.Integer(string="Conos")
    peso_bruto = fields.Float(string="Peso bruto", digits='Stock Weight')
    tara_bolsa = fields.Float(compute='_compute_tara_bolsa', store=True, digits='Stock Weight')
    tara_cono = fields.Float(compute='_compute_tara_cono', store=True, digits='Stock Weight')
    tara_cono_total = fields.Float(compute='_compute_tara_cono', store=True, digits='Stock Weight')
    peso_neto = fields.Float(compute='_compute_peso_neto', store=True, digits='Stock Weight')

    @api.depends('package_type_id.base_weight')
    def _compute_tara_bolsa(self):
        for line in self:
            line.tara_bolsa = line.package_type_id.base_weight or 0.0

    @api.depends('cono_id.tara_cono', 'cantidad_conos')
    def _compute_tara_cono(self):
        for line in self:
            line.tara_cono = line.cono_id.tara_cono or 0.0
            line.tara_cono_total = line.tara_cono * (line.cantidad_conos or 0)

    @api.depends('peso_bruto', 'tara_bolsa', 'tara_cono_total')
    def _compute_peso_neto(self):
        for line in self:
            line.peso_neto = (line.peso_bruto or 0.0) - line.tara_bolsa - line.tara_cono_total