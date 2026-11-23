# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockPackageDispatchWizard(models.TransientModel):
    _name = 'stock.package.dispatch.wizard'
    _description = 'Selección masiva de paquetes para despacho'
    # El asistente se reabre después de cada desglose: se conserva más que el valor por defecto
    _transient_max_hours = 24.0

    move_id = fields.Many2one('stock.move', string="Movimiento", required=True, ondelete='cascade')
    picking_id = fields.Many2one(related='move_id.picking_id', string="Traslado")
    product_id = fields.Many2one(related='move_id.product_id', string="Producto")
    descripcion = fields.Text(related='move_id.product_id.product_tmpl_id.descripcion', string="Descripción")
    color_code = fields.Char(related='move_id.product_id.product_tmpl_id.product_color_id.codigo', string="Código color")
    product_uom_id = fields.Many2one(related='move_id.product_uom', string="Unidad")
    demand_qty = fields.Float(related='move_id.product_uom_qty', string="Demanda", digits='Stock Weight')

    line_ids = fields.One2many('stock.package.dispatch.wizard.line', 'wizard_id', string="Paquetes disponibles")

    selected_count = fields.Integer(compute='_compute_totals', string="Paquetes seleccionados")
    selected_conos = fields.Integer(compute='_compute_totals', string="Conos seleccionados")
    selected_bruto = fields.Float(compute='_compute_totals', string="Bruto seleccionado", digits='Stock Weight')
    selected_qty = fields.Float(compute='_compute_totals', string="Neto seleccionado", digits='Stock Weight')
    difference_qty = fields.Float(compute='_compute_totals', string="Diferencia", digits='Stock Weight')
    # Datos que guían el desglose: lo que falta sin contar los paquetes marcados para desglosar
    breakdown_count = fields.Integer(compute='_compute_totals', string="Paquetes a desglosar")
    breakdown_base_qty = fields.Float(compute='_compute_totals', string="Neto sin paquetes a desglosar", digits='Stock Weight')
    breakdown_target_qty = fields.Float(compute='_compute_totals', string="Falta cubrir con el desglose", digits='Stock Weight')

    @api.depends('line_ids.selected', 'line_ids.to_breakdown', 'line_ids.peso_neto',
                 'line_ids.peso_bruto', 'line_ids.cantidad_conos', 'demand_qty')
    def _compute_totals(self):
        for wizard in self:
            selected = wizard.line_ids.filtered('selected')
            breakdown = wizard.line_ids.filtered('to_breakdown')
            wizard.selected_count = len(selected)
            wizard.selected_conos = sum(selected.mapped('cantidad_conos'))
            wizard.selected_bruto = sum(selected.mapped('peso_bruto'))
            wizard.selected_qty = sum(selected.mapped('peso_neto'))
            wizard.difference_qty = wizard.selected_qty - wizard.demand_qty
            wizard.breakdown_count = len(breakdown)
            wizard.breakdown_base_qty = sum((selected - breakdown).mapped('peso_neto'))
            wizard.breakdown_target_qty = wizard.demand_qty - wizard.breakdown_base_qty

    # -------------------------------------------------------------------------
    # Carga de paquetes
    # -------------------------------------------------------------------------
    @api.model
    def _get_available_package_quants(self, move):
        """Quants empaquetados del producto en la ubicación de origen que no están reservados por otros movimientos."""
        quants = self.env['stock.quant'].search([
            ('product_id', '=', move.product_id.id),
            ('location_id', 'child_of', move.location_id.id),
            ('location_id.usage', '=', 'internal'),
            ('package_id', '!=', False),
            ('quantity', '>', 0),
        ])
        own_lines = move.move_line_ids
        rounding = move.product_id.uom_id.rounding
        result = self.env['stock.quant']
        for quant in quants:
            own_reserved = sum(own_lines.filtered(
                lambda ml: ml.package_id == quant.package_id and ml.location_id == quant.location_id
            ).mapped('quantity'))
            reserved_by_others = quant.reserved_quantity - own_reserved
            if float_compare(reserved_by_others, 0.0, precision_rounding=rounding) > 0:
                continue
            result |= quant
        return result

    @api.model
    def _prepare_line_vals(self, package, selected=False, is_new=False):
        return {
            'package_id': package.id,
            'selected': selected,
            'is_new': is_new,
        }

    @api.model
    def action_open_for_move(self, move):
        move.ensure_one()
        if move.picking_code != 'outgoing':
            raise UserError("La selección masiva de paquetes solo está disponible en despachos.")
        if move.state in ('done', 'cancel'):
            raise UserError("No se pueden seleccionar paquetes en un movimiento cerrado o cancelado.")

        quants = self._get_available_package_quants(move)
        current_packages = move.move_line_ids.mapped('package_id')
        packages = (quants.mapped('package_id') | current_packages).sorted(lambda p: p.name or '')

        wizard = self.create({
            'move_id': move.id,
            'line_ids': [
                (0, 0, self._prepare_line_vals(package, selected=package in current_packages))
                for package in packages
            ],
        })
        return wizard._get_reopen_action()

    def _get_reopen_action(self):
        self.ensure_one()
        return {
            'name': "Selección de paquetes",
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(self.env.ref('flt_stock_extended.view_stock_package_dispatch_wizard_form').id, 'form')],
            'target': 'new',
            'context': {'dialog_size': 'extra-large'},
        }

    # -------------------------------------------------------------------------
    # Acciones
    # -------------------------------------------------------------------------
    def action_select_all(self):
        self.ensure_one()
        self.line_ids.write({'selected': True})
        return self._get_reopen_action()

    def action_unselect_all(self):
        self.ensure_one()
        self.line_ids.write({'selected': False, 'to_breakdown': False})
        return self._get_reopen_action()

    def action_open_breakdown(self):
        self.ensure_one()
        breakdown_lines = self.line_ids.filtered('to_breakdown')
        if not breakdown_lines:
            raise UserError("Marque en la columna «Desglosar» al menos un paquete para abrir el desglose.")

        desglose = self.env['stock.packages.desglose'].create({
            'dispatch_wizard_ref': self.id,
            'origin_move_id': self.move_id.id,
            'dispatch_demand_qty': self.demand_qty,
            'dispatch_base_qty': self.breakdown_base_qty,
            'source_line_ids': [(0, 0, {'package_id': line.package_id.id}) for line in breakdown_lines],
        })
        return desglose._get_dispatch_form_action()

    def _apply_breakdown_result(self, source_packages, new_packages_vals):
        """Quita los paquetes desglosados y agrega los nuevos paquetes creados en el desglose."""
        self.ensure_one()
        self.line_ids.filtered(lambda l: l.package_id in source_packages).unlink()
        existing = self.line_ids.mapped('package_id')
        self.write({
            'line_ids': [
                (0, 0, self._prepare_line_vals(package, selected=selected, is_new=True))
                for package, selected in new_packages_vals
                if package not in existing
            ],
        })

    def action_confirm(self):
        """Deja en el movimiento exactamente los paquetes seleccionados."""
        self.ensure_one()
        move = self.move_id
        if move.state in ('done', 'cancel'):
            raise UserError("El movimiento ya está cerrado o cancelado.")

        selected_lines = self.line_ids.filtered('selected')
        selected_packages = selected_lines.mapped('package_id')

        # Se eliminan las líneas de paquetes que ya no se despachan
        lines_to_remove = move.move_line_ids.filtered(
            lambda ml: ml.package_id and ml.package_id not in selected_packages
        )
        lines_to_remove.unlink()

        # Se crean líneas solo para los paquetes que aún no están en el movimiento
        current_packages = move.move_line_ids.mapped('package_id')
        rounding = move.product_id.uom_id.rounding
        vals_list = []
        for package in selected_packages - current_packages:
            quants = package.quant_ids.filtered(
                lambda q: q.product_id == move.product_id
                and float_compare(q.quantity, 0.0, precision_rounding=rounding) > 0
            )
            if not quants:
                raise UserError(
                    "El paquete %s ya no tiene stock de %s." % (package.name, move.product_id.display_name)
                )
            quant = quants[0]
            vals_list.append({
                'move_id': move.id,
                'picking_id': move.picking_id.id,
                'product_id': move.product_id.id,
                'product_uom_id': move.product_uom.id,
                'company_id': move.company_id.id,
                'location_id': quant.location_id.id,
                'location_dest_id': move.location_dest_id.id,
                'package_id': package.id,
                'lot_id': quant.lot_id.id,
                'owner_id': quant.owner_id.id,
                'quantity': package.peso_neto,
            })
        if vals_list:
            # El create sincroniza conos, taras y pesos desde el paquete
            self.env['stock.move.line'].create(vals_list)

        return move.action_show_details()

    def action_cancel(self):
        self.ensure_one()
        return self.move_id.action_show_details()


class StockPackageDispatchWizardLine(models.TransientModel):
    _name = 'stock.package.dispatch.wizard.line'
    _description = 'Paquete disponible para despacho'
    _order = 'is_new desc, id'

    wizard_id = fields.Many2one('stock.package.dispatch.wizard', required=True, ondelete='cascade')
    package_id = fields.Many2one('stock.quant.package', string="Paquete", required=True, readonly=True)
    location_id = fields.Many2one('stock.location', string="Ubicación", compute='_compute_package_data')
    product_id = fields.Many2one('product.product', string="Producto", compute='_compute_package_data')
    descripcion = fields.Text(string="Descripción", compute='_compute_package_data')
    color_code = fields.Char(string="Código color", compute='_compute_package_data')
    cantidad_conos = fields.Integer(related='package_id.cantidad_conos', string="Conos")
    peso_bruto = fields.Float(related='package_id.peso_bruto', string="Peso bruto", digits='Stock Weight')
    peso_neto = fields.Float(related='package_id.peso_neto', string="Peso neto", digits='Stock Weight')
    selected = fields.Boolean(string="Seleccionar")
    to_breakdown = fields.Boolean(string="Desglosar")
    is_new = fields.Boolean(string="Nuevo (desglose)", readonly=True)

    @api.depends('package_id')
    def _compute_package_data(self):
        for line in self:
            # Según la lógica de la empresa un paquete contiene un único producto
            quant = line.package_id.quant_ids[:1]
            template = quant.product_id.product_tmpl_id
            line.location_id = quant.location_id
            line.product_id = quant.product_id
            line.descripcion = template.descripcion
            line.color_code = template.product_color_id.codigo

    @api.onchange('to_breakdown')
    def _onchange_to_breakdown(self):
        # Un paquete a desglosar forma parte de la selección
        if self.to_breakdown:
            self.selected = True
