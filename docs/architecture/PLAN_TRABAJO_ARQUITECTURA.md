# Plan de arquitectura — Cotizador de Bordados

**Documento rector del trabajo de arquitectura y diseño**  
**Marco de documentación:** arc42, adaptado al contexto y a la madurez del proyecto.

## 1. Propósito

Construir progresivamente la arquitectura del sistema de gestión integral del negocio de bordados, partiendo de una comprensión verificable del negocio y del sistema existente, y definiendo una arquitectura objetivo que sirva como referencia para su implementación posterior.

Utilizaremos arc42 como estructura de referencia para organizar la descripción arquitectónica. No adoptaremos la plantilla de manera mecánica: cada sección se desarrollará cuando existan preguntas, evidencia y decisiones suficientes para justificarla.

Las clases del curso **no organizarán los archivos ni los entregables**. La ruta curricular indicará qué conceptos aprender y aplicar; los resultados se incorporarán a los artefactos arquitectónicos correspondientes.

## 2. Fuentes de referencia

### 2.1 Referencias arquitectónicas

- [arc42](https://arc42.org/): estructura de documentación arquitectónica y guía de trabajo iterativo.
- [ISO/IEC/IEEE 42010](https://www.iso.org/standard/74393.html): referencia para describir arquitectura mediante stakeholders, preocupaciones, puntos de vista, vistas y modelos. No prescribe una metodología ni una estructura de carpetas.

Estas referencias orientan la documentación; no sustituyen el análisis del negocio ni justifican por sí solas decisiones técnicas.

### 2.2 Ruta curricular

- Repositorio: [acuscorp/SoftwareArchitecture](https://github.com/acuscorp/SoftwareArchitecture)
- Ruta: [LEARNING_PATH.md](https://github.com/acuscorp/SoftwareArchitecture/blob/main/LEARNING_PATH.md)

Las fichas oficiales determinan los conceptos, objetivos y criterios de aprendizaje. La trazabilidad curricular se conservará en los artefactos, sin convertir cada clase en un documento arquitectónico independiente.

### 2.3 Sistema analizado

- Repositorio: [acuscorp/embroidery-price-estimator](https://github.com/acuscorp/embroidery-price-estimator)

El código, las pruebas y la documentación del repositorio se utilizarán como evidencia del sistema existente. La evidencia deberá indicar la referencia o commit inspeccionado cuando sea relevante.

## 3. Alcance y límites

Este espacio de trabajo comprende análisis, arquitectura y diseño.

**Incluye:**
- Comprender el negocio, sus participantes, objetivos, procesos y reglas.
- Analizar el sistema existente con evidencia.
- Identificar requisitos, restricciones, riesgos y atributos de calidad.
- Construir modelos, vistas y decisiones arquitectónicas.
- Definir una arquitectura objetivo y una estrategia de evolución.
- Mantener la trazabilidad entre evidencia, propuestas y decisiones.

**No incluye:**
- Modificar código ni implementar funcionalidades.
- Ejecutar refactorizaciones.
- Dar por implementada una capacidad solo porque aparezca en una especificación o modelo.
- Aprobar decisiones técnicas sin analizar alternativas, consecuencias y contexto.

La implementación se realizará en otro espacio de trabajo y utilizará los artefactos arquitectónicos aprobados como referencia.

## 4. Organización de la documentación con arc42

La documentación se organizará por preguntas arquitectónicas, no por clases curriculares. La siguiente estructura es el destino lógico; los archivos se crearán o separarán solo cuando aporten valor.

| Sección arc42 | Pregunta que debe responder | Estado |
|---|---|---|
| 1. Introducción y objetivos | ¿Qué sistema estamos construyendo y qué objetivos debe satisfacer? | Borrador creado; pendiente de validación |
| 2. Restricciones arquitectónicas | ¿Qué condiciones limitan las soluciones posibles? | Pendiente de consolidación |
| 3. Contexto y alcance | ¿Quién utiliza el sistema, con qué actores y sistemas externos interactúa y qué queda dentro/fuera? | En elaboración |
| 4. Estrategia de solución | ¿Qué decisiones fundamentales orientan la solución y por qué? | Pendiente de evidencia y evaluación |
| 5. Vista de bloques de construcción | ¿Qué módulos o bloques componen el sistema y cuáles son sus responsabilidades y dependencias? | Análisis actual en curso; la vista objetivo aún no está definida |
| 6. Vista de ejecución | ¿Cómo colaboran los bloques durante escenarios relevantes en tiempo de ejecución? | Pendiente |
| 7. Vista de despliegue | ¿En qué infraestructura y entorno se ejecuta el sistema? | Pendiente de requisitos y alternativas |
| 8. Conceptos transversales | ¿Qué reglas y soluciones atraviesan varios bloques? | Pendiente |
| 9. Decisiones arquitectónicas | ¿Qué decisiones importantes se tomaron, qué alternativas se evaluaron y cuáles son sus consecuencias? | Registro por iniciar cuando existan decisiones aprobadas |
| 10. Requisitos de calidad | ¿Qué atributos de calidad importan y cómo se concretan en escenarios verificables? | Preocupaciones iniciales identificadas; falta especificación |
| 11. Riesgos y deuda técnica | ¿Qué riesgos, incertidumbres y problemas conocidos afectan la arquitectura? | En elaboración |
| 12. Glosario | ¿Qué términos del negocio y de la arquitectura deben tener un significado compartido? | Evolutivo |

No se considera que una sección esté completa por llenar su encabezado. Se documentará lo conocido, se marcarán explícitamente las incertidumbres y se dejarán vacías o pendientes las partes que todavía no puedan justificarse.

## 5. Artefactos de trabajo y fuentes de verdad

Los artefactos se mantendrán como documentos vivos. Su separación física dependerá de su tamaño, frecuencia de cambio y utilidad para los lectores.

- **Visión y objetivos:** propósito, alcance, stakeholders, necesidades y objetivos de calidad. Alimenta arc42 1, 3 y 10.
- **Contexto del sistema:** actores, sistemas externos, límites e interfaces del entorno. Alimenta arc42 3.
- **Restricciones:** restricciones de negocio, técnicas, organizativas, regulatorias y operativas. Alimenta arc42 2.
- **Inventario del sistema actual:** elementos conceptuales y técnicos, evidencia de implementación y estado de capacidades. Alimenta arc42 5 y 11.
- **Responsabilidades y relaciones:** responsabilidades, límites, dependencias y colaboraciones. Alimenta arc42 5; las interacciones dinámicas relevantes alimentarán arc42 6.
- **Modelos del dominio y glosario:** conceptos, reglas y relaciones del negocio. Alimenta arc42 3, 5 y 12.
- **Escenarios de calidad:** estímulo, contexto, respuesta esperada y medida. Alimenta arc42 10.
- **Vistas arquitectónicas:** modelos estáticos, dinámicos y de despliegue seleccionados según las preguntas de stakeholders. Alimentan arc42 5, 6 y 7.
- **Registro ADR:** decisiones, contexto, alternativas, consecuencias y estado. Alimenta arc42 4 y 9.
- **Riesgos y brechas:** incertidumbres, deuda técnica, diferencias entre estado actual y objetivo. Alimenta arc42 11.
- **Estrategia de evolución:** etapas y transición desde el sistema actual hasta la arquitectura objetivo. Se vincula con arc42 4, 9 y 11.

No se crearán todos estos archivos de inmediato. Se consolidará primero el contenido existente y después se separarán los artefactos cuando sea necesario.

## 6. Método de trabajo

El trabajo será iterativo. Las actividades pueden repetirse y retroalimentarse; no se asumirá que la arquitectura se descubre siguiendo una secuencia rígida.

1. Identificar la pregunta arquitectónica y a quién necesita responder.
2. Consultar la ficha curricular pertinente, cuando el trabajo esté vinculado con una clase.
3. Revisar la evidencia disponible del negocio, el código y la documentación.
4. Distinguir estado actual, necesidad futura e hipótesis.
5. Elaborar o actualizar el artefacto que responda esa pregunta.
6. Evaluar alternativas cuando exista una decisión por tomar.
7. Registrar decisiones aprobadas y sus consecuencias.
8. Revisar consistencia y trazabilidad con los demás artefactos.

No se avanzará a una decisión solo porque el curso presente un concepto. El alcance curricular orienta el aprendizaje; la evidencia y las necesidades del sistema determinan qué puede concluirse.

## 7. Clasificación y estado de la información

Cada afirmación relevante debe poder identificarse como una de estas categorías:

- **Hecho observado:** confirmado en código, documentación, pruebas o información explícita del negocio.
- **Inferencia:** interpretación derivada de hechos, todavía no confirmada.
- **Problema:** condición no deseada respaldada por evidencia.
- **Propuesta:** alternativa de solución aún no aprobada.
- **Decisión aprobada:** elección aceptada, con fundamento y consecuencias registrados.
- **Pendiente de evidencia:** asunto que no puede concluirse con la información disponible.

Para capacidades del sistema se utilizarán estos estados:
- **Implementado:** existe evidencia funcional en el alcance revisado.
- **Parcialmente implementado:** hay partes relacionadas, pero no evidencia suficiente de un flujo funcional completo.
- **Sin evidencia funcional suficiente:** la revisión no encontró evidencia bastante para afirmar que está implementado. No demuestra ausencia absoluta.

Toda clasificación de implementación debe indicar el alcance y, cuando sea posible, el commit revisado.

## 8. Trazabilidad curricular

Las clases se relacionarán con los artefactos que ayudan a construir o revisar. Una clase puede alimentar varios artefactos y un artefacto puede evolucionar durante varias clases.

| Referencia curricular | Aplicación principal en los artefactos |
|---|---|
| CL01.01.01 — Concepto y propósito de la arquitectura | Visión, objetivos, contexto, preocupaciones de calidad y abstracciones iniciales. |
| CL01.02.01 — Elementos, responsabilidades y relaciones | Inventario, responsabilidades, dependencias y modelo conceptual. |
| CL01.02.02 — Estructura, runtime y vistas introductorias | Vistas estructurales y de ejecución, según evidencia. |
| CL01.03.01 — Arquitectura, diseño e implementación | Delimitación de decisiones arquitectónicas frente a decisiones de diseño e implementación. |
| CL01.04.01 — Contexto y participantes | Stakeholders, contexto y preocupaciones. |
| CL01.05.01 — Decisiones arquitectónicas | Evaluación de alternativas y registro ADR. |

La tabla se ampliará conforme avance la ruta curricular. No implica que debamos completar una sección arc42 por cada clase.

## 9. Reglas de consistencia

1. No confundir el sistema actual con el sistema objetivo.
2. No forzar la arquitectura objetivo para que reproduzca la estructura actual.
3. No asumir que un concepto del dominio equivale a un módulo técnico.
4. No inferir comportamiento funcional a partir de la mera existencia de modelos, contratos o especificaciones.
5. No convertir una propuesta en decisión sin aprobación explícita.
6. No registrar como hecho algo que solo se discutió como posibilidad.
7. Mantener visibles las capacidades pendientes aunque no se diseñen en la etapa actual.
8. Evitar duplicar información: cada dato tendrá un artefacto principal y los demás lo referenciarán.
9. Mantener los documentos versionados junto al sistema.
10. No modificar código en este espacio de trabajo.

## 10. Criterio de consolidación

La arquitectura estará suficientemente consolidada para guiar la implementación cuando:
- Los objetivos, stakeholders, alcance y restricciones estén documentados.
- Las necesidades funcionales y los escenarios de calidad relevantes estén suficientemente definidos.
- El sistema actual esté descrito con evidencia y limitaciones explícitas.
- La arquitectura objetivo tenga bloques, responsabilidades, relaciones y vistas pertinentes.
- Las decisiones importantes tengan justificación y consecuencias registradas.
- Los riesgos, brechas y asuntos pendientes estén visibles.
- Exista una estrategia de evolución verificable hacia la implementación.

No es necesario que todas las secciones arc42 tengan el mismo nivel de detalle. La documentación debe ser suficiente para comprender, evaluar, comunicar y evolucionar la arquitectura.

---

## Principio rector

**La ruta curricular define qué conceptos debemos aprender y aplicar. arc42 organiza cómo describimos la arquitectura. El Cotizador de Bordados aporta el contexto real, la evidencia y las necesidades que guían el diseño.**
