# -*- coding: utf-8 -*-
from odoo import api, models, fields
from odoo.exceptions import UserError

class StockQuant(models.Model):
    _inherit = 'stock.quant'
    
    cantidad_conos = fields.Integer(string="Conos")
    tara_cono = fields.Float(string="Tara cono unitaria", digits='Stock Weight')
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
    paquetes = fields.Integer(
        string="# Paquetes",
        compute='_compute_paquetes',
        store=True,
    )
    peso_bruto = fields.Float(
        string="Cantidad bruto",
        related='package_id.peso_bruto',
        readonly=True,
        digits='Stock Weight',
    )
    agrupacion_total = fields.Char(
        string="Total",
        compute='_compute_agrupacion_total',
        store=True,
    )

    def _compute_agrupacion_total(self):
        for quant in self:
            quant.agrupacion_total = "Total"

    @api.depends('package_id')
    def _compute_paquetes(self):
        for quant in self:
            quant.paquetes = 1 if quant.package_id else 0

    def action_print_label(self):
        self.ensure_one()
        if not self.package_id:
            raise UserError("Debe asignar un paquete antes de imprimir la etiqueta.")

        report = self.env['ir.actions.report'].search([
            ('report_name', '=', 'stock.label_package_template_view')
        ], limit=1)
        if not report:
            raise UserError("No se encontró la acción de informe para la etiqueta del paquete.")

        return report.report_action(self.package_id)

    def _update_available_quantity(self, product_id, location_id, quantity=0, lot_id=None, package_id=None, owner_id=None, in_date=None, **kwargs):
        """Override to retrieve custom fields from context and update quant accordingly"""
        
        cantidad_conos = self.env.context.get('quant_cantidad_conos', 0)
        tara_cono = self.env.context.get('quant_tara_cono', 0.0)
        
        move_line_location_id = self.env.context.get('move_line_location_id')
        move_line_package_id = self.env.context.get('move_line_package_id')
        
        package_id_val = package_id.id if package_id else False
        is_source = (location_id.id == move_line_location_id and package_id_val == move_line_package_id)
        
        if is_source:
            cantidad_conos = -cantidad_conos
        
        res = super(StockQuant, self)._update_available_quantity(product_id, location_id, quantity, lot_id=lot_id, package_id=package_id, owner_id=owner_id, in_date=in_date, **kwargs)
        
        if quantity and ('quant_cantidad_conos' in self.env.context or 'quant_tara_cono' in self.env.context):
            self = self.sudo()
            quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
            if quants:
                quant = quants[0]
                quant.write({
                    'cantidad_conos': quant.cantidad_conos + cantidad_conos,
                    'tara_cono': tara_cono or quant.tara_cono,
                })
        
        return res

    def _get_inventory_fields_create(self):
        inventory_fields_create = super()._get_inventory_fields_create()
        inventory_fields_create += ['cantidad_conos', 'tara_cono']
        return inventory_fields_create
