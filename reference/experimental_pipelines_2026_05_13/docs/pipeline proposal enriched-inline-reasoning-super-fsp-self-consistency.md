# Propuesta de pipeline: enriched-inline-reasoning-super-fsp-self-consistency

## Objetivo

Crear una variante de self-consistency que use como llamada base
`enriched-inline-reasoning-super-fsp`, no el FSP corto del Quijote.

Nombre implementado:

`enriched-inline-reasoning-super-fsp-self-consistency`

La idea es mantener la agregacion modular de
`enriched-inline-reasoning-self-consistency`, pero hacer que cada trial vea el
super FSP sintetico de `super_fsp.py`. Ese ejemplo cubre mas formas de
extraccion que el FSP cultural original: verbatim corto y largo, strings
directos, summaries, enums, fechas, numeros, booleans, nulls grounded, arrays
simples, arrays vacios, arrays de entidades, objetos complejos, arrays con
metricas, enums en array, scores acotados y patrones/sentinels.

## Motivacion

GenSIE premia tres cosas a la vez:

- adherencia estricta al schema JSON;
- valores grounded en el texto fuente;
- buen F1 a nivel de campos aplanados, con exact match para tipos rigidos y
  similitud hibrida para free text.

El self-consistency actual estabiliza respuestas, pero todos sus trials parten
del mismo ejemplo corto. Eso ayuda a formato y razonamiento por campo, pero no
demuestra suficientes subproblemas del benchmark: nulls por informacion
insuficiente, arrays vacios, labels de entidades, normalizacion numerica,
sentinels y evidencias verbatim largas.

El super FSP intenta mover diversidad antes del sampling: cada trial sigue
siendo independiente, pero parte de una demostracion mas amplia y mas cercana a
las trampas del task. La agregacion despues puede aprovechar que mas trials
produzcan candidatos correctos, no solo votar entre errores repetidos.

## Diferencias con el self-consistency actual

La maquinaria de inferencia y agregacion es la misma:

1. construir schema de generacion con wrappers `{reasoning, value}`;
2. ejecutar varios trials con sampling configurable;
3. desenvolver cada output con `unwrap_inline_reasoning_output`;
4. agregar finales campo a campo con `SchemaAwareSelfConsistencyAggregator`;
5. guardar cada trial y el aggregate en tracing.

La diferencia deliberada esta en el prompt base:

- antes: `build_enriched_inline_reasoning_prompt(task)`;
- ahora: `build_enriched_inline_reasoning_super_fsp_prompt(task)`.

El schema estricto de salida no cambia. El super FSP vive solo en el prompt y
no introduce una reparacion posterior ni una llamada adicional al SLM.

## Flujo propuesto

```text
run(task, model)
  prompt = build_enriched_inline_reasoning_super_fsp_prompt(task)
  generation_schema = build_inline_reasoning_schema(task.target_schema)
  budget = TrialBudgetPlanner.estimate(...)

  para cada trial permitido:
    llamar SLM con el prompt super FSP y sampling
    parsear JSON reasoned
    unwrap a valores finales
    actualizar budget dinamico
    trazar self_consistency_trial_NN

  final = SchemaAwareSelfConsistencyAggregator.aggregate(candidatos, schema)
  trazar self_consistency_aggregate
  devolver final
```

## Prompt base con super FSP

`super_fsp.py` define un texto sintetico sobre Atlas-IE y un conjunto de
subtareas reusables. La variante implementada usa el super FSP completo, igual
que el pipeline de una llamada `enriched-inline-reasoning-super-fsp`.

Esto conserva una propiedad importante: el pipeline no depende de ejemplos del
dominio real del task. El ejemplo es sintetico y se usa para ensenar patrones
de extraccion, no contenido.

Patrones que interesa que el SLM copie:

- citar evidencia exacta dentro de `reasoning`;
- devolver `value` limpio, sin explicaciones;
- usar el literal exacto de enums;
- normalizar fechas y numeros solo cuando hay evidencia;
- devolver `null` ante informacion ausente o insuficiente;
- devolver `[]` cuando un array no tiene elementos;
- no resumir campos que piden fragmento verbatim/source text/evidence;
- no omitir campos nullable requeridos por el wrapper.

## Budget

El super FSP aumenta tokens de entrada. Por eso esta variante mantiene el
budget dinamico del self-consistency actual en vez de fijar un numero global de
trials.

Consecuencia esperada:

- con el mismo `GENSIE_SC_TOKEN_BUDGET`, esta variante puede ejecutar menos
  trials que `enriched-inline-reasoning-self-consistency`;
- si el super FSP aumenta la calidad individual, menos trials pueden ser
  suficientes;
- si el modelo sigue cometiendo errores sistematicos, el coste extra puede no
  compensar.

Configuracion inicial recomendada:

```text
GENSIE_SC_MAX_TRIALS=12
GENSIE_SC_TEMPERATURE=0.5
GENSIE_SC_TOP_K=40
GENSIE_SC_ARRAY_SELECTOR=recall_biased_mbr
GENSIE_SC_RECALL_MBR_TOLERANCE=0.06
GENSIE_SC_USE_IDENTITY_CLUSTERING=1
GENSIE_SC_STRING_SIMILARITY=lexical
```

Si el budget recorta demasiado pronto, probar primero:

```text
GENSIE_SC_TOKEN_BUDGET=32000
GENSIE_SC_TOKEN_BUDGET_RATIO=0.90
GENSIE_SC_MAX_TRIALS=8
```

## Agregacion

No se cambia el agregador en esta variante.

La razon es mantener una ablation limpia:

- diferencia A: prompt corto vs prompt super FSP;
- diferencia B, futura: agregador general vs agregador especializado.

Los problemas abiertos del self-consistency original siguen aplicando:

- fields verbatim pueden perder si la mayoria devuelve una respuesta corta;
- items de array con soporte 1 pueden quedar fuera por floors conservadores;
- fechas que requieren combinar partes del texto no se reconstruyen si ningun
  trial produjo el candidato completo;
- errores sistematicos del modelo se pueden reforzar.

La expectativa es que el super FSP reduzca la frecuencia de esos candidatos
malos antes de que lleguen al agregador.

## Tracing

Los nombres de steps se mantienen:

```text
self_consistency_trial_01
self_consistency_trial_02
...
self_consistency_aggregate
```

El `response_format.name` cambia a:

```text
enriched_inline_reasoning_super_fsp_self_consistency
```

Esto permite distinguir la variante en payloads y trazas sin cambiar el formato
de diagnostics.

## Tests recomendados

Ya se cubre lo minimo:

- el pipeline queda registrado en `OfficialParticipant`;
- la variante usa el prompt de Atlas-IE y no el FSP del Quijote;
- el schema de respuesta sigue siendo el wrapper de inline reasoning;
- ejecuta varios trials y agrega los valores finales.

Tests adicionales utiles:

- verificar que el budget permite menos trials que el self-consistency corto con
  el mismo limite de tokens;
- comparar outputs en campos `evidence`/`fragment` para medir si el super FSP
  reduce respuestas demasiado cortas;
- ablation full super FSP vs `build_super_fsp_example_for_schema` dinamico;
- regression para arrays vacios y nulls grounded en tasks con trampas de
  hallucination.

## Riesgos

- El super FSP puede consumir demasiados tokens en schemas grandes.
- Un ejemplo demasiado amplio puede diluir la instruccion real si el modelo es
  pequeno.
- Puede sesgar al modelo hacia el estilo de Atlas-IE, aunque el contenido sea
  sintetico.
- Si hay menos trials, el soporte estadistico de la agregacion baja.
- El FSP completo no siempre sera mejor que una seleccion dinamica de subtareas.

## Decision recomendada

Mantenerlo como variante experimental fuerte y comparable contra:

- `enriched-inline-reasoning-super-fsp`;
- `enriched-inline-reasoning-self-consistency`;
- `enriched-inline-reasoning`.

La pregunta empirica principal es si el aumento de calidad por trial compensa la
reduccion potencial del numero de trials dentro del budget de GenSIE.
