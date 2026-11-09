/** @odoo-module **/

import { useEffect, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";

// Modelos en los que el total del pie se calcula sobre todos los registros
const TARGET_MODELS = new Set(["product.product"]);
const SUPPORTED_TYPES = new Set(["integer", "float"]);
const formatters = registry.category("formatters");

patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        this.fltOrm = useService("orm");
        // Estado reactivo: clave de la consulta y totales devueltos por el servidor
        this.fltGlobalTotals = useState({ key: null, values: null });

        useEffect(
            (key) => {
                if (key) {
                    this._fltFetchGlobalTotals(key);
                } else if (this.fltGlobalTotals.key !== null) {
                    this.fltGlobalTotals.key = null;
                    this.fltGlobalTotals.values = null;
                }
            },
            () => [this._fltGetGlobalTotalsKey()]
        );
    },

    /**
     * Campos numéricos visibles con atributo sum en la vista.
     */
    _fltGetSumFieldNames() {
        const names = [];
        for (const column of this.allColumns || []) {
            if (column.type !== "field" || !column.attrs?.sum) {
                continue;
            }
            const field = this.fields[column.name];
            if (!field || !SUPPORTED_TYPES.has(field.type)) {
                continue;
            }
            if (
                column.name in this.optionalActiveFields &&
                !this.optionalActiveFields[column.name]
            ) {
                continue;
            }
            names.push(column.name);
        }
        return names;
    },

    /**
     * Clave que identifica la consulta actual; null si no aplica el total global
     * (modelo no objetivo, lista agrupada o todos los registros ya cargados).
     */
    _fltGetGlobalTotalsKey() {
        const list = this.props.list;
        if (!list || !TARGET_MODELS.has(list.resModel) || list.isGrouped) {
            return null;
        }
        if (list.count <= list.records.length) {
            return null;
        }
        const fieldNames = this._fltGetSumFieldNames();
        if (!fieldNames.length) {
            return null;
        }
        return JSON.stringify({
            model: list.resModel,
            domain: list.domain,
            fields: fieldNames,
            count: list.count,
            to_date: list.context?.to_date || false,
            location: list.context?.location || false,
            warehouse_id: list.context?.warehouse_id || false,
        });
    },

    async _fltFetchGlobalTotals(key) {
        if (this.fltGlobalTotals.key === key) {
            return;
        }
        this.fltGlobalTotals.key = key;
        this.fltGlobalTotals.values = null;
        const list = this.props.list;
        try {
            const values = await this.fltOrm.call(
                list.resModel,
                "flt_get_global_totals",
                [list.domain, this._fltGetSumFieldNames()],
                { context: list.context }
            );
            // Se ignora la respuesta si la consulta cambió mientras tanto
            if (this.fltGlobalTotals.key === key) {
                this.fltGlobalTotals.values = values;
            }
        } catch {
            // Si falla, se mantiene el total por página estándar de Odoo
            if (this.fltGlobalTotals.key === key) {
                this.fltGlobalTotals.values = null;
            }
        }
    },

    get aggregates() {
        const aggregates = super.aggregates;
        const state = this.fltGlobalTotals;
        // Con selección activa se respeta la suma de los registros seleccionados
        if (!state?.values || this.props.list.selection?.length) {
            return aggregates;
        }
        if (state.key !== this._fltGetGlobalTotalsKey()) {
            return aggregates;
        }
        for (const column of this.allColumns) {
            const name = column.name;
            if (column.type !== "field" || !(name in state.values) || !(name in aggregates)) {
                continue;
            }
            const field = this.fields[name];
            const formatter =
                formatters.get(column.widget, false) || formatters.get(field.type, false);
            const digits = column.attrs.digits ? JSON.parse(column.attrs.digits) : field.digits;
            const value = state.values[name];
            aggregates[name] = {
                ...aggregates[name],
                help: `${aggregates[name].help || ""} (total global)`.trim(),
                value: formatter ? formatter(value, { digits, escape: true }) : value,
            };
        }
        return aggregates;
    },
});
