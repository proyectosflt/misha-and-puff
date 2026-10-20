/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";

const META_MARKER = "\n__FLT_PRODUCT_SEARCH_META__";
const PRODUCT_MODELS = new Set(["product.product", "product.template"]);

patch(Many2XAutocomplete.prototype, {
    search(name) {
        if (!PRODUCT_MODELS.has(this.props.resModel)) {
            return super.search(...arguments);
        }

        return this.orm.call(this.props.resModel, "name_search", [], {
            name,
            operator: "ilike",
            args: this.props.getDomain(),
            limit: this.props.searchLimit + 1,
            context: {
                ...this.props.context,
                _flt_product_search_dropdown: true,
            },
        });
    },

    mapRecordToOption(result) {
        const option = super.mapRecordToOption(...arguments);
        if (!PRODUCT_MODELS.has(this.props.resModel)) {
            return option;
        }

        const markerIndex = result[1].lastIndexOf(META_MARKER);
        if (markerIndex < 0) {
            return option;
        }

        const displayName = result[1].slice(0, markerIndex);
        const metadata = JSON.parse(result[1].slice(markerIndex + META_MARKER.length));
        const previousCode = metadata.codificacion_anterior || "—";
        const templateId = metadata.product_template_id || "—";

        return {
            ...option,
            label: `${displayName} | ${previousCode} | ${templateId}`,
            displayName,
        };
    },
});
