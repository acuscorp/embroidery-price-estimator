# Handoff: arquitectura de cotizaciones y pedidos

## Ruta SDD vigente

Se reorganizó el trabajo en un flujo de Spec-Driven Development. La fuente normativa y el orden de continuación son:

1. [`specs/pedidos/spec.md`](./specs/pedidos/spec.md): reglas de negocio y criterios de aceptación acordados; revisar y aprobar formalmente antes de implementar.
2. [`specs/pedidos/plan.md`](./specs/pedidos/plan.md): propuesta de arquitectura y migración, subordinada a la especificación.
3. [`specs/pedidos/tasks.md`](./specs/pedidos/tasks.md): tareas trazables a requisitos. Todas están pendientes; empezar implementación solo después de cerrar el Gate 0.
4. Implementar tarea por tarea, actualizar su estado y verificar los criterios/tests antes de marcarla terminada.

`PLAN_IMPLEMENTACION.md` conserva la hoja de ruta de fases a alto nivel. Si sus detalles duplicados difieren de `spec.md`, prevalece la especificación; si hay conflicto entre diseño propuesto y requisito, prevalece `spec.md`.

## Objetivo

La especificación fue aprobada formalmente el 22 de noviembre de 2026. Continuar desde el Gate 0 y después refactorizar el Cotizador de bordados para separar responsabilidades, definir contratos claros e incorporar el flujo de pedidos y autenticación por roles. Este documento resume las decisiones acordadas y la ruta de implementación; no significa que el trabajo ya esté implementado.

## Estado al crear este handoff

- Proyecto: aplicación local de Streamlit con persistencia SQLite.
- La raíz del repositorio estaba limpia al revisar el estado de Git.
- No se modificó código ni la base de datos durante la definición de estas reglas.
- La aplicación todavía no tiene entidad, persistencia, pantalla ni flujo de pedidos.
- La aplicación todavía no tiene inicio de sesión ni roles.
- El historial actual es una vista de cotizaciones; el cotizador es una pantalla/caso de uso.
- Línea base: 23 pruebas unittest pasan y la compilación principal no reporta errores. SQLite contiene las tablas `clientes`, `configuracion_app`, `cotizaciones`, `diseno_consecutivos`, `diseno_imagenes`, `diseno_subcategorias` y `disenos`; las claves foráneas están desactivadas por defecto.
- Los hallazgos de arquitectura de la revisión anterior se conservan en el checkpoint `004-especificando-el-objeto-pedido.md` de la sesión.

## Decisiones de negocio acordadas

### Cotizaciones

- Una cotización aceptada por el cliente puede originar varios pedidos; la aceptación registra fecha/hora, usuario que la registró y medio.
- Se puede crear una cotización nueva copiando los datos de una anterior para evitar volver a capturarlos.
- La nueva cotización recibe un folio nuevo y copia los datos necesarios, incluyendo cliente, diseños, medidas, cantidades, cargos y precios/totales históricos.
- Al crear una copia, los valores copiados no se recalculan automáticamente. Se recalculan solo si el usuario lo solicita o modifica datos que requieran recálculo.
- Al confirmar la creación de una cotización de reemplazo, la anterior se marca cancelada y se conserva en el historial; nunca se borra ni se edita retroactivamente.

### Pedidos y cantidades

- La aceptación del cliente se registra en el detalle de la cotización dentro de Historial de cotizaciones. Un Operador o Administrador captura el medio; el sistema guarda fecha/hora y usuario. Después se habilita `Crear pedido`. Una cotización cancelada no puede ser aceptada.
- No hay aprobación adicional del pedido por el cliente: los pedidos se crean en estado `Pendiente`, que inicia el flujo operativo.
- Cada pedido corresponde a un único diseño/bordado y una cantidad total de piezas, sin desglose por talla. Una cotización con varios diseños puede generar pedidos separados; la cantidad de un diseño se puede dividir entre varios pedidos.
- Los pedidos pueden dividir una cotización. Cada línea de cotización tiene un ID único; al duplicarla, la línea copiada conserva el ID de linaje/origen, no su ID único. Las cantidades asignadas no pueden superar lo disponible para la línea concreta de la cotización fuente.
- Cancelar un pedido antes de iniciar el trabajo libera las cantidades asignadas para que puedan usarse en otro pedido.
- Un pedido guarda los datos aprobados como snapshot, de modo que cambios posteriores al catálogo o a la cotización no alteren su historial.
- Al confirmar el reemplazo, la cotización anterior se cancela. Todos sus pedidos `Pendientes` que nunca iniciaron producción también se cancelan y liberan cantidades.
- Los pedidos iniciados no se cancelan al reemplazar la cotización, sin importar si están `En producción`, `Listo para entregar` o `Entregado`. Los pedidos `En producción` se pueden actualizar desde una nueva cotización aceptada, con autorización y confirmación de un Administrador.
- La asignación se mueve atómicamente a la nueva cotización y se rechaza si no hay cantidades disponibles suficientes o si la nueva cantidad queda debajo de lo ya entregado neto. La actualización puede conservar el diseño o cambiarlo por otro diseño incluido en la nueva cotización.
- Cada versión del pedido referencia la cotización que la originó. La actualización conserva versiones, estado y pagos. Si el total nuevo es menor que los pagos netos, se muestra el importe pendiente de devolver; se registra la devolución cuando se realiza.

### Estados y operación

- Estados: `Pendiente`, `En producción`, `Listo para entregar`, `Entregado` y `Cancelado`.
- El flujo normal avanza: `Pendiente → En producción → Listo para entregar → Entregado`.
- Se permiten retrocesos o reaperturas desde `Entregado`, pero `Cancelado` es terminal; siempre se pide confirmación.
- Cada cambio de estado registra estado anterior/nuevo, usuario y fecha/hora; los retrocesos y reaperturas requieren motivo.
- Cancelar un pedido solo está permitido mientras está `Pendiente` y nunca ha iniciado producción, aunque su estado se haya retrocedido.
- Si un pedido iniciado retrocede a `Pendiente`, conserva el bloqueo de cancelación y no permite edición libre; cambios posteriores requieren actualización administrativa desde una nueva cotización aceptada.
- Datos operativos del pedido: fecha de inicio de producción, fecha prometida de entrega, fecha de entrega completa (derivada) y notas internas.
- Se permiten entregas parciales desde `Listo para entregar`, con fecha y cantidad de piezas. Ajustes/devoluciones de piezas referencian la entrega y no la alteran; las piezas vuelven a quedar pendientes. El pedido pasa a `Entregado` cuando se completan todas las cantidades netas. Si un ajuste reduce el entregado neto de un pedido `Entregado`, el estado vuelve automáticamente a `Listo para entregar`.

### Pagos y devoluciones

- Los pagos se registran como movimientos asociados al pedido con fecha, importe, método (efectivo, transferencia, tarjeta u otro) y nota opcional.
- Se pueden registrar varios pagos o anticipos.
- Las devoluciones se registran como movimientos separados; no se borra ni modifica el pago original.
- Los pagos se registran directamente en el pedido correspondiente; no existe distribución automática de un pago único entre varios pedidos.
- Los cargos directos únicos de la cotización se prorratean entre pedidos de acuerdo con su subtotal. Al crear un pedido parcial adicional, se recalcula y persiste el prorrateo completo de todos los pedidos derivados existentes de esa cotización.
- En un pedido cancelado no se muestra deuda por el pedido. Se muestran los pagos y devoluciones registrados y se señala si queda dinero por devolver.
- Para pedidos activos, mostrar el saldo del total vigente menos pagos netos. Si hay excedente, mostrar el importe pendiente de devolver. Para pedidos cancelados, no mostrar deuda y señalar lo pendiente de devolución.

### Usuarios y permisos

- Roles: `Administrador` y `Operador`.
- Ambos roles pueden trabajar con las funciones normales de la aplicación.
- Solo un administrador puede autorizar la actualización de un pedido que ya está en producción.
- Solo un usuario con rol Administrador puede crear y desactivar cuentas, tanto de operadores como de otros administradores. Un Operador no puede crear usuarios.
- No se puede desactivar ni cambiar el rol de la última cuenta Administrador activa.
- No hay registro público.
- La primera cuenta de administrador se crea en un asistente de primer inicio y define sus propias credenciales; no debe existir una contraseña predeterminada.
- El asistente solo está disponible cuando no hay cuentas; el Administrador inicial debe configurarse localmente antes de exponer la aplicación a otras computadoras.
- La aplicación actual no tiene autenticación. La incorporación de cuentas, inicio/cierre de sesión, autorización y protección de las pantallas/casos de uso es parte explícita del alcance.

## Ruta de trabajo sugerida

### 1. Aprobar especificación y documentar decisiones técnicas

Las decisiones de negocio cerradas quedan registradas en `specs/pedidos/spec.md`: pagos por pedido sin distribución automática, prorrateo completo al crear pedidos parciales, conservación de pedidos iniciados al reemplazar, cambio de diseño permitido en actualización, bloqueo posterior a retroceder a `Pendiente`, rechazo de aceptación cancelada y retorno automático a `Listo para entregar` tras ajustar una entrega completada. Todavía deben cerrarse estos detalles técnicos:

- Política de folios para pedidos y versiones del pedido.
- Esquema SQLite concreto de versiones, asignaciones, entregas y auditoría.
- Política técnica de sesiones/contraseñas e idempotencia.

Obtener aprobación formal de `specs/pedidos/spec.md`; los detalles técnicos no deben modificar sus reglas.

### 2. Definir contratos y límites

Diseñar modelos tipados antes de reestructurar la interfaz. Como mínimo:

- `Quote` y `QuoteLine`: identidad/folio, estado, cliente y snapshot de cliente, líneas con referencias opcionales al catálogo y snapshots de diseño, medidas, cantidad, precio, costos/cargos y totales.
- `Order` y `OrderLine`: identidad/folio, cotización origen/versiones, estado, datos operativos, snapshots de líneas/precios y cantidades asignadas.
- `Delivery`: fecha y cantidad entregada para el diseño único del pedido.
- `DeliveryAdjustment`: devolución/corrección de piezas que referencia una entrega anterior sin modificarla.
- `Payment` y `Refund`: movimientos inmutables vinculados al pedido.
- `User` y `Role`: cuenta activa, rol y datos de autenticación sin guardar contraseñas en texto claro.
- Contrato/versionado de snapshots JSON para poder cargar registros históricos cuando cambien los modelos.

Separar el cálculo de precios como servicio sin efectos secundarios de Streamlit o SQLite; los repositorios se encargan de persistencia/transacciones; las páginas solo coordinan la interacción y presentan resultados.

### 3. Diseñar persistencia y migraciones

- Añadir tablas/repositorios de pedidos, líneas de pedido/versiones, pagos/devoluciones y usuarios según el modelo acordado.
- Añadir persistencia de entregas parciales y transiciones basadas en cantidades entregadas.
- Implementar transacciones para crear pedidos y asignar cantidades, cancelar/liberar asignaciones y actualizar pedidos desde cotizaciones.
- Evitar que operaciones concurrentes o errores parciales superen cantidades cotizadas.
- Activar `PRAGMA foreign_keys = ON` en cada conexión SQLite y cubrirlo con pruebas.
- Preservar compatibilidad de cotizaciones antiguas y no alterar la base `cotizaciones.db` del usuario sin migraciones respaldadas y comprobadas.

### 4. Implementar autenticación y permisos

- Añadir asistente de bootstrap para crear el primer administrador solo cuando todavía no haya cuentas.
- Guardar contraseñas únicamente con hashing seguro apropiado; nunca en texto claro ni con valores predeterminados.
- Implementar inicio/cierre de sesión y controles de autorización en operaciones, no solo ocultando controles visuales.
- Restringir en servicios la creación/desactivación de usuarios y aprobación de actualización de pedidos a Administradores; probar que Operadores no pueden crear cuentas.
- No permitir desactivar o perder el último administrador activo sin una alternativa segura.

### 5. Incorporar flujos y pantallas

- Crear pedidos de diseño único desde una cotización aceptada, con cantidades disponibles asignables por diseño.
- Mostrar cantidades cotizadas, comprometidas, canceladas/liberadas y disponibles por línea.
- Añadir listado/detalle de pedidos, transiciones de estado con confirmación, captura de pagos/devoluciones y fechas/notas.
- Añadir captura de entregas parciales y ajustes de piezas desde `Listo para entregar`, con fecha y cantidad.
- Añadir flujo de duplicación de cotización con nuevo folio e importes históricos iniciales.
- En el detalle del historial, añadir registro de aceptación y habilitar `Crear pedido` solo para cotizaciones aceptadas.
- Añadir flujo de actualización de pedido en producción: elegir nueva cotización, mostrar diferencias, solicitar confirmación de administrador, guardar versión previa y registrar auditoría.

### 6. Validar y cerrar

- Añadir pruebas de servicios/repositorios y migraciones SQLite, además de pruebas de interfaz donde ya haya patrones de Streamlit AppTest.
- Cubrir al menos: solo cotizaciones aceptadas generan pedidos; pedido de diseño único; asignaciones no exceden cotización; cancelación previa libera cantidades; estados inválidos y reaperturas requieren confirmación/auditoría; entregas parciales y ajustes; pagos/devoluciones y saldos; actualización de producción con autorización/versionado; solo Administradores crean usuarios; siempre queda un Administrador activo; bootstrap sin registro público; compatibilidad con datos históricos.
- Ejecutar pruebas enfocadas, suite existente y compilación antes de dar por terminado el cambio.
- No crear un commit hasta que se solicite o se acuerde explícitamente para esta implementación.

## Archivos de partida relevantes

- `views/application.py`: punto de entrada, inicialización de BD y navegación actual.
- `views/pages/quote.py`: orquesta cotizador, estado, cálculos, snapshot y guardado.
- `views/pages/history.py`: restauración/carga de cotizaciones desde el historial.
- `repositories/quote_repository.py`: esquema/migraciones SQLite y persistencia de cotizaciones.
- `repositories/client_repository.py`: persistencia de clientes.
- `repositories/design_repository.py`: catálogo y consecutivos de diseños.
- `repositories/configuration_repository.py`: configuración económica global.
- `models/designs.py`: contratos tipados existentes para diseños y líneas.
- `tests/`: localizar aquí patrones y cobertura existentes antes de crear pruebas nuevas.

## Hallazgos previos que deben revisarse al tocar esas áreas

- La cotización se guarda como `datos_json`; el contrato histórico no tiene una versión de esquema explícita.
- La columna `cotizaciones.client_id` se agregó sin restricción `REFERENCES` y el guardado no valida actualmente el cliente.
- Las conexiones SQLite observadas no activan `PRAGMA foreign_keys`; su valor por defecto es `0`.
- La pantalla del cotizador mezcla renderizado, cálculo, validación, construcción de snapshot y persistencia.
- Se observó posible interferencia entre snapshots de cotización y configuración global en el estado de sesión; revisar `_start_new_quote`, `_restore_quote` y navegación a Configuración antes de refactorizar.

## Pruebas y estado previo

Un checkpoint anterior reportó 23 pruebas pasando, además de una prueba de configuración con AppTest y compilación Python. No se debe asumir que eso describe el estado actual: volver a ejecutar validaciones relevantes al empezar cambios.
