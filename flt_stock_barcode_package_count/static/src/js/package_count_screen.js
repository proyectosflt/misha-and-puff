/** @odoo-module **/

import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class PackageCountComponent extends Component {
    static template = "stock_barcode_package_count.PackageCountScreen";

    setup() {
        this.rpc = useService("rpc");
        this.action = useService("action");
        this.notification = useService("notification");
        this.barcode = useService("barcode");

        this.inputRef = useRef("searchInput");

        this.state = useState({
            searchQuery: "",
            product: null,
            packages: [],
            loading: false,
        });

        this._onBarcodeScanned = this._onBarcodeScanned.bind(this);

        onMounted(() => {
            if (this.barcode) {
                this.barcode.bus.addEventListener("barcode_scanned", this._onBarcodeScanned);
            }
            if (this.inputRef.el) {
                this.inputRef.el.focus();
            }
        });

        onWillUnmount(() => {
            if (this.barcode) {
                this.barcode.bus.removeEventListener("barcode_scanned", this._onBarcodeScanned);
            }
        });
    }

    get totalPackages() {
        return this.state.packages.length;
    }

    get scannedPackagesCount() {
        return this.state.packages.filter(p => p.scanned).length;
    }

    async _onBarcodeScanned(ev) {
        const barcode = ev.detail ? ev.detail.barcode : ev;
        if (!barcode) return;

        if (!this.state.product) {
            this.state.searchQuery = barcode;
            await this.searchProduct();
        } else {
            this.processPackageScan(barcode);
        }
    }

    async searchProduct() {
        const query = this.state.searchQuery.trim();
        if (!query) return;

        this.state.loading = true;

        try {
            const res = await this.rpc("/web/dataset/call_kw/stock.quant.package/search_packages_by_product", {
                model: "stock.quant.package",
                method: "search_packages_by_product",
                args: [query],
                kwargs: {},
            });

            if (res.error) {
                this.notification.add(res.error, { type: "danger" });
                this.state.loading = false;
                return;
            }

            this.state.product = res.product;
            this.state.packages = res.packages || [];

            if (this.state.packages.length === 0) {
                this.notification.add("El producto no tiene paquetes asignados en inventario.", { type: "warning" });
            }
        } catch (err) {
            this.notification.add("Error al buscar el producto.", { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    processPackageScan(barcode) {
        const cleanBarcode = barcode.trim();
        const pkg = this.state.packages.find(p => p.name === cleanBarcode || p.barcode === cleanBarcode);

        if (pkg) {
            if (pkg.scanned) {
                this.notification.add(`El paquete ${pkg.name} ya fue verificado.`, { type: "info" });
            } else {
                pkg.scanned = true;
                this.notification.add(`Paquete ${pkg.name} verificado OK.`, { type: "success" });
            }
        } else {
            this.notification.add(`El código ${cleanBarcode} no pertenece a ningún paquete de este producto.`, { type: "warning" });
        }
    }

    resetProduct() {
        this.state.product = null;
        this.state.packages = [];
        this.state.searchQuery = "";
        setTimeout(() => {
            if (this.inputRef.el) this.inputRef.el.focus();
        }, 100);
    }

    goBack() {
        this.action.doAction({ type: "ir.actions.client", tag: "reload" });
    }
}

registry.category("actions").add("stock_barcode_package_count_action", PackageCountComponent);