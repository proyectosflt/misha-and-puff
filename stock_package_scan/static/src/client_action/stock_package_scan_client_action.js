/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef, onWillStart, onMounted, onWillUnmount } from "@odoo/owl";

export class StockPackageScanClientAction extends Component {
    static template = "stock_package_scan.ClientAction";
    static props = ["*"];

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        // "barcode" is the service the core `barcode` module registers to
        // turn hardware-scanner keystrokes into `barcode_scanned` events.
        this.barcodeService = useService("barcode");
        this.inputRef = useRef("barcodeInput");

        this.state = useState({
            scanId: null,
            name: "",
            productName: "",
            lines: [],
            scannedCount: 0,
            lineCount: 0,
            manualValue: "",
            isLoading: true,
        });

        onWillStart(() => this.initSession());

        onMounted(() => {
            this.barcodeService.bus.addEventListener("barcode_scanned", this.onBarcodeScanned);
            this.focusInput();
        });

        onWillUnmount(() => {
            this.barcodeService.bus.removeEventListener("barcode_scanned", this.onBarcodeScanned);
        });
    }

    focusInput() {
        this.inputRef.el?.focus();
    }

    async initSession() {
        const activeId = this.props.action.context.active_id;
        if (activeId) {
            this.state.scanId = activeId;
        } else {
            const [newId] = await this.orm.create("stock.package.scan", [{}]);
            this.state.scanId = newId;
        }
        await this.refresh();
        this.state.isLoading = false;
    }

    onBarcodeScanned = (ev) => {
        this.submitBarcode(ev.detail.barcode);
    };

    async onManualKeydown(ev) {
        if (ev.key === "Enter" && this.state.manualValue.trim()) {
            await this.submitBarcode(this.state.manualValue.trim());
            this.state.manualValue = "";
        }
    }

    async submitBarcode(barcode) {
        try {
            const result = await this.orm.call(
                "stock.package.scan",
                "process_barcode",
                [[this.state.scanId], barcode]
            );
            this.notification.add(result.message, {
                type: result.result === "error" ? "danger" : result.result,
            });
            await this.refresh();
        } catch (error) {
            this.notification.add(error.data?.message || error.message, { type: "danger" });
        } finally {
            this.focusInput();
        }
    }

    async refresh() {
        const [scan] = await this.orm.read(
            "stock.package.scan",
            [this.state.scanId],
            ["name", "product_id", "scanned_count", "line_count"]
        );
        this.state.name = scan.name;
        this.state.productName = scan.product_id ? scan.product_id[1] : "";
        this.state.scannedCount = scan.scanned_count;
        this.state.lineCount = scan.line_count;
        this.state.lines = await this.orm.searchRead(
            "stock.package.scan.line",
            [["scan_id", "=", this.state.scanId]],
            ["package_id", "location_id", "product_qty", "scanned"],
            { order: "scanned asc, id asc" }
        );
    }

    async onLineClick(line) {
        // Fallback for testing without a physical scanner: tap a line to
        // check it off directly instead of typing its barcode.
        if (line.scanned) {
            return;
        }
        await this.orm.call("stock.package.scan.line", "action_mark_scanned", [[line.id]]);
        await this.refresh();
    }
}

registry.category("actions").add("stock_package_scan_client_action", StockPackageScanClientAction);
