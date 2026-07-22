/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import * as MainModule from "@stock_barcode/components/main";

// Detecta si MainComponent es default export o named export
const MainComponent = MainModule.default || MainModule.MainComponent;

if (MainComponent) {
    patch(MainComponent.prototype, {
        openPackageCount() {
            // Compatibilidad con los nombres del servicio de acciones en Odoo 18
            const actionService = this.actionService || this.action || this.env.services.action;

            actionService.doAction({
                type: "ir.actions.client",
                tag: "stock_barcode_package_count_action",
                target: "fullscreen",
                name: "Conteo de Paquetes",
            });
        }
    });
}