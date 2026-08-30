# Stock Package Scan

A small Odoo 18 module that opens a barcode-app-style screen: scan (or
type) a product's barcode to list every package that currently holds
that product, then scan each package to check it off.

## Requirements

- Odoo 18. Community is enough — this only depends on `stock` and the
  core `barcode` module (the same one behind hardware-scanner input in
  Inventory / POS). No Enterprise `stock_barcode` needed. If `depends`
  fails to find `barcode` on your install, check the exact technical
  name in Apps (it's the small module, not the full Barcode app).

## How it works

- `stock.package.scan` is the session header; `stock.package.scan.line`
  is one row per package.
- Every scan (product or package) goes through one input box and one
  server method, `stock.package.scan.process_barcode()`:
  1. If the barcode matches a package already listed and not yet
     scanned, that line is marked scanned.
  2. Otherwise the barcode is looked up as a product (or a product
     packaging) barcode. Every `stock.quant` for that product with a
     `package_id` set and `quantity > 0` is found, and any package not
     already in the list is added as a new line.
- Packages are matched to a scanned barcode by their `name` field —
  the identifier `stock.quant.package` gets by default from its
  sequence (e.g. `PACK0000123`). If your printed package labels encode
  something else, add a dedicated field on `stock.quant.package` and
  match on that instead in `_find_product_by_barcode`/`process_barcode`.
- Scanning a second product barcode in the same session *adds* its
  packages to the existing list rather than replacing it — handy for
  building a multi-product pick/check list in one pass. Call
  `action_reset()` (or start a new session) to clear it instead.
- The client action (`static/src/client_action/`) creates a new
  `stock.package.scan` record the moment it opens with no `active_id`
  in context — matching the "open it and go" feel of the Barcode app.
  Opening it from a saved record's form (the "Open Scanner" button)
  passes `active_id` and resumes that session instead.

## Extending

- For camera-based scanning on phones without external hardware, look
  at `web`'s mobile barcode scanner service and offer it as a second
  input option alongside the hardware-scanner listener already wired
  up here.
- Add a `picking_type_id` / warehouse concept if this should be tied
  to a specific operation type rather than a free-standing tool.
- Add scan sound/vibration feedback the way the Barcode app does,
  using the Web Audio API inside the client action.
- For GS1/nomenclature-aware parsing instead of a flat `barcode`-field
  match, route scans through `barcode.nomenclature` before
  `_find_product_by_barcode`.
- Drop a 140x130 `icon.png` in `static/description/` and reference it
  with `web_icon` on the root menu for a custom Apps-switcher tile.
