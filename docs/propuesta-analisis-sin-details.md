# Analisis posibles sin nuevos pipelines ni details

Este documento organiza los analisis que se pueden hacer ahora sin correr ningun
pipeline de generacion nuevo y sin disponer de los artifacts detallados
(`pred.json`, `gold.json`, `task.json` por corrida). La idea es explotar tres
fuentes disponibles:

- `data/test`: tasks, schemas, outputs gold y metadatos.
- `data/dev` y corpus FSP: schemas y ejemplos usados por retrieval.
- `results/final_results*.json`: metricas por task ya agregadas
  (`tps`, `gold_keys`, `system_keys`, tiempos, tokens, status, error).

La restriccion importante es que, sin predicciones por campo, no se puede
descomponer F1/precision/recall por tipo de campo real. Si hace falta ese
analisis, se necesitan details o re-ejecutar guardando details. Lo que si se
puede hacer es analizar resultados por propiedades del schema, del retrieval y
del costo.

## 1. Retrieval-only sobre todo el test

Este es el analisis mas importante que no requiere llamadas al modelo. El
retrieval es determinista para una task y el corpus FSP, y es compartido por los
pipelines RAG single-call y por los trials RAG de Mixed-SC.

Para cada task del test:

- Determinar si hay ejemplos same-schema en el corpus FSP usando el mismo
  fingerprint estructural que usa el sistema.
- Registrar si el retrieval oficial entraria por la ruta same-schema o por el
  fallback de field-RAG.
- Para casos same-schema:
  - ids de los candidatos same-schema;
  - scores de similitud same-schema;
  - ejemplos seleccionados por el retrieval oficial;
  - posicion del primer y segundo ejemplo en el corpus;
  - distribucion de similitud entre test y corpus.
- Para casos sin same-schema:
  - ranking por field score independiente;
  - par complementario seleccionado por el retrieval oficial;
  - top-2 independiente por score;
  - score del par complementario;
  - score del top-2 independiente;
  - ganancia de complementariedad;
  - cobertura de campos de la query por los ejemplos recuperados;
  - mejor campo FSP alineado para cada campo del schema test.

Salidas recomendadas:

- `analysis/retrieval_only/test_retrieval_trace.json`
- `analysis/retrieval_only/test_retrieval_by_task.csv`
- `analysis/retrieval_only/retrieval_summary.md`

Tablas/figuras para el paper:

- Conteo de tasks same-schema vs non-same-schema.
- Histograma de scores same-schema.
- Histograma de field scores en casos non-same-schema.
- Comparacion par complementario vs top-2 independiente.
- Mapa de dominios/schema types recuperados para cada dominio test.

## 2. Cruzar retrieval-only con resultados finales

Una vez producido el retrieval-only, se puede cruzar por `task_id` con
`results/final_results*.json`. Esto permite evaluar si el rendimiento observado
se asocia a la calidad o tipo de retrieval, sin correr modelos nuevos.

Agrupaciones utiles:

- same-schema vs non-same-schema;
- bins de similitud same-schema;
- bins de field score en non-same-schema;
- bins de ganancia de complementariedad;
- tasks donde el par complementario difiere del top-2 independiente;
- tasks donde ambos ejemplos recuperados vienen del mismo dominio vs dominios
  distintos;
- tasks con retrieval de alta cobertura de campos vs baja cobertura.

Metricas por grupo:

- F1, precision y recall micro usando `tps`, `gold_keys`, `system_keys`;
- tokens promedio;
- tiempo promedio;
- tasa de `calls=0`;
- tasa de `status != PASS`;
- diferencia entre `system_keys` y `gold_keys`.

Interpretacion valida:

- Se puede decir que el rendimiento es mayor o menor en grupos definidos por el
  retrieval.
- Se puede usar como evidencia diagnostica de utilidad o limitaciones del RAG.
- No conviene presentarlo como causalidad completa sin la ablation de retrieval.

## 3. RAG vs baseline con resultados existentes

Ya hay resultados finales para:

- Gemma baseline.
- Gemma `enriched-schema-rag`.
- Qwen baseline.
- Qwen `enriched-schema-rag`.

Analisis posibles:

- Delta task-level de RAG sobre baseline.
- Delta por schemas vistos/no vistos.
- Delta por same-schema/non-same-schema retrieval.
- Delta por bins de score retrieval.
- Delta por complejidad del task (`gold_keys`, numero de campos, nesting).
- Casos donde RAG mejora mucho, empeora mucho o no cambia.

Tablas recomendadas:

- RAG vs baseline por modelo.
- RAG vs baseline por seen/unseen schema.
- RAG vs baseline por same-schema/non-same-schema.
- Top improvements y top regressions por task.

Este es uno de los analisis mas defendibles para el paper, porque usa una
comparacion real contra baseline ya corrida.

## 4. Mixed-SC vs extractores single-call

Sin details internos no se pueden ver votos, acuerdos ni candidatos, pero si se
puede medir la utilidad externa de self-consistency.

Comparaciones disponibles:

- Gemma `mixed-extractors-self-consistency-rag` vs Gemma
  `enriched-schema-rag`.
- Gemma `mixed-extractors-self-consistency-rag` vs Gemma
  `enriched-inline-reasoning-rag`.
- Qwen `mixed-extractors-self-consistency-rag` vs Qwen
  `enriched-schema-rag`.

Analisis:

- Delta F1/precision/recall por task y agregado.
- Delta por seen/unseen schema.
- Delta por same-schema/non-same-schema retrieval.
- Delta por complejidad estructural.
- Costo adicional: tokens, calls y tiempo.
- Eficiencia: ganancia de F1 por aumento de tokens/tiempo.
- Casos donde Mixed-SC recupera fallos del single extractor.
- Casos donde Mixed-SC empeora respecto al single extractor.

Para el paper, este analisis puede justificar Mixed-SC como mecanismo de
robustez, aunque no permita explicar internamente cada decision de agregacion.

## 5. Reasoning con lo disponible

No hay resultados Qwen para `enriched-inline-reasoning-rag`, asi que el analisis
de reasoning debe limitarse a Gemma:

- Gemma `enriched-inline-reasoning-rag` vs Gemma `enriched-schema-rag`.

Sin details no se puede medir por tipo de campo real, pero si por composicion
del schema:

- tasks con muchos campos string;
- tasks con campos numericos/booleanos;
- tasks con enums;
- tasks con arrays;
- tasks con arrays de objetos;
- tasks con objetos anidados;
- tasks con mayor nesting depth;
- tasks con mas `gold_keys`.

Metricas:

- delta F1/precision/recall;
- delta de tokens;
- delta de tiempo;
- cambio en `system_keys - gold_keys`;
- tasa de fallos o `calls=0`.

Lectura para el paper:

- Presentar como trade-off de reasoning por tipo de schema, no por tipo de campo.
- Indicar explicitamente que el analisis field-level requiere details.

## 6. Analisis estatico del schema y composicion del test

Usando solo `data/test` se puede caracterizar el benchmark y explicar por que
ciertos subsets son mas dificiles.

Features por task:

- schema title o fingerprint;
- seen/unseen respecto a dev;
- numero de campos top-level;
- numero de hojas flatten con `expand_lists=False`;
- numero de required fields;
- presencia de arrays;
- presencia de arrays de objetos;
- presencia de objetos anidados;
- presencia de enums;
- presencia de numeric/boolean/date fields;
- nesting depth;
- longitud del input;
- longitud del schema;
- dominio inferido por `task_id`.

Cruces con resultados:

- performance por numero de campos;
- performance por `gold_keys`;
- performance por presencia de arrays;
- performance por nesting;
- performance por dominio;
- performance por seen/unseen.

Estos analisis son seguros y utiles para contextualizar los resultados
experimentales.

## 7. Rendering Pydantic vs JSON Schema original

Sin correr modelos nuevos no se puede medir el impacto causal del rendering
Pydantic, pero si se puede hacer un analisis estatico de prompt/schema.

Para cada task:

- longitud en caracteres del JSON Schema original;
- longitud aproximada en tokens del JSON Schema original;
- longitud del rendering Pydantic plain;
- longitud del rendering Pydantic reasoned;
- diferencia absoluta y porcentual;
- numero de lineas;
- numero de definiciones/classes;
- numero de fields renderizados;
- casos donde Pydantic compacta;
- casos donde Pydantic expande.

Uso en el paper:

- Justificar Pydantic como representacion estructural legible y compacta en
  muchos schemas.
- Evitar afirmar mejora empirica especifica si no hay ablation corrida.
- Reportar como analisis de costo de prompt y diseño, no como resultado causal.

## 8. Fallos, underproduction y overproduction

`final_results` permite estudiar robustez sin predicciones.

Analisis:

- tasks con `calls=0`;
- tasks con `system_keys=0`;
- tasks con `system_keys < gold_keys`;
- tasks con `system_keys > gold_keys`;
- distribucion de `system_keys - gold_keys`;
- status/error por pipeline y modelo;
- fallos comunes a todos los pipelines;
- fallos especificos de modelo;
- relacion con tiempo, tokens, schema size, input length y retrieval subset.

Esto ayuda a explicar por que precision y recall difieren aun con schemas
required y `additionalProperties=false`: la salida final puede ser error,
timeout, parse failure, output parcial o respuesta sin JSON valido.

## 9. Costo: tokens y tiempos

Los `final_results` ya guardan tokens y elapsed por task.

Analisis:

- tokens promedio y total por pipeline/modelo;
- tiempo promedio y maximo;
- calls totales;
- costo por F1;
- costo incremental de reasoning;
- costo incremental de Mixed-SC;
- relacion tokens vs F1 task-level;
- relacion tiempo vs F1 task-level;
- tasks outlier de costo.

Tablas para paper:

- Performance/cost summary por pipeline/modelo.
- Delta de costo y delta de F1 para Mixed-SC.
- Delta de costo y delta de F1 para reasoning en Gemma.

## 10. Comparacion Gemma vs Qwen

Con los resultados existentes se puede comparar:

- baseline Gemma vs baseline Qwen;
- `enriched-schema-rag` Gemma vs Qwen;
- Mixed-SC Gemma vs Qwen.

Agrupaciones:

- all tasks;
- sin los 18 `calls=0` comunes;
- seen/unseen;
- same-schema/non-same-schema;
- schema complexity bins;
- domain.

Preguntas:

- Que modelo mejora mas con RAG respecto a su baseline.
- Que modelo aprovecha mas Mixed-SC.
- Donde Qwen o Gemma fallan de forma diferencial.
- Si los errores de `calls=0` son comunes o especificos.

## 11. Analisis no recomendados sin details

Estos analisis deberian posponerse o marcarse como no disponibles:

- F1/precision/recall exacto por tipo de campo.
- Comparacion constrained decoding vs free JSON decoding.
- Self-consistency por acuerdo interno, votos o estabilidad de candidatos.
- Analisis de errores semanticos por campo.
- Ablation causal de Pydantic rendering.
- Ablation causal de RAG complementario vs top-2 independiente.
- Ablation same-schema primer ejemplo vs segundo ejemplo.

Algunos se pueden aproximar por features del schema o por retrieval-only, pero
no deben presentarse como metricas field-level o ablations completas.

## 12. Prioridad de implementacion

Prioridad alta:

1. Script retrieval-only para todo `data/test`.
2. Join retrieval-only + `final_results`.
3. RAG vs baseline por modelo y subset.
4. Mixed-SC vs single-call por modelo y subset.
5. Schema composition + performance.

Prioridad media:

6. Reasoning Gemma por composicion del schema.
7. Cost/performance tokens y tiempos.
8. Fallos, `calls=0`, underproduction y overproduction.

Prioridad baja:

9. Analisis estatico Pydantic vs JSON Schema.
10. Tablas de outliers y casos cualitativos candidatos.

## 13. Artefactos finales esperados

Scripts sugeridos:

- `scripts/analyze_retrieval_only.py`
- `scripts/analyze_final_results_with_retrieval.py`
- `scripts/analyze_schema_composition.py`
- `scripts/analyze_cost_tradeoffs.py`

Outputs sugeridos:

- `analysis/retrieval_only/`
- `analysis/final_results_crosscuts/`
- `analysis/schema_composition/`
- `analysis/cost_tradeoffs/`

Material directamente usable en el paper:

- Tabla principal de performance/cost por pipeline/modelo.
- Tabla RAG vs baseline por seen/unseen y same-schema/non-same-schema.
- Tabla Mixed-SC vs single extractor por subset.
- Figura de distribucion de retrieval scores.
- Figura de delta RAG-baseline por complejidad.
- Figura de delta Mixed-SC por costo.
- Parrafo de limitaciones: no details, no field-level F1, no causal claims para
  ablations no corridas.
