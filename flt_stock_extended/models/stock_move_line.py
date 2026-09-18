# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from odoo.tools.translate import _


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # Campos bloqueados una vez la línea está validada o cancelada
    FLT_PROTECTED_FIELDS = (
        'peso_bruto', 'peso_neto', 'tara_bolsa', 'tara_cono', 'tara_cono_total',
        'cantidad_conos', 'cono_id', 'package_type_id', 'result_package_id', 'product_id',
    )

    cantidad_conos = fields.Integer(string="Conos")
    cono_id = fields.Many2one('tipo.cono', string='Tipo de Cono')
    package_type_id = fields.Many2one('stock.package.type', string='Tipo de paquete')
    tara_bolsa = fields.Float(string="Tara bolsa", compute='_compute_tara_bolsa', store=True, readonly=False, digits='Stock Weight')
    tara_cono = fields.Float(string="Tara cono unitaria", compute='_compute_tara_cono', store=True, readonly=False, digits='Stock Weight')
    tara_cono_total = fields.Float(string="Tara cono total", compute='_compute_tara_cono', store=True, readonly=False, digits='Stock Weight')
    peso_bruto = fields.Float(string="Peso bruto", digits='Stock Weight')
    peso_neto = fields.Float(string="Peso neto", compute='_compute_peso_neto', store=True, readonly=False, digits='Stock Weight')

    validation_state = fields.Selection([
        ('pending', 'Pendiente'),
        ('validated', 'Validado'),
        ('cancel', 'Cancelado'),
    ], string="Validación", default='pending', required=True, copy=False, index=True, readonly=True)
    validation_user_id = fields.Many2one('res.users', string="Validado por", readonly=True, copy=False)
    validation_date = fields.Datetime(string="Fecha de validación", readonly=True, copy=False)
    package_auto_created = fields.Boolean(string="Paquete creado automáticamente", readonly=True, copy=False)

    @api.depends('package_type_id', 'result_package_id.package_type_id')
    def _compute_tara_bolsa(self):
        for record in self:
            if not record.exists() or record.state == 'done' or record.validation_state != 'pending':
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
            if not record.exists() or record.state == 'done' or record.validation_state != 'pending':
                continue
            if not record.tara_cono and record.cono_id:
                record.tara_cono = record.cono_id.tara_cono or 0.0
            record.tara_cono_total = (record.tara_cono or 0.0) * (record.cantidad_conos or 0)

    @api.depends('peso_bruto', 'tara_bolsa', 'tara_cono', 'cantidad_conos')
    def _compute_peso_neto(self):
        for record in self:
            if not record.exists() or record.state == 'done' or record.validation_state != 'pending':
                continue
            try:
                value = (record.peso_bruto or 0.0) - (record.tara_bolsa or 0.0) - ((record.tara_cono or 0.0) * (record.cantidad_conos or 0))
                record.peso_neto = value
                if value != 0:
                    record.quantity = value
            except Exception:
                continue

    def write(self, vals):
        if not self.env.context.get('flt_bypass_line_lock') and set(vals) & set(self.FLT_PROTECTED_FIELDS):
            bloqueadas = self.filtered(
                lambda l: l.validation_state != 'pending' and l.state not in ('done', 'cancel')
            )
            if bloqueadas:
                raise UserError(_(
                    "No se puede modificar una línea validada o cancelada. "
                    "Use «Reabrir» si necesita corregirla."
                ))
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        # Una línea nueva vuelve a dejar pendiente un movimiento ya validado
        moves = lines.move_id.filtered(
            lambda m: m.state not in ('done', 'cancel') and m.validation_state == 'validated')
        if moves:
            moves._update_validation_state()
        return lines

    def unlink(self):
        moves = self.move_id.filtered(lambda m: m.state not in ('done', 'cancel'))
        res = super().unlink()
        moves.exists()._update_validation_state()
        return res

    def action_duplicar(self):
        for record in self:
            record.copy({
                'result_package_id': False,
                'peso_bruto': 0.0,
                'peso_neto': 0.0,
                'quantity': 0.0,
            })

    # -------------------------------------------------------------------------
    # Validación por línea
    # -------------------------------------------------------------------------
    def action_validate_line(self):
        """Valida la línea: controla la tolerancia del movimiento, crea el
        paquete destino si hace falta y, cuando ya no quedan líneas pendientes,
        valida el movimiento y finalmente el albarán."""
        moves = self.env['stock.move']
        for line in self:
            if line.state in ('done', 'cancel'):
                raise UserError(_("No se puede validar una línea de un traslado ya procesado o cancelado."))
            if line.validation_state == 'validated':
                raise UserError(_("Esta línea ya se encuentra validada."))
            if line.validation_state == 'cancel':
                raise UserError(_("Esta línea está cancelada. Use «Reabrir» para volver a trabajarla."))

            rounding = line.product_uom_id.rounding or 0.01
            if float_compare(line.quantity, 0, precision_rounding=rounding) <= 0:
                raise UserError(_(
                    "No se puede validar la línea del producto '%s' sin cantidad. "
                    "Registre el peso antes de validar."
                ) % line.product_id.display_name)

            line._check_tolerancia_linea()
            line._ensure_result_package()

            line.with_context(flt_bypass_line_lock=True).write({
                'validation_state': 'validated',
                'validation_user_id': self.env.user.id,
                'validation_date': fields.Datetime.now(),
            })
            moves |= line.move_id

        return self._cascade_validation(moves)

    def action_cancel_line(self):
        """Cancela la línea: queda fuera del conteo de validación y no aporta
        cantidad al movimiento."""
        moves = self.env['stock.move']
        for line in self:
            if line.state in ('done', 'cancel'):
                raise UserError(_("No se puede cancelar una línea de un traslado ya procesado o cancelado."))
            if line.validation_state == 'cancel':
                raise UserError(_("Esta línea ya está cancelada."))

            line._release_auto_package()
            line.with_context(flt_bypass_line_lock=True).write({
                'validation_state': 'cancel',
                'validation_user_id': False,
                'validation_date': False,
                'quantity': 0.0,
                'peso_neto': 0.0,
            })
            moves |= line.move_id

        return self._cascade_validation(moves)

    def action_reset_line(self):
        """Devuelve la línea al estado pendiente para poder corregirla."""
        moves = self.env['stock.move']
        for line in self:
            if line.state in ('done', 'cancel'):
                raise UserError(_("No se puede reabrir una línea de un traslado ya procesado o cancelado."))
            if line.validation_state == 'pending':
                continue
            line.with_context(flt_bypass_line_lock=True).write({
                'validation_state': 'pending',
                'validation_user_id': False,
                'validation_date': False,
            })
            moves |= line.move_id

        moves._update_validation_state()
        return True

    def _cascade_validation(self, moves):
        """Propaga la validación: movimiento completo -> albarán completo."""
        pickings = moves._update_validation_state()
        if pickings:
            return pickings.button_validate()
        return True

    def _check_tolerancia_linea(self):
        """La línea no puede validarse si, sumada a las ya validadas del mismo
        movimiento, supera la demanda más la tolerancia."""
        self.ensure_one()
        move = self.move_id
        if not move:
            return
        qty = 0.0
        for ml in move.move_line_ids:
            if ml.validation_state == 'cancel':
                continue
            if ml != self and ml.validation_state != 'validated':
                continue
            if ml.product_uom_id and move.product_uom and ml.product_uom_id != move.product_uom:
                qty += ml.product_uom_id._compute_quantity(ml.quantity, move.product_uom, rounding_method='HALF-UP')
            else:
                qty += ml.quantity
        move._check_tolerancia(qty)

    def _ensure_result_package(self):
        """Crea el paquete destino cuando el usuario no lo indicó, con la
        referencia definitiva para que la etiqueta impresa coincida."""
        self.ensure_one()
        package = self.result_package_id
        if not package:
            vals = {}
            if self.package_type_id:
                vals['package_type_id'] = self.package_type_id.id
            package = self.env['stock.quant.package'].create(vals)
            self.with_context(flt_bypass_line_lock=True).write({
                'result_package_id': package.id,
                'package_auto_created': True,
            })
        elif self.package_type_id and not package.package_type_id:
            package.package_type_id = self.package_type_id
        # El paquete aún no tiene quants: se le fija ya la referencia definitiva
        # para que la etiqueta impresa ahora coincida con el nombre final.
        package._ensure_template_name(self.product_id.product_tmpl_id)
        return package

    def _release_auto_package(self):
        """Elimina el paquete creado automáticamente si todavía está vacío."""
        self.ensure_one()
        package = self.result_package_id
        if not package or not self.package_auto_created:
            return
        self.with_context(flt_bypass_line_lock=True).write({
            'result_package_id': False,
            'package_auto_created': False,
        })
        if not package.quant_ids and not package.pending_move_line_ids:
            package.unlink()

    def action_print_label(self):
        """Imprime la etiqueta ZPL del paquete de la línea."""
        self.ensure_one()
        if not self.result_package_id:
            raise UserError(_("Debe validar la línea antes de imprimir la etiqueta del paquete."))

        report = self.env['ir.actions.report'].search([
            ('report_name', '=', 'stock.label_package_template_view')
        ], limit=1)

        if not report:
            raise UserError(_("No se encontró la acción de informe para la etiqueta del paquete."))

        return report.report_action(self.result_package_id)

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
