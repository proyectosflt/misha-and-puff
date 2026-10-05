/** @odoo-module **/

import { useExternalListener } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

// Avisa al usuario si intenta salir de un traslado que aún no ha sido validado.
patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        if (this.props.resModel === "stock.picking") {
            // Cierre de pestaña/ventana o recarga: el navegador solo permite su
            // diálogo genérico, no uno personalizado.
            useExternalListener(window, "beforeunload", (ev) => {
                if (this._isUnvalidatedPicking()) {
                    ev.preventDefault();
                    ev.returnValue = "";
                }
            });
        }
    },

    _isUnvalidatedPicking() {
        const record = this.model.root;
        return (
            this.props.resModel === "stock.picking" &&
            !!record.resId &&
            !["done", "cancel"].includes(record.data.state)
        );
    },

    async beforeLeave() {
        // Primero el comportamiento estándar (guardar cambios pendientes)
        const result = await super.beforeLeave(...arguments);
        if (result === false || !this._isUnvalidatedPicking()) {
            return result;
        }

        const record = this.model.root;
        return new Promise((resolve) => {
            this.env.services.dialog.add(
                ConfirmationDialog,
                {
                    title: _t("Traslado sin validar"),
                    body: _t(
                        "El traslado %s aún no ha sido validado. ¿Desea salir de todos modos?",
                        record.data.name
                    ),
                    confirmLabel: _t("Salir de todos modos"),
                    confirm: () => resolve(true),
                    cancelLabel: _t("Quedarse"),
                    cancel: () => resolve(false),
                },
                { onClose: () => resolve(false) }
            );
        });
    },
});
