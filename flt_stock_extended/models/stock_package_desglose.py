# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError

class StockPackagesDesglose(models.Model):
    _name = 'stock.packages.desglose'
    _description = 'Desglose y reempacado de bolsas'

    state = fields.Selection([
        ('draft', 'Abierto'),
        ('done', 'Cerrado')
    ], string="Estado", default='draft', required=True, copy=False)

    source_line_ids = fields.One2many('stock.packages.desglose.source', 'desglose_id', string="Paquetes de Origen")
    dest_line_ids = fields.One2many('stock.packages.desglose.dest', 'desglose_id', string="Nuevos Paquetes (Destino)")

    theoretical_conos = fields.Integer(compute='_compute_theoreticals', string="Conos Teóricos")
    theoretical_bruto = fields.Float(compute='_compute_theoreticals', string="Peso Bruto Teórico", digits='Stock Weight')
    theoretical_neto = fields.Float(compute='_compute_theoreticals', string="Peso Neto Teórico", digits='Stock Weight')

    remaining_conos = fields.Integer(compute='_compute_remainings', string="Conos Restantes")
    remaining_bruto = fields.Float(compute='_compute_remainings', string="Peso Bruto Restante", digits='Stock Weight')
    remaining_neto = fields.Float(compute='_compute_remainings', string="Peso Neto Restante", digits='Stock Weight')

    @api.depends('source_line_ids.cantidad_conos', 'source_line_ids.peso_bruto', 'source_line_ids.peso_neto')
    def _compute_theoreticals(self):
        for rec in self:
            rec.theoretical_conos = sum(rec.source_line_ids.mapped('cantidad_conos'))
            rec.theoretical_bruto = sum(rec.source_line_ids.mapped('peso_bruto'))
            rec.theoretical_neto = sum(rec.source_line_ids.mapped('peso_neto'))

    @api.depends('theoretical_conos', 'theoretical_bruto', 'theoretical_neto',
                 'dest_line_ids.cantidad_conos', 'dest_line_ids.peso_bruto', 'dest_line_ids.peso_neto')
    def _compute_remainings(self):
        for rec in self:
            rec.remaining_conos = rec.theoretical_conos - sum(rec.dest_line_ids.mapped('cantidad_conos'))
            rec.remaining_bruto = rec.theoretical_bruto - sum(rec.dest_line_ids.mapped('peso_bruto'))
            rec.remaining_neto = rec.theoretical_neto - sum(rec.dest_line_ids.mapped('peso_neto'))

    def action_finalizar(self):
        self.ensure_one()

        if self.state == 'done':
            raise UserError("Este registro ya se encuentra cerrado.")

        if not self.source_line_ids:
            raise UserError("Debe agregar al menos un paquete de origen.")
        
        if not self.dest_line_ids:
            raise UserError("Debe generar al menos un paquete nuevo de destino.")

        if self.remaining_conos != 0:
            raise UserError("No puede finalizar. La cantidad de conos restantes debe ser exactamente cero.")

        unapplied_lines = self.dest_line_ids.filtered(lambda l: not l.is_applied)
        for line in unapplied_lines:
            line.action_apply_line()

        Quant = self.env['stock.quant'].with_context(inventory_mode=True)
        quants_to_apply = self.env['stock.quant']

        for source_line in self.source_line_ids:
            for quant in source_line.package_id.quant_ids:
                quant.cantidad_conos = 0
                quant.tara_cono = 0.0
                quant.inventory_quantity = 0.0
                quants_to_apply |= quant

        if quants_to_apply:
            quants_to_apply.action_apply_inventory()

        self.write({'state': 'done'})


class StockPackagesDesgloseSource(models.Model):
    _name = 'stock.packages.desglose.source'
    _description = 'Paquete de Origen para Desglose'

    desglose_id = fields.Many2one('stock.packages.desglose', ondelete='cascade')
    package_id = fields.Many2one('stock.quant.package', string="Paquete", required=True)
    cantidad_conos = fields.Integer(string="Conos", compute='_compute_package_data', store=True)
    peso_neto = fields.Float(string="Peso Neto", compute='_compute_package_data', store=True, digits='Stock Weight')
    peso_bruto = fields.Float(string="Peso Bruto", compute='_compute_package_data', store=True, digits='Stock Weight')

    @api.depends('package_id')
    def _compute_package_data(self):
        for line in self:
            if line.package_id:
                quants = line.package_id.quant_ids
                conos = sum(quants.mapped('cantidad_conos'))
                neto = sum(quants.mapped('quantity'))
                tara_conos = sum((q.tara_cono * q.cantidad_conos) for q in quants)
                tara_bolsa = line.package_id.package_type_id.base_weight or 0.0
                
                line.cantidad_conos = conos
                line.peso_neto = neto
                line.peso_bruto = neto + tara_conos + tara_bolsa
            else:
                line.cantidad_conos = 0
                line.peso_neto = 0.0
                line.peso_bruto = 0.0


class StockPackagesDesgloseDest(models.Model):
    _name = 'stock.packages.desglose.dest'
    _description = 'Nuevo Paquete Destino'

    desglose_id = fields.Many2one('stock.packages.desglose', ondelete='cascade')
    location_id = fields.Many2one(
        'stock.location', 
        string="Ubicación Destino", 
        required=True,
        domain=[('usage', '=', 'internal')]
    )
    package_type_id = fields.Many2one('stock.package.type', string="Tipo de paquete", required=True)
    cono_id = fields.Many2one('tipo.cono', string="Tipo de cono")
    cantidad_conos = fields.Integer(string="Conos")
    peso_bruto = fields.Float(string="Peso bruto", digits='Stock Weight')
    tara_bolsa = fields.Float(compute='_compute_tara_bolsa', readonly=False, store=True, digits='Stock Weight')
    tara_cono = fields.Float(compute='_compute_tara_cono', readonly=False, store=True, digits='Stock Weight')
    tara_cono_total = fields.Float(compute='_compute_tara_cono_total', store=True, digits='Stock Weight')
    peso_neto = fields.Float(compute='_compute_peso_neto', store=True, digits='Stock Weight')
    
    package_id = fields.Many2one('stock.quant.package', string="Paquete Creado", readonly=True, copy=False)
    is_applied = fields.Boolean(string="Aplicado", default=False, copy=False)

    @api.onchange('desglose_id')
    def _onchange_desglose_id(self):
        if self.desglose_id and self.desglose_id.source_line_ids and not self.location_id:
            self.location_id = self.desglose_id.source_line_ids[0].package_id.location_id

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

    def action_apply_line(self):
        for line in self:
            if line.is_applied:
                raise UserError("Esta línea ya ha sido aplicada.")
            
            if line.desglose_id.state == 'done':
                raise UserError("No se pueden aplicar líneas en un registro cerrado.")

            products = line.desglose_id.source_line_ids.mapped('package_id.quant_ids.product_id')
            if not products:
                raise UserError("Los paquetes seleccionados no tienen inventario/productos.")
            if len(products) > 1:
                raise UserError("Los paquetes de origen contienen múltiples productos. Solo se permite reempacar un producto a la vez.")

            product = products[0]
            Quant = self.env['stock.quant'].with_context(inventory_mode=True)

            new_package = self.env['stock.quant.package'].create({
                'package_type_id': line.package_type_id.id,
            })

            new_quant = Quant.create({
                'product_id': product.id,
                'location_id': line.location_id.id,
                'package_id': new_package.id,
            })

            new_quant.write({
                'cantidad_conos': line.cantidad_conos or 0,
                'tara_cono': line.tara_cono or 0.0,
                'inventory_quantity': line.peso_neto,
            })

            new_quant.action_apply_inventory()
            
            line.write({
                'package_id': new_package.id,
                'is_applied': True,
            })

    def action_copy_line(self):
        self.ensure_one()
        return self.copy(default={
            'peso_bruto': 0.0,
            'package_id': False,
            'is_applied': False,
            'tara_bolsa': self.tara_bolsa,
            'tara_cono': self.tara_cono,
        })

    def action_print_label(self):
        self.ensure_one()
        if not self.package_id:
            raise UserError("Debe aplicar la línea antes de imprimir la etiqueta del paquete.")

        # Search for the report action using the template name
        report = self.env['ir.actions.report'].search([
            ('report_name', '=', 'stock.label_package_template_view')
        ], limit=1)

        if not report:
            raise UserError("No se encontró la acción de informe para la etiqueta del paquete.")

        return report.report_action(self.package_id)