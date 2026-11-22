# Tareas: implementación de cotizaciones y pedidos

Las tareas son una lista de ejecución trazable a `spec.md` y `plan.md`. Por ahora todas están **pendientes**; no se ha iniciado implementación. No marcar una tarea como terminada sin pruebas y verificación del criterio.

## Gate 0 — Línea base y aprobación de especificación

- [x] **T-001** Ejecutar línea base: estado Git, pruebas actuales, compilación y esquema SQLite. Evidencia: rama `master` con los documentos SDD como cambios nuevos; 23 pruebas unittest pasan; compilación Python sin errores; tablas existentes: `clientes`, `configuracion_app`, `cotizaciones`, `diseno_consecutivos`, `diseno_imagenes`, `diseno_subcategorias`, `disenos`; SQLite reporta `foreign_keys=0` por defecto. Requisitos: NFR-04, NFR-07.
- [x] **T-002** Revisar con el usuario y aprobar la especificación `spec.md`; aprobación formal registrada el 22 de noviembre de 2026. Requisitos: Q-01–Q-05, O-01–O-12, P-01–P-05, A-01–A-05, NFR-01–NFR-07, AC-16–AC-18.
- [x] **T-003** Resolver los pendientes de negocio de `spec.md`: pagos por pedido sin distribución automática; recálculo completo del prorrateo al crear pedidos parciales; conservar pedidos iniciados al reemplazar; permitir cambio de diseño en actualización; bloquear edición/cancelación después de retroceder a `Pendiente`; rechazar aceptación de cotización cancelada; retornar automáticamente a `Listo para entregar` tras ajuste de entrega completada. Requisitos: Q-03–Q-05, O-07–O-11, P-01–P-05, AC-16–AC-18.
- [ ] **T-004** Documentar decisiones técnicas de folios, esquema SQLite, autenticación/sesión e idempotencia sin alterar los requisitos aprobados. Requisitos: NFR-02–NFR-06.

**Dependencia:** T-001–T-004 son el gate previo a implementar. Gate 1 iniciado con contratos y reglas puras implementadas; falta completar migración técnica T-004 antes de Gate 2. No avanzar a T-005 hasta completar baseline, resolver pendientes bloqueantes y obtener aprobación de `spec.md`.

## Gate 1 — Contratos y dominio

- [x] **T-005** Definir contratos tipados y versionados para cotización, aceptación del cliente, cliente snapshot y líneas. Requisitos: Q-01–Q-05, O-05, NFR-05.
- [x] **T-006** Definir contratos de pedido de diseño único, versiones, entregas/ajustes y estados. Requisitos: O-01–O-12.
- [x] **T-007** Definir contratos de pago, devolución y cálculos monetarios exactos; registrar pagos directamente en pedidos sin distribución automática. Requisitos: P-01–P-05.
- [x] **T-008** Definir contratos de usuario, rol y eventos de auditoría. Requisitos: A-01–A-05, O-12, NFR-06.
- [x] **T-009** Implementar y probar reglas puras para cantidades, entregas/ajustes, prorrateo completo al crear pedidos parciales, saldos y transiciones. Requisitos: Q-05, O-03, O-06–O-08, O-10, P-03–P-05, AC-16–AC-18.
- [x] **T-010** Crear adaptadores de lectura/versionado para los snapshots históricos existentes. Requisitos: Q-01, NFR-04–NFR-05.

## Gate 2 — Persistencia

- [ ] **T-011** Centralizar la conexión SQLite; activar y probar foreign keys en cada conexión. Requisitos: NFR-03–NFR-04.
- [ ] **T-012** Diseñar e implementar migraciones aditivas/idempotentes para pedidos de diseño único, versiones, entregas/ajustes y relaciones. Requisitos: O-01–O-12, NFR-04–NFR-05.
- [ ] **T-013** Implementar repositorios de pedidos y transacciones de creación/asignación por diseño. Requisitos: O-01–O-05.
- [ ] **T-014** Implementar cancelación atómica de pedidos elegibles y liberación de cantidades. Requisitos: Q-03, O-04, O-08.
- [ ] **T-015** Implementar persistencia de pagos/devoluciones y consulta de saldos/asignaciones a pedidos. Requisitos: P-01–P-04.
- [ ] **T-016** Implementar persistencia de usuarios/roles, bootstrap sin credenciales predeterminadas y protección del último Administrador activo. Requisitos: A-01–A-05, NFR-06.
- [ ] **T-017** Implementar persistencia de versiones/auditoría para cambios de estado, entregas/ajustes y actualizaciones. Requisitos: O-07, O-10–O-12.
- [ ] **T-018** Probar migración, integridad, rollback y compatibilidad usando una copia temporal de la base. Requisitos: NFR-03–NFR-05.

## Gate 3 — Autenticación y casos de uso

- [ ] **T-019** Implementar autenticación, cierre de sesión y control de sesión. Requisitos: A-01, A-04–A-05, NFR-06.
- [ ] **T-020** Implementar autorización en servicios: solo Administrador crea/desactiva usuarios y autoriza cambios en producción. Requisitos: A-02–A-03, NFR-02.
- [ ] **T-021** Implementar casos de uso para duplicar/aceptar/cancelar cotización y crear pedido con un diseño; rechazar aceptación de cotizaciones canceladas. Requisitos: Q-01–Q-05, O-01–O-05.
- [ ] **T-022** Implementar casos de uso de cambio de estado, pago, devolución y consulta financiera; mantener bloqueo de cancelación tras iniciar y retroceder a `Pendiente`. Requisitos: O-06–O-09, P-01–P-05.
- [ ] **T-023** Implementar entregas parciales y ajustes/devoluciones de piezas sin modificar movimientos anteriores; ajustar automáticamente `Entregado` a `Listo para entregar` cuando el entregado neto disminuya. Requisitos: O-07, O-09–O-10, AC-13, AC-18.
- [ ] **T-024** Implementar actualización confirmada/versionada del pedido de un solo diseño desde una nueva cotización aceptada; permitir conservar o cambiar el diseño, mover asignaciones atómicamente, respetar entregas netas y calcular importe pendiente de devolución. Requisitos: O-03, O-07, O-11–O-12, P-03.
- [ ] **T-025** Probar casos de uso con roles distintos, errores, reintentos y rollback. Requisitos: O-03, A-02–A-03, NFR-02–NFR-03.

## Gate 4 — Interfaz

- [ ] **T-026** Integrar login/bootstrap y proteger la navegación por rol. Requisitos: A-01–A-05.
- [ ] **T-027** Añadir administración de usuarios solo para Administradores; probar que Operador no puede crear usuarios. Requisitos: A-02.
- [ ] **T-028** En el detalle del Historial de cotizaciones, añadir `Registrar aceptación del cliente`; capturar medio y guardar usuario/fecha-hora. Habilitar `Crear pedido` solo después de aceptación y crear el pedido en `Pendiente` sin aprobación adicional. Requisitos: Q-04, AC-01a, AC-01b.
- [ ] **T-029** Añadir creación de pedidos desde cotizaciones aceptadas: un pedido por diseño y cantidad total, permitiendo varios pedidos parciales para el mismo diseño. Requisitos: Q-04, O-01–O-05.
- [ ] **T-030** Añadir listado/detalle de pedidos, fechas, notas, estado, entregas/ajustes y movimientos financieros. Requisitos: O-06–O-10, P-01–P-04.
- [ ] **T-031** Añadir confirmaciones para cambios de estado y actualizaciones en producción, con vista de diferencias y autorización de administrador. Requisitos: O-07, O-11–O-12.
- [ ] **T-032** Añadir duplicación/reemplazo de cotización con nuevo folio, cancelación confirmada de la anterior e indicador de importes históricos; conservar sin cancelar pedidos iniciados en cualquier estado operativo. Requisitos: Q-01–Q-03.
- [ ] **T-033** Ejecutar pruebas de interfaz y regresión de las pantallas existentes. Requisitos: NFR-07.

## Gate 5 — Verificación y entrega

- [ ] **T-034** Ejecutar y revisar los escenarios AC-01–AC-18 de `spec.md`, incluidos AC-01a y AC-01b.
- [ ] **T-035** Ejecutar suite enfocada, suite completa y compilación; resolver regresiones introducidas.
- [ ] **T-036** Actualizar documentación de usuario/arquitectura y reportar migración, pruebas y límites conocidos.
- [ ] **T-037** Revisar el diff final y confirmar que no se modificaron secretos ni datos locales.

## Regla de seguimiento

- Antes de trabajar en una tarea, cambiar su casilla a `[~]` y anotar cualquier decisión adicional en la especificación.
- Al terminarla, cambiarla a `[x]` y registrar la prueba o evidencia que satisface sus requisitos.
- Si una implementación descubre ambigüedad que afecta cantidades, dinero, permisos o historial, detener esa parte y actualizar `spec.md` para revisión; no resolverla implícitamente en código.
