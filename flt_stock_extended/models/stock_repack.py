# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero

class StockRepack(models.Model):
    _name = 'stock.repack'
    _description = 'Empacado por conteo con corrección de inventario'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    state = fields.Selection([
        ('draft', 'Abierto'),
        ('done', 'Cerrado')
    ], string="Estado", default='draft', required=True, copy=False, tracking=True)

    product_id = fields.Many2one('product.product', required=True, string="Producto")
    descripcion = fields.Text(
            string="Descripción",
            related='product_id.product_tmpl_id.descripcion',
            readonly=True,
        )
    product_titulo_id = fields.Many2one(
            related='product_id.product_tmpl_id.product_titulo_id',
            string="Título",
            readonly=True,
        )
    product_color_id = fields.Many2one(
        related='product_id.product_tmpl_id.product_color_id',
        string="Color",
        readonly=True,
    )
    procuct_color_family_id = fields.Many2one(
        related='product_id.product_tmpl_id.color_family_id',
        string="Familia de color",
        readonly=True,
    )
    product_color_name = fields.Char(
        related='product_id.product_tmpl_id.product_color_id.name',
        string="Nombre color",
        readonly=True,
    )
    location_id = fields.Many2one('stock.location', required=True,
                                   domain=[('usage', '=', 'internal')], string="Ubicación de Origen")
    theoretical_qty = fields.Float(compute='_compute_theoretical_qty',
                                   digits='Stock Weight', string="Stock actual sin empacar")
    cantidad_empacada = fields.Float(compute='_compute_cantidad_empacada',
                                     digits='Stock Weight', string="Cantidad empacada")
    line_ids = fields.One2many('stock.repack.line', 'repack_id', string="Líneas de empaque")
    remaining_qty = fields.Float(compute='_compute_remaining_qty',
                                  digits='Stock Weight', string="Diferencia")

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

    @api.depends('line_ids.peso_neto')
    def _compute_cantidad_empacada(self):
        for w in self:
            w.cantidad_empacada = sum(w.line_ids.mapped('peso_neto'))

    @api.depends('cantidad_empacada', 'theoretical_qty')
    def _compute_remaining_qty(self):
        for w in self:
            w.remaining_qty = w.cantidad_empacada - w.theoretical_qty

    def action_finalizar(self):
        self.ensure_one()

        if self.state == 'done':
            raise UserError("Este registro ya se encuentra cerrado.")

        # Las líneas aplicadas ya se descontaron del stock suelto: solo restan las pendientes
        pending_lines = self.line_ids.filtered(lambda l: not l.is_applied)
        remnant_qty = self.theoretical_qty - sum(pending_lines.mapped('peso_neto'))

        rounding = self.product_id.uom_id.rounding
        if float_compare(remnant_qty, 0.0, precision_rounding=rounding) > 0:
            return {
                'name': 'Confirmar Remanente',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.repack.confirm.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_repack_id': self.id,
                    'default_remaining_qty': remnant_qty,
                }
            }
        
        return self._process_finalization(delete_remanent=True)

    def _get_loose_quants(self):
        self.ensure_one()
        return self.env['stock.quant'].with_context(inventory_mode=True).search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.location_id.id),
            ('package_id', '=', False),
            ('lot_id', '=', False),
            ('owner_id', '=', False),
        ])

    def _apply_quant_adjustment(self, quants):
        # Si devuelve una acción es un asistente y el ajuste no se aplicó
        if quants and quants.action_apply_inventory():
            raise UserError(
                "El ajuste de inventario de %s requiere confirmación manual." % self.product_id.display_name
            )

    def _deduct_loose_stock(self, quantity):
        """Descuenta la cantidad del stock suelto sin bajar de cero y devuelve lo que no se pudo descontar."""
        self.ensure_one()
        rounding = self.product_id.uom_id.rounding
        loose_quants = self._get_loose_quants()
        quants_to_apply = loose_quants.browse()
        pending_qty = quantity

        for loose_quant in loose_quants:
            deduction = min(max(loose_quant.quantity, 0.0), pending_qty)
            if float_is_zero(deduction, precision_rounding=rounding):
                continue
            loose_quant.inventory_quantity = loose_quant.quantity - deduction
            quants_to_apply |= loose_quant
            pending_qty -= deduction

        self._apply_quant_adjustment(quants_to_apply)
        return pending_qty

    def _process_finalization(self, delete_remanent=True):
        self.ensure_one()

        unapplied_lines = self.line_ids.filtered(lambda l: not l.is_applied)
        for line in unapplied_lines:
            line.action_apply_line()

        # Lo empacado ya se descontó al aplicar cada línea: conservar no requiere ajuste
        if delete_remanent:
            loose_quants = self._get_loose_quants()
            for loose_quant in loose_quants:
                loose_quant.cantidad_conos = 0
                loose_quant.tara_cono = 0.0
                loose_quant.inventory_quantity = 0.0
            self._apply_quant_adjustment(loose_quants)

        self.write({'state': 'done'})
        self.message_post(
            body=Markup(f"<p>Se finalizó el empacado por conteo para <b>{self.product_id.display_name}</b> en <b>{self.location_id.display_name}</b>. El registro quedó en estado <b>Cerrado</b>.</p>"),
        )


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
    package_type_id = fields.Many2one('stock.package.type', string="Tipo de bolsa", required=True)
    cono_id = fields.Many2one('tipo.cono', string="Tipo de cono")
    cantidad_conos = fields.Integer(string="Conos")
    peso_bruto = fields.Float(string="Peso bruto", digits='Stock Weight')
    tara_bolsa = fields.Float(compute='_compute_tara_bolsa', readonly=False, store=True, digits='Stock Weight')
    tara_cono = fields.Float(compute='_compute_tara_cono', readonly=False, store=True, digits='Stock Weight')
    tara_cono_total = fields.Float(string="Tara total", compute='_compute_tara_cono_total', store=True, digits='Stock Weight')
    peso_neto = fields.Float(compute='_compute_peso_neto', store=True, digits='Stock Weight',readonly=False)

    package_id = fields.Many2one('stock.quant.package', string="Paquete Creado", readonly=True, copy=False)
    is_applied = fields.Boolean(string="Aplicado", default=False, copy=False)

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

    @api.depends('tara_bolsa', 'tara_cono', 'cantidad_conos')
    def _compute_tara_cono_total(self):
        for line in self:
            line.tara_cono_total = (line.tara_bolsa or 0.0) + (line.tara_cono or 0.0) * (line.cantidad_conos or 0)

    @api.depends('peso_bruto', 'tara_cono_total')
    def _compute_peso_neto(self):
        for line in self:
            line.peso_neto = (line.peso_bruto or 0.0) - (line.tara_cono_total or 0.0)

    def action_apply_line(self):
        for line in self:
            if line.is_applied:
                raise UserError("Esta línea ya ha sido aplicada.")

            if line.repack_id.state == 'done':
                raise UserError("No se pueden aplicar líneas en un registro cerrado.")

            # Una línea copiada sin pesar tiene peso neto negativo y crearía stock negativo
            rounding = line.repack_id.product_id.uom_id.rounding
            if float_compare(line.peso_neto, 0.0, precision_rounding=rounding) <= 0:
                raise UserError("No se puede aplicar una línea con peso neto igual o menor a cero.")

            Quant = self.env['stock.quant'].with_context(inventory_mode=True)

            package = self.env['stock.quant.package'].create({
                'package_type_id': line.package_type_id.id,
            })

            target_location = line.location_id or line.repack_id.location_id

            quant = Quant.create({
                'product_id': line.repack_id.product_id.id,
                'location_id': target_location.id,
                'package_id': package.id,
            })

            quant.write({
                'cantidad_conos': line.cantidad_conos or 0,
                'tara_cono': line.tara_cono or 0.0,
                'inventory_quantity': line.peso_neto,
            })

            line.repack_id._apply_quant_adjustment(quant)
            # Lo empacado sale siempre de la ubicación de origen del registro
            line.repack_id._deduct_loose_stock(line.peso_neto)

            line.write({
                'package_id': package.id,
                'is_applied': True,
            })
            line.repack_id.message_post(
                body=Markup(f"<p>Se aplicó la línea de empaque: <b>{package.name}</b> en <b>{line.location_id.display_name}</b>.</p>"),
            )

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


class StockRepackConfirmWizard(models.TransientModel):
    _name = 'stock.repack.confirm.wizard'
    _description = 'Confirmación de Cantidades Remanentes'

    repack_id = fields.Many2one('stock.repack', required=True)
    remaining_qty = fields.Float(string="Cantidad Restante", digits='Stock Weight', readonly=True)

    def action_confirm_yes(self):
        return self.repack_id._process_finalization(delete_remanent=True)

    def action_confirm_no(self):
        return self.repack_id._process_finalization(delete_remanent=False)