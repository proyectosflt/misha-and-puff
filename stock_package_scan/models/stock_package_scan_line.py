# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPackageScanLine(models.Model):
    _name = 'stock.package.scan.line'
    _description = 'Package Content Scan Line'
    _order = 'scanned asc, id asc'

    scan_id = fields.Many2one(
        'stock.package.scan', required=True, ondelete='cascade', index=True)
    package_id = fields.Many2one(
        'stock.quant.package', required=True, string='Package', ondelete='restrict')
    location_id = fields.Many2one(
        related='package_id.location_id', string='Current Location', store=True)
    product_qty = fields.Float(
        string='Qty Found',
        help="Quantity of the searched product that was in this package "
             "when it was added to the list.")
    scanned = fields.Boolean(default=False)
    scanned_date = fields.Datetime()
    scanned_by = fields.Many2one('res.users')

    _sql_constraints = [
        ('scan_package_uniq', 'unique(scan_id, package_id)',
         'A package can only appear once per scan session.'),
    ]

    def action_mark_scanned(self):
        self.write({
            'scanned': True,
            'scanned_date': fields.Datetime.now(),
            'scanned_by': self.env.user.id,
        })

    def action_reset_scanned(self):
        self.write({'scanned': False, 'scanned_date': False, 'scanned_by': False})
