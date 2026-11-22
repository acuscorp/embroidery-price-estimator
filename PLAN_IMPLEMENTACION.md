# Hoja de ruta: arquitectura de cotizaciones y pedidos

> **Proceso SDD:** la especificación normativa fue aprobada formalmente el 22 de noviembre de 2026 y está en [`specs/pedidos/spec.md`](./specs/pedidos/spec.md), el diseño técnico en [`specs/pedidos/plan.md`](./specs/pedidos/plan.md) y el trabajo ejecutable en [`specs/pedidos/tasks.md`](./specs/pedidos/tasks.md). Este documento es solo la vista resumida por fases. No iniciar implementación hasta aprobar la especificación y cerrar las tareas del Gate 0.

Este plan desarrolla el alcance acordado en [HANDOFF.md](./HANDOFF.md). Es un plan de trabajo; no implica que estas fases estén implementadas ni autoriza cambios destructivos en la base existente.

## Resultado esperado

Una aplicación con contratos explícitos para cotizaciones, pedidos, pagos y usuarios; persistencia relacional segura y compatible con el historial; autenticación con roles; y flujos probados para registrar aceptación del cliente en el Historial de cotizaciones y crear pedidos de diseño único desde cotizaciones aceptadas.

## Principios de ejecución

1. Levantar la línea base antes de tocar código: estado de Git, pruebas actuales, esquema y copia segura de la base local para pruebas de migración.
2. Separar decisiones de negocio de decisiones técnicas. Las siete decisiones de negocio ya están cerradas en `spec.md`; las decisiones técnicas pendientes deben resolverse antes de diseñar una migración irreversible.
3. Implementar primero modelos/servicios/repo y pruebas; después integrar las pantallas.
4. Migrar de forma aditiva y compatible, preservando cotizaciones y sus snapshots. No sobrescribir ni borrar registros históricos.
5. Hacer cumplir permisos y reglas en la capa de servicio/repositorio, no solo en la interfaz.
6. Completar y validar cada fase antes de avanzar a la siguiente. Mantener commits separados por unidad lógica si el usuario pide o autoriza commits.

## Fase 0 — Línea base y aprobación de especificación

### Tareas

- Confirmar rama y estado limpio/dirty; no descartar cambios ajenos.
- Ejecutar la suite existente y registrar resultados.
- Inspeccionar esquema/índices/datos representativos de la base, sin publicar información sensible.
- Preparar una copia de la base en un directorio temporal de pruebas y validar restauración.
- Obtener aprobación formal de `specs/pedidos/spec.md`.
- Documentar los detalles técnicos abiertos (folios, esquema/versiones, sesiones/autenticación e idempotencia) sin cambiar los requisitos aprobados.
- Identificar pruebas de restauración y compatibilidad para cotizaciones ya guardadas.

### Criterio de salida

- Línea base documentada; cualquier fallo preexistente separado de fallos nuevos.
- Especificación aprobada y línea base conocida antes de tocar el esquema. Evidencia actual: 23 pruebas unittest pasan, compilación correcta y esquema SQLite existente enumerado sin publicar datos.

## Fase 1 — Contratos y reglas de dominio

### Tareas

- Definir contratos tipados/versionados de:
  - Cotización, cliente snapshot y línea de cotización.
  - Pedido, línea de pedido y snapshot/versiones del pedido.
  - Pago y devolución.
  - Usuario y rol.
- Definir enums/valores válidos para estado, método de pago y rol.
- Extraer reglas puras para cantidades disponibles, totales/saldos y transiciones.
- Especificar transiciones permitidas y qué operaciones exigen confirmación.
- Especificar la semántica de “iniciar trabajo” como transición a `En producción`.
- Definir migración/lectura de snapshots JSON antiguos mediante una versión por contrato.

### Criterio de salida

- Contratos y reglas documentados en código, con pruebas unitarias para cálculos y validaciones.
- Sin dependencia de Streamlit o SQLite en los cálculos puros.

## Fase 2 — Persistencia y transacciones

### Tareas

- Añadir tablas para pedidos, líneas/versiones, pagos/devoluciones, usuarios y auditoría según los contratos aprobados.
- Añadir entidades de entrega parcial con fecha y cantidad por línea.
- Añadir repositorios separados por agregado y mantener el repositorio de cotizaciones compatible.
- Centralizar conexiones SQLite y activar `PRAGMA foreign_keys = ON` en cada conexión.
- Crear migraciones idempotentes, transaccionales y con verificación de integridad.
- Implementar operaciones atómicas para:
  - Crear pedido de un solo diseño desde cotización aceptada asignando cantidades disponibles.
  - Cancelar pedido pendiente y liberar cantidades.
  - Registrar pagos directamente en pedidos y devoluciones sin mutar movimientos anteriores; no distribuir automáticamente un pago único entre pedidos.
  - Actualizar pedido en producción desde una nueva cotización, tras autorización, guardando snapshot/versiones y auditoría.
  - Mover asignaciones del pedido desde la cotización anterior a la nueva en la misma transacción; rechazar la actualización si no hay cantidades suficientes.
  - Registrar entregas parciales y ajustes solo desde `Listo para entregar`; marcar `Entregado` al completar todas las cantidades netas.
- Evitar que una falla parcial deje cantidades comprometidas, pagos o versiones en estado inconsistente.

### Criterio de salida

- Pruebas sobre base temporal cubren migración desde esquema anterior, integridad referencial y rollback ante errores.
- Operaciones concurrentes o repetidas no duplican pedidos/versiones ni sobreasignan cantidades.
- Los datos históricos siguen consultables y sin cambios inesperados.

## Fase 3 — Autenticación y autorización

### Tareas

- Implementar asistente de primer inicio que cree el primer administrador solo cuando no exista ninguna cuenta.
- Implementar almacenamiento seguro de credenciales mediante hashing de contraseñas; nunca persistir contraseñas en texto claro ni usar credenciales predeterminadas.
- Implementar inicio/cierre de sesión y estado de sesión coherente con Streamlit.
- Aplicar roles Administrador/Operador a casos de uso y repositorios/servicios.
- Restringir creación/desactivación de usuarios a administradores; impedir desactivar accidentalmente al último administrador activo.
- Impedir también cambiar el rol de la última cuenta Administrador activa.
- Comprobar la autorización en el servicio: solo Administrador puede crear usuarios; Operador no puede hacerlo aunque invoque directamente el caso de uso.
- Restringir aprobación de actualizaciones de pedidos en producción a administradores.
- Registrar actor, instante y decisión de operaciones sensibles conforme a la política acordada.

### Criterio de salida

- Operador no puede ejecutar operaciones administrativas ni aprobar actualizaciones, incluso invocando directamente el caso de uso.
- El primer administrador puede crearse una sola vez; no hay registro público ni secretos predeterminados.
- Contraseñas no aparecen en base, logs, errores ni snapshots.

## Fase 4 — Servicios de aplicación

### Tareas

- Crear casos de uso explícitos para crear/duplicar cotizaciones, registrar su aceptación o cancelación, crear/cancelar pedidos, cambiar estados, registrar pagos/devoluciones y actualizar pedidos.
- Separar orquestación de UI y persistencia.
- Definir límites de edición:
  - Cotización persistida no se edita; se crea una nueva copia con folio.
  - Los valores copiados se conservan hasta que se solicite recálculo o se editen datos relevantes.
  - Un pedido se crea desde una cotización aceptada, contiene un solo diseño y conserva snapshot.
  - Actualización de pedido en producción requiere nueva cotización aceptada, autorización de Administrador, confirmación y registro de versión; permite conservar o cambiar el diseño.
  - Confirmar el reemplazo cancela la cotización anterior y cualquier pedido pendiente que nunca inició producción; conserva los pedidos iniciados en todos los estados operativos.
- Validar que la suma de cantidades en pedidos activos no exceda cada línea cotizada y aplicar la regla acordada para cancelaciones/versiones.

### Criterio de salida

- Servicios tienen pruebas independientes de Streamlit.
- Las restricciones se cumplen para todas las rutas de acceso, no solo la navegación normal de la UI.

## Fase 5 — Interfaz Streamlit

### Tareas

- Añadir autenticación antes de mostrar las funciones protegidas.
- Añadir administración de usuarios solo para Administradores; impedir crear/desactivar usuarios a Operadores.
- En el detalle del Historial de cotizaciones, registrar aceptación del cliente (medio, usuario y fecha/hora); habilitar `Crear pedido` solo después de aceptar.
- Añadir generación de pedidos desde cotización aceptada: un diseño por pedido, con capacidad de dividir la cantidad de ese diseño entre pedidos; iniciar en `Pendiente`, sin segunda aprobación del cliente.
- Añadir listado/detalle de pedidos con estado, fechas, notas, saldo, pagos y devoluciones.
- Añadir registro de entregas parciales y ajustes de piezas desde `Listo para entregar`.
- Añadir confirmación explícita de cambios de estado retroactivos/reapertura y cancelación cuando corresponda.
- Añadir flujo de duplicación de cotización con nuevo folio e indicador claro de que los precios copiados son históricos y no se recalcularon.
- Añadir flujo de actualización de pedido en producción: comparar versión actual con nueva cotización, permitir conservar o cambiar el diseño, mostrar cambios e impacto monetario, exigir autorización admin y confirmar antes de persistir.
- Mantener mensajes claros si el usuario no tiene permisos o si cantidades/saldos no permiten una acción.

### Criterio de salida

- Los flujos principales son utilizables con roles de administrador y operador.
- Una confirmación cancelada no persiste cambios.
- Las vistas históricas muestran las versiones y los movimientos sin permitir alterar registros inmutables.

## Fase 6 — Pruebas de regresión, documentación y entrega

### Matriz mínima de pruebas

- Cotización no aceptada no puede generar pedidos; una cotización cancelada tampoco puede ser aceptada; la aceptación se registra desde su detalle en el Historial.
- Cada pedido contiene un solo diseño; una cotización con varios diseños puede generar varios pedidos y asignaciones parciales por diseño.
- La suma asignada no excede cantidades cotizadas; cancelación previa libera cantidades según la regla acordada.
- Pedido cancelado después de iniciar trabajo se rechaza.
- Retrocesos/reaperturas exigen confirmación y conservan historial; retroceder un pedido iniciado a `Pendiente` bloquea edición libre y cancelación.
- Duplicar cotización genera folio nuevo y conserva inicialmente precios/totales; recálculo ocurre solo de forma explícita o ante cambio relevante.
- Pagos/devoluciones son movimientos separados y asociados al pedido; no hay distribución automática entre pedidos; el prorrateo se recalcula al crear pedidos parciales y el saldo cancelado/activo es correcto.
- Actualización de pedido en producción exige cotización aceptada, administrador y confirmación; puede conservar o cambiar el diseño, mueve asignaciones atómicamente, respeta piezas entregadas netas y conserva estado, pagos, versión previa y auditoría.
- Entregas parciales no exceden cantidades pedidas; `Entregado` se alcanza solo al completar el pedido y un ajuste que reduce el entregado neto vuelve automáticamente a `Listo para entregar`.
- Solo Administrador puede crear/desactivar usuarios o aprobar la actualización; Operador no puede crear cuentas y no se puede desactivar ni cambiar el rol de la última cuenta Administrador activa.
- Bootstrap, login, logout y manejo de sesión funcionan sin cuenta predeterminada.
- Migraciones conservan cotizaciones previas, manejan snapshots antiguos y activan claves foráneas.
- Suite existente, pruebas enfocadas y compilación pasan.

### Criterio de salida

- Pruebas relevantes pasan; resultados y cualquier limitación se reportan.
- Documentación de uso y decisiones de dominio se actualiza.
- Diff revisado para evitar cambios no relacionados y secretos.

## Dependencias y orden

`Fase 0 → Fase 1 → Fase 2 → Fase 3 → Fase 4 → Fase 5 → Fase 6`

La Fase 3 puede desarrollarse en paralelo con partes de la Fase 2 solo si los contratos de usuario/auditoría y las decisiones de seguridad ya están cerrados; la integración final de autorización depende de los servicios de la Fase 4.

## Riesgos principales y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Datos históricos cambian al añadir pedidos/versiones | Migraciones aditivas, snapshots versionados y pruebas con copia de la base |
| Sobreasignación de cantidades | Validación transaccional por línea y pruebas de repetición/concurrencia |
| Cambios monetarios inesperados al actualizar pedidos | Mostrar diferencias, conservar pagos y mostrar el excedente como pendiente de devolver; registrar la devolución cuando se realice |
| Operaciones administrativas protegidas solo por la UI | Autorizar dentro de servicios/casos de uso y probar acceso directo |
| Bloqueo del último administrador o credenciales inseguras | Reglas de administración, bootstrap de una sola vez y pruebas de seguridad de credenciales |
| Refactorización grande rompe el cotizador existente | Cambios incrementales, pruebas de regresión por fase y evitar reescritura completa en una sola entrega |
