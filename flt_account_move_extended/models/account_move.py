# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    # This model extension is here for future customizations if needed
    # The main fix is in the view inheritance
    pass
