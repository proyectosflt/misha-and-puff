# Copyright © 2026 TugIT. All rights reserved.

from odoo import http
from odoo.http import request
import requests
import base64
import tempfile
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

class ZplLabelController(http.Controller):

    @http.route("/zpl-label-report", type="json", auth="user", csrf=False)
    def render_zpl(self, **kw):
        action = kw.get("action")
        try:
            report_obj = request.env['ir.actions.report'].sudo()
            report_name = action.get('report_name')
            active_ids = action['context'].get('active_ids')
            if not report_name or not active_ids:
                return {'success':False, 'message': "No reports or active records provided."}
            report_id = report_obj.search([('report_name', '=', report_name)], limit=1)
            if report_id.report_type == 'qweb-text':
                zpl_command = report_obj._render_qweb_text(report_name, active_ids, data=action.get('data'))[0]
                config = request.env["ir.config_parameter"].sudo()
                skip = config.get_param("qz_tray.skip_modal") == "True"
                printer = config.get_param("qz_tray.default_printer") or ""
                return {'success':True, 'zpl_command': zpl_command, 'skip_modal': skip, 'default_printer': printer}
            else:
                return {'success':False, 'message': "The report is not for ZPL."}
        except Exception as e:
            return {'success':False, 'message': f'Error in ZPL Label Report: {str(e)}'}

class QzSigningController(http.Controller):
    @http.route("/qz-certificate", auth="public", csrf=False)
    def qz_certificate(self, **kwargs):
        config_param = request.env["ir.config_parameter"].sudo()
        cert = config_param.get_param("qz.certificate", default=False)
        return request.make_response(cert, [("Content-Type", "text/plain")])

    @http.route("/qz-sign-message", auth="public", csrf=False)
    def qz_sign_message(self, **kwargs):
        config_param = request.env["ir.config_parameter"].sudo()
        key_pem = config_param.get_param("qz.key", default=False)
        private_key = serialization.load_pem_private_key(
            key_pem.encode("utf-8"), password=None, backend=default_backend()
        )
        message = kwargs.get("request", "").encode("utf-8")
        signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA512())
        return request.make_response(base64.b64encode(signature), [("Content-Type", "text/plain")])