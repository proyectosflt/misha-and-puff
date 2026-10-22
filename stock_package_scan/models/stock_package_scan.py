# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPackageScan(models.Model):
    _name = 'stock.package.scan'
    _description = 'Escaneo de contenido de paquetes'
    _order = 'id desc'

    name = fields.Char(string='Referencia', default=lambda self: _('Nuevo'), copy=False, readonly=True)
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('in_progress', 'En progreso'),
        ('done', 'Hecho'),
    ], string='Estado', default='draft', required=True, copy=False)

    product_id = fields.Many2one(
        'product.product', string='Producto',
        help="Se identifica al escanear uno de sus paquetes.")
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
    location_id = fields.Many2one(
        'stock.location', string='Limitar a ubicación',
        domain=[('usage', '=', 'internal')],
        help="Opcional. Solo se muestran paquetes dentro de esta ubicación "
             "(y sus sububicaciones).")
    user_id = fields.Many2one(
        'res.users', string='Escaneado por', default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', string='Compañía', default=lambda self: self.env.company, required=True)
    date = fields.Datetime(string='Fecha de escaneo', default=fields.Datetime.now)

    line_ids = fields.One2many(
        'stock.package.scan.line', 'scan_id', string='Líneas de paquete')
    line_count = fields.Integer(string='Paquetes encontrados', compute='_compute_line_stats')
    scanned_count = fields.Integer(string='Paquetes escaneados', compute='_compute_line_stats')
    progress = fields.Float(compute='_compute_line_stats', string='Progreso (%)')

    @api.depends('line_ids.scanned')
    def _compute_line_stats(self):
        for scan in self:
            lines = scan.line_ids
            scan.line_count = len(lines)
            scan.scanned_count = len(lines.filtered('scanned'))
            scan.progress = (scan.scanned_count / scan.line_count * 100.0) if lines else 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nuevo')) == _('Nuevo'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'stock.package.scan') or _('Nuevo')
        return super().create(vals_list)

    def action_open_scanner(self):
        """Reopen this session inside the barcode-style client action."""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'stock_package_scan_client_action',
            'name': self.name,
            'target': 'main',
            'context': {'active_id': self.id},
        }

    def action_done(self):
        for scan in self:
            if scan.scanned_count < scan.line_count:
                raise UserError(_(
                    "%(scanned)s de %(total)s paquetes han sido escaneados. "
                    "Escanee el resto o elimine las líneas que no necesite "
                    "antes de cerrar esta sesión.",
                    scanned=scan.scanned_count, total=scan.line_count))
            scan.state = 'done'

    def action_reset(self):
        self.line_ids.unlink()
        self.write({'state': 'draft', 'product_id': False})

    # ------------------------------------------------------------------
    # Scanning logic — called from the client action for every barcode read
    # ------------------------------------------------------------------
    def process_barcode(self, barcode):
        """Resolve scanned package barcodes and mark listed packages scanned.

        Returns a dict with:
          - 'result': 'success' | 'warning' | 'error'
          - 'message': text for a notification in the UI
        """
        self.ensure_one()
        barcode = (barcode or '').strip()
        if not barcode:
            return {'result': 'error', 'message': _('Código de barras vacío.')}

        # 1) Does it match a package we're already tracking?
        line = self.line_ids.filtered(lambda l: l.package_id.name == barcode)
        if line:
            if line.scanned:
                return {
                    'result': 'warning',
                    'message': _('El paquete %(package)s ya fue escaneado.',
                                package=line.package_id.name),
                }
            line.action_mark_scanned()
            if self.state == 'draft':
                self.state = 'in_progress'
            return {
                'result': 'success',
                'message': _('Paquete %(package)s escaneado (%(done)s/%(total)s).',
                            package=line.package_id.name,
                            done=self.scanned_count, total=self.line_count),
            }

        # A package barcode identifies its product through the stock quants
        # currently held in that package.
        package = self.env['stock.quant.package'].search(
            [('name', '=', barcode)], limit=1)
        if package:
            quants = self.env['stock.quant'].search([
                ('package_id', '=', package.id),
                ('quantity', '>', 0),
                ('location_id.usage', '=', 'internal'),
            ])
            products = quants.product_id
            if len(products) != 1:
                return {
                    'result': 'error',
                    'message': _('No se pudo identificar un único producto en el paquete %(package)s.',
                                package=package.name),
                }

            product = products
            added = self._load_packages_for_product(product)
            scanned_line = self.line_ids.filtered(
                lambda line: line.package_id == package)
            if scanned_line and not scanned_line.scanned:
                scanned_line.action_mark_scanned()
                if self.state == 'draft':
                    self.state = 'in_progress'

            if not added and not scanned_line:
                return {
                    'result': 'warning',
                    'message': _('No se encontraron otros paquetes disponibles para %(product)s.',
                                product=product.display_name),
                }
            return {
                'result': 'success',
                'message': _('%(count)s paquete(s) nuevo(s) añadidos para %(product)s.',
                            count=added,
                            product=product.display_name),
            }

        return {
            'result': 'error',
            'message': _('Código de paquete %(barcode)s no reconocido.', barcode=barcode),
        }

    def _load_packages_for_product(self, product):
        """Add one line per package currently holding `product` that isn't
        already listed. Returns how many lines were added.
        """
        self.ensure_one()
        self.product_id = product.id
        domain = [
            ('product_id', '=', product.id),
            ('package_id', '!=', False),
            ('quantity', '>', 0),
            ('location_id.usage', '=', 'internal'),
        ]
        if self.location_id:
            domain.append(('location_id', 'child_of', self.location_id.id))
        quants = self.env['stock.quant'].search(domain)

        new_packages = quants.package_id - self.line_ids.package_id
        vals_list = [{
            'scan_id': self.id,
            'package_id': package.id,
            'product_qty': package.peso_neto,
        } for package in new_packages]

        if vals_list:
            self.env['stock.package.scan.line'].create(vals_list)
            if self.state == 'draft':
                self.state = 'in_progress'
        return len(vals_list)
