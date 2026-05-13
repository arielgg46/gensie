# Propuesta de pipeline: enriched-inline-reasoning-self-consistency-judge

## Objetivo

Crear una variante de `enriched-inline-reasoning-self-consistency` donde la agregación final no sea heurística, sino una llamada adicional al SLM con rol de juez cuando haya suficiente evidencia comparativa entre trials.

Nombre implementado:

`enriched-inline-reasoning-self-consistency-judge`

## Flujo

1. Ejecuta los trials igual que `enriched-inline-reasoning-self-consistency`.
2. Cada trial usa el schema estricto con campos `{reasoning, value}`.
3. Se desenvuelven los trials para obtener candidatos finales.
4. Si solo hay un trial válido, se omite el juez y ese candidato se usa directamente como salida final.
5. Si hay dos o más trials válidos, se construye un resumen de votos por campo para el juez.
6. El juez recibe instrucción, schema Pydantic con `Reasoned[T]`, texto fuente y votos.
7. El juez devuelve el mismo schema `{reasoning, value}` y el pipeline retorna solo los `value`.

## Fallbacks y robustez

El juez solo aporta valor cuando puede comparar varios candidatos. Por eso, si tras ejecutar los trials queda exactamente un candidato válido, el pipeline no hace la llamada extra al modelo y retorna ese candidato. Esta decisión reduce coste, latencia y riesgo de fallo innecesario.

Si existen varios candidatos válidos pero falla la consulta al juez, el pipeline degrada de forma determinista al primer trial válido y lo usa como salida final. El error del juez queda registrado en el trace (`self_consistency_judge`) junto con `fallback_used=true`, `fallback_reason="judge_failed"` y el `final_output` usado.

Si no hay ningún trial válido, se conserva el comportamiento base de self-consistency: el pipeline devuelve un error porque no existe ningún candidato seguro para usar como fallback.

## Resumen para el juez

Para campos escalares, el prompt agrupa valores distintos:

- `value`
- `count`
- `trial_indices`
- `reasonings`, activable por variable de entorno

Para campos de tipo lista, el prompt agrupa elementos distintos, no listas completas:

- `value`
- `count`
- `trial_indices`

Los reasonings de listas se añaden al final del bloque del campo como `trial_reasonings`, también controlado por una variable distinta.

## Variables nuevas

- `GENSIE_SC_JUDGE_INCLUDE_SCALAR_REASONINGS`: incluye reasonings por valor escalar. Default: `false`.
- `GENSIE_SC_JUDGE_INCLUDE_ARRAY_REASONINGS`: incluye reasonings por trial para campos lista. Default: `false`.
- `GENSIE_SC_JUDGE_TEMPERATURE`: temperatura del juez. Default: `0.0`.
- `GENSIE_SC_JUDGE_TOP_P`: `top_p` opcional del juez.
- `GENSIE_SC_JUDGE_TOP_K`: `top_k` opcional del juez.
- `GENSIE_SC_JUDGE_MAX_TOKENS`: `max_tokens` opcional del juez.

Las variables de trials y sampling base se mantienen iguales a self-consistency:

- `GENSIE_SC_TRIALS`
- `GENSIE_SC_MAX_TRIALS`
- `GENSIE_SC_MIN_TRIALS`
- `GENSIE_SC_DYNAMIC_TRIALS`
- `GENSIE_SC_TEMPERATURE`
- `GENSIE_SC_TOP_P`
- `GENSIE_SC_TOP_K`
- `GENSIE_SC_MAX_TOKENS`

## Hipótesis

La agregación heurística es barata y estable, pero puede perder información cuando la respuesta correcta aparece con bajo soporte o cuando un campo requiere combinar evidencia. El juez puede comparar candidatos, reasonings y texto fuente para decidir mejor, especialmente en:

- campos `null` donde la mayoría podría estar alucinando;
- strings verbatim donde un candidato largo minoritario está mejor fundamentado;
- arrays donde conviene aceptar elementos con soporte parcial;
- enums o inferencias donde el reasoning de un trial explica mejor la categoría correcta.

El coste aumenta por una llamada extra al modelo cuando hay dos o más trials válidos, así que esta variante conviene evaluarla contra la heurística con el mismo número de trials. En casos con un único trial válido, el coste efectivo coincide con self-consistency sin juez porque no se realiza la llamada de agregación.
