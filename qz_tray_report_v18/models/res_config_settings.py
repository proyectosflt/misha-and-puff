# qz_tray_report_v18/models/res_config_settings.py
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    qz_skip_modal = fields.Boolean(
        string="Omitir ventana de diálogo QZ Tray",
        config_parameter="qz_tray.skip_modal",
    )
    qz_default_printer = fields.Char(
        string="Impresora por defecto",
        config_parameter="qz_tray.default_printer",
    )