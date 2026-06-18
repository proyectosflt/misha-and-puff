# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    descripcion = fields.Text(
        string='Descripción',
        help='Descripción del producto'
    )
    
    product_familia_id = fields.Many2one('product.familia', string='Familia')
    product_rubro_id = fields.Many2one('product.rubro', string='Rubro', domain="[('familia_ids', 'in', product_familia_id)]")
    product_material_id = fields.Many2one('product.material', string='Material', domain="[('familia_ids', 'in', product_familia_id)]")
    product_detalle_id = fields.Many2one('product.detalle', string='Detalle', domain="[('familia_ids', 'in', product_familia_id)]")
    product_titulo_id = fields.Many2one('product.title', string='Título', domain="[('familia_ids', 'in', product_familia_id)]")
    product_type_id = fields.Many2one('product.type', string='Tipo', domain="[('familia_ids', 'in', product_familia_id)]")
    product_model_id = fields.Many2one('product.model', string='Modelo', domain="[('familia_ids', 'in', product_familia_id)]")
    product_tenido_id = fields.Many2one('product.tenido', string='Teñido', domain="[('familia_ids', 'in', product_familia_id)]")
    product_color_id = fields.Many2one('product.color', string='Color', domain="[('familia_ids', 'in', product_familia_id)]")
    product_medida_id = fields.Many2one('product.medida', string='Medida', domain="[('familia_ids', 'in', product_familia_id)]")
    product_texto_id = fields.Many2one('product.texto', string='Texto', domain="[('familia_ids', 'in', product_familia_id)]")
    product_talla_id = fields.Many2one('product.talla', string='Talla', domain="[('familia_ids', 'in', product_familia_id)]")
    product_otros_id = fields.Many2one('product.otros', string='Otros Atributos', domain="[('familia_ids', 'in', product_familia_id)]")
    
    show_rubro = fields.Boolean(compute='_compute_attribute_visibility')
    show_material = fields.Boolean(compute='_compute_attribute_visibility')
    show_detalle = fields.Boolean(compute='_compute_attribute_visibility')
    show_titulo = fields.Boolean(compute='_compute_attribute_visibility')
    show_type = fields.Boolean(compute='_compute_attribute_visibility')
    show_model = fields.Boolean(compute='_compute_attribute_visibility')
    show_tenido = fields.Boolean(compute='_compute_attribute_visibility')
    show_color = fields.Boolean(compute='_compute_attribute_visibility')
    show_medida = fields.Boolean(compute='_compute_attribute_visibility')
    show_texto = fields.Boolean(compute='_compute_attribute_visibility')
    show_talla = fields.Boolean(compute='_compute_attribute_visibility')
    show_otros = fields.Boolean(compute='_compute_attribute_visibility')
    
    codificacion = fields.Char(
    string='Codificación',
    compute='_compute_codificacion',
    store=True,
    help='Codificación única del producto basada en sus atributos'
    )

    @api.depends('product_familia_id', 'product_familia_id.property_ids', 
                 'product_rubro_id', 'product_material_id', 'product_detalle_id', 
                 'product_titulo_id', 'product_type_id', 'product_model_id', 
                 'product_tenido_id', 'product_color_id', 'product_medida_id', 
                 'product_texto_id', 'product_talla_id', 'product_otros_id')
    def _compute_codificacion(self):
        for record in self:
            if not record.product_familia_id or not record.product_familia_id.property_ids:
                record.codificacion = ''
                continue
            
            codes = []
            if record.product_familia_id.codigo:
                codes.append(record.product_familia_id.codigo)
            for prop in record.product_familia_id.property_ids:
                field_value = record[prop.property_field]
                if field_value and hasattr(field_value, 'codigo'):
                    codes.append(field_value.codigo or '')
                else:
                    codes.append('')
            
            record.codificacion = '-'.join(codes)

    @api.depends('product_familia_id')
    def _compute_attribute_visibility(self):
        for record in self:
            familia_id = record.product_familia_id.id
            if not familia_id:
                record.show_rubro = False
                record.show_material = False
                record.show_detalle = False
                record.show_titulo = False
                record.show_type = False
                record.show_model = False
                record.show_tenido = False
                record.show_color = False
                record.show_medida = False
                record.show_texto = False
                record.show_talla = False
                record.show_otros = False
                continue
            
            record.show_rubro = self.env['product.rubro'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0
            record.show_material = self.env['product.material'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0
            record.show_detalle = self.env['product.detalle'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0
            record.show_titulo = self.env['product.title'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0
            record.show_type = self.env['product.type'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0
            record.show_model = self.env['product.model'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0
            record.show_tenido = self.env['product.tenido'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0
            record.show_color = self.env['product.color'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0
            record.show_medida = self.env['product.medida'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0
            record.show_texto = self.env['product.texto'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0
            record.show_talla = self.env['product.talla'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0
            record.show_otros = self.env['product.otros'].search_count([('familia_ids', 'in', familia_id)], limit=1) > 0


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

