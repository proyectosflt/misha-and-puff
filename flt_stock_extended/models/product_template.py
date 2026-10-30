# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
import csv
import logging
from odoo import _, models, fields, api
from odoo.modules.module import get_module_resource
from odoo.osv import expression
from .product_search_utils import format_product_search_result
                        
from collections import defaultdict

_logger = logging.getLogger(__name__)
PLACEHOLDER_NAME = 'Nuevo producto'

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    name = fields.Char(default=PLACEHOLDER_NAME)

    @api.constrains('name')
    def _check_unique_name(self):
        for template in self:
            if not template.name or template.name == PLACEHOLDER_NAME:
                continue
            duplicate = self.sudo().with_context(active_test=False).search([
                ('name', '=', template.name),
                ('id', '!=', template.id),
            ], limit=1)
            if duplicate:
                raise ValidationError(_('El nombre del producto debe ser único.'))
    
    descripcion = fields.Text(
        string='Descripción',
        compute='_compute_descripcion',
        store=True,
        help='Descripción del producto basada en sus atributos; usa el código para el color'
    )

    x_studio_design_name = fields.Char(string='Design Name')
    x_studio_content = fields.Char(string='Content')
    x_studio_percent = fields.Char(string='Percent')
    
    product_familia_id = fields.Many2one('product.familia', string='Familia')
    product_rubro_id = fields.Many2one('product.rubro', string='Rubro', domain="[('familia_ids', 'in', product_familia_id)]")
    product_material_id = fields.Many2one('product.material', string='Material', domain="[('familia_ids', 'in', product_familia_id)]")
    product_detalle_id = fields.Many2one('product.detalle', string='Detalle', domain="[('familia_ids', 'in', product_familia_id)]")
    product_titulo_id = fields.Many2one('product.title', string='Título', domain="[('familia_ids', 'in', product_familia_id)]")
    product_type_id = fields.Many2one('product.type', string='Tipo', domain="[('familia_ids', 'in', product_familia_id)]")
    product_model_id = fields.Many2one('product.model', string='Modelo', domain="[('familia_ids', 'in', product_familia_id)]")
    product_tenido_id = fields.Many2one('product.tenido', string='Teñido', domain="[('familia_ids', 'in', product_familia_id)]")
    product_color_id = fields.Many2one('product.color', string='Color', domain="[('familia_ids', 'in', product_familia_id)]")
    product_color_name = fields.Char(string='Nombre color', related='product_color_id.name', store=True, readonly=True)
    color_family_id = fields.Many2one('color.family', string='Familia de Color', related='product_color_id.color_family_id', store=True, readonly=True)
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
    
    codificacion_anterior = fields.Char(
        string='Codificación Anterior',
        help='Codificación anterior del producto, si existía'
    )
    product_template_id_aux = fields.Integer(string='ID auxiliar', copy=False)
    product_template_id = fields.Integer(string='ID', readonly=True, copy=False, index=True)

    _sql_constraints = [
        ('product_template_id_uniq',
         'UNIQUE(product_template_id)',
         'The product template ID must be unique.'),
    ]

    def _sync_name_with_codificacion(self):
        if self.env.context.get('skip_name_sync'):
            return
        langs = [code for code, _name in self.env['res.lang'].get_installed()]
        for rec in self:
            if not isinstance(rec.id, int) or not rec.codificacion:
                continue
            if any(rec.with_context(lang=l).name != rec.codificacion for l in langs):
                for l in langs:
                    rec.with_context(skip_name_sync=True, lang=l).write({'name': rec.codificacion})
            
    @api.constrains('product_template_id_aux')
    def _check_aux_unique(self):
        for rec in self.filtered('product_template_id_aux'):
            dup = self.with_context(active_test=False).sudo().search_count([
                ('product_template_id_aux', '=', rec.product_template_id_aux),
                ('id', '!=', rec.id),
            ])
            if dup:
                raise ValidationError("Another product already uses this auxiliary ID.")

    @api.model
    def _get_free_product_template_id(self):
        """Smallest positive integer not used as product_template_id."""
        self.flush_model(['product_template_id'])
        self.env.cr.execute("""
            SELECT MIN(c.n)
              FROM (SELECT 1 AS n
                    UNION ALL
                    SELECT product_template_id + 1
                      FROM product_template
                     WHERE product_template_id IS NOT NULL) c
             WHERE NOT EXISTS (SELECT 1 FROM product_template p
                                WHERE p.product_template_id = c.n)
        """)
        return self.env.cr.fetchone()[0]

    def _assign_product_template_id(self):
        Template = self.with_context(active_test=False).sudo()
        # Records with an aux go first so they win against others in the same batch
        for rec in self.sorted(key=lambda r: not r.product_template_id_aux):
            wanted = rec.product_template_id_aux or rec.id
            if rec.product_template_id == wanted:
                continue

            holder = Template.search([
                ('product_template_id', '=', wanted),
                ('id', '!=', rec.id),
            ], limit=1)

            if holder and not (rec.product_template_id_aux and not holder.product_template_id_aux):
                # The holder has priority (or neither has aux and the holder was there first):
                # the current record looks for another value.
                wanted = self._get_free_product_template_id()
            elif holder:
                # The current record has the aux, so the holder moves.
                # Flush before assigning, because the unique constraint is checked immediately.
                holder.product_template_id = self._get_free_product_template_id()
                holder.flush_recordset(['product_template_id'])

            rec.product_template_id = wanted
            rec.flush_recordset(['product_template_id'])

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = list(args or [])
        if not name:
            return super().name_search(name=name, args=args, operator=operator, limit=limit)
        
        domain = [
            '|', '|', '|',
            ('name', operator, name),
            ('default_code', operator, name),
            ('barcode', operator, name),
            ('codificacion_anterior', operator, name),
        ]

        if name.isdigit():
            domain = ['|'] + domain + [('product_template_id', '=', int(name))]

        if args:
            domain = ['&'] + args + domain

        templates = self.search_fetch(
            domain,
            ['display_name', 'codificacion_anterior', 'product_template_id'],
            limit=limit,
        )
        if self.env.context.get('_flt_product_search_dropdown'):
            return [(tmpl.id, format_product_search_result(tmpl)) for tmpl in templates]
        return [(tmpl.id, tmpl.display_name) for tmpl in templates]

    @api.depends('product_familia_id', 'product_familia_id.property_ids.sequence', 'product_familia_id.property_ids.property_field',
                 'product_rubro_id', 'product_rubro_id.codigo',
                 'product_material_id', 'product_material_id.codigo',
                 'product_detalle_id', 'product_detalle_id.codigo',
                 'product_titulo_id', 'product_titulo_id.codigo',
                 'product_type_id', 'product_type_id.codigo',
                 'product_model_id', 'product_model_id.codigo',
                 'product_tenido_id', 'product_tenido_id.codigo',
                 'product_color_id', 'product_color_id.codigo',
                 'product_medida_id', 'product_medida_id.codigo',
                 'product_texto_id', 'product_texto_id.codigo',
                 'product_talla_id', 'product_talla_id.codigo',
                 'product_otros_id', 'product_otros_id.codigo')
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
                    code = (field_value.codigo or '').strip()
                    if code:
                        codes.append(code)

            # if record.id:
            #     codes.append(str(record.id))

            record.codificacion = '-'.join(codes) if codes else ''
        self._sync_name_with_codificacion()

    @api.depends('product_familia_id', 'product_familia_id.property_ids.sequence', 'product_familia_id.property_ids.property_field',
                 'product_familia_id.name',
                 'product_rubro_id', 'product_rubro_id.name',
                 'product_material_id', 'product_material_id.name',
                 'product_detalle_id', 'product_detalle_id.name',
                 'product_titulo_id', 'product_titulo_id.name',
                 'product_type_id', 'product_type_id.name',
                 'product_model_id', 'product_model_id.name',
                 'product_tenido_id', 'product_tenido_id.name',
                 'product_color_id', 'product_color_id.name',
                 'product_color_id.codigo',
                 'product_medida_id', 'product_medida_id.name',
                 'product_texto_id', 'product_texto_id.name',
                 'product_talla_id', 'product_talla_id.name',
                 'product_otros_id', 'product_otros_id.name')
    def _compute_descripcion(self):
        for record in self:
            if not record.product_familia_id or not record.product_familia_id.property_ids:
                record.descripcion = ''
                continue

            names = []
            sorted_properties = record.product_familia_id.property_ids.sorted(key=lambda p: p.sequence)

            for prop in sorted_properties:
                field_value = record[prop.property_field]
                if field_value and hasattr(field_value, 'name'):
                    value = (
                        f'{field_value.codigo} ({field_value.name})'
                        if prop.property_field == 'product_color_id'
                        else field_value.name
                    )
                    value = (value or '').strip()
                    if value:
                        names.append(value)

            record.descripcion = '-'.join(names) if names else ''

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
        records = super(ProductTemplate, self).create(vals_list)
        records._assign_product_template_id()
        records._sync_name_with_codificacion()
        return records

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if 'product_template_id_aux' in vals:
            self._assign_product_template_id()
        # Update name with codificacion whenever attributes change in standard write operations
        self._sync_name_with_codificacion()
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
    
    def _pick_by_stock(self, templates):
        """Return (best_template, {template_id: stock}), ordered by stock desc, then id asc."""
        if len(templates) == 1:
            return templates, {}
        quants = self.env['stock.quant'].sudo().with_context(active_test=False)._read_group(
            [('product_id.product_tmpl_id', 'in', templates.ids),
             ('location_id.usage', '=', 'internal')],
            ['product_id'],
            ['quantity:sum'],
        )
        stock = defaultdict(float)
        for product, qty in quants:
            stock[product.product_tmpl_id.id] += qty
        best = sorted(templates, key=lambda t: (-stock[t.id], t.id))[0]
        return best, dict(stock)

    def _merge_precheck(self, dup, keeper):
        if not keeper.active:
            return False, 'the product holding this codificacion is archived'
        if len(dup.product_variant_ids) != 1 or len(keeper.product_variant_ids) != 1:
            return False, 'more than one variant, merge manually'
        if dup.uom_id != keeper.uom_id:
            return False, 'different unit of measure'
        return True, ''

    def _merge_into(self, dup, keeper):
        """Repoint references from dup to keeper, then delete, else archive, else report."""
        mapping = {
            'product.template': (dup.id, keeper.id),
            'product.product': (dup.product_variant_id.id, keeper.product_variant_id.id),
        }
        skip = {
            'product.template', 'product.product',
            'product.template.attribute.line', 'product.template.attribute.value',
            'product.template.attribute.exclusion',
        }
        problems = []
        for model_name in list(self.env.registry):
            model = self.env[model_name]
            if model._abstract or model._transient or not model._auto or model_name in skip:
                continue
            for field in model._fields.values():
                if (field.type != 'many2one' or not field.store or field.compute
                        or field.related or field.company_dependent):
                    continue
                pair = mapping.get(field.comodel_name)
                if not pair:
                    continue
                old_id, new_id = pair
                try:
                    with self.env.cr.savepoint():
                        self.env.cr.execute(
                            'UPDATE "%s" SET "%s" = %%s WHERE "%s" = %%s'
                            % (model._table, field.name, field.name), (new_id, old_id))
                        if self.env.cr.rowcount:
                            _logger.info('Merge %s -> %s: %s.%s moved %s rows',
                                         dup.id, keeper.id, model_name, field.name,
                                         self.env.cr.rowcount)
                except Exception as e:
                    problems.append('%s.%s: %s' % (model_name, field.name, e))

        self.env.invalidate_all()

        try:
            with self.env.cr.savepoint():
                dup.unlink()
            return 'deleted', problems
        except Exception as e:
            problems.append('delete failed: %s' % e)
        try:
            with self.env.cr.savepoint():
                dup.write({'active': False})
            return 'archived', problems
        except Exception as e:
            problems.append('archive failed: %s' % e)
        return 'failed', problems

    @api.model
    def _cron_sync_product_codificacion_from_csv(self, do_merge=True):
        csv_path = get_module_resource('flt_stock_extended', 'data', self._CSV_FILENAME)
        if not csv_path:
            _logger.warning('Codificacion CSV not found: %s', self._CSV_FILENAME)
            return

        Template = self.sudo().with_context(active_test=False)
        processed = set()
        csv_names = set()
        review = []
        merged_any = False

        def _candidates(csv_name):
            return Template.search([
                ('active', '=', True),
                '|', ('name', '=ilike', csv_name),
                     ('codificacion_anterior', '=ilike', csv_name),
                ('id', 'not in', list(processed)),
            ], order='id')

        with open(csv_path, newline='', encoding='utf-8-sig') as csv_file:
            reader = csv.reader(csv_file)
            next(reader, None)

            for line_no, row in enumerate(reader, start=2):
                if not row or not any((c or '').strip() for c in row):
                    continue
                csv_name = self._csv_cell(row, 1)
                if not csv_name:
                    continue
                csv_names.add(csv_name)

                candidates = _candidates(csv_name)
                if not candidates:
                    _logger.info('Line %s: nothing pending for %r', line_no, csv_name)
                    continue

                migrated = candidates.filtered('codificacion_anterior')
                template, stock = self._pick_by_stock(migrated or candidates)

                code = self._predict_codificacion_from_row(row)
                if '-' not in code:
                    review.append((line_no, csv_name, 'only family code: %s' % code))
                    continue

                holder = Template.search([
                    ('id', '!=', template.id),
                    '|', ('codificacion', '=ilike', code), ('name', '=ilike', code),
                ], order='active desc, id', limit=1)

                if holder:
                    ok, reason = self._merge_precheck(template, holder)
                    if not ok:
                        review.append((line_no, csv_name,
                                       'not merged into template %s: %s' % (holder.id, reason)))
                        continue
                    if not do_merge:
                        _logger.warning('WOULD MERGE line %s: template %s (%r) into %s (%r)',
                                        line_no, template.id, template.name, holder.id, holder.name)
                        continue
                    dup_id, dup_name = template.id, template.name
                    outcome, problems = self._merge_into(template, holder)
                    processed.add(dup_id)
                    merged_any = True
                    _logger.warning('MERGED line %s: template %s (%r) into %s -> %s',
                                    line_no, dup_id, dup_name, holder.id, outcome)
                    if outcome != 'deleted' or problems:
                        review.append((line_no, csv_name,
                                       'merge into %s ended as %s; problems: %s'
                                       % (holder.id, outcome, problems)))
                    continue

                try:
                    with self.env.cr.savepoint():
                        values = self._prepare_codificacion_vals_from_row(row)
                        if not values:
                            continue
                        vals = dict(values)
                        if not template.codificacion_anterior:
                            vals['codificacion_anterior'] = template.name
                        template.write(vals)
                    processed.add(template.id)
                except ValidationError as e:
                    review.append((line_no, csv_name, str(e)))

        if merged_any and hasattr(self.env['stock.quant'], '_merge_quants'):
            self.env['stock.quant'].sudo()._merge_quants()

        for csv_name in csv_names:
            for tmpl in _candidates(csv_name):
                review.append((None, csv_name,
                               'template %s matches this CSV name but was not assigned' % tmpl.id))

        _logger.warning('Codificacion sync: %s items need review', len(review))
        for item in review:
            _logger.warning('REVIEW line %s %r: %s', *item)


    def _predict_codificacion_from_row(self, row):
        parts = []
        for field_name, model_name, name_index, code_index in self._CSV_FIELD_MAP:
            raw_name = self._csv_cell(row, name_index)
            raw_code = self._csv_cell(row, code_index) if code_index is not None else ''
            if not raw_name and not raw_code:
                continue
            code = self._csv_code(raw_code or raw_name)
            if code:
                parts.append(code)
        return '-'.join(parts)

    @api.model
    def _dry_run_codificacion_csv(self):
        csv_path = get_module_resource('flt_stock_extended', 'data', self._CSV_FILENAME)
        if not csv_path:
            _logger.warning('CSV not found')
            return

        current = {}
        for t in self.sudo().with_context(active_test=False).search([]):
            current.setdefault((t.name or '').lower(), []).append(t.id)

        by_code = defaultdict(list)
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader, None)
            for line_no, row in enumerate(reader, start=2):
                if not row or not any((c or '').strip() for c in row):
                    continue
                csv_name = self._csv_cell(row, 1)
                if not csv_name:
                    continue
                code = self._predict_codificacion_from_row(row)
                by_code[code.lower()].append((line_no, csv_name, code))

        # 1) Different rows producing the same codificacion
        for key, items in by_code.items():
            if len(items) > 1:
                _logger.warning('DUPLICATE CODE %r from rows: %s', key, items)

        # 2) Predicted code equals the current name of another template
        for key, items in by_code.items():
            holders = current.get(key, [])
            for line_no, csv_name, code in items:
                others = [i for i in holders if csv_name.lower() != key]
                if others:
                    _logger.warning('NAME CLASH line %s: %r -> %r already used by template ids %s',
                                    line_no, csv_name, code, others)

        # 3) Same source name appearing more than once, or matching several templates
        names = defaultdict(list)
        for items in by_code.values():
            for line_no, csv_name, _code in items:
                names[csv_name.lower()].append(line_no)
        for name, lines in names.items():
            if len(lines) > 1:
                _logger.warning('CSV NAME REPEATED %r on lines %s', name, lines)
            if len(current.get(name, [])) > 1:
                _logger.warning('SOURCE NAME MATCHES SEVERAL TEMPLATES %r ids %s',
                                name, current[name])