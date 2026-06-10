# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    descripcion = fields.Text(
        string='Descripción',
        help='Descripción del producto'
    )
    
    product_category = fields.Selection([
        ('hilo', 'Hilo'),
        ('avio', 'Avío')
    ], string='Categoría')

    product_rubro_id = fields.Many2one('product.rubro', string='Rubro')
    product_familia_id = fields.Many2one('product.familia', string='Familia')
    product_material_id = fields.Many2one('product.material', string='Material')
    product_detalle_id = fields.Many2one('product.detalle', string='Detalle')
    product_titulo_id = fields.Many2one('product.titulo', string='Título')
    product_type_id = fields.Many2one('product.type', string='Tipo')
    product_model_id = fields.Many2one('product.model', string='Modelo')
    product_tenido_id = fields.Many2one('product.tenido', string='Teñido')
    product_color_id = fields.Many2one('product.color', string='Color')
    product_medida_id = fields.Many2one('product.medida', string='Medida')
    product_texto_id = fields.Many2one('product.texto', string='Texto')
    product_talla_id = fields.Many2one('product.talla', string='Talla')
    product_otros_id = fields.Many2one('product.otros', string='Otros Atributos')
    
    codificacion = fields.Char(
        string='Codificación',
        compute='_compute_codificacion',
        store=True,
        help='Codificación única del producto basada en sus atributos'
    )
    
    @api.depends('product_category', 'product_rubro_id', 'product_familia_id', 'product_material_id', 'product_detalle_id', 'product_titulo_id', 'product_type_id', 'product_model_id', 'product_tenido_id', 'product_color_id', 'product_medida_id', 'product_texto_id', 'product_talla_id', 'product_otros_id')
    def _compute_codificacion(self):
        for record in self:
            if record.product_category == 'hilo':
                record.codificacion = f"{record.product_rubro_id.codigo if record.product_rubro_id else ''}-{record.product_familia_id.codigo if record.product_familia_id else ''}-{record.product_material_id.codigo if record.product_material_id else ''}-{record.product_detalle_id.codigo if record.product_detalle_id else ''}-{record.product_titulo_id.codigo if record.product_titulo_id else ''}-{record.product_tenido_id.codigo if record.product_tenido_id else ''}-{record.product_color_id.codigo if record.product_color_id else ''}-{record.product_otros_id.codigo if record.product_otros_id else ''}"
            elif record.product_category == 'avio':
                record.codificacion = f"{record.product_rubro_id.codigo if record.product_rubro_id else ''}-{record.product_familia_id.codigo if record.product_familia_id else ''}-{record.product_material_id.codigo if record.product_material_id else ''}-{record.product_type_id.codigo if record.product_type_id else ''}-{record.product_model_id.codigo if record.product_model_id else ''}-{record.product_medida_id.codigo if record.product_medida_id else ''}-{record.product_color_id.codigo if record.product_color_id else ''}-{record.product_texto_id.codigo if record.product_texto_id else ''}-{record.product_talla_id.codigo if record.product_talla_id else ''}-{record.product_otros_id.codigo if record.product_otros_id else ''}"
            else:
                record.codificacion = ''

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'uom_id' in vals:
                uom = self.env['uom.uom'].browse(vals['uom_id'])
                if uom.name == 'kg' and vals.get('weight', 0) == 0:
                    vals['weight'] = 1.0
        return super(ProductTemplate, self).create(vals_list)

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        # Trigger recomputation on variants when template is updated
        self.product_variant_ids._compute_studio_fields()
        return res

    @api.onchange('uom_id')
    def _onchange_uom_id_weight(self):
        if self.uom_id.name == 'kg' and self.weight == 0:
            self.weight = 1.0

