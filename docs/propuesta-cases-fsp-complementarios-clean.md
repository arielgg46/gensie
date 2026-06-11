# Propuesta: cases FSP complementarios

## Objetivo

Crear nuevos `StructuredFspCase` para FSP/RAG que cubran mejor los schemas del
development set curado (`dev_rev`) sin sobreajustar al modelo a un solo patrón
de salida.

La unidad de trabajo será cada `PREFIJO`, porque ahí se mezclan schema, dominio,
estilo de texto y vocabulario. Algunos prefijos comparten schema con otros, pero
trabajar por prefijo permite controlar mejor qué ejemplos se usan, qué
dualidades interesan y qué estructura deben tener los nuevos `input_text`.

El case final debe seguir la estructura actual de
`src/gensie/fsp/resources/cases/cultural_literature_quijote.json`:

- `source_text`, `instruction` y `schema` como base común.
- `field_examples` con `value`, `tags` y `reasoning` por campo.
- `judge`, cuando aplique, como vista adicional sobre el mismo case.

No conviene guardar prompts cerrados a mano. Los renderers actuales ya pueden
proyectar esa base común a extracción directa, extracción con `Reasoned[T]` y
ejemplos de juez.

## Por Qué Dos Cases

Un solo ejemplo puede sesgar al modelo cuando un campo admite dos regímenes
válidos:

- nullable: `null` vs valor grounded.
- arrays: `[]` vs lista con items.
- booleanos inferidos: `true`/`false`.
- enums: una clase frecuente vs otra menos frecuente.
- campos obligatorios no-null: valor directo vs valor con distractores,
  normalización o ambigüedad controlada.
- campos textuales: fragmento casi verbatim vs síntesis grounded.

Si el único ejemplo de un schema pone un campo nullable en `null`, el modelo
puede aprender que ese campo suele ser `null`. Si el único ejemplo de un array
siempre está poblado, puede inventar items cuando el texto no los sostiene. Por
eso los cases deben venir en pares complementarios.

## Máscara Complementaria

Para cada prefijo se identifican los campos con dualidad útil. Sea `n` la
cantidad de campos duales:

1. Construimos una máscara balanceada con `floor(n / 2)` bits en `1` y
   `ceil(n / 2)` bits en `0`.
2. Mezclamos esa máscara con una semilla reproducible, idealmente derivada del
   `PREFIJO` o del id base del case.
3. Creamos dos cases:
   - case A: `1` significa valor no vacío/no null, `0` significa `null` o `[]`.
   - case B: usa la máscara inversa.

En la práctica, no todos los campos encajan en una máscara estrictamente binaria.
Algunos se controlan como variación cualitativa: enum A vs enum B, texto directo
vs texto con distractores, fecha explícita vs fecha no relacionada, veredicto
verbatim vs síntesis. Esas decisiones deben quedar documentadas antes de generar
los JSON.

## Reglas para Crear Cada Par

Los dos cases de un par deben compartir schema e instrucción, pero usar textos
fuente distintos o suficientemente diferenciados para que cada valor sea natural
y grounded. No basta con cambiar el JSON esperado: el texto debe justificar cada
`value`, `null` o `[]`.

Para campos no duales, conviene variar entidades, cantidades, fechas, enums y
formas de evidencia entre los dos cases. La complementariedad no debe convertir
los ejemplos en clones artificiales.

Los campos requeridos por el schema no se fuerzan a `null` salvo que el schema
lo permita. Si una combinación de la máscara produce un texto poco natural o
contradictorio, se ajusta ese bit y se documenta la excepción.

Los tags deben describir el tipo de razonamiento, no solo el dominio:
`grounded_null`, `empty_array`, `simple_array`, `complex_object_array`,
`date_normalization`, `numeric_normalization`, `enum_classification`,
`long_verbatim_evidence`, `sentinel_pattern`, etc. Esto ayuda al retrieval a
seleccionar ejemplos por forma de problema.

## Criterios de Escritura

Estos criterios aplican tanto a `docs/rag/<prefijo>.md` como a los JSON finales:

- Respetar tildes, eñes y puntuación natural en español.
- Mantener cada `input_text` sintético en un máximo de 1600 caracteres, salvo que
  el usuario indique otra cosa para un prefijo concreto.
- Evitar frases demasiado evidentes o benchmark-aware que revelen directamente
  la decisión esperada, por ejemplo: "no hay un actor", "la reseña no identifica
  a una persona que la dirija", "queda muy claro el reparto principal" o "sin
  nota numérica". El texto debe sonar como una fuente natural, no como una
  explicación del gold.
- Para `null` y arrays vacíos, la ausencia debe inferirse por grounding desde el
  contexto natural más cercano, no por una frase que anuncie mecánicamente la
  ausencia.
- Preferir fragmentos verbatim cuando el campo no pida resumir, normalizar o
  inferir algo distinto. Esto aplica especialmente a arrays como `pros`, `cons`,
  entidades, fragmentos de evidencia y listas de rasgos mencionados.
- Si un campo pide una síntesis, la salida puede ser resumida, pero debe estar
  claramente apoyada por los fragmentos relevantes.
- Los ejemplos primero se escriben y revisan en el `.md`; los JSON solo se
  actualizan cuando el usuario aprueba ese paso.

## Algoritmo de Trabajo por Prefijo

Para cada `PREFIJO` se sigue este flujo:

1. Revisar hasta 2 tasks de ese prefijo en `data/dev_rev`, porque esos son los
   ejemplos curados.
2. Completar con tasks del mismo prefijo en `data/dev` hasta tener 3 ejemplos
   de referencia como mínimo y, cuando haya dudas de estilo, dualidades o
   extracción correcta, ampliar la revisión hasta 5 ejemplos en total. Los
   ejemplos de `data/dev` no deben asumirse como gold perfecto: se usan sobre
   todo para comparar estructura, longitud, tono y distribución de ruido del
   `input_text`, y hay que ser crítico con sus outputs.
3. Crear `docs/rag/<prefijo>.md`.
4. En ese `.md`, escribir primero una versión breve y revisable con:
   - un solo párrafo describiendo el tipo de task;
   - los paths de los 3 a 5 ejemplos revisados;
   - la opinión sobre la dualidad de cada campo del schema;
   - una tabla `Propuesta de los dos ejemplos`, campo por campo;
   - una descripción aproximada de la estructura común de los `input_text`,
     incluyendo una comparación fina con los ejemplos reales de `dev_rev` y
     `dev`: encabezados, presencia o ausencia de `Source:`, longitud,
     secciones, estilo narrativo/descriptivo, densidad de ruido y forma de
     mencionar ausencias sin frases benchmark-aware.
5. El usuario revisa ese `.md` y corrige la propuesta.
6. Revisar las modificaciones del usuario y, en el mismo `.md`, añadir una
   sección con el `input_text`, el `output` esperado y los `reasoning` de los dos
   cases. Antes de escribir el texto final, comprobar que los dos ejemplos
   cubren las dualidades de los campos del schema de forma complementaria. Esta
   cobertura de dualidades es más estricta que imitar perfectamente el estilo
   superficial del `input_text`: el estilo debe alinearse finamente con `dev`,
   pero no a costa de dejar campos sin contraste `null`/no `null`, lista
   vacía/lista poblada, enum alternativo, cantidad explícita/ausente u otras
   variaciones importantes. Los `reasoning` deben escribirse ya con la
   estructura final: `field_asks`, `relevant_fragments` y `final_value`.
7. El usuario revisa esos `input_text`, `output` y `reasoning`, y vuelve a
   indicar cambios si hacen falta.
8. Solo después de esa aprobación, generar los JSON finales en
   `src/gensie/fsp/resources/cases`.
9. Al generar los JSON, añadir `field_examples`, `tags` y `reasoning` por campo,
   validarlos con el loader de `gensie.fsp.resources` o con una validación
   estructural equivalente, y dejarlos en `src/gensie/fsp/resources/cases`. El
   RAG de extracción carga automáticamente los cases de esa carpeta, excluyendo
   el case fijo `cultural_literature_quijote.json`.

Este flujo mantiene pequeñas las revisiones humanas: primero se valida la
intención, luego los textos y outputs, y al final se produce el recurso
estructurado completo.

## Insights Sobre Citas en Evidence

Estos son aprendizajes para diseñar buenos ejemplos FSP y, más adelante, reglas
de prompt. No son todavía una versión final del prompt.

- La cita debe probar la decisión sobre ese candidato, no demostrar que el
  modelo encontró una frase cualquiera donde aparece el literal.
- La cita debe ser tan corta como sea posible, pero incluir el contexto semántico
  que hace útil al candidato: definición, relación, lista, negación, condición o
  ausencia relevante.
- `relevant_fragments` no debe incluir distractores solo para mostrar que había
  otras opciones. Sí puede incluir fragmentos cercanos si soportan la decisión,
  desambiguan el campo o ubican semánticamente la información. Por ejemplo:
  `"# 2. COMPOSICIÓN CUALITATIVA Y CUANTITATIVA [...] Cada comprimido contiene
  18 mg de lactosa monohidrato."`.
- Si un fragmento basta para probar la respuesta, se cita solo ese fragmento.
  Los contrastes se incluyen únicamente cuando influyen en la decisión o cuando
  son necesarios para justificar una ambigüedad real.
- `[...]` solo debe usarse para omitir texto intermedio dentro de una cita. No
  debe usarse al inicio o final como marcador de "hay más texto alrededor".
- Si una cita corta ya contiene lo necesario, no se usa `[...]`.
- El `evidence` no debe explicar la mecánica de la cita. No debe decir "la cita
  omite..." ni "no hace falta usar elipsis...". Debe razonar sobre el candidato.
- Para aceptar un candidato, la cita debe mostrar por qué pertenece al campo
  pedido, no solo que el string aparece.
- Para campos con `enum`, `field_asks` debe mencionar explícitamente todos los
  valores permitidos, y `final_value` debe justificar el veredicto apoyándose en
  los fragmentos relevantes inmediatamente anteriores.
- Para rechazar un candidato, la cita debe mostrar la diferencia relevante:
  abreviatura vs nombre completo, forma normalizada vs literal textual, tema vs
  género, evidencia contextual insuficiente, o ausencia de una afirmación
  explícita.
- Para arrays, no hace falta repetir la lista completa en cada candidato. Se
  puede citar la lista completa una vez cuando aporta recall, y en candidatos
  posteriores comprimir alrededor del item: `"con versiones para [...] macOS
  [...]"`.
- Para variantes duplicadas, la evidencia debe preferir el literal más fiel al
  texto y explicar por qué la variante alternativa duplicaría o normalizaría de
  más.
- Para `null`, la evidencia debe citar el contexto más cercano revisado y
  explicar qué afirmación falta. No debe limitarse a decir "no aparece".

## Plan de Cobertura por Prefijo

El orden de trabajo prioriza primero variedad de `Complexity Level`, luego
variedad de schema/description, y finalmente la cobertura de prefijos hermanos
que comparten schema.

### Pasada 0: Prefijo ya iniciado

| Orden | Prefijo | Nivel | Motivo |
| --- | --- | --- | --- |
| 0 | `cultural_media` | L5 | Ya iniciado; cubre crítica cultural, metadatos factuales, opinión, arrays y nulls. |

### Pasada 1: Máxima variedad de complexity level

| Orden | Prefijo | Nivel | Motivo |
| --- | --- | --- | --- |
| 1 | `medical_extraction` | L1 | Extracción literal verbatim; tiene 3 tasks curados en `data/dev_rev`. |
| 2 | `cultural_literature` | L2 | Metadata bibliográfica y temas; ya existe el case del Quijote, pero falta un par complementario. |
| 3 | `cultural_monuments` | L3 | Normalización BIC: códigos, fechas, booleanos y sentinel cuando el schema no permite `null`. |
| 4 | `environmental_ecology` | L4 | Noticias sparse con campos null/missing; es el L4 con más curados en `data/dev_rev`. |
| 5 | `legal_legislation` | L7 | Agregación dispersa de metadata y estado de leyes españolas. |
| 6 | `medical_drug` | L8 | Descripción anidada de medicación, listas y mapping semántico. |
| 7 | `technical_software` | L9 | Descripción técnica con trampas adversariales de null. |
| 8 | `lifestyle_recipes` | L10 | Razonamiento holístico sobre receta, dieta y complejidad. |

### Pasada 2: Completar schemas/descriptions distintos

| Orden | Prefijo | Nivel | Motivo |
| --- | --- | --- | --- |
| 9 | `stem_astronomy_detailed` | L5 | Precisión y normalización numérica/orbital. |
| 10 | `medical_diseases` | L5 | Extracción médica jerárquica de enfermedades y patologías. |
| 11 | `legal_contracts` | L5 | Parámetros centrales y estructura semántica de acuerdos. |
| 12 | `technical_entities` | L5 | Primer representante del schema de entidades categorizadas en una lista. |

### Pasada 3: Cubrir prefijos restantes que comparten schema

| Orden | Prefijo | Nivel | Familia compartida |
| --- | --- | --- | --- |
| 13 | `general_disasters` | L4 | Noticias sparse. |
| 14 | `legal_judicial` | L4 | Noticias sparse. |
| 15 | `medical_health_news` | L4 | Noticias sparse; solo 1 task curado en `data/dev_rev`. |
| 16 | `technical_extraction` | L1 | Extracción literal verbatim. |
| 17 | `cultural_extraction` | L1 | Extracción literal verbatim. |
| 18 | `legal_extraction` | L1 | Extracción literal verbatim; solo 1 task curado en `data/dev_rev`. |
| 19 | `cultural_entities` | L5 | Entidades categorizadas. |
| 20 | `medical_entities` | L5 | Entidades categorizadas. |
| 21 | `legal_entities` | L5 | Entidades categorizadas; solo 1 task curado en `data/dev_rev`. |

## Resultado Esperado

El dataset FSP quedaría como una pequeña biblioteca de ejemplos balanceados.
Cada prefijo tendría un par que enseña los comportamientos críticos: extraer
cuando hay evidencia, abstenerse cuando no la hay y resolver las variaciones
propias del schema sin inventar información. Eso debería reducir
alucinaciones, listas inventadas y sesgos por ejemplo único, manteniendo la
compatibilidad con la implementación actual de `gensie.fsp`.

## Algoritmo para revisión de estilo y descriptions enriquecidas

Esta pasada se hace prefijo por prefijo, uno a la vez, sin modificar los JSONs
finales de `src/gensie/fsp/resources/cases`.

1. Revisar el `.md` existente del prefijo en `docs/rag`.
2. Si el `.md` tiene menos de 5 fuentes revisadas, mirar solo los nombres de
   archivos disponibles en `data/dev_rev` y `data/dev` para ese prefijo y
   seleccionar fuentes adicionales hasta llegar a 5 o al máximo posible. En esta
   selección no se leen todavía las fuentes.
3. Al completar fuentes desde `data/dev`, no elegir siempre solo las siguientes
   por orden inicial: incluir algunos ejemplos finales del prefijo, porque a
   veces los últimos archivos tienen estructuras, estilos o trampas distintas.
4. Revisar todas las fuentes seleccionadas, tanto las que ya estaban en el `.md`
   como las nuevas.
5. Comparar finamente los `input_text` sintéticos contra los revisados:
   encabezados, presencia o ausencia de `Source:`, uso de `[...]`, secciones,
   longitud, estilo narrativo/descriptivo, densidad de ruido, distractores y
   forma natural de expresar ausencias.
6. Si los `input_text` sintéticos no imitan bien el estilo del prefijo,
   modificarlos en el `.md` sin tocar JSONs.
7. Después de cualquier cambio en `input_text`, revisar y corregir si hace falta
   el `output` esperado y todos los `reasoning.relevant_fragments`, para asegurar
   que cada valor siga estando grounded en el texto final.
8. Añadir en el `.md` una tabla `Descriptions enriquecidas para RAG` con una
   fila por campo del schema. Cada description debe estar en español, ser breve
   y útil para prompt: debe explicar cómo extraer el campo y advertir trampas
   típicas observadas, sin volverse una explicación larga.
9. Validar que los bloques JSON embebidos en el `.md` sigan parseando y que los
   `input_text` sintéticos respeten el límite acordado de longitud, salvo
   excepción explícita.
