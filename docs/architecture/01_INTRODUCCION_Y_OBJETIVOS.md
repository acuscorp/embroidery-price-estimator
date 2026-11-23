# arc42 — 1. Introducción y objetivos

**Sistema:** Sistema de gestión integral del negocio de bordados  
**Proyecto de referencia:** Cotizador de Bordados  
**Estado:** Borrador inicial; requiere validación de stakeholders y alcance  
**Última actualización:** 2026-11-22

> Este documento describe el sistema objetivo. No debe interpretarse como descripción de capacidades ya implementadas ni como aprobación de una arquitectura técnica.

## 1.1 Resumen y motivación

El objetivo es evolucionar el Cotizador de Bordados hacia un sistema que permita gestionar de forma coherente el ciclo comercial y operativo del negocio de bordados.

El sistema objetivo debe dar continuidad a la información desde que se prepara una cotización hasta que el trabajo se acepta, se organiza en órdenes y pedidos, se produce, se entrega y se cobra. También debe conservar el historial necesario para consultar qué se ofreció, qué se acordó y qué ocurrió durante la atención del cliente.

El sistema actual es un cotizador. La visión objetivo es más amplia: un sistema de gestión integral. Esta diferencia es intencional y constituye una motivación central del trabajo arquitectónico.

## 1.2 Requisitos funcionales esenciales

A nivel de objetivos, el sistema debe permitir:

1. **Gestionar clientes y diseños:** mantener la información necesaria para identificar al cliente y los diseños de bordado relacionados con sus trabajos.
2. **Preparar y conservar cotizaciones:** calcular propuestas comerciales con conceptos, diseños, cantidades, costos, precios, importes y vigencia.
3. **Registrar la aceptación y el compromiso:** conservar la propuesta aceptada y relacionarla con la orden u órdenes que correspondan. La regla para dividir una cotización en varias órdenes sigue pendiente de definición.
4. **Gestionar pedidos:** representar los trabajos individuales incluidos en una orden, con su diseño, cantidad y condiciones acordadas.
5. **Dar seguimiento a producción y entregas:** consultar el avance de cada pedido y registrar entregas parciales o completas.
6. **Registrar pagos:** conservar los importes recibidos y su aplicación a órdenes y pedidos. Las reglas de distribución, abonos, saldos y ajustes requieren definición.
7. **Consultar historial e información del negocio:** relacionar la actividad del cliente con cotizaciones, órdenes, pedidos, producción, entregas y pagos, y permitir análisis posterior.
8. **Atribuir operaciones a usuarios:** identificar quién realizó acciones relevantes y cuándo, sujeto a la definición de usuarios, roles y permisos.

Esta lista expresa capacidades objetivo de alto nivel. No es todavía una especificación funcional completa ni implica que todas estén implementadas.

## 1.3 Objetivos de calidad

Se identificaron las siguientes preocupaciones de calidad. Su prioridad relativa y sus criterios medibles todavía deben validarse; no se establece aquí un orden definitivo.

| Objetivo de calidad | Por qué importa | Criterio o aspecto por concretar |
|---|---|---|
| Exactitud y consistencia | Los errores en costos, precios, cantidades, importes o saldos afectan las cotizaciones y los compromisos comerciales. | Reglas de cálculo compartidas, precisión monetaria, redondeos y consistencia entre cotización, orden y pedido. |
| Integridad y conservación de datos | La información comercial y operativa debe mantenerse coherente y no perderse ante errores o interrupciones. | Transacciones, respaldos, recuperación, retención y pérdida de datos admisible. |
| Seguridad y privacidad | Los datos de clientes, precios, cotizaciones y pagos no deben consultarse ni modificarse sin autorización. | Identidades, roles, permisos, protección de datos y obligaciones aplicables. |
| Trazabilidad | Se necesita conocer quién realizó una operación y cuándo, especialmente ante cambios en compromisos y registros financieros. | Eventos que deben auditarse, datos mínimos y periodo de conservación. |
| Modificabilidad | Las reglas y procesos del negocio pueden evolucionar; los cambios no deberían obligar a reconstruir partes no relacionadas. | Separación de responsabilidades, dependencias y coste aceptable de cambio. |
| Disponibilidad y recuperabilidad | Se espera poder trabajar desde computadora o celular y recuperar la operación después de interrupciones. | Horarios de uso, disponibilidad esperada, RTO y RPO. |
| Rendimiento | Consultar clientes, cotizar y revisar pedidos debe mantener tiempos de respuesta razonables. | Volumen de datos, usuarios concurrentes y tiempos objetivo para operaciones representativas. |

La preferencia expresada hasta ahora es proteger la integridad de la información incluso si alguna medida reduce la edición simultánea. Por ejemplo, se consideró aceptable que una persona espere mientras otra modifica una cotización, si eso evita sobrescrituras. Esto no aprueba todavía una estrategia técnica de bloqueo.

## 1.4 Stakeholders y sus preocupaciones

La identificación siguiente es inicial. Los roles y expectativas que no estén confirmados se marcan como pendientes de validación.

| Stakeholder | Relación con el sistema | Intereses y preocupaciones | Estado |
|---|---|---|---|
| Responsable del negocio | Define cómo se cotiza, acepta y controla el trabajo; necesita consultar la operación y sus resultados. | Exactitud de precios y costos, control de compromisos, seguimiento de pedidos, pagos, historial y rentabilidad. | Rol inferido por el propósito del sistema; confirmar quién lo desempeña y sus responsabilidades. |
| Personal que opera el negocio | Podría registrar clientes, cotizaciones, pedidos, producción, entregas o pagos. | Facilidad de uso, evitar captura duplicada, claridad de estados y protección frente a errores. | La existencia, cantidad y distribución de estos usuarios están pendientes de confirmar. |
| Cliente del negocio | Recibe cotizaciones y acuerda trabajos; recibe los productos o servicios contratados. | Claridad de la propuesta, conservación de lo acordado, cumplimiento de cantidades y entregas. | Stakeholder del dominio identificado; falta definir si tendrá interacción directa con el software. |
| Responsable de mantenimiento o evolución del software | Construye, corrige y mantiene la aplicación. | Comprensibilidad, modificabilidad, pruebas, trazabilidad de decisiones y operación sostenible. | Stakeholder necesario para la evolución; identificar quién asumirá el rol y con qué capacidades. |

No se presupone que los clientes tengan cuentas o acceso directo al sistema. Tampoco se da por hecho que exista un equipo técnico separado. Estos aspectos deberán confirmarse antes de diseñar permisos, interfaces o despliegue.

## 1.5 Alcance inicial y límites

### Dentro de la visión objetivo

- Gestión de clientes y diseños.
- Cotizaciones y conservación de las condiciones aceptadas.
- Órdenes y pedidos individuales.
- Seguimiento de producción.
- Entregas parciales y completas.
- Registro y aplicación de pagos.
- Historial, trazabilidad y reportes.
- Usuarios y permisos, según necesidades que se validen.

### Fuera de alcance confirmado por ahora

No se ha aprobado incorporar como parte del sistema:
- Contabilidad fiscal o sustitución de un sistema contable.
- Facturación electrónica.
- Pasarelas o procesamiento automático de pagos.
- Portal de autoservicio para clientes.
- Integraciones con proveedores, paqueterías u otros sistemas externos.
- Automatizaciones o capacidades de inteligencia artificial.

Estos puntos no se descartan definitivamente; quedan fuera de la línea base hasta que exista una necesidad de negocio explícita y se evalúe su conveniencia.

## 1.6 Preguntas abiertas para validar

1. ¿Quiénes utilizarán el sistema en la operación diaria y qué responsabilidades tendrá cada persona?
2. ¿Los clientes solo recibirán cotizaciones y comprobantes generados por el negocio, o necesitarán consultar o aceptar información directamente en el sistema?
3. ¿La aceptación de una cotización siempre genera una orden o puede generar varias? ¿Bajo qué reglas?
4. ¿Cómo se asignan los pagos a órdenes y pedidos cuando hay anticipos, abonos, pagos parciales o ajustes?
5. ¿Qué estados y transiciones necesita cada pedido desde su aceptación hasta su entrega?
6. ¿Qué reportes necesita realmente el responsable del negocio para controlar costos, margen, ventas y operación?
7. ¿Cuántos usuarios trabajarán simultáneamente y desde qué dispositivos o ubicaciones?
8. ¿Qué nivel de disponibilidad, respaldo y recuperación es necesario y económicamente razonable?
9. ¿Qué información histórica debe conservarse y durante cuánto tiempo?
10. ¿Qué obligaciones fiscales, legales o de privacidad condicionan el tratamiento de datos y documentos?

Estas preguntas no bloquean la descripción inicial del propósito, pero sí condicionan el detalle de requisitos, contexto, calidad y decisiones arquitectónicas posteriores.

## 1.7 Trazabilidad y fuentes

- Diagnóstico inicial y propósito: [CL01.01.01 — Concepto y propósito de la arquitectura](./diagnostico/CL01.01.01_CONCEPTO_Y_PROPOSITO.md).
- Elementos y capacidades del sistema objetivo: [CL01.02.01 — Elementos, responsabilidades y relaciones](./diagnostico/CL01.02.01_ELEMENTOS_RESPONSABILIDADES_Y_RELACIONES.md).
- Organización del trabajo: [Plan de arquitectura](./PLAN_TRABAJO_ARQUITECTURA.md).
- Marco de documentación: [arc42](https://arc42.org/).

La descripción del sistema actual y sus capacidades implementadas se mantiene en los diagnósticos técnicos correspondientes. Este documento recoge la visión objetivo y no sustituye esa evidencia.

## Estado de esta sección

**Borrador para validación.** El propósito y las capacidades objetivo proceden del trabajo arquitectónico previo. La identificación de stakeholders contiene roles inferidos y pendientes de confirmación. Los objetivos de calidad son preocupaciones iniciales, todavía sin escenarios medibles ni prioridades aprobadas.
