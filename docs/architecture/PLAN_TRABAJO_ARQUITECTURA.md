# Plan de trabajo
## Aplicación de Arquitectura y Diseño de Software al Cotizador de Bordados

**Documento rector del trabajo**

## 1. Propósito

Aplicar los conocimientos del curso de Arquitectura de Software al proyecto real **Cotizador de Bordados**, que posteriormente se convertirá en una aplicación que se pondrá en práctica.

El proyecto será el contexto común para comprender, analizar y diseñar. Las clases del curso seguirán siendo la referencia académica: no se cambiarán sus conceptos, objetivos ni alcance. Lo que adaptaremos será la forma de practicar y demostrar lo aprendido.

## 2. Fuentes de referencia

### 2.1 Repositorio curricular oficial

- Repositorio: [acuscorp/SoftwareArchitecture](https://github.com/acuscorp/SoftwareArchitecture)
- Ruta curricular: [LEARNING_PATH.md](https://github.com/acuscorp/SoftwareArchitecture/blob/main/LEARNING_PATH.md)

La ruta curricular y los documentos de cada clase son la referencia para identificar el contenido y alcance, respetar la secuencia, consultar objetivos y criterios, y evitar introducir contenidos de clases posteriores antes de tiempo.

### 2.2 Proyecto que será analizado

- Repositorio: [acuscorp/embroidery-price-estimator](https://github.com/acuscorp/embroidery-price-estimator)

Este repositorio contiene el sistema actual que utilizaremos como objeto de análisis. El código podrá consultarse como evidencia sobre su estructura y comportamiento, pero no se modificará en este trabajo.

## 3. Objetivo general

Construir progresivamente una comprensión arquitectónica del Cotizador de Bordados y definir su diseño futuro, aplicando los conocimientos de las clases estudiadas.

Al terminar, debemos contar con un diagnóstico fundamentado del sistema actual, decisiones de diseño y arquitectura justificadas, y una propuesta de arquitectura objetivo que sirva como base para desarrollar la aplicación.

## 4. Alcance y límites

Este trabajo comprende exclusivamente **análisis, arquitectura y diseño**.

### Permitido
- Consultar el código y la documentación existente como fuentes de evidencia.
- Analizar estructura, responsabilidades, relaciones y comportamiento.
- Identificar requisitos, restricciones, riesgos y necesidades.
- Elaborar diagramas, modelos, vistas y documentación de diseño.
- Comparar alternativas y justificar decisiones cuando el contenido de la clase lo requiera.
- Registrar decisiones, dudas y asuntos pendientes.

### Fuera de alcance
- Escribir o modificar código.
- Implementar funcionalidades.
- Ejecutar refactorizaciones.
- Cambiar archivos del repositorio.
- Realizar cambios técnicos en la aplicación.

La implementación se realizará en una etapa posterior, una vez que el diseño y la arquitectura estén suficientemente definidos.

## 5. Etapa 1: Aplicar al cotizador las clases ya estudiadas

Se trabajará en el orden de la ruta curricular. En esta etapa no repetiremos las clases como lecciones teóricas: aplicaremos sus conceptos y criterios al sistema actual.

| Clase y referencia oficial | Aplicación al Cotizador de Bordados |
|---|---|
| **CL01.01.01 — Concepto y propósito de la arquitectura**. [Abrir clase](https://github.com/acuscorp/SoftwareArchitecture/blob/main/Classes/M01%20-%20Pensamiento%20arquitect%C3%B3nico%20y%20fundamentos/CL01.01.01%20-%20Concepto%20y%20prop%C3%B3sito%20de%20la%20arquitectura.md) | Examinar el propósito del sistema, qué necesidades atiende y cómo la arquitectura actual contribuye a ellas. |
| **CL01.02.01 — Distinguir elementos, responsabilidades y relaciones**. [Abrir clase](https://github.com/acuscorp/SoftwareArchitecture/blob/main/Classes/M01%20-%20Pensamiento%20arquitect%C3%B3nico%20y%20fundamentos/CL01.02.01%20-%20Distinguir%20elementos%2C%20responsabilidades%20y%20relaciones.md) | Identificar los elementos del cotizador, sus responsabilidades, relaciones y dependencias. |
| **CL01.02.02 — Conectar estructura, runtime y vistas introductorias**. [Abrir clase](https://github.com/acuscorp/SoftwareArchitecture/blob/main/Classes/M01%20-%20Pensamiento%20arquitect%C3%B3nico%20y%20fundamentos/CL01.02.02%20-%20Conectar%20estructura%2C%20runtime%20y%20vistas%20introductorias.md) | Relacionar la organización estática del sistema con su comportamiento durante la ejecución y representarlo mediante vistas pertinentes. |
| **CL01.03.01 — Arquitectura, diseño e implementación**. [Abrir clase](https://github.com/acuscorp/SoftwareArchitecture/blob/main/Classes/M01%20-%20Pensamiento%20arquitect%C3%B3nico%20y%20fundamentos/CL01.03.01%20-%20Arquitectura%2C%20dise%C3%B1o%20e%20implementaci%C3%B3n.md) | Distinguir qué aspectos del cotizador corresponden a arquitectura, cuáles a diseño y cuáles son detalles de implementación. |
| **CL01.04.01 — Contexto y participantes**. [Abrir clase](https://github.com/acuscorp/SoftwareArchitecture/blob/main/Classes/M01%20-%20Pensamiento%20arquitect%C3%B3nico%20y%20fundamentos/CL01.04.01%20-%20Contexto%20y%20participantes.md) | Identificar el contexto del negocio, los participantes, sus necesidades e intereses y las restricciones relevantes para el sistema. |
| **CL01.05.01 — Decisiones arquitectónicas**. [Abrir clase](https://github.com/acuscorp/SoftwareArchitecture/blob/main/Classes/M01%20-%20Pensamiento%20arquitect%C3%B3nico%20y%20fundamentos/CL01.05.01%20-%20Decisiones%20arquitect%C3%B3nicas.md) | Examinar las decisiones arquitectónicas existentes y las que necesita el cotizador; justificar qué conservar, modificar o decidir. |

**Regla:** el documento oficial de cada clase determina qué conceptos y criterios deben aplicarse. La tabla anterior describe su contexto de aplicación al cotizador; no reemplaza ni redefine el contenido curricular.

## 6. Etapa 2: Reconstruir las clases con el cotizador como caso práctico

Al terminar CL01.05.01, volveremos a recorrer las clases CL01.01.01 a CL01.05.01.

Esta vez reconstruiremos las actividades para que el Cotizador de Bordados sea el caso práctico continuo:

- Los ejemplos se basarán en elementos y situaciones reales del cotizador.
- Los ejercicios pedirán analizar, modelar y diseñar partes del sistema.
- Los diagramas representarán sus elementos, relaciones y comportamientos.
- Las actividades conectarán los conceptos de cada clase con decisiones concretas del proyecto.
- Los resultados se incorporarán progresivamente al diseño arquitectónico de la aplicación.

No se trata de eliminar la teoría ni de cambiar los objetivos de las clases. Se trata de aprender y demostrar esos mismos contenidos con un proyecto que conocemos y que realmente vamos a desarrollar.

## 7. Método de trabajo para cada clase

1. **Consultar la fuente:** revisar el documento oficial de la clase y sus criterios.
2. **Delimitar el alcance:** identificar qué conceptos de esa clase corresponden trabajar, sin adelantar contenidos posteriores.
3. **Ubicar el contexto:** determinar qué partes o necesidades del cotizador permiten aplicar esos conceptos.
4. **Obtener evidencia:** consultar documentación y código existente cuando sea necesario.
5. **Analizar:** explicar cómo se presenta actualmente el concepto en el sistema.
6. **Evaluar:** identificar fortalezas, problemas, limitaciones y aspectos desconocidos.
7. **Diseñar:** elaborar modelos o propuestas dentro del alcance de la clase.
8. **Justificar:** explicar las razones y consecuencias de las decisiones que se planteen.
9. **Documentar:** registrar resultados, decisiones y pendientes para las siguientes clases.

No todos los pasos producirán necesariamente un cambio. Una conclusión válida puede ser conservar el diseño existente o determinar que falta evidencia.

## 8. Clasificación de hallazgos

- **Conservar:** el elemento o decisión actual es adecuado para las necesidades conocidas.
- **Corregir:** existe un problema identificado que requiere corrección.
- **Mejorar:** funciona, pero hay una oportunidad de evolución justificada.
- **Rediseñar:** es necesario replantear su estructura o enfoque.
- **Pendiente de evidencia:** no hay información suficiente para concluir.

Estas categorías describen el resultado del análisis, no implican que vayamos a implementar cambios en este chat.

## 9. Cómo registraremos la información

Mantendremos separadas las siguientes clases de información:

- **Hecho observado:** dato confirmado en el código, documentación o información del negocio.
- **Inferencia:** interpretación razonable derivada de hechos, pero todavía no confirmada.
- **Problema:** comportamiento o condición no deseada respaldada por evidencia.
- **Propuesta:** alternativa de diseño que se somete a evaluación.
- **Decisión aprobada:** decisión aceptada después de analizar sus fundamentos y consecuencias.
- **Pendiente:** pregunta o información que hace falta resolver.

No presentaremos una inferencia como si fuera un hecho ni una propuesta como si ya fuera una decisión aprobada.

## 10. Entregables esperados

- Diagnóstico de la arquitectura actual.
- Inventario de elementos, responsabilidades, relaciones y dependencias.
- Vistas y modelos estructurales y de comportamiento que sean pertinentes.
- Identificación de necesidades, participantes y restricciones.
- Registro de decisiones arquitectónicas (ADR).
- Inventario de fortalezas, problemas y oportunidades.
- Diseño y arquitectura objetivo propuestos.
- Plan de evolución hacia la aplicación que se implementará posteriormente.

Los entregables concretos de cada clase dependerán de sus objetivos y criterios oficiales.

## 11. Reglas para evitar desviaciones

1. Respetar la secuencia de la ruta curricular oficial.
2. Consultar la clase original antes de definir sus actividades.
3. Mantener los conceptos, objetivos y alcance de cada clase.
4. Utilizar el cotizador como contexto de aplicación, no como excusa para cambiar el contenido académico.
5. No repetir teoría sin conectarla con el proyecto.
6. No adelantar contenidos de clases posteriores.
7. No proponer soluciones sin identificar el problema o necesidad que atienden.
8. No asumir que todo lo existente está mal ni que se necesita una arquitectura nueva.
9. No convertir preferencias tecnológicas en requisitos sin justificación.
10. Distinguir hechos, inferencias, propuestas y decisiones aprobadas.
11. No escribir ni modificar código en este trabajo.
12. Utilizar los resultados de cada clase como entrada para las siguientes.
13. Registrar los temas que correspondan a etapas posteriores sin desviar la actividad actual.

## 12. Criterio de finalización

La primera etapa termina cuando hayamos aplicado al cotizador los criterios de CL01.01.01 a CL01.05.01.

La segunda etapa termina cuando hayamos reconstruido las actividades de esas clases utilizando el cotizador como caso práctico y contemos con los artefactos de análisis y diseño correspondientes.

El trabajo de arquitectura y diseño estará suficientemente consolidado cuando exista una propuesta de arquitectura objetivo, respaldada por modelos, requisitos, restricciones y decisiones justificadas, además de un plan de evolución.

La implementación de la aplicación será una etapa posterior y no forma parte de este trabajo.

---

## Principio rector

**Las clases del repositorio definen qué debemos aprender y aplicar. El Cotizador de Bordados define dónde lo vamos a practicar.**

No cambiaremos la materia para adaptarla al proyecto; adaptaremos los ejemplos, ejercicios y evidencias para aprender los mismos conceptos mediante el análisis y diseño del sistema que realmente vamos a construir.
