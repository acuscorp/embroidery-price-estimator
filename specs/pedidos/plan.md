# Plan técnico: cotizaciones y pedidos

- **Estado:** Propuesta técnica; validar contra `spec.md` antes de implementar.
- **Propósito:** describir límites, contratos e infraestructura que satisfarían los requisitos.

## Límites arquitectónicos propuestos

1. **Presentación (`views/`)**: captura interacción, muestra resultados y solicita confirmación. No contiene reglas de negocio ni SQL.
2. **Casos de uso/servicios (`services/`)**: coordina cotización, pedido, pagos, usuarios y permisos; aplica invariantes antes de persistir.
3. **Dominio y contratos (`models/`)**: tipos, estados, snapshots, movimientos y reglas puras. No depende de Streamlit ni de SQLite.
4. **Persistencia (`repositories/`)**: mapea contratos a SQLite y ejecuta transacciones/migraciones.
5. **Configuración global**: costos y materiales compartidos siguen separados de los cargos directos y snapshots de cada cotización/pedido.

## Agregados y contratos candidatos

Los nombres son propuestas de diseño, no APIs aprobadas.

- `Quote`: folio, estado, referencia opcional a cliente, snapshot de cliente, aceptación registrada (fecha/hora, actor, medio), líneas, cargos por cotización, totales y versión de snapshot.
- `QuoteLine`: identidad persistente de línea, referencia opcional al diseño de catálogo, snapshot del diseño, medidas, cantidades, consumos, costos y precio acordados.
- `Order`: folio, estado, fechas/notas operativas, cotización(es) de origen y versión vigente.
- `OrderVersion`: snapshot completo anterior/nuevo, actor, fecha, cotización fuente y motivo/confirmación si se requiere.
- `Order` contiene exactamente un diseño/bordado y una cantidad total de piezas, sin desglose por talla. Si se divide el trabajo, se crean varios pedidos para el mismo diseño.
- `OrderLine` (si se necesita como relación normalizada) debe tener exactamente una fila por versión del pedido, su propio ID único y referencias a `quote_line_id` (la línea concreta asignada) y `lineage_id` (el linaje compartido al duplicar cotizaciones).
- `Delivery`: fecha y cantidad entregada para el diseño único del pedido; varios registros por pedido.
- `DeliveryAdjustment`: devolución/corrección que referencia un movimiento de entrega y reduce las piezas entregadas netas sin editar el movimiento original.
- `Payment` / `Refund`: movimientos separados, inmutables, fechados y asociados directamente al pedido; no se asignan automáticamente a otros pedidos.
- Cargo directo de cotización: se asigna a pedidos según prorrateo por subtotal. Al crear cada pedido parcial, se recalcula y persiste el prorrateo completo de todos los pedidos derivados existentes de la cotización.
- `User`: identificador, nombre de usuario normalizado, hash de contraseña, rol y estado activo.
- `AuditEvent`: actor, operación, entidad, fecha y referencia a snapshots/versiones cuando sea necesario.
- `Payment` / `Refund`: cada pago se registrará directamente en su pedido. La asignación automática de un pago único a varios pedidos queda fuera del alcance acordado.

## Servicios candidatos

- `QuoteService`: duplicar, registrar aceptación del cliente, cancelar y obtener cotizaciones con sus snapshots.
- `OrderService`: crear pedido desde cotización aceptada, asignar/liberar cantidades, cambiar estado y actualizar desde nueva cotización aceptada.
- `PaymentService`: registrar pagos/devoluciones y calcular saldos sin modificar movimientos.
- `UserService` / `AuthService`: bootstrap, autenticación, cambios de cuentas y verificación de permisos.
- `QuoteCalculator`: cálculo puro que recibe datos de entrada y configuración explícita, sin leer estado global de Streamlit ni escribir en la base.

Los servicios deben aceptar un contexto de actor o una dependencia de autorización; no deben confiar en que la UI haya ocultado la acción. `UserService` solo permite administrar cuentas a un actor Administrador; un Operador no puede crear usuarios, y no se puede desactivar ni cambiar el rol de la última cuenta Administrador activa.

## Persistencia propuesta

- Añadir entidades relacionales para pedido y líneas, versiones, pagos/devoluciones, usuarios y auditoría según se validen las cardinalidades.
- Mantener snapshots JSON versionados para los datos históricos de venta y snapshots de versiones del pedido.
- El snapshot del pedido incluye los datos de cliente usados, líneas/diseños y medidas, cantidades, precios/cargos/totales y datos de cálculo de la cotización. Estado, fechas/notas operativas, entregas y pagos pertenecen al pedido.
- Guardar importes con una representación decimal precisa compatible con SQLite; no depender de operaciones monetarias de punto flotante binario.
- Habilitar claves foráneas en cada conexión SQLite y ejecutar las mutaciones relacionadas dentro de transacciones.
- Mantener migraciones idempotentes, probadas sobre una copia de la base existente; nunca probar migración destructiva directamente sobre la base de trabajo.
- Definir índices/constraints de unicidad para folios, usernames y claves de idempotencia/versionado.

## Flujos técnicos críticos

### Crear pedido

1. Invocar la acción `Crear pedido` disponible en el detalle del Historial solo cuando la cotización esté aceptada.
2. Cargar la cotización y su diseño/línea.
3. Determinar cantidades disponibles para la línea concreta de la cotización fuente; conservar su `lineage_id` para relacionarla con las líneas de cotizaciones duplicadas sin confundir sus IDs únicos.
4. Validar que el pedido corresponda a un solo diseño, tenga cantidad positiva y no supere lo disponible.
5. En una transacción, crear un pedido con snapshot del diseño, cantidad y asignación; su estado inicial es `Pendiente`, sin aprobación adicional.
6. Si cualquier paso falla, rollback de toda la operación.

### Registrar aceptación de cotización

1. Abrir la cotización desde el Historial de cotizaciones y seleccionar `Registrar aceptación del cliente`.
2. Capturar el medio de aceptación y confirmar.
3. Guardar medio, fecha/hora y usuario que registra la aceptación.
4. Rechazar la operación si la cotización está cancelada.
5. Habilitar `Crear pedido` únicamente después de que la cotización quede aceptada.

### Cancelar pedido pendiente

1. Cargar estado actual.
2. Rechazar si ya no está `Pendiente`.
3. En una transacción, marcar cancelación y liberar asignaciones según la regla aprobada. `Cancelado` es terminal; solo se cancelan pedidos que nunca iniciaron producción.
4. Conservar movimientos financieros y snapshots; no borrar registros.

### Reemplazar cotización

1. Solicitar confirmación explícita de que se creará una cotización de reemplazo.
2. En una transacción, crear la copia con folio nuevo y marcar cancelada la cotización anterior.
3. Si la anterior tiene pedidos `Pendientes` que nunca iniciaron producción, cancelar todos y liberar sus cantidades; conservar pagos y mostrar importes pendientes de devolución.
4. Si algún pedido ya inició, no cancelarlo. Mantener los que están `En producción` hasta que una nueva cotización aceptada se use en el flujo de actualización de O-11.
5. Conservar sin cancelarse todos los pedidos iniciados, incluidos los estados `En producción`, `Listo para entregar` y `Entregado`.

### Actualizar pedido en producción

1. Autenticar usuario y verificar rol Administrador en el caso de uso.
2. Cargar pedido de un solo diseño y una nueva cotización aceptada que incluya el diseño/línea destino. Permitir conservar el diseño actual o cambiarlo por otro diseño incluido en la nueva cotización.
3. Mostrar diferencias y consecuencias monetarias antes de confirmar.
4. Revalidar cantidades/estado/permisos al guardar (no confiar en la pantalla previa).
5. En una transacción, validar disponibilidad y que la nueva cantidad no sea menor que las piezas entregadas netas; mover asignaciones desde la cotización anterior a la nueva; guardar versión anterior, aplicar snapshot del diseño, mantener estado/pagos, registrar auditoría y actualizar el excedente pendiente de devolver si lo hay.
6. Si alguna cantidad no está disponible o es menor que lo entregado neto, rechazar la operación completa sin cambios parciales.

### Transición retroactiva a Pendiente

1. Permitir el cambio de estado de un pedido iniciado a `Pendiente` solo con confirmación y motivo.
2. Registrar la transición y conservar la prohibición de cancelación.
3. Bloquear edición libre; las modificaciones posteriores deben pasar por una actualización en producción desde una nueva cotización aceptada y autorización Administrador.

### Registrar entregas parciales

1. Permitir registrar una entrega solo cuando el pedido está `Listo para entregar`.
2. Guardar cada entrega como movimiento con fecha y cantidad del diseño único del pedido.
3. Rechazar cualquier entrega que exceda la cantidad pendiente (cantidad pedida menos entregas netas).
4. Cambiar a `Entregado` solo cuando las cantidades acumuladas entregadas completen la cantidad del pedido.
5. Si un ajuste reduce el entregado neto de un pedido `Entregado`, cambiar automáticamente su estado a `Listo para entregar`.

### Registrar devolución/ajuste de entrega

1. Crear un movimiento que referencia la entrega original y la cantidad devuelta/corregida.
2. No editar ni borrar la entrega original; calcular entregado neto con movimientos.
3. La cantidad devuelta vuelve a estar pendiente de entrega y puede registrarse en una nueva entrega.
4. Si la orden se reabre, conservar las entregas y ajustes; no anularlos automáticamente.

### Bootstrap de usuario

1. El modo bootstrap está disponible solo si no existe ninguna cuenta.
2. El primer administrador se crea desde la ejecución local antes de exponer la app a otras computadoras.
3. Crear el primer Administrador con hash de contraseña seguro y transacción.
4. Una vez creado, exigir autenticación y ocultar/deshabilitar el bootstrap en solicitudes posteriores.
5. No incluir credenciales por defecto ni registro público.
6. Impedir desactivar o cambiar el rol de la última cuenta Administrador activa.

## Migración gradual

1. Añadir tests de caracterización y capturar la línea base.
2. Centralizar conexión/configuración SQLite y activar foreign keys con pruebas.
3. Añadir modelos/servicios nuevos sin reescribir de inmediato la UI completa.
4. Migrar snapshots antiguos mediante adaptadores/versionadores de lectura; escribir el formato nuevo solo donde corresponda.
5. Añadir repositorios y operaciones transaccionales.
6. Integrar autenticación y casos de uso protegidos antes de exponer acciones en UI.
7. Añadir páginas, flujos y regresiones.

## Decisiones técnicas por resolver durante diseño detallado

Las reglas de negocio acordadas están en `spec.md` y las decisiones cerradas incluyen pagos por pedido, recálculo completo de prorrateos al crear pedidos parciales, conservación de pedidos iniciados al reemplazar, cambio de diseño en actualizaciones, bloqueo posterior al retroceso a `Pendiente`, rechazo de aceptación cancelada y retorno automático a `Listo para entregar` tras ajustar una entrega completada. Antes de migrar, documentar formato de folios, esquema SQLite, autenticación/sesiones e idempotencia sin cambiar los requisitos aprobados.
