# Especificación: cotizaciones, pedidos y acceso por roles

- **Estado:** Aprobada formalmente el 22 de noviembre de 2026; autorizada para iniciar la implementación después de cerrar el Gate 0.
- **Alcance:** definir comportamiento de negocio y criterios verificables para la evolución arquitectónica del Cotizador de bordados.
- **Fuente normativa:** este documento contiene las reglas acordadas. Los detalles técnicos de `plan.md` no pueden contradecirlas.
- **Trazabilidad:** los IDs `Q`, `O`, `P`, `A` y `NFR` se enlazan con tareas de `tasks.md` y diseño de `plan.md`.

## Contexto

La aplicación actual es local, está construida con Streamlit y usa SQLite. Hoy cuenta con cotizaciones, clientes, catálogo de diseños, configuración e historial de cotizaciones, pero no cuenta con pedidos ni autenticación. La pantalla del cotizador también realiza varias responsabilidades de aplicación y persistencia.

## Objetivos

1. Añadir pedidos derivados de cotizaciones aceptadas por el cliente, con asignación controlada de cantidades y seguimiento operativo.
2. Preservar el historial de cotizaciones, pedidos, pagos y cambios; no modificar silenciosamente snapshots existentes.
3. Añadir cuentas con roles Administrador y Operador, incluyendo bootstrap seguro del primer administrador.
4. Separar UI, reglas de negocio y persistencia sin romper los flujos existentes.

## Fuera de alcance inicial

- Registro público o autoservicio de usuarios.
- Reescritura completa de la aplicación sin preservar comportamiento.
- Edición retroactiva de cotizaciones ya guardadas: los cambios se hacen en una nueva cotización.

## Requisitos funcionales acordados

### Cotizaciones

- **Q-01 — Duplicación:** el usuario puede crear una cotización nueva copiando una anterior. La nueva cotización recibe un folio nuevo y copia los datos necesarios, incluyendo cliente, diseños, medidas, cantidades, cargos y precios/totales existentes. Cada línea de cada cotización tiene su propio ID único; las líneas copiadas conservan un ID de linaje/origen para relacionarlas con la línea copiada, y las líneas nuevas reciben un nuevo ID de linaje.
- **Q-02 — Precios copiados:** al copiar una cotización, los importes se conservan inicialmente. No se recalculan automáticamente; el recálculo ocurre cuando se solicita expresamente o cuando se modifican datos que lo requieren.
- **Q-03 — Reemplazo e historial:** una cotización anterior se conserva y no se modifica retroactivamente. Al confirmar la creación de una cotización de reemplazo, la anterior se marca cancelada. Todos sus pedidos `Pendientes` que nunca iniciaron producción también se cancelan y liberan sus cantidades. Los pedidos cuyo trabajo ya inició no se cancelan, sin importar si están `En producción`, `Listo para entregar` o `Entregado`; los pedidos `En producción` pueden actualizarse individualmente mediante O-11 cuando la nueva cotización esté aceptada por el cliente.
- **Q-04 — Aceptación:** solo una cotización aceptada por el cliente puede originar pedidos. La aceptación se registra desde el detalle de esa cotización en el Historial de cotizaciones. Un Operador o Administrador registra el medio de aceptación; el sistema guarda fecha/hora y usuario que la registró. Después de guardarla, la acción `Crear pedido` queda disponible. Una cotización cancelada no puede ser aceptada; la operación se rechaza.
- **Q-05 — Cargos compartidos:** los cargos directos registrados una sola vez en la cotización se prorratean entre los pedidos derivados según el subtotal de las piezas asignadas a cada pedido. El prorrateo usa centavos; cualquier diferencia de redondeo se asigna al pedido con mayor subtotal y, si todos los subtotales son cero, se reparte en partes iguales. Cada vez que se crea un pedido parcial, se recalcula y persiste el prorrateo completo de todos los pedidos derivados existentes de esa cotización.

### Pedidos y cantidades

- **O-01 — Pedido por diseño:** un pedido corresponde a un solo diseño/bordado del catálogo y a una cantidad total de piezas de ese diseño; no se desglosa por talla. Una cotización con varios diseños puede originar pedidos separados, uno por cada diseño que el cliente encargue.
- **O-02 — Pedidos parciales por diseño:** se pueden crear varios pedidos para el mismo diseño de una cotización, cada uno con una parte de la cantidad cotizada. Cada pedido conserva su propia cantidad, estado, entregas, pagos e historial.
- **O-03 — Límite e identidad de cantidades:** cada línea de cotización tiene un ID único y un ID de linaje. Al duplicar una cotización, cada línea nueva conserva el ID de linaje de su origen, pero recibe su propio ID único; las líneas añadidas reciben ambos IDs nuevos. La suma comprometida no debe superar la cantidad disponible del linaje en la cotización que origina cada pedido/versión vigente.
- **O-04 — Liberación:** cancelar un pedido antes de iniciar el trabajo libera las cantidades asignadas.
- **O-05 — Snapshot:** los datos aprobados usados por el pedido se conservan como snapshot y no cambian cuando se edita el catálogo o se crea otra cotización.
- **O-06 — Estados:** los estados son `Pendiente`, `En producción`, `Listo para entregar`, `Entregado` y `Cancelado`. El flujo normal es `Pendiente → En producción → Listo para entregar → Entregado`.
- **O-07 — Reapertura y retroceso:** se permiten cambios a estados anteriores y reaperturas desde `Entregado`, pero `Cancelado` es terminal. Antes de guardar se pide confirmación. Cada cambio registra estado anterior/nuevo, usuario y fecha/hora; se requiere motivo al retroceder o reabrir. Las entregas registradas son inmutables: una devolución/ajuste de piezas referencia la entrega original y reduce la cantidad entregada neta; si se vuelven a entregar piezas, se crea otra entrega. Si un pedido iniciado retrocede a `Pendiente`, puede conservar datos operativos y mantiene el bloqueo de cancelación; no se permite edición libre ni cancelación hasta que se haga una actualización autorizada desde una nueva cotización aceptada.
- **O-08 — Cancelación:** un pedido solo se puede cancelar mientras está `Pendiente` y nunca ha iniciado el trabajo. Haber iniciado producción previamente impide cancelarlo aunque luego se retroceda a `Pendiente`.
- **O-09 — Datos operativos:** el pedido registra fecha de inicio de producción, fecha prometida de entrega, fecha de entrega completa y notas internas. La fecha de entrega completa se deriva de la fecha del movimiento que completa todas las piezas; no se edita por separado.
- **O-10 — Entregas parciales:** se permiten varios registros de entrega por pedido. Cada registro guarda fecha y cantidad de piezas del único diseño del pedido. Solo se capturan desde `Listo para entregar`; el pedido pasa a `Entregado` cuando se completa la cantidad pedida neta de ajustes/devoluciones. No se puede entregar más que la cantidad pendiente. Si un ajuste reduce la cantidad entregada neta de un pedido `Entregado`, el pedido cambia automáticamente a `Listo para entregar`.
- **O-11 — Actualización en producción:** para reflejar cambios en un pedido `En producción`, se crea una nueva cotización y el cliente debe aceptarla. Un Administrador autoriza y confirma la actualización. En una sola transacción se mueve la asignación del pedido desde la cotización anterior a la nueva; si las cantidades necesarias no están disponibles, se rechaza la operación sin cambios parciales. No se permite reducir la cantidad del pedido por debajo de las piezas ya entregadas netas; las entregas no se revierten automáticamente. Se conserva la versión previa; la nueva versión contiene un solo diseño y puede tomar de la nueva cotización el diseño, cantidad y precio acordados, siempre que el diseño pertenezca a esa cotización. Mantiene estado y pagos. Si el total nuevo es menor que los pagos netos, se permite la actualización y se muestra el importe pendiente de devolver; la devolución se registra como movimiento cuando se realiza.
- **O-12 — Versionado y auditoría:** cada versión del pedido referencia la cotización que la originó; la versión más reciente es la vigente. La actualización registra que fue autorizada por un Administrador. Los cambios de estado siguen además la auditoría definida en O-07.

### Pagos y devoluciones

- **P-01 — Pagos:** un pedido admite varios pagos o anticipos. Cada movimiento incluye fecha, importe, método (`efectivo`, `transferencia`, `tarjeta` u `otro`) y nota opcional.
- **P-02 — Devoluciones:** las devoluciones son movimientos separados; nunca se elimina ni se sobrescribe el pago original.
- **P-03 — Saldo:** para pedidos activos se calcula el saldo a partir del total vigente menos pagos netos (pagos registrados menos devoluciones realizadas). Si los pagos netos superan el total vigente, se muestra el excedente pendiente de devolver, sin alterar los movimientos originales.
- **P-04 — Pedido cancelado:** no se muestra deuda por el pedido cancelado. Se muestran pagos y devoluciones y el importe neto pendiente de devolver. Esto también aplica cuando un pedido `Pendiente` se cancela al reemplazar su cotización.
- **P-05 — Pago en varios pedidos:** un pago no se distribuye automáticamente entre pedidos. Cada pago se registra de forma independiente en el pedido correspondiente.

### Usuarios y permisos

- **A-01 — Roles:** existen los roles `Administrador` y `Operador`; ambos pueden usar las funciones normales de la aplicación.
- **A-02 — Administración de usuarios:** únicamente un usuario con rol Administrador puede crear cuentas de usuario o desactivarlas. Los Operadores no pueden crear cuentas. La autorización se aplica en el servicio/caso de uso, no solo en la interfaz. No se puede desactivar ni cambiar el rol de la última cuenta Administrador activa.
- **A-03 — Aprobación:** solo un Administrador puede autorizar una actualización de un pedido en producción.
- **A-04 — Sin registro público:** no existe registro abierto de cuentas.
- **A-05 — Bootstrap:** cuando aún no existe ninguna cuenta, un asistente de primer inicio permite crear la primera cuenta Administrador definiendo sus credenciales. No hay usuario ni contraseña predeterminados. El asistente solo está disponible con cero usuarios; la primera cuenta debe crearse localmente antes de exponer la aplicación a otras computadoras.

### Arquitectura y compatibilidad

- **NFR-01 — Separación:** UI Streamlit, reglas/casos de uso y persistencia deben tener responsabilidades separadas.
- **NFR-02 — Autorización efectiva:** permisos y reglas se validan en los servicios/casos de uso, no solo ocultando botones.
- **NFR-03 — Integridad:** las operaciones que asignan o liberan cantidades, crean pedidos o actualizan versiones deben persistir de manera atómica.
- **NFR-04 — Historial:** los registros existentes y sus snapshots deben seguir siendo consultables. Las migraciones no deben borrar ni cambiar datos históricos sin una regla aprobada.
- **NFR-05 — Versionado:** los snapshots persistidos deben poder leerse a través de cambios de contrato.
- **NFR-06 — Seguridad de credenciales:** contraseñas nunca se almacenan en texto claro ni se exponen en logs o snapshots.
- **NFR-07 — Regresión:** los flujos existentes de clientes, diseños, configuración, cotización e historial deben conservar su comportamiento salvo cambios explícitamente especificados.

## Escenarios de aceptación

### AC-01: crear pedido de una cotización aceptada

**Dado** una cotización aceptada con uno o más diseños,
**cuando** un Operador crea pedidos para los diseños encargados,
**entonces** cada pedido contiene exactamente un diseño y una cantidad total de piezas,
**y** se guardan los snapshots y las cantidades disponibles por diseño se actualizan consistentemente.

### AC-01a: aceptar cotización

**Dado** una cotización no aceptada,
**cuando** un Operador o Administrador abre su detalle en el Historial de cotizaciones, registra el medio de aceptación y confirma,
**entonces** se guardan fecha/hora y usuario, la cotización queda aceptada y aparece la acción `Crear pedido`.

### AC-01b: crear pedido sin segunda aprobación

**Dado** una cotización aceptada por el cliente,
**cuando** se crea un pedido desde ella,
**entonces** el pedido inicia en `Pendiente` sin una aprobación adicional del cliente; su estado representa producción/entrega y no aceptación comercial.

### AC-02: impedir exceder cantidades

**Dado** que un diseño cotizado ya tiene cantidades comprometidas en pedidos,
**cuando** se intenta comprometer más que la cantidad restante,
**entonces** la operación se rechaza sin modificar el pedido ni las asignaciones.

### AC-03: cancelar pedido pendiente

**Dado** un pedido `Pendiente` que no ha iniciado el trabajo,
**cuando** se cancela,
**entonces** el pedido queda `Cancelado` y sus cantidades vuelven a estar disponibles.

### AC-04: no cancelar pedido iniciado

**Dado** un pedido en `En producción` o un estado posterior,
**cuando** se intenta cancelarlo,
**entonces** se rechaza la cancelación y se conserva el pedido.

### AC-05: retroceder o reabrir

**Dado** un pedido en cualquier estado salvo `Cancelado`, incluso `Entregado`,
**cuando** un usuario solicita retroceder o reabrir el estado,
**entonces** la aplicación solicita confirmación y solo guarda el cambio si se confirma.

### AC-06: duplicar cotización

**Dado** una cotización existente,
**cuando** se crea una copia,
**entonces** se genera un folio distinto, se conservan inicialmente los valores y snapshots copiados y no se recalculan sin solicitud o edición relevante.

### AC-07: actualizar pedido en producción

**Dado** un pedido `En producción` y una nueva cotización aceptada con cantidades disponibles suficientes,
**cuando** un Administrador autoriza y confirma la actualización,
**entonces** se mueve la asignación en una sola transacción, se conserva la versión anterior, se actualizan diseños/cantidades/precios desde la nueva cotización y se preservan estado y movimientos de pago.
**Y** si no hay cantidades suficientes, no se guarda ningún cambio.
**Y** si el total nuevo es menor que los pagos netos, se muestra el importe pendiente de devolver.

### AC-08: administración de usuarios y permisos

**Dado** un usuario Operador,
**cuando** intenta crear/desactivar cuentas o autorizar una actualización en producción,
**entonces** la operación se rechaza en el servicio aunque se invoque fuera de la interfaz.
**Y dado** un usuario Administrador,
**cuando** crea una cuenta válida,
**entonces** la cuenta se crea con el rol seleccionado y queda disponible para iniciar sesión.

### AC-09: pagos y cancelación

**Dado** un pedido con pagos y devoluciones,
**cuando** se consulta el saldo,
**entonces** el historial de movimientos no se altera; si el pedido está cancelado, no se presenta deuda y se muestra cualquier importe por devolver.

### AC-10: primer administrador

**Dado** una instalación sin cuentas,
**cuando** se ejecuta el asistente de primer inicio,
**entonces** se puede crear el primer Administrador sin credenciales predeterminadas; después, el registro público no está disponible.

### AC-11: entregas parciales

**Dado** un pedido `Listo para entregar` de un diseño específico,
**cuando** se registran varias entregas,
**entonces** cada entrega guarda fecha y cantidad de piezas, ninguna suma neta entregada supera lo pedido y el estado cambia a `Entregado` solo al completar todas las piezas.
**Y** la fecha real de entrega es la fecha del movimiento que completó las piezas y no se modifica manualmente.

### AC-12: reemplazar una cotización

**Dado** una cotización anterior con uno o varios pedidos,
**cuando** el usuario confirma la creación de una cotización de reemplazo,
**entonces** la cotización anterior y todos sus pedidos `Pendientes` que nunca iniciaron producción se cancelan, sus cantidades se liberan y los pagos permanecen registrados con el importe pendiente de devolver si corresponde. Los pedidos que ya iniciaron no se cancelan.
**Y** todos los pedidos cuyo trabajo ya inició, incluidos los estados `En producción`, `Listo para entregar` y `Entregado`, se conservan sin cancelarse.

### AC-13: devolución o ajuste de piezas

**Dado** un pedido con una entrega registrada,
**cuando** el cliente devuelve piezas o se corrige una entrega,
**entonces** se registra un ajuste que referencia la entrega original sin editarla; las piezas vuelven a contar como pendientes y cualquier nueva entrega queda como otro movimiento. Si el ajuste reduce el entregado neto de un pedido `Entregado`, el estado cambia automáticamente a `Listo para entregar`.

### AC-14: pedido de diseño único

**Dado** una cotización aceptada con dos diseños,
**cuando** se generan pedidos,
**entonces** cada pedido contiene solo uno de esos diseños y su cantidad total, sin desglose por talla; se pueden crear varios pedidos para asignar parcialmente la cantidad de un mismo diseño.

### AC-15: último administrador

**Dado** que solo existe un Administrador activo,
**cuando** se intenta desactivarlo o cambiar su rol,
**entonces** la operación se rechaza para mantener siempre al menos un Administrador activo.

### AC-16: pagos y prorrateo por pedidos parciales

**Dado** una cotización con cargos directos y varios pedidos derivados,
**cuando** se registra un pago de la cotización o se crea un pedido parcial adicional,
**entonces** el pago se registra directamente en el pedido correspondiente y no se distribuye automáticamente entre pedidos. Al crear el pedido parcial, el prorrateo completo de cargos se recalcula y persiste para todos los pedidos derivados existentes de esa cotización, usando centavos y el mismo criterio de diferencia de redondeo definido por Q-05.

### AC-17: cotización cancelada y retroceso de pedido iniciado

**Dado** una cotización cancelada,
**cuando** se intenta registrar su aceptación,
**entonces** la operación se rechaza y no se habilita `Crear pedido`.
**Y dado** un pedido iniciado que retrocede a `Pendiente`,
**entonces** conserva su bloqueo de cancelación y no permite edición libre; los cambios posteriores deben pasar por una actualización autorizada desde una nueva cotización aceptada.

### AC-18: ajuste desde Entregado

**Dado** un pedido `Entregado` cuya entrega tiene ajustes que reducen las piezas netas,
**cuando** se confirma el ajuste,
**entonces** el pedido pasa automáticamente a `Listo para entregar` y las piezas pendientes vuelven a estar disponibles para una nueva entrega.
## Decisiones técnicas por documentar en el diseño

Estas no son reglas de negocio pendientes, pero deben diseñarse y probarse antes de migrar:

- Formato de folios de pedidos/versiones, manteniendo unicidad.
- Esquema SQLite concreto para líneas estables, asignaciones, versiones, entregas y auditoría.
- Política técnica de contraseñas/sesión adecuada al modo de ejecución local de Streamlit.
- Tratamiento de idempotencia y rollback para operaciones concurrentes o reintentadas.

## Decisiones de negocio cerradas

- **Pago de varios pedidos:** se mantienen pagos asociados por pedido; no existe distribución automática de un pago único entre pedidos (P-05).
- **Cargos prorrateados con pedidos parciales:** al crear cada pedido parcial se recalcula y persiste el prorrateo completo de todos los pedidos derivados existentes de la cotización (Q-05).
- **Reemplazo con pedidos ya iniciados fuera de `En producción`:** se conservan sin cancelarse todos los pedidos iniciados, estén `En producción`, `Listo para entregar` o `Entregado` (Q-03).
- **Cambio de diseño en actualización:** una actualización `En producción` puede cambiar el pedido a otro diseño incluido en la nueva cotización aceptada (O-11).
- **Retroceso a Pendiente después de iniciar:** el pedido conserva el bloqueo de cancelación y no permite edición libre; cambios posteriores requieren actualización administrativa desde una nueva cotización aceptada (O-07 y O-11).
- **Aceptar cotización cancelada:** se rechaza la aceptación y no se habilita `Crear pedido` (Q-04).
- **Estado tras ajuste de entrega:** si un ajuste reduce el entregado neto de un pedido `Entregado`, el estado cambia automáticamente a `Listo para entregar` (O-10).

## Criterio de aprobación de esta especificación

- El usuario aprueba formalmente los requisitos, decisiones de negocio cerradas y escenarios de aceptación de este documento.
- Cualquier cambio posterior de comportamiento se refleja aquí antes de modificar tareas o código.
- `plan.md` y `tasks.md` permanecen subordinados a esta especificación.
