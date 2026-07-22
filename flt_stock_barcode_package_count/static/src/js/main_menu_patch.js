/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MainComponent } from "@stock_barcode/components/main";

patch(MainComponent.prototype, {
    openPackageCount() {
        this.actionService.doAction({
            type: "ir.actions.client",
            tag: "stock_barcode_package_count_action",
            target: "fullscreen",
            name: "Conteo de Paquetes",
        });
    }
});