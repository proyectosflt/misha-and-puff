# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
import csv
import logging
from odoo import models, fields, api
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)
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
    
    tolerancia_compra = fields.Float(
        string='Tolerancia Compra',
        help='Tolerancia para compras'
    )
    tolerancia_venta = fields.Float(
        string='Tolerancia Venta',
        help='Tolerancia para ventas'
    )
    
    fecha_minima_tolerancia_compra = fields.Date(
        string='Fecha de Inicio Tolerancia Compra',
        help='Fecha mínima para la tolerancia de compra'
    )
    
    fecha_minima_tolerancia_venta = fields.Date(
        string='Fecha de Inicio Tolerancia Venta',
        help='Fecha mínima para la tolerancia de venta'
    )
    
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

    @api.depends('product_familia_id', 'product_familia_id.property_ids.sequence', 'product_familia_id.property_ids.property_field', 
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
            
            sorted_properties = record.product_familia_id.property_ids.sorted(key=lambda p: p.sequence)
            
            for prop in sorted_properties:
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


    _CSV_FILENAME = 'product_codificacion.csv'

    _CSV_FIELD_MAP = [
        ('product_rubro_id', 'product.rubro', 3, 4),
        ('product_familia_id', 'product.familia', 5, 6),
        ('product_material_id', 'product.material', 7, 8),
        ('product_detalle_id', 'product.detalle', 9, 10),
        ('product_titulo_id', 'product.title', 11, 12),
        ('product_tenido_id', 'product.tenido', 13, 14),
        ('product_color_id', 'product.color', 15, 16),
        ('product_medida_id', 'product.medida', 17, None),
        ('product_model_id', 'product.model', 18, None),
        ('product_otros_id', 'product.otros', 19, None),
        ('product_talla_id', 'product.talla', 20, None),
        ('product_texto_id', 'product.texto', 21, None),
    ]

    _CSV_PROPERTY_ORDER = [
        'product_rubro_id',
        'product_familia_id',
        'product_material_id',
        'product_detalle_id',
        'product_titulo_id',
        'product_tenido_id',
        'product_color_id',
        'product_medida_id',
        'product_model_id',
        'product_otros_id',
        'product_talla_id',
        'product_texto_id',
    ]

    @staticmethod
    def _csv_value(value):
        return (value or '').strip()

    @staticmethod
    def _csv_code(value):
        return (value or '').strip().strip('-').strip()

    def _csv_cell(self, row, index):
        if index is None or len(row) <= index:
            return ''
        return self._csv_value(row[index])

    def _find_or_create_code_record(self, model_name, name, code, family=False):
        Model = self.env[model_name].sudo()
        clean_name = self._csv_value(name)
        clean_code = self._csv_code(code or name)

        domain = []
        if clean_code and clean_name:
            domain = ['|', ('codigo', '=', clean_code), ('name', '=ilike', clean_name)]
        elif clean_code:
            domain = [('codigo', '=', clean_code)]
        elif clean_name:
            domain = [('name', '=ilike', clean_name)]

        record = Model.search(domain, limit=1) if domain else Model.browse()
        if record:
            values = {}
            if clean_name and record.name != clean_name:
                values['name'] = clean_name
            if clean_code and record.codigo != clean_code:
                values['codigo'] = clean_code
            if family and 'familia_ids' in record._fields and family not in record.familia_ids:
                values['familia_ids'] = [(4, family.id)]
            if values:
                record.write(values)
            return record

        values = {
            'name': clean_name or clean_code,
            'codigo': clean_code or clean_name,
        }
        if family and 'familia_ids' in Model._fields:
            values['familia_ids'] = [(4, family.id)]
        return Model.create(values)

    def _sync_family_property_order(self, family):
        existing = {prop.property_field: prop for prop in family.property_ids}
        for sequence, field_name in enumerate(self._CSV_PROPERTY_ORDER, start=1):
            prop = existing.get(field_name)
            if prop:
                if prop.sequence != sequence:
                    prop.write({'sequence': sequence})
            else:
                self.env['product.familia.property'].sudo().create({
                    'familia_id': family.id,
                    'sequence': sequence,
                    'property_field': field_name,
                })

    def _prepare_codificacion_vals_from_row(self, row):
        family_name = self._csv_cell(row, 5)
        family_code = self._csv_cell(row, 6)
        family = self._find_or_create_code_record('product.familia', family_name, family_code)
        if not family:
            return False

        self._sync_family_property_order(family)

        values = {'product_familia_id': family.id}

        for field_name, model_name, name_index, code_index in self._CSV_FIELD_MAP:
            if field_name == 'product_familia_id':
                continue

            raw_name = self._csv_cell(row, name_index)
            raw_code = self._csv_cell(row, code_index) if code_index is not None else ''

            if not raw_name and not raw_code:
                values[field_name] = False
                continue

            if code_index is None:
                clean_value = self._csv_code(raw_name)
                record = self._find_or_create_code_record(model_name, clean_value, clean_value, family)
            else:
                record = self._find_or_create_code_record(model_name, raw_name, raw_code, family)

            values[field_name] = record.id if record else False

        return values

    @api.model
    def _cron_sync_product_codificacion_from_csv(self):
        csv_path = get_module_resource('flt_stock_extended', 'data', self._CSV_FILENAME)
        if not csv_path:
            _logger.warning('Codificacion CSV not found: %s', self._CSV_FILENAME)
            return

        with open(csv_path, newline='', encoding='utf-8-sig') as csv_file:
            reader = csv.reader(csv_file)
            next(reader, None)

            for row in reader:
                if not row or not any((cell or '').strip() for cell in row):
                    continue

                reference = self._csv_cell(row, 1)
                if not reference:
                    continue

                templates = self.sudo().search([('default_code', '=', reference)])
                if not templates:
                    _logger.info('No product.template found for default_code %s', reference)
                    continue

                values = self._prepare_codificacion_vals_from_row(row)
                if values:
                    templates.write(values)