# Algoritmo de Retrieval FSP RAG con Same Schema Estricto

## Preprocesamiento del corpus FSP para RAG

Para cada ejemplo/case del corpus FSP usado por RAG:

1. Construir el schema normalizado para comparación estructural:
   - Recorrer el JSON Schema de forma recursiva.
   - Reemplazar todo valor de `description` por string vacío.
   - Canonizar el orden de claves de objetos/dicts.
   - Ordenar listas semánticamente no ordenadas, al menos `required`, `enum` y `type` cuando `type` sea array.
   - No reordenar por defecto listas donde el orden pueda ser parte de la interpretación o del renderizado, como `oneOf`, `anyOf`, `allOf` o `items` en forma de tupla, salvo que se decida explícitamente.

2. Calcular y guardar el fingerprint del schema normalizado.

3. Construir y guardar los textos de embeddings por campo, usando la misma lógica de generación de texto que produce `data/fsp_index/dev_field_embeddings.meta.json`.

4. Calcular y guardar los embeddings de esos textos por campo, para reutilizarlos en el algoritmo fallback de similitud campo a campo.

5. Construir un string de similitud global del task/example:
   - `id`
   - `instruction`
   - textos de todos los campos generados en el paso anterior, en orden estable

6. Calcular y guardar el embedding de ese string global, para usarlo en la detección de ejemplos `same_schema`.

## Retrieval en runtime

Para una task nueva:

1. Construir el schema normalizado de la task nueva con el mismo procedimiento del preprocesamiento:
   - `description` vacías.
   - claves canonizadas.
   - `required`, `enum` y `type` array ordenados.

2. Calcular el fingerprint del schema normalizado de la task nueva.

3. Filtrar el corpus FSP y quedarse solo con los examples cuyo fingerprint normalizado sea igual al de la task nueva.

4. Si hay candidatos con fingerprint igual:
   - Construir el string global de la task nueva:
     - `id`
     - `instruction`
     - textos de todos los campos generados con la misma lógica de embeddings por campo
   - Calcular el embedding de ese string global.
   - Comparar ese embedding contra los embeddings globales guardados de los candidatos.
   - Usar similitud coseno como métrica, donde valores más altos significan mayor similitud.
   - Conservar solo candidatos con similitud coseno `>= threshold_same_schema`, inicialmente `0.6` y configurable en el módulo RAG.

5. Si quedan al menos 2 candidatos `same_schema`:
   - Ordenarlos por similitud coseno descendente.
   - Seleccionar los 2 más similares.
   - Renderizarlos como ejemplos `same_schema`, es decir, con el schema en el system prompt y los examples en layout compacto.
   - Terminar el retrieval.

6. Si quedan menos de 2 candidatos `same_schema`:
   - Ejecutar el algoritmo actual de retrieval por embeddings de campos.
   - Este fallback compara la task nueva contra el corpus mediante vectores alineados a los campos de primer nivel de la task.
   - El fallback no puede marcar resultados como `same_schema`, aunque el schema estructural coincida.
   - Los ejemplos seleccionados por fallback se renderizan en el user prompt con el layout normal, sin activar el renderizado compacto de `same_schema`.

## Logging esperado

El `retrieval.json` debe reflejar ambas fases:

1. Fase `same_schema`:
   - fingerprint normalizado de la task nueva.
   - candidatos con fingerprint igual.
   - similitud coseno global por candidato.
   - candidatos descartados por threshold.
   - candidatos seleccionados, si hubo al menos 2.

2. Fase fallback, solo si aplica:
   - schemas/cases considerados.
   - campos de primer nivel de la task nueva en orden.
   - vector de similitudes alineado a esos campos.
   - mejor campo del schema/case candidato para cada campo de la task nueva.
   - casos finalmente seleccionados.
