# Escaneo de paquetes

Módulo para Odoo 18 que abre una pantalla de escaneo de códigos de barras:
escanee (o escriba) el código de un paquete para identificar el producto que
contiene y listar todos los paquetes disponibles de ese producto. Después,
escanee cada paquete para marcarlo como completado.

## Requisitos

- Odoo 18. La edición Community es suficiente. El módulo solo depende de
  `stock` y del módulo `stock_barcode`, que proporciona la entrada de
  lectores de códigos de barras en Inventario y Punto de venta. Si Odoo no
  encuentra `stock_barcode`, compruebe su nombre técnico en Aplicaciones.

## Funcionamiento

- `stock.package.scan` representa la sesión y `stock.package.scan.line`
  contiene una línea por paquete.
- Todos los escaneos se procesan desde una única entrada y el método de servidor
  `stock.package.scan.process_barcode()`:
  1. Si el código coincide con un paquete de la lista que aún no se ha
     escaneado, la línea se marca como escaneada.
  2. De lo contrario, se busca el paquete por su campo `name`. El producto se
     identifica a partir de las existencias (`stock.quant`) dentro del paquete;
     se asume que cada paquete contiene un solo producto.
  3. Se añaden los paquetes con existencias positivas en ubicaciones internas
     que contienen ese producto. El paquete que se acaba de escanear se marca
     como escaneado si está dentro del ámbito de ubicación seleccionado.
- Al escanear otro paquete de un producto distinto durante la misma sesión,
  sus paquetes se agregan a la lista existente. Para vaciar la lista, ejecute
  `action_reset()` o inicie una sesión nueva.
- La acción de cliente (`static/src/client_action/`) crea un registro nuevo de
  `stock.package.scan` al abrirse sin `active_id` en el contexto. Al abrirla
  desde el formulario de una sesión guardada mediante el botón «Abrir
  escáner», recibe el `active_id` y reanuda esa sesión.

## Posibles ampliaciones

- Para escanear con la cámara de teléfonos sin un lector externo, consulte
  el servicio de escaneo móvil de códigos de barras de `web` y ofrézcalo como
  alternativa al detector de lectores físicos ya integrado.
- Añada un concepto `picking_type_id` o de almacén si la herramienta debe
  vincularse a un tipo de operación específico.
- Añada sonidos o vibración al escanear, como en la aplicación de códigos de
  barras, mediante la API Web Audio en la acción de cliente.
- Para interpretar nomenclaturas GS1 en lugar de buscar directamente en el
  campo `name` del paquete, procese los escaneos con `barcode.nomenclature`
  antes de `process_barcode`.
- Para mostrar un icono propio en el selector de aplicaciones, añada un
  archivo `icon.png` de 140x130 en `static/description/` y especifique
  `web_icon` en el menú raíz.
