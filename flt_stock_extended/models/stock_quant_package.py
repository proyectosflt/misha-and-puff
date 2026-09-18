# -*- coding: utf-8 -*-
from odoo import api, models, fields

class StockQuantPackage(models.Model):
    _inherit = 'stock.quant.package'

    cantidad_conos = fields.Integer(string="Conos", compute='_compute_totals', store=True)
    peso_bruto = fields.Float(string="Peso bruto", compute='_compute_totals', store=True, digits='Stock Weight')
    peso_neto = fields.Float(string="Peso neto", compute='_compute_totals', store=True, digits='Stock Weight')

    pending_move_line_ids = fields.One2many(
        'stock.move.line', 'result_package_id', string="Líneas de operación")

    name = fields.Char(
        string='Package Reference', 
        compute='_compute_dynamic_name', 
        store=True, 
        readonly=False,
        copy=False
    )

    def _next_name_for_template(self, product_tmpl):
        """Siguiente referencia de paquete para una plantilla de producto.

        Se usa tanto por el cálculo almacenado como al crear el paquete desde
        una línea de operación, para que la etiqueta se imprima con la
        referencia definitiva aunque el paquete todavía no tenga quants.
        """
        if not product_tmpl:
            return False

        prefix = str(product_tmpl.id)
        seq_code = f"stock.quant.package.custom.{prefix}"
        sequence_obj = self.env['ir.sequence'].sudo()

        existing_seq = sequence_obj.search([('code', '=', seq_code)], limit=1)

        if not existing_seq:
            existing_seq = sequence_obj.create({
                'name': f"Package Sequence for {prefix}",
                'code': seq_code,
                'implementation': 'standard',
                'padding': 8,
                'number_increment': 1,
                'number_next': 1,
                'use_date_range': False
            })

        return f"{prefix}-{existing_seq.next_by_id()}"

    def _ensure_template_name(self, product_tmpl):
        """Fija la referencia definitiva de un paquete todavía vacío, para que
        la etiqueta impresa antes de validar el traslado no cambie después."""
        self.ensure_one()
        if not product_tmpl or self.quant_ids:
            return
        if self.name and self.name.startswith(f"{product_tmpl.id}-"):
            return
        name = self._next_name_for_template(product_tmpl)
        if name:
            self.name = name

    @api.depends('quant_ids.product_id.product_tmpl_id')
    def _compute_dynamic_name(self):
        for package in self:
            if not package.quant_ids or not package.quant_ids[0].product_id.product_tmpl_id:
                if not package.name:
                    package.name = f"PACK-{str(package.id).zfill(8)}"
                continue
                
            product_tmpl = package.quant_ids[0].product_id.product_tmpl_id
            prefix = str(product_tmpl.id)
            
            if package.name and package.name.startswith(f"{prefix}-"):
                continue

            package.name = self._next_name_for_template(product_tmpl)

    @api.depends('quant_ids.quantity', 'quant_ids.cantidad_conos', 'quant_ids.tara_cono', 'package_type_id.base_weight',
                 'pending_move_line_ids.peso_bruto', 'pending_move_line_ids.peso_neto',
                 'pending_move_line_ids.cantidad_conos', 'pending_move_line_ids.validation_state')
    def _compute_totals(self):
        for package in self:
            if not package.quant_ids:
                # Paquete todavía sin existencias (creado al validar una línea de
                # operación): los totales de la etiqueta salen de esas líneas.
                lines = package.pending_move_line_ids.filtered(
                    lambda l: l.validation_state != 'cancel' and l.state != 'cancel')
                package.cantidad_conos = sum(lines.mapped('cantidad_conos'))
                package.peso_neto = sum(lines.mapped('peso_neto'))
                package.peso_bruto = sum(lines.mapped('peso_bruto'))
                continue

            conos = sum(package.quant_ids.mapped('cantidad_conos'))
            # Net weight is directly the sum of stock quantity in the package
            neto = sum(package.quant_ids.mapped('quantity'))
            
            # Total cone tare for all quants inside
            total_tara_cono = sum(q.cantidad_conos * q.tara_cono for q in package.quant_ids)
            # Bag/Package tare applied once per package
            tara_bolsa = package.package_type_id.base_weight or 0.0
            
            package.cantidad_conos = conos
            package.peso_neto = neto
            package.peso_bruto = neto + total_tara_cono + tara_bolsa
