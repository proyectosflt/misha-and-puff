# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    cantidad_conos = fields.Integer(string="Conos")
    cono_id = fields.Many2one('tipo.cono', string='Tipo de Cono')
    package_type_id = fields.Many2one('stock.package.type', string='Tipo de bolsa')
    picking_type_code = fields.Selection(related='picking_type_id.code')
    tara_bolsa = fields.Float(string="Tara bolsa", compute='_compute_tara_bolsa', store=True, readonly=False, digits='Stock Weight')
    tara_cono = fields.Float(string="Tara cono", compute='_compute_tara_cono', store=True, readonly=False, digits='Stock Weight')
    tara_cono_total = fields.Float(string="Tara total", compute='_compute_tara_cono_total', store=True, readonly=False, digits='Stock Weight')
    peso_bruto = fields.Float(string="Peso bruto", digits='Stock Weight')
    peso_neto = fields.Float(string="Peso neto", compute='_compute_peso_neto', store=True, readonly=False, digits='Stock Weight')

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._sync_package_values()
        return lines

    def write(self, vals):
        result = super().write(vals)
        if 'package_id' in vals:
            self._sync_package_values()
        return result

    @api.onchange('package_id')
    def _onchange_package_id(self):
        for line in self:
            if line.package_id and line.picking_type_code != 'incoming':
                for field_name, value in line._get_package_values().items():
                    line[field_name] = value

    @api.onchange('location_id', 'product_id')
    def _onchange_location_or_product_id(self):
        Quant = self.env['stock.quant']
        for line in self:
            if (line.picking_type_code == 'incoming' or line.package_id
                    or not line.location_id or not line.product_id):
                continue

            quants = Quant.search([
                ('location_id', 'child_of', line.location_id.id),
                ('product_id', '=', line.product_id.id),
                ('package_id', '!=', False),
                ('quantity', '>', 0),
            ])
            if line.lot_id:
                quants = quants.filtered(lambda quant: quant.lot_id == line.lot_id)

            packages = quants.mapped('package_id')
            if len(packages) == 1:
                line.package_id = packages
                for field_name, value in line._get_package_values().items():
                    line[field_name] = value

    def _get_package_values(self):
        self.ensure_one()
        package = self.package_id
        quants = package.quant_ids
        cantidad_conos = sum(quants.mapped('cantidad_conos'))
        tara_cono_total = sum(quant.cantidad_conos * quant.tara_cono for quant in quants)
        tara_cono = tara_cono_total / cantidad_conos if cantidad_conos else 0.0

        cone_tares = {quant.tara_cono for quant in quants if quant.cantidad_conos}
        cono = False
        if len(cone_tares) == 1:
            cono = self.env['tipo.cono'].search([('tara_cono', '=', tara_cono)], limit=1)

        return {
            'cantidad_conos': cantidad_conos,
            'cono_id': cono.id or False,
            'package_type_id': package.package_type_id.id or False,
            'tara_bolsa': package.package_type_id.base_weight or 0.0,
            'tara_cono': tara_cono,
            'tara_cono_total': (package.package_type_id.base_weight or 0.0) + tara_cono_total,
            'peso_bruto': package.peso_bruto,
            'peso_neto': package.peso_neto,
            'quantity': package.peso_neto,
        }

    def _sync_package_values(self):
        for line in self:
            if line.package_id and line.picking_type_code != 'incoming':
                super(StockMoveLine, line).write(line._get_package_values())

    @api.depends('package_type_id', 'result_package_id.package_type_id')
    def _compute_tara_bolsa(self):
        for record in self:
            if not record.exists() or record.state == 'done':
                continue 
            try:
                package_type = record.package_type_id or record.result_package_id.package_type_id
                if not record.tara_bolsa and package_type:
                    record.tara_bolsa = package_type.base_weight or 0.0
            except Exception:
                continue

    @api.depends('cono_id')
    def _compute_tara_cono(self):
        for record in self:
            if not record.exists() or record.state == 'done':
                continue
            if not record.tara_cono and record.cono_id:
                record.tara_cono = record.cono_id.tara_cono or 0.0

    @api.depends('tara_bolsa', 'tara_cono', 'cantidad_conos')
    def _compute_tara_cono_total(self):
        for record in self:
            record.tara_cono_total = (record.tara_bolsa or 0.0) + (record.tara_cono or 0.0) * (record.cantidad_conos or 0)
            
    

    @api.depends('peso_bruto', 'tara_cono_total')
    def _compute_peso_neto(self):
        for record in self:
            if not record.exists() or record.state == 'done':
                continue
            try:
                value = (record.peso_bruto or 0.0) - (record.tara_cono_total or 0.0)
                record.peso_neto = value
                if value != 0:
                    record.quantity = value
            except Exception:
                continue

    def action_duplicar(self):
        for record in self:
            record.copy({
                'result_package_id': False,
                'peso_bruto': 0.0,
                'peso_neto': 0.0,
                'quantity': 0.0,
            })

    def action_apply_package(self):
        self.ensure_one()
        if self.picking_id.picking_type_code != 'incoming':
            raise UserError("Solo se pueden crear paquetes desde recepciones.")
        if self.picking_id.state in ('done', 'cancel'):
            raise UserError("No se pueden crear paquetes en un traslado cerrado.")
        if self.result_package_id:
            raise UserError("Esta línea ya tiene un paquete asignado.")
        if not self.package_type_id:
            raise UserError("Debe seleccionar un tipo de bolsa antes de crear el paquete.")

        package = self.env['stock.quant.package'].create({
            'package_type_id': self.package_type_id.id,
        })
        package.name = package._get_next_name_for_product(self.product_id)
        self.result_package_id = package

    def action_print_zpl_label(self):
        self.ensure_one()
        if self.picking_id.picking_type_code != 'incoming' or self.picking_id.state == 'cancel':
            raise UserError("La etiqueta ZPL desde la línea solo está disponible para recepciones activas.")
        if not self.result_package_id:
            raise UserError("Debe crear el paquete antes de imprimir la etiqueta.")

        if self.picking_id.state == 'done':
            report = self.env['ir.actions.report'].search([
                ('report_name', '=', 'stock.label_package_template_view')
            ], limit=1)
            if not report:
                raise UserError("No se encontró la acción de informe para la etiqueta del paquete.")
            return report.report_action(self.result_package_id)

        report = self.env.ref('flt_stock_extended.action_report_move_line_package_zpl', raise_if_not_found=False)
        if not report:
            raise UserError("No se encontró el informe ZPL para la línea de movimiento.")
        return report.report_action(self)

    def _action_done(self):
        """Override to pass custom fields in context for stock.quant updates"""
        for ml in self:
            ctx = dict(ml.env.context or {})
            ctx.update({
                'quant_cantidad_conos': ml.cantidad_conos or 0,
                'quant_tara_cono': ml.tara_cono or 0.0,
                'move_line_location_id': ml.location_id.id,
                'move_line_location_dest_id': ml.location_dest_id.id,
                'move_line_package_id': ml.package_id.id if ml.package_id else False,
                'move_line_result_package_id': ml.result_package_id.id if ml.result_package_id else False,
            })
            super(StockMoveLine, ml.with_context(ctx))._action_done()
        return True