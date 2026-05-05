# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TipoCono(models.Model):
    _name = 'tipo.cono'
    _description = 'Tipo de Cono'

    name = fields.Char(string='Nombre', required=True)
    tara_cono = fields.Float(string='Tara Cono', required=True, default=0.0, digits='Stock Weight')
