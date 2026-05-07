# Propuesta de pipeline: enriched-inline-reasoning-self-consistency

## Objetivo

Crear un pipeline de self-consistency encima de `enriched-inline-reasoning`.

La idea base es ejecutar varias llamadas independientes al SLM con el mismo prompt enriquecido y el mismo schema estricto, obtener varios outputs finales candidatos, y despues agregarlos campo a campo con una estrategia consciente del schema.

Nombre implementado:

`enriched-inline-reasoning-self-consistency`

El pipeline conserva las fortalezas de `enriched-inline-reasoning`:

- prompt con schema tipo Pydantic;
- wrapper top-level `{reasoning, value}`;
- GCD/structured output contra el schema instrumentado;
- postproceso que devuelve solo los `value`;
- FSP del Quijote, ahora enriquecido con un campo verbatim largo.

Y suma:

- varias muestras por task;
- budget dinamico por task;
- parametros de sampling configurables;
- agregacion modular para scalars, objetos y arrays;
- diagnostics de agregacion en el trace final.

## Hipotesis

`enriched-inline-reasoning` mejora una llamada individual, pero sigue siendo sensible a variacion de sampling y a errores locales:

- omite items de arrays;
- cambia etiquetas de entidades;
- devuelve strings demasiado cortos para campos verbatim;
- rellena algunos campos nullable de forma inconsistente;
- escoge enums distintos cuando el texto admite varias lecturas.

Self-consistency deberia ayudar cuando la respuesta correcta aparece de forma estable en una parte suficiente de los trials. En esos casos, la agregacion puede:

1. estabilizar campos escalares;
2. corregir labels de objetos agrupados por identidad;
3. construir arrays item-wise mejores que cualquier array individual;
4. descartar outliers de bajo soporte;
5. dejar trazabilidad de por que gano cada valor.

La hipotesis no es que self-consistency arregle todo. Si todos o casi todos los trials cometen el mismo error, el agregador lo va a reforzar. Esto se vio en campos string que piden fragmentos verbatim: cuando la mayoria devuelve solo la entidad corta, el consenso escoge la entidad corta.

## Restricciones

- La llamada base sigue siendo `enriched-inline-reasoning`.
- Cada trial usa el mismo schema wrapper estricto de `inline-reasoning`.
- El output de cada trial se desenvuelve con `unwrap_inline_reasoning_output`.
- La agregacion se hace sobre outputs finales, no sobre reasonings.
- No hay una llamada adicional al SLM para juzgar o reparar.
- No se verifica evidencia textual en postproceso; se considero demasiado fragil para esta fase.
- La cantidad de trials se decide por task, con presupuesto de tokens y tiempo.
- El trace debe guardar cada trial como step separado y un step final de agregacion.

## Diferencias con `enriched-inline-reasoning`

### Frente a una sola llamada

`enriched-inline-reasoning` hace:

1. construir prompt enriquecido;
2. llamar al SLM una vez;
3. desenvolver `{reasoning, value}`;
4. devolver el JSON final.

`enriched-inline-reasoning-self-consistency` hace:

1. construir el mismo prompt enriquecido;
2. estimar presupuesto inicial de trials;
3. llamar al SLM varias veces con sampling;
4. desenvolver cada salida;
5. recalcular presupuesto despues de cada trial;
6. agregar los candidatos campo a campo;
7. guardar diagnostics con clusters, soportes, candidate arrays y decision final.

### Frente a votar el output completo

No se elige un trial completo como ganador.

Eso seria demasiado rigido: un trial puede tener buen `headline` y mal `date`, mientras otro tiene buen `date` y malos arrays. La agregacion se hace por campo y, para arrays, por item.

## Prompt base

El prompt base sigue siendo el de `enriched-inline-reasoning`.

Se hizo un ajuste al FSP: el ejemplo del Quijote se mantiene como unico ejemplo, pero su schema/output se enriquecen localmente con un campo adicional:

`literary_impact_evidence`

Ese campo pide un fragmento verbatim largo y el output demuestra que `value` debe copiar el fragmento minimo completo, no una etiqueta corta como `novela moderna`.

Tambien se agrego una regla global:

```text
Si un campo pide fragmento verbatim/source text/evidence, copia el fragmento minimo completo del texto que responde la pregunta; no devuelvas solo la entidad o respuesta normalizada.
```

Esto intenta atacar el fallo observado en tasks como `cultural_extraction_001` y `cultural_extraction_002`, donde el modelo tiende a devolver solo `Martin Campbell` o `Anna Torv y Sam Reid` aunque el schema pide un fragmento verbatim.

## Sampling

Cada trial llama al mismo modelo con la misma entrada, pero con sampling configurable.

Defaults implementados:

- `GENSIE_SC_TEMPERATURE=0.5`
- `GENSIE_SC_TOP_K` opcional via `extra_body={"top_k": ...}`
- `GENSIE_SC_TOP_P` opcional
- `GENSIE_SC_MAX_TOKENS` opcional
- `GENSIE_SC_FIRST_TEMPERATURE` opcional para hacer el primer trial distinto

La temperatura por defecto sigue la recomendacion general de self-consistency: generar diversidad razonable sin perder demasiado grounding.

## Budget dinamico de trials

La cantidad de trials no es fija globalmente. Se estima por task con:

- tokens de prompt;
- estimacion de completion tokens;
- duracion observada;
- limite total de tokens;
- limite total de tiempo;
- max/min trials configurables.

Defaults implementados:

- `max_trials = 12`
- `min_trials = 1`
- `token_budget = 32000`
- `token_budget_ratio = 0.85`
- `time_budget_s = 60`
- `time_budget_ratio = 0.85`
- `completion_token_safety_factor = 1.5`
- `time_safety_factor = 1.15`

El primer estimate se hace con fallback aproximado. Despues de cada trial, si hay usage real, se recalcula:

- prompt tokens por trial;
- max completion tokens observado, multiplicado por safety factor;
- peor duracion observada, multiplicada por safety factor.

Esto explica casos como `environmental_ecology_001`, donde el estimate inicial permitia 5 trials, pero despues de observar completions mas grandes el limite por tokens bajo a 4.

Variables decidibles:

- `GENSIE_SC_MAX_TRIALS`
- `GENSIE_SC_MIN_TRIALS`
- `GENSIE_SC_DYNAMIC_TRIALS`
- `GENSIE_SC_TOKEN_BUDGET`
- `GENSIE_SC_TOKEN_BUDGET_RATIO`
- `GENSIE_SC_TIME_BUDGET_S`
- `GENSIE_SC_TIME_BUDGET_RATIO`
- `GENSIE_SC_COMPLETION_TOKEN_SAFETY_FACTOR`
- `GENSIE_SC_TIME_SAFETY_FACTOR`
- `GENSIE_SC_CHARS_PER_TOKEN`
- `GENSIE_SC_TRIALS` como fallback legacy para max trials

## Agregacion general

La agregacion vive en `SchemaAwareSelfConsistencyAggregator`.

Conceptualmente:

```text
aggregate(outputs, schema)
  si object: agregar cada propiedad recursivamente
  si array: construir consenso item-wise
  si scalar: clusterizar valores y elegir representante
```

Para cada valor se crean `ValueCandidate` con:

- `value`
- `trial_index`
- `item_index` para items de arrays

Los candidatos se agrupan en `ValueCluster`. El soporte de un cluster es el numero de trials distintos que lo contienen.

Los clusters se ordenan por:

1. mayor soporte;
2. primera posicion observada.

Esto se aplica tanto a matching difuso como a matching exacto. Es importante para enums, numeros y booleanos: si `ENVIRONMENT` aparece dos veces y `OTHER` una, debe ganar `ENVIRONMENT` aunque `OTHER` haya aparecido primero.

## Strings

Para strings se usa clustering por similitud.

Default:

`GENSIE_SC_STRING_SIMILARITY=lexical`

La similitud lexical combina:

- match exacto;
- F1 de tokens;
- F1 de char n-grams.

Una vez elegido el cluster ganador, el valor final es el medoid del cluster: el candidato mas central respecto a los demas miembros.

Esto ayuda para strings tipo summaries, donde no es razonable esperar repeticion exacta.

Limitacion observada:

- para campos verbatim, el cluster mayoritario puede ser la respuesta corta;
- si el gold exige el fragmento largo y la mayoria dice solo la entidad, el medoid no corrige eso.

Decision pendiente posible:

- detectar campos verbatim por description/name y usar un agregador string especializado;
- dentro de un cluster o familia de strings relacionados, preferir candidatos mas largos que contengan la respuesta corta;
- bajar el threshold para agrupar fragmentos cortos y largos de la misma evidencia;
- elegir el fragmento largo si tiene soporte no trivial y cubre semanticamente al corto.

## Similaridad por embeddings

Hay una estrategia opcional:

`FastEmbedStringSimilarity`

Se activa con:

`GENSIE_SC_STRING_SIMILARITY=fastembed`

Variables:

- `GENSIE_SC_EMBEDDING_MODEL`
- `GENSIE_SC_EMBEDDING_WEIGHT`

La implementacion carga `fastembed` lazy y cae a lexical si el paquete/modelo no esta disponible.

Esto esta pensado para el setup donde se pueda empaquetar un modelo de embeddings pequeño dentro del contenedor. Por defecto no se usa, porque lexical es mas barato, reproducible y sin dependencia adicional.

## Enums, numeros y booleanos

Estos campos usan matching exacto.

Casos:

- enum;
- integer;
- number;
- boolean.

La regla correcta es mayoria por soporte, con tie-break por primera posicion. Esto se documento porque se encontro un bug: el branch exacto agrupaba por valor pero devolvia los grupos en orden de insercion. Eso podia hacer ganar `OTHER` aunque `ENVIRONMENT` tuviera mas soporte. Se corrigio ordenando tambien los clusters exactos.

## Nullables

Los nulls se tratan aparte.

Si todos los valores son null, se devuelve null cuando el schema lo permite.

Si hay valores no-null, se compara el soporte del mejor cluster no-null contra `null_count`.

Default:

- null gana si tiene mas soporte estricto que el mejor no-null;
- no gana empates, salvo que se active `null_wins_ties`.

Variable:

`GENSIE_SC_NULL_WINS_TIES`

Ejemplo observado:

En `environmental_ecology_001`, `date` quedo `null` porque 3/4 trials devolvieron null y solo uno devolvio una fecha parcial. Self-consistency no pudo reconstruir `13 al 17 de noviembre de 2014` porque eso exigia combinar fecha del cuerpo con año del titular.

## Objetos

Los objetos se agregan recursivamente campo a campo.

Para campos requeridos se agregan siempre. Para propiedades opcionales dentro de objetos no-root, se exige soporte minimo segun:

`GENSIE_SC_OPTIONAL_PROPERTY_SUPPORT_RATIO`

Default:

`0.50`

Esto reduce propiedades espurias que aparecen en pocos trials.

## Arrays

Los arrays son la parte mas delicada.

No se elige el array completo mas repetido. En extraccion, puede que ningun trial tenga el array perfecto; por eso se hace item-wise.

Pipeline de arrays:

1. aplanar items de todos los trials;
2. deduplicar items casi identicos dentro de cada trial;
3. clusterizar items entre trials;
4. agregar cada cluster para obtener un item representativo;
5. construir candidate arrays desde clusters;
6. seleccionar el mejor candidate array.

### Arrays de simples

Para strings:

- clustering por similitud string;
- threshold default `GENSIE_SC_ARRAY_STRING_THRESHOLD=0.78`;
- soporte minimo default `GENSIE_SC_SIMPLE_ITEM_SUPPORT_FLOOR=2`.

Para enum/number/bool:

- matching exacto;
- soporte minimo igual.

### Arrays de objetos

Hay dos modos:

1. comparar objetos completos por schema-aware similarity;
2. detectar un campo identidad y clusterizar por ese campo.

El modo actual intenta detectar identidad por defecto.

Variables:

- `GENSIE_SC_USE_IDENTITY_CLUSTERING`
- `GENSIE_SC_IDENTITY_MIN_SCORE`
- `GENSIE_SC_IDENTITY_MIN_MARGIN`
- `GENSIE_SC_IDENTITY_STRING_THRESHOLD`

## Campos identidad

El selector implementado es `HeuristicIdentityFieldSelector`.

Busca campos que parecen identificar un item del array, no atributos secundarios.

Puntua positivamente:

- campo requerido;
- string libre;
- nombres como `text`, `name`, `title`, `reaction`, `symptom`, `ingredient`, `entity`, `mention`;
- descriptions con `verbatim`, `name`, `mention`, `source`, `ingredient`, `symptom`, `adverse effect`, `reaction`.

Penaliza:

- enums, numeros, booleanos;
- nombres como `label`, `category`, `class`, `type`, `probability`, `frequency`, `impact`, `severity`, `amount`, `unit`, `date`, `year`, `count`, `score`, `is_`, `has_`.

Ejemplos esperados:

- `entities[]`: identidad `text`, no `label`;
- `ingredients[]`: identidad `name`, no `amount`/`unit`;
- `symptoms[]`: identidad `name`, no `severity_level`;
- `side_effects[]`: identidad `reaction`, no `probability`/`impact`.

La razon de esto es que en arrays de objetos los atributos secundarios pueden variar entre trials. En NER, por ejemplo, `Hollywood` puede aparecer como `LOCATION` o `ORGANIZATION`, pero el item es el mismo por `text`. Primero conviene juntar por mension y despues votar/agregar sus subcampos.

Limitacion:

El campo identidad no siempre es una llave unica perfecta. En algunos schemas puede haber duplicados reales con la misma identidad primaria y distinto atributo secundario. Por eso esto debe seguir siendo configurable y ablation-friendly.

## Construccion de candidate arrays

Hay builders modulares:

### `SupportThresholdArrayCandidateBuilder`

Crea arrays con clusters cuyo soporte supera ciertos floors.

Los floors salen de:

- `simple_item_support_floor` u `object_item_support_floor`;
- ratios `support_ratios`.

Defaults:

- floor base simple: `2`;
- floor base objeto: `2`;
- ratios: `0.40`, `0.50`, `0.60`.

### `GreedyMbrArrayCandidateBuilder`

Empieza con array vacio y agrega clusters que mejoran el expected utility contra los arrays observados.

Esto sirve como candidato mas MBR/central.

### Original arrays

Se puede incluir arrays originales como candidatos, pero por defecto esta apagado:

`GENSIE_SC_INCLUDE_ORIGINAL_ARRAY_CANDIDATES=False`

El objetivo es permitir que el final sea una recombinacion mejor que cualquier trial individual.

Variables:

- `GENSIE_SC_INCLUDE_GREEDY_ARRAY_CANDIDATE`
- `GENSIE_SC_INCLUDE_THRESHOLD_ARRAY_CANDIDATES`
- `GENSIE_SC_INCLUDE_ORIGINAL_ARRAY_CANDIDATES`
- `GENSIE_SC_SIMPLE_ITEM_SUPPORT_FLOOR`
- `GENSIE_SC_OBJECT_ITEM_SUPPORT_FLOOR`

## Seleccion de arrays

Hay dos selectores:

### `MbrArrayCandidateSelector`

Elige el candidate array con mayor similitud esperada contra los arrays observados.

Fortaleza:

- precision-biased;
- evita incluir muchos items debiles.

Debilidad:

- puede dejar fuera items correctos de soporte medio porque el array mas corto queda ligeramente mas central.

### `RecallBiasedMbrArrayCandidateSelector`

Default actual.

Primero calcula el score MBR de todos los candidatos. Luego toma todos los candidatos dentro de una tolerancia respecto al mejor score y elige el mas largo.

Default:

`GENSIE_SC_ARRAY_SELECTOR=recall_biased_mbr`

Tolerancia:

`GENSIE_SC_RECALL_MBR_TOLERANCE=0.06`

Esto se hizo porque en extraccion suele doler mas omitir un item correcto que incluir un item con soporte razonable. En los resultados locales ayudo a recuperar items como `Nakatomi`, `Hollywood` y fechas cuando aparecian con soporte medio.

Variable para ablation:

`GENSIE_SC_ARRAY_SELECTOR=mbr`

## Diagnostics y tracing

Cada trial se guarda como step independiente:

```text
self_consistency_trial_01
self_consistency_trial_02
...
```

El step final:

```text
self_consistency_aggregate
```

incluye:

- `trials`;
- `trial_errors`;
- `budget_estimates`;
- `final_candidates`;
- `aggregation_diagnostics`;
- `final_output`.

Los diagnostics incluyen por campo:

- strategy;
- schema type;
- sample/null count;
- final value;
- clusters;
- soporte;
- trial indices;
- representative;
- member values;
- candidate arrays;
- scores MBR;
- selected candidate index;
- identity field decision cuando aplica.

Tambien se ajusto el resumen del CLI para distinguir:

- requests reales al modelo;
- steps de agregacion;
- duracion de modelo;
- duracion de agregacion.

Esto evita que el aggregate cuente como llamada al SLM o distorsione la duracion promedio de request.

## Variables de configuracion

### Sampling

- `GENSIE_SC_TEMPERATURE`
- `GENSIE_SC_FIRST_TEMPERATURE`
- `GENSIE_SC_TOP_P`
- `GENSIE_SC_TOP_K`
- `GENSIE_SC_MAX_TOKENS`

### Budget

- `GENSIE_SC_MAX_TRIALS`
- `GENSIE_SC_MIN_TRIALS`
- `GENSIE_SC_TRIALS`
- `GENSIE_SC_DYNAMIC_TRIALS`
- `GENSIE_SC_TOKEN_BUDGET`
- `GENSIE_SC_TOKEN_BUDGET_RATIO`
- `GENSIE_SC_TIME_BUDGET_S`
- `GENSIE_SC_TIME_BUDGET_RATIO`
- `GENSIE_SC_COMPLETION_TOKEN_SAFETY_FACTOR`
- `GENSIE_SC_TIME_SAFETY_FACTOR`
- `GENSIE_SC_CHARS_PER_TOKEN`

### String similarity

- `GENSIE_SC_STRING_SIMILARITY=lexical|fastembed`
- `GENSIE_SC_EMBEDDING_MODEL`
- `GENSIE_SC_EMBEDDING_WEIGHT`

### Scalar/object/array aggregation

- `GENSIE_SC_SCALAR_STRING_THRESHOLD`
- `GENSIE_SC_ARRAY_STRING_THRESHOLD`
- `GENSIE_SC_OBJECT_ITEM_THRESHOLD`
- `GENSIE_SC_SIMPLE_ITEM_SUPPORT_FLOOR`
- `GENSIE_SC_OBJECT_ITEM_SUPPORT_FLOOR`
- `GENSIE_SC_OPTIONAL_PROPERTY_SUPPORT_RATIO`
- `GENSIE_SC_INTRA_TRIAL_DEDUPE_THRESHOLD`
- `GENSIE_SC_NULL_WINS_TIES`

### Identity clustering

- `GENSIE_SC_USE_IDENTITY_CLUSTERING`
- `GENSIE_SC_IDENTITY_MIN_SCORE`
- `GENSIE_SC_IDENTITY_MIN_MARGIN`
- `GENSIE_SC_IDENTITY_STRING_THRESHOLD`

### Array candidates/selection

- `GENSIE_SC_INCLUDE_GREEDY_ARRAY_CANDIDATE`
- `GENSIE_SC_INCLUDE_THRESHOLD_ARRAY_CANDIDATES`
- `GENSIE_SC_INCLUDE_ORIGINAL_ARRAY_CANDIDATES`
- `GENSIE_SC_ARRAY_SELECTOR=mbr|recall_biased_mbr`
- `GENSIE_SC_RECALL_MBR_TOLERANCE`

## Lo que es decidible

### Numero de trials

Si se quiere mas estabilidad, subir `GENSIE_SC_MAX_TRIALS` y/o presupuestos. Si se quiere controlar coste, bajar max trials o ratios.

El punto sensible es que pocos trials pueden hacer que soporte 1 sea demasiado ruidoso y soporte 2 parezca fuerte. Muchos trials hacen mas confiables los thresholds.

### Temperature/top-k

Si hay demasiada variacion o hallucination, bajar temperature.

Si todos los trials repiten el mismo error, subir temperature puede producir candidatos alternativos utiles. `top_k=40` es una opcion alineada con self-consistency si el backend la soporta.

### String similarity

`lexical` es barato y estable.

`fastembed` puede ayudar en summaries o strings parafraseados, pero cuesta RAM/dependencias y puede agrupar strings semanticamente cercanos que no deberian mezclarse cuando el schema pide verbatim.

### Thresholds de strings

Subir thresholds aumenta precision de clusters.

Bajarlos aumenta recall, pero puede mezclar respuestas distintas. Para verbatim, bajar threshold puede ayudar a agrupar fragmentos cortos y largos de la misma evidencia, si despues se usa una seleccion sesgada a fragmento completo.

### Identity clustering

Activarlo ayuda en arrays de objetos cuando hay un campo obvio como `text` o `name`.

Apagarlo sirve para ablation o schemas donde una misma identidad primaria puede representar varios items distintos.

### Selector de arrays

`mbr` es mas conservador.

`recall_biased_mbr` es mejor cuando los gold arrays tienden a contener items de soporte medio.

La tolerancia controla cuanto recall se acepta:

- menor tolerancia: mas parecido a MBR puro;
- mayor tolerancia: mas items, mas riesgo de falsos positivos.

### Support floors

Floor `2` protege contra items solitarios.

Pero si hay pocos trials o si el modelo omite mucho, puede borrar items correctos. En `environmental_ecology_001`, `Tokai` y `Universidad de La Serena` aparecieron solo en 1/4 trials, por lo que el array final de organizaciones quedo vacio.

Permitir floor `1` o incluir original arrays podria mejorar recall, pero tambien mete ruido como paises mal puestos como organizaciones.

### Null policy

Con `null_wins_ties=False`, un valor no-null de igual soporte que null puede sobrevivir.

Con `true`, el pipeline se vuelve mas conservador en campos nullable.

### Verbatim strings

Este es el punto mas abierto.

Hay que decidir si se implementa un modo especializado para descriptions que contienen `verbatim`, `source text`, `evidence`, `fragment`.

Opciones:

1. seguir con medoid general;
2. preferir el candidato mas largo dentro del cluster ganador;
3. si hay un cluster corto mayoritario y un cluster largo minoritario que contiene al corto, elegir el largo si supera un soporte minimo;
4. usar embeddings para detectar que el fragmento largo responde lo mismo que el corto;
5. hacer un postproceso textual local que busque en input_text el fragmento que contiene la respuesta corta.

La opcion 5 parece tentadora pero fue descartada por ahora porque la comprobacion de evidencia textual puede volverse compleja y fragil.

## Resultados cualitativos observados

### Fortalezas

- Estabiliza campos con respuestas repetidas.
- En arrays de objetos, identity clustering corrige labels variables.
- Recall-biased MBR recupera items de soporte medio.
- El trace permite auditar por que el final quedo como quedo.
- El budget dinamico evita exceder tokens/tiempo por task.

### Debilidades

- No recupera items con soporte cero.
- Puede borrar items correctos de soporte 1 por floors conservadores.
- En strings verbatim, la mayoria corta gana contra la minoria larga.
- En fechas o summaries que requieren combinar partes del texto, el consenso no inventa una composicion si ningun trial la produjo.
- Si el modelo confunde sistematicamente la categoria, self-consistency solo estabiliza la confusion.

## Tests recomendados

Ya hay tests para:

- strings con medoid;
- arrays de strings item-wise;
- arrays de objetos;
- deteccion de identity fields;
- uso de identity field antes de agregar subcampos;
- selector recall-biased;
- agente con varios trials y step aggregate;
- limite dinamico por token budget;
- default cap mayor que 3;
- registro del pipeline;
- FSP enriquecido con campo verbatim;
- prompt con reglas antes del FSP.

Tests adicionales convenientes:

- enum exacto mayoritario gana aunque aparezca despues;
- strings verbatim cortos vs largos;
- support floor `1` en arrays con pocos trials;
- ablation `GENSIE_SC_ARRAY_SELECTOR=mbr`;
- ablation `GENSIE_SC_USE_IDENTITY_CLUSTERING=0`;
- fastembed fallback cuando no existe el modelo;
- diagnostics de identity field en arrays de objetos con `$ref`.

## Riesgos

- Mas llamadas implica mas coste y mas tiempo.
- El sampling puede producir diversidad util o ruido.
- El budget dinamico puede cortar antes de lo esperado si un trial tarda mucho.
- Los thresholds son sensibles al numero de trials.
- Identity heuristics pueden elegir mal en schemas raros.
- Recall-biased arrays pueden incluir falsos positivos si la tolerancia es alta.
- El FSP verbatim puede no ser suficiente para cambiar el comportamiento sistematico del SLM.
- Los diagnostics son voluminosos, aunque valiosos para debug.

## Decision recomendada

Mantener este pipeline como variante experimental fuerte de `enriched-inline-reasoning`, no como reemplazo automatico.

Configuracion recomendada para seguir probando:

```text
GENSIE_SC_MAX_TRIALS=12
GENSIE_SC_TEMPERATURE=0.5
GENSIE_SC_TOP_K=40
GENSIE_SC_ARRAY_SELECTOR=recall_biased_mbr
GENSIE_SC_RECALL_MBR_TOLERANCE=0.06
GENSIE_SC_USE_IDENTITY_CLUSTERING=1
GENSIE_SC_STRING_SIMILARITY=lexical
```

Siguientes mejoras mas prometedoras:

1. agregador especializado para strings verbatim;
2. politica de arrays que pueda considerar items de soporte 1 cuando el numero de trials es bajo y el candidate array tiene buen MBR;
3. mejor tratamiento de fechas que combinan fecha explicita con año implicito en titulo;
4. test y ablation sistematicos de `mbr` vs `recall_biased_mbr`;
5. evaluar embeddings solo para summaries/inferencias, no para todo string verbatim.

