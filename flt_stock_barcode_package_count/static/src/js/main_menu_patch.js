/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { registry } from "@web/core/registry";

// En lugar de adivinar la ruta del archivo, obtenemos la clase del menú 
// directamente desde el registro de acciones del cliente de Odoo.
const MainMenu = registry.category("actions").get("stock_barcode_main_menu");

if (MainMenu) {
    patch(MainMenu.prototype, {
        openPackageCount() {
            // Utilizamos el entorno (env) para llamar al servicio de acciones
            this.env.services.action.doAction({
                type: "ir.actions.client",
                tag: "stock_barcode_package_count_action",
                target: "fullscreen",
                name: "Conteo de Paquetes",
            });
        }
    });
} else {
    console.error("No se pudo encontrar el menú principal de Barcode en el registro.");
}