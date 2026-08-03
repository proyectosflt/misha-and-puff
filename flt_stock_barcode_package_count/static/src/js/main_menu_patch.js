/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import * as MainMenuModule from "@stock_barcode/components/main_menu";

// Detecta el componente correcto del menú principal en Odoo 18
const MainMenu = MainMenuModule.default || MainMenuModule.MainMenu;

if (MainMenu) {
    patch(MainMenu.prototype, {
        openPackageCount() {
            // Ejecutamos la acción con el servicio disponible
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