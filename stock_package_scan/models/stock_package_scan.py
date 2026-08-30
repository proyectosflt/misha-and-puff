# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPackageScan(models.Model):
    _name = 'stock.package.scan'
    _description = 'Package Content Scan'
    _order = 'id desc'

    name = fields.Char(default=lambda self: _('New'), copy=False, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], default='draft', required=True, copy=False)

    product_id = fields.Many2one(
        'product.product', string='Last Product Searched',
        help="Every time a product barcode is scanned, the packages that "
             "hold it are appended to the lines below. Scanning a second "
             "product adds to the same list instead of replacing it.")
    location_id = fields.Many2one(
        'stock.location', string='Limit To Location',
        domain=[('usage', '=', 'internal')],
        help="Optional. Only packages inside this location (and its "
             "sub-locations) are proposed when a product is searched.")
    user_id = fields.Many2one(
        'res.users', string='Scanned By', default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.company, required=True)
    date = fields.Datetime(default=fields.Datetime.now)

    line_ids = fields.One2many(
        'stock.package.scan.line', 'scan_id', string='Package Lines')
    line_count = fields.Integer(compute='_compute_line_stats')
    scanned_count = fields.Integer(compute='_compute_line_stats')
    progress = fields.Float(compute='_compute_line_stats', string='Progress (%)')

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
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'stock.package.scan') or _('New')
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
                    "%(scanned)s of %(total)s packages have been scanned. "
                    "Scan the rest, or remove the lines you don't need, "
                    "before closing this session.",
                    scanned=scan.scanned_count, total=scan.line_count))
            scan.state = 'done'

    def action_reset(self):
        self.line_ids.unlink()
        self.write({'state': 'draft', 'product_id': False})

    # ------------------------------------------------------------------
    # Scanning logic — called from the client action for every barcode read
    # ------------------------------------------------------------------
    def process_barcode(self, barcode):
        """Single entry point for the scanner UI. Works out whether the
        scanned barcode is a package line waiting to be checked off, or a
        product to search for, and acts accordingly.

        Returns a dict with:
          - 'result': 'success' | 'warning' | 'error'
          - 'message': text for a notification in the UI
        """
        self.ensure_one()
        barcode = (barcode or '').strip()
        if not barcode:
            return {'result': 'error', 'message': _("Empty barcode.")}

        # 1) Does it match a package we're already tracking?
        line = self.line_ids.filtered(lambda l: l.package_id.name == barcode)
        if line:
            if line.scanned:
                return {
                    'result': 'warning',
                    'message': _("Package %(package)s was already scanned.",
                                  package=line.package_id.name),
                }
            line.action_mark_scanned()
            if self.state == 'draft':
                self.state = 'in_progress'
            return {
                'result': 'success',
                'message': _("Package %(package)s scanned (%(done)s/%(total)s).",
                              package=line.package_id.name,
                              done=self.scanned_count, total=self.line_count),
            }

        # 2) Otherwise, try to resolve it as a product (or packaging) barcode
        product = self._find_product_by_barcode(barcode)
        if product:
            added = self._load_packages_for_product(product)
            if not added:
                return {
                    'result': 'warning',
                    'message': _("No packages found holding %(product)s.",
                                  product=product.display_name),
                }
            return {
                'result': 'success',
                'message': _("%(count)s package(s) added for %(product)s.",
                              count=added, product=product.display_name),
            }

        return {
            'result': 'error',
            'message': _("Barcode %(barcode)s not recognized.", barcode=barcode),
        }

    def _find_product_by_barcode(self, barcode):
        self.ensure_one()
        product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)
        if product:
            return product
        # Fallback: a case/pallet packaging barcode rather than the unit barcode
        packaging = self.env['product.packaging'].search([('barcode', '=', barcode)], limit=1)
        return packaging.product_id if packaging else self.env['product.product']

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
            'product_qty': sum(quants.filtered(lambda q: q.package_id == package).mapped('quantity')),
        } for package in new_packages]

        if vals_list:
            self.env['stock.package.scan.line'].create(vals_list)
            if self.state == 'draft':
                self.state = 'in_progress'
        return len(vals_list)
