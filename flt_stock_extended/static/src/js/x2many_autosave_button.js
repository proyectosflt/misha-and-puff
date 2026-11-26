/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { pick } from "@web/core/utils/objects";
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

// Clase que se agrega a los botones de línea que deben guardar el registro padre antes de ejecutarse
const AUTOSAVE_CLASS = "o_flt_autosave";

patch(ListRenderer.prototype, {
    /**
     * Devuelve el onClick del botón de línea. Por defecto Odoo bloquea los botones de las
     * líneas nuevas de un x2many con "Primero guarde sus cambios"; para los botones marcados
     * con AUTOSAVE_CLASS se guarda el registro padre y luego se ejecuta el botón.
     */
    fltGetButtonOnClick(record, button) {
        if (!(this.isX2Many && record.isNew)) {
            return "";
        }
        const classes = (button.className || "").split(/\s+/);
        if (classes.includes(AUTOSAVE_CLASS)) {
            return () => this._fltSaveAndExecute(record, button);
        }
        return this.displaySaveNotification.bind(this);
    },

    async _fltSaveAndExecute(record, button) {
        // Evita dobles clics mientras se guarda
        if (this._fltAutosaveRunning) {
            return;
        }
        this._fltAutosaveRunning = true;
        try {
            const list = this.props.list;
            const resModel = list.resModel;
            const index = list.records.indexOf(record);
            const length = list.records.length;
            const root = list.model.root;

            const saved = await root.save();
            if (!saved) {
                // La validación falló: Odoo ya marca los campos inválidos
                return;
            }

            // Tras guardar, el registro puede haber sido reemplazado por uno nuevo al recargar
            let target = record.resId ? record : null;
            if (!target && index >= 0) {
                const newList = this._fltFindStaticList(root, resModel, length);
                target = newList?.records[index]?.resId ? newList.records[index] : null;
            }
            if (!target) {
                this.notificationService.add(
                    _t("Los cambios se guardaron. Vuelva a presionar el botón."),
                    { type: "info" }
                );
                return;
            }

            const resParams = pick(target, "context", "evalContext", "resModel", "resId", "resIds");
            await this.env.onClickViewButton({
                clickParams: button.clickParams,
                getResParams: () => resParams,
            });
        } finally {
            this._fltAutosaveRunning = false;
        }
    },

    /**
     * Busca en los datos del registro raíz la lista x2many del modelo dado.
     */
    _fltFindStaticList(rootRecord, resModel, length) {
        for (const value of Object.values(rootRecord.data || {})) {
            if (
                value &&
                Array.isArray(value.records) &&
                value.resModel === resModel &&
                value.records.length === length
            ) {
                return value;
            }
        }
        return null;
    },
});
