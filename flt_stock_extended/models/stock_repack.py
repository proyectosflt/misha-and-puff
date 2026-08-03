# -*- coding: utf-8 -*-
from odoo import models, fields, api

class StockRepack(models.Model):
    _name = 'stock.repack'
    _description = 'Empacado por conteo con corrección de inventario'

    product_id = fields.Many2one('product.product', required=True, string="Producto")
    location_id = fields.Many2one('stock.location', required=True,
                                   domain=[('usage', '=', 'internal')], string="Ubicación de Origen")
    theoretical_qty = fields.Float(compute='_compute_theoretical_qty',
                                   digits='Stock Weight', string="Cantidad teórica")
    line_ids = fields.One2many('stock.repack.line', 'repack_id', string="Líneas de empaque")
    remaining_qty = fields.Float(compute='_compute_remaining_qty',
                                  digits='Stock Weight', string="Cantidad restante")

    @api.depends('product_id', 'location_id')
    def _compute_theoretical_qty(self):
        for w in self:
            w.theoretical_qty = 0.0
            if w.product_id and w.location_id:
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', w.product_id.id),
                    ('location_id', '=', w.location_id.id),
                    ('package_id', '=', False),
                ])
                w.theoretical_qty = sum(quants.mapped('quantity'))

    @api.depends('theoretical_qty', 'line_ids.peso_neto')
    def _compute_remaining_qty(self):
        for w in self:
            w.remaining_qty = w.theoretical_qty - sum(w.line_ids.mapped('peso_neto'))

    def action_apply(self):
        self.ensure_one()
        if self.remaining_qty > 0:
            return {
                'name': 'Confirmar Remanente',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.repack.confirm.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_repack_id': self.id,
                    'default_remaining_qty': self.remaining_qty,
                }
            }
        
        return self._process_repack(delete_remanent=True)

    def _process_repack(self, delete_remanent=True):
        self.ensure_one()
        Quant = self.env['stock.quant'].with_context(inventory_mode=True)
        quants_to_apply = self.env['stock.quant']

        # 1. Handle loose (unpackaged) stock on origin location
        loose_quants = Quant.search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.location_id.id),
            ('package_id', '=', False),
            ('lot_id', '=', False),
            ('owner_id', '=', False),
        ])

        if delete_remanent:
            for loose_quant in loose_quants:
                loose_quant.cantidad_conos = 0
                loose_quant.tara_cono = 0.0
                loose_quant.inventory_quantity = 0.0
                quants_to_apply |= loose_quant
        else:
            for loose_quant in loose_quants:
                loose_quant.inventory_quantity = self.remaining_qty
                quants_to_apply |= loose_quant

        # 2. Create NEW packages and quants using each line's specified destination location
        for line in self.line_ids:
            package = self.env['stock.quant.package'].create({
                'package_type_id': line.package_type_id.id,
            })

            target_location = line.location_id or self.location_id

            quant = Quant.create({
                'product_id': self.product_id.id,
                'location_id': target_location.id,
                'package_id': package.id,
            })

            quant.write({
                'cantidad_conos': line.cantidad_conos or 0,
                'tara_cono': line.tara_cono or 0.0,
                'inventory_quantity': line.peso_neto,
            })
            quants_to_apply |= quant

        # 3. Apply inventory adjustment
        if quants_to_apply:
            quants_to_apply.action_apply_inventory()

        # 4. Delete the repack record
        self.unlink()

        # 5. Redirect back to list view
        return self.env.ref('flt_stock_extended.action_stock_repack').read()[0]


class StockRepackLine(models.Model):
    _name = 'stock.repack.line'
    _description = 'Línea de Empacado por conteo'

    repack_id = fields.Many2one('stock.repack', ondelete='cascade')
    location_id = fields.Many2one(
        'stock.location', 
        string="Ubicación Destino", 
        required=True,
        domain=[('usage', '=', 'internal')],
        default=lambda self: self._default_location_id()
    )
    package_type_id = fields.Many2one('stock.package.type', string="Tipo de paquete", required=True)
    cono_id = fields.Many2one('tipo.cono', string="Tipo de cono")
    cantidad_conos = fields.Integer(string="Conos")
    peso_bruto = fields.Float(string="Peso bruto", digits='Stock Weight')
    tara_bolsa = fields.Float(compute='_compute_tara_bolsa', readonly=False, digits='Stock Weight')
    tara_cono = fields.Float(compute='_compute_tara_cono', readonly=False, digits='Stock Weight')
    tara_cono_total = fields.Float(compute='_compute_tara_cono_total', digits='Stock Weight')
    peso_neto = fields.Float(compute='_compute_peso_neto', digits='Stock Weight')

    def _default_location_id(self):
        repack_id = self.env.context.get('default_repack_id')
        if repack_id:
            repack = self.env['stock.repack'].browse(repack_id)
            return repack.location_id.id
        return False

    @api.onchange('repack_id')
    def _onchange_repack_id(self):
        if self.repack_id and not self.location_id:
            self.location_id = self.repack_id.location_id

    @api.depends('package_type_id')
    def _compute_tara_bolsa(self):
        for line in self:
            line.tara_bolsa = line.package_type_id.base_weight or 0.0

    @api.depends('cono_id')
    def _compute_tara_cono(self):
        for line in self:
            line.tara_cono = line.cono_id.tara_cono or 0.0

    @api.depends('tara_cono', 'cantidad_conos')
    def _compute_tara_cono_total(self):
        for line in self:
            line.tara_cono_total = (line.tara_cono or 0.0) * (line.cantidad_conos or 0)

    @api.depends('peso_bruto', 'tara_bolsa', 'tara_cono_total')
    def _compute_peso_neto(self):
        for line in self:
            line.peso_neto = (line.peso_bruto or 0.0) - (line.tara_bolsa or 0.0) - (line.tara_cono_total or 0.0)


class StockRepackConfirmWizard(models.TransientModel):
    _name = 'stock.repack.confirm.wizard'
    _description = 'Confirmación de Cantidades Remanentes'

    repack_id = fields.Many2one('stock.repack', required=True)
    remaining_qty = fields.Float(string="Cantidad Restante", digits='Stock Weight', readonly=True)

    def action_confirm_yes(self):
        return self.repack_id._process_repack(delete_remanent=True)

    def action_confirm_no(self):
        return self.repack_id._process_repack(delete_remanent=False)