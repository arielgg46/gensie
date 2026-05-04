# Propuesta de pipeline: inline-reasoning

## Objetivo

Implementar un pipeline de una sola llamada que fuerce al SLM a producir razonamiento local por campo dentro del propio JSON generado. La salida generada por el modelo no sera directamente la respuesta final de GenSIE: sera una version instrumentada del schema donde cada campo de primer nivel contiene:

- `reasoning`: string con analisis breve, evidencia textual y justificacion.
- `value`: respuesta final del campo, con el mismo tipo/schema que el campo original.

Despues de la llamada, el pipeline reconstruye el output oficial extrayendo solo los `value` de cada campo.

La hipotesis es que este formato obliga al modelo a mirar el texto y el schema campo por campo, pero sin pagar varias consultas ni depender de loops de self-correction. Es mas caro que `simple-clean-schema` en tokens de salida, pero sigue siendo una sola llamada.

## Nombre

`inline-reasoning`

## Idea central

El pipeline usa dos schemas distintos con propositos distintos:

- **Schema legible en prompt:** configurable. Puede ser el schema final limpio de `simple-clean-schema`, o una vista modificada con `{reasoning, value}` para que el modelo vea exactamente el formato que debe producir.
- **Schema de generacion/GCD:** schema derivado del `target_schema` original, modificado para envolver cada propiedad de primer nivel en un objeto `{ reasoning, value }`.

El schema original no se pierde. Se conserva dentro de cada `value` y se usa para reconstruir la salida oficial.

Ademas, el pipeline puede insertar un ejemplo few-shot de `data/dev_rev/cultural_literature_001.json`. Este ejemplo se anadio porque, sin una demostracion concreta, el SLM tendia a producir reasonings pobres, incompletos o sin citas textuales estrictas. La idea del FSP no es ensenar el dominio literario, sino ensenar el formato de razonamiento esperado: que cite, justifique y despues coloque la respuesta final en `value`.

## Restricciones principales

- Una sola consulta al modelo por `Task`.
- No hay segunda llamada, retry con modelo ni repair semantico.
- El prompt puede funcionar zero-shot o con un ejemplo few-shot controlado por constante.
- El schema del prompt es configurable por constante: puede mostrarse como schema final limpio o como schema modificado con `{reasoning, value}`.
- El schema de GCD se modifica solo para forzar razonamiento inline.
- La conversion del schema no es recursiva: solo afecta a las propiedades directas del objeto raiz.
- El output devuelto por el agente debe ser el JSON oficial, sin `reasoning`.

## Diferencia con `simple-clean-schema`

`simple-clean-schema` intenta mejorar el baseline solo con prompting y schema limpio en el prompt. El schema usado para GCD es el original.

`inline-reasoning` mantiene el mismo prompt base, pero cambia el schema de generacion para que el modelo tenga que completar una mini-traza por cada campo antes de dar el valor final.

En la version actual tambien puede incluir un FSP. Esto lo vuelve menos minimalista que `simple-clean-schema`, pero sigue siendo una sola consulta. El coste extra se paga en tokens de entrada y se justifica si mejora la calidad del `reasoning`: citas textuales, nulls grounded y explicaciones completas.

Ejemplo conceptual:

Schema original:

```json
{
  "type": "object",
  "properties": {
    "director": {
      "type": ["string", "null"],
      "description": "Verbatim span answering who directed the movie"
    },
    "release_year": {
      "type": ["integer", "null"]
    }
  }
}
```

Schema de generacion:

```json
{
  "type": "object",
  "properties": {
    "director": {
      "type": "object",
      "properties": {
        "reasoning": { "type": "string" },
        "value": {
          "type": ["string", "null"],
          "description": "Verbatim span answering who directed the movie"
        }
      },
      "required": ["reasoning", "value"],
      "additionalProperties": false
    },
    "release_year": {
      "type": "object",
      "properties": {
        "reasoning": { "type": "string" },
        "value": {
          "type": ["integer", "null"]
        }
      },
      "required": ["reasoning", "value"],
      "additionalProperties": false
    }
  }
}
```

Output generado por el modelo:

```json
{
  "director": {
    "reasoning": "The field asks for a verbatim span answering who directed the movie. The source says: \"tras las camaras de 'Cleaner' esta uno de los mejores directores de accion de los 90 y los 00: Martin Campbell.\" This supports the answer as the complete relevant span.",
    "value": "tras las camaras de 'Cleaner' esta uno de los mejores directores de accion de los 90 y los 00: Martin Campbell."
  },
  "release_year": {
    "reasoning": "The field asks for a release year, but the text does not state one. Since null is allowed, the value should be null.",
    "value": null
  }
}
```

Output oficial reconstruido:

```json
{
  "director": "tras las camaras de 'Cleaner' esta uno de los mejores directores de accion de los 90 y los 00: Martin Campbell.",
  "release_year": null
}
```

## Semantica del `reasoning`

El campo `reasoning` debe pedir explicitamente cuatro cosas, en este orden:

1. Que se identifique que pide el campo.
2. Que se cite estrictamente la parte o partes del texto que soportan la respuesta, o que se diga que no hay evidencia textual.
3. Que se razone brevemente como se pasa de la evidencia al valor.
4. Que se indique que el valor final se coloca solo en `value`.

No hace falta que sea largo. De hecho, deberia ser corto y verificable. La utilidad viene de obligar al modelo a aterrizar la respuesta antes de producir el valor, no de generar una cadena extensa.

## Reglas por tipo de campo

### Campos simples

Aplica a:

- `string`
- `boolean`
- `integer`
- `number`
- `enum`
- variantes `anyOf` / `type` que incluyan `null`

Cada campo se envuelve con su propio `reasoning` y `value`.

El razonamiento debe ser individual:

- Para strings: citar el span relevante; si la descripcion pide verbatim, preferir el fragmento completo relevante, no solo la entidad minima.
- Para numeros: citar el fragmento textual y justificar la normalizacion.
- Para booleanos: citar evidencia positiva/negativa; si no hay evidencia y el boolean no permite null, justificar `false` solo si esa es la convencion del schema.
- Para enums: citar evidencia y explicar por que se elige exactamente una opcion del enum.
- Para nulls: declarar que el texto no da evidencia suficiente y que `null` esta permitido por el schema.

### Arrays de simples

Para campos como `list[str]`, `list[int]`, `list[enum]`:

- Un solo `reasoning` para todo el array.
- `value` contiene el array completo.
- El reasoning debe citar las partes del texto que soportan los items.
- Debe justificar listas vacias cuando no hay items respaldados.

Esto evita un schema demasiado grande con razonamiento por item, y evita que arrays largos exploten el output.

### Objetos

Para campos objeto:

- Un solo `reasoning` antes del objeto completo.
- `value` mantiene el schema original del objeto, sin envolver recursivamente sus propiedades.

La razon es pragmatica: envolver recursivamente objetos anidados puede volver el schema enorme, confuso para SLMs y dificil de postprocesar. Ademas, muchos objetos representan una unidad semantica compacta donde un razonamiento global del campo basta.

### Arrays de objetos

Para arrays de objetos:

- Un solo `reasoning` antes del array completo.
- `value` mantiene el array original, con sus items objeto intactos.

Este caso es especialmente importante en tareas como `medical_drug`, donde `side_effects` puede ser una lista larga de objetos con campos internos como reaccion, sistema, frecuencia e impacto. Envolver cada campo interno multiplicaria mucho la salida y probablemente empeoraria la adherencia.

El razonamiento del campo debe explicar:

- Que lista se esta extrayendo.
- De que seccion o fragmentos del texto salen los items.
- Que mapeos semanticos se aplican de forma general, por ejemplo frecuencia textual a enum o severidad clinica.
- Por que la lista puede estar vacia si no hay evidencia.

## Transformacion del schema de generacion

Entrada: `task.target_schema`.

Salida: `reasoning_schema`.

Reglas:

- Copiar profundamente el schema original.
- Conservar `$defs` del schema original en la raiz para que los `$ref` dentro de `value` sigan resolviendo.
- La raiz debe seguir siendo `type: object`.
- Para cada propiedad directa de `schema["properties"]`, reemplazar la propiedad por:

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "reasoning": {
      "type": "string",
      "description": "Brief field-level reasoning. First explain what the field asks for; quote exact supporting text or say no textual evidence exists; explain the inference/normalization; then put the final answer only in value."
    },
    "value": ORIGINAL_FIELD_SCHEMA
  },
  "required": ["reasoning", "value"]
}
```

- La conversion no baja a propiedades internas de objetos ni a items de arrays de objetos.
- Si el campo original usa `$ref`, `value` conserva ese `$ref`.
- Si el campo original tiene `anyOf` con `null`, `value` conserva ese `anyOf`.
- Si el campo original tiene `enum`, `value` conserva el `enum`.
- Si el campo original tiene `description`, `value` la conserva.
- El `required` de la raiz modificada deberia incluir todas las propiedades de primer nivel para forzar que haya razonamiento y value por campo.

Punto a decidir en implementacion:

- Mantener tambien el `required` original en algun metadato interno no es necesario para GCD, pero puede ayudar para debugging.
- Para OpenAI Structured Outputs estrictos, puede ser mejor hacer `required` de todos los campos de primer nivel. Si algun campo original no era requerido, igualmente se obliga a producir su wrapper; el `value` puede ser `null`, `[]`, `false` o el valor que el schema permita.

## Schema mostrado en el prompt

Hay dos vistas posibles para el schema que se incluye como texto en el prompt. La eleccion se controla con una constante de codigo, no con `--pipeline`, para poder alternar rapido durante experimentos sin registrar pipelines adicionales:

- `INLINE_PROMPT_SCHEMA_FINAL_VALUES`: muestra el schema final limpio, igual que `simple-clean-schema`. En esta vista, el prompt explica verbalmente que la generacion real va envuelta en `{reasoning, value}`.
- `INLINE_PROMPT_SCHEMA_REASONING_WRAPPER`: muestra tambien el wrapper de primer nivel con `reasoning` y `value`. Esta es la vista preferida actualmente, porque hace mas explicito el formato que debe producir el SLM.

La vista `reasoning-wrapper` para prompt no es exactamente igual al schema de GCD. Es una version legible y reducida:

- Cada campo de primer nivel pasa a ser un objeto con `reasoning` y `value`.
- `reasoning` solo tiene `{"type": "string"}`; no incluye `description`, para reducir ruido.
- La `description` original del campo se mueve al objeto que engloba `reasoning` y `value`.
- `value` conserva el tipo/schema original limpio del campo, pero sin la `description` que ya fue movida al wrapper.
- Se sigue eliminando ruido como `additionalProperties`, `title`, `default` y `required` en el schema mostrado en prompt.

Ejemplo de vista para prompt:

```json
{
  "type": "object",
  "properties": {
    "author": {
      "type": "object",
      "description": "The primary author or creator of the work",
      "properties": {
        "reasoning": { "type": "string" },
        "value": { "type": "string" }
      }
    }
  }
}
```

Esta vista existe porque solo decir "razona y luego responde" no fue suficiente: el modelo necesitaba ver que `reasoning` es una parte estructural del output, no una instruccion opcional.

## Few-shot prompting

El pipeline incluye una opcion de few-shot prompting controlada por constante:

`INCLUDE_INLINE_REASONING_FEW_SHOT = True | False`

El ejemplo usado es `data/dev_rev/cultural_literature_001.json` (`Don Quijote de la Mancha`) porque es curated, relativamente compacto y cubre varios comportamientos utiles:

- strings directos (`title`, `author`);
- normalizacion numerica (`publication_year`);
- arrays de simples (`genres`, `key_themes`);
- null grounded (`original_language`);
- razonamiento sobre un caso donde hay informacion tentadora pero no suficientemente explicita.

El bloque FSP incluye:

- `INSTRUCCION DEL EJEMPLO`: `task.instruction` mas la `description` externa del schema, incluyendo `Complexity`.
- `INPUT TEXT DEL EJEMPLO`: texto fuente del ejemplo.
- `SCHEMA MODIFICADO DEL EJEMPLO`: schema visible con `{reasoning, value}`.
- `OUTPUT DEL EJEMPLO`: JSON completo con reasonings y values.

Los reasonings del ejemplo son deliberadamente completos:

- dicen que pide el campo;
- citan fragmentos exactos del texto;
- explican como se pasa de la evidencia al valor;
- justifican normalizacion, listas y nulls;
- dejan la respuesta final solo en `value`.

La motivacion practica fue que, sin este FSP, el SLM era demasiado laxo: producia reasonings genericos, sin citas textuales, o simplemente repetia el valor con una frase pobre. El FSP funciona como una demostracion concreta de "razonamiento grounded", no como memoria de dominio.

## Postprocesamiento

El output crudo del modelo tiene forma:

```json
{
  "field_a": { "reasoning": "...", "value": ... },
  "field_b": { "reasoning": "...", "value": ... }
}
```

El output oficial debe reconstruirse como:

```json
{
  "field_a": ...,
  "field_b": ...
}
```

Reglas:

- Para cada propiedad de primer nivel del schema original, tomar `raw[field]["value"]`.
- Ignorar `reasoning`.
- No modificar valores internos.
- No hacer reparaciones semanticas.
- Si falta un wrapper o falta `value`, devolver una estructura de error o fallback controlado, pero no hacer una segunda llamada.

Recomendacion:

- Guardar en tracing tanto el output crudo como el output final reconstruido. El score usa el output final, pero el crudo es clave para debug.

## Prompt propuesto

El prompt parte de `simple-clean-schema`, pero ahora debe explicar que el schema de generacion esta instrumentado y, opcionalmente, mostrar un ejemplo few-shot antes de la tarea real.

### System

```text
Eres un motor experto de extraccion de informacion en espanol.
Devuelve solo el objeto JSON requerido por el schema.
Usa solo evidencia del texto fuente.
Para cada campo de primer nivel, escribe tu razonamiento antes del valor final.
En cada reasoning, cita texto exacto cuando exista evidencia, o indica que no hay evidencia textual.
```

### User

Estructura sugerida:

```text
{optional_few_shot_example}

TAREA:
Extrae informacion estructurada del TEXTO FUENTE en espanol.
El SCHEMA muestra el formato generado: cada campo de primer nivel contiene reasoning y value.

INSTRUCCION:
{task.instruction}
{root_description}

FORMATO DE RAZONAMIENTO:
- En cada campo, completa primero reasoning y despues value.
- reasoning debe citar evidencia textual exacta o indicar que no existe, y justificar inferencias, enums, normalizaciones o nulls.
- value contiene solo la respuesta final, sin explicaciones.
- En objetos, arrays de objetos y arrays de simples, haz un unico reasoning para todo el campo y luego rellena value completo. No repitas elementos.
- Si un string pide verbatim, usa el span relevante completo cuando sea posible.

SCHEMA:
{prompt_schema_json}

TEXTO FUENTE:
{task.input_text}
```

## Implementacion propuesta

### 1. Reutilizar limpieza del schema para prompt

Reusar `clean_schema_for_prompt` y el estilo de `build_simple_clean_schema_prompt`.

La vista del schema en prompt debe ser configurable por constante:

- una vista de valores finales limpios;
- una vista wrapper con `{reasoning, value}`.

La vista wrapper es la preferida actualmente, pero conviene mantener la otra para ablation.

### 2. Crear transformador de schema para GCD

Helper sugerido:

`build_inline_reasoning_schema(schema: dict) -> dict`

Responsabilidades:

- Copiar profundamente el schema.
- Validar que la raiz sea objeto con `properties`.
- Construir una raiz nueva con:
  - `type: object`
  - `$defs` original si existe
  - `additionalProperties: false`
  - `properties` transformadas
  - `required` con todas las propiedades de primer nivel
- Para cada propiedad:
  - crear wrapper `{ reasoning, value }`
  - poner el schema original del campo en `value`
  - no transformar nada dentro de `value`

### 3. Crear builder de prompt

Helper sugerido:

`build_inline_reasoning_prompt(task: Task) -> str`

Responsabilidades:

- Usar el schema visible segun `INLINE_PROMPT_SCHEMA_VIEW`.
- Incluir instruction, descripcion externa, reglas de razonamiento y texto.
- Insertar el bloque FSP cuando `INCLUDE_INLINE_REASONING_FEW_SHOT` este activo.
- Mantener el schema de GCD separado del schema mostrado en prompt.

Helpers adicionales:

- `build_inline_reasoning_prompt_schema(schema: dict) -> dict`: crea la vista legible con `{reasoning, value}`, moviendo la `description` original al wrapper y dejando `reasoning` como string sin description.
- `build_inline_reasoning_few_shot_example() -> str`: construye el bloque de ejemplo con instruction, schema description, input text, schema modificado y output razonado.

### 4. Crear agente

Clase sugerida:

`InlineReasoningAgent(GenSIEAgent)`

Responsabilidades:

- Construir `prompt = build_inline_reasoning_prompt(task)`.
- Construir `reasoning_schema = build_inline_reasoning_schema(task.target_schema)`.
- Enviar `response_format` con `reasoning_schema`, no con `task.target_schema`.
- Hacer una sola llamada.
- Parsear JSON crudo.
- Reconstruir output final con `unwrap_inline_reasoning_output(raw_output, task.target_schema)`.
- Devolver el output final.
- Registrar en tracing:
  - prompt
  - request payload con schema modificado
  - response cruda
  - opcionalmente output final reconstruido en metadata/metrics o archivo auxiliar si el tracing lo permite

### 5. Postprocesador

Helper sugerido:

`unwrap_inline_reasoning_output(raw: dict, original_schema: dict) -> dict`

Responsabilidades:

- Iterar sobre `original_schema["properties"]`.
- Para cada campo:
  - si `raw[field]` es dict y contiene `value`, usar ese `value`.
  - si falta, decidir error controlado.
- No validar contra Pydantic ni modificar tipos.

Politica recomendada ante errores:

- Si el wrapper falta por completo, devolver `None` para ese campo solo si el schema original permite null; si no, devolver un error top-level puede ser mas honesto.
- En la primera version, preferir fallo explicito con `{"error": ...}` antes que inventar valores. Si GCD funciona, este caso deberia ser raro.

### 6. Registro del pipeline

En `OfficialParticipant`:

- Registrar `"inline-reasoning": InlineReasoningAgent()`.
- Agregar `PipelineInfo`.

Tener en cuenta el limite de pipelines si aplica. Este pipeline es candidato a reemplazar una variante que este rindiendo peor.

## Tests recomendados

- El transformador no muta el schema original.
- El schema modificado conserva `$defs`.
- Cada propiedad de primer nivel se convierte en objeto con `reasoning` y `value`.
- `value` es igual al schema original del campo.
- La transformacion no es recursiva dentro de objetos.
- La transformacion no es recursiva dentro de arrays de objetos.
- La raiz modificada requiere todas las propiedades de primer nivel.
- El prompt puede usar el schema limpio final o la vista wrapper segun constante.
- La vista wrapper de prompt incluye `reasoning` como `{"type": "string"}` sin description.
- La vista wrapper de prompt mueve la `description` original del campo al objeto que engloba `reasoning` y `value`.
- El FSP se puede activar/desactivar por constante.
- El FSP incluye instruction, descripcion externa del schema, input text, schema modificado y output razonado.
- El agente envia el schema wrapper en `response_format`.
- El postprocesador elimina `reasoning` y conserva solo `value`.
- Caso con `$ref` dentro de `value`.
- Caso con `anyOf` que permite `null`.
- Caso con array simple.
- Caso con array de objetos.

## Evaluacion local

Comparar contra:

- `baseline`
- `simple-clean-schema`

Datasets:

- `data/starter/`
- `data/dev_rev/`
- `data/dev/` si se quiere volumen, sabiendo que `dev_rev` es mas confiable para inspeccion cualitativa.

Metricas:

- Micro-F1.
- Tasa de errores de parseo/postproceso.
- Tokens de salida por instancia.
- Diferencia de F1 por tipo de tarea.
- Campos con null traps.
- Campos enum rigid.
- Listas largas, especialmente `medical_drug`.

Debug cualitativo:

- Revisar reasoning crudo en casos donde el valor final falla.
- Mirar si el modelo cita texto inexistente.
- Comparar con y sin FSP para medir si el coste extra compensa.
- Comparar `INLINE_PROMPT_SCHEMA_FINAL_VALUES` contra `INLINE_PROMPT_SCHEMA_REASONING_WRAPPER`.
- Mirar si el reasoning se vuelve demasiado largo y desplaza presupuesto de output.
- Mirar si arrays de objetos pierden items por el coste de razonar demasiado.

## Riesgos y mitigaciones

- Riesgo: el output es mas largo y puede subir coste/latencia.
  Mitigacion: pedir reasoning breve, una sola vez por campo top-level, y no recursivo.

- Riesgo: el modelo aprende a justificar una respuesta incorrecta.
  Mitigacion: exigir citas exactas y revisar si las citas son realmente del texto.

- Riesgo: en arrays de objetos largos, el reasoning global no basta para cada item.
  Mitigacion: mantenerlo global en primera version por coste; evaluar `medical_drug` y decidir si hace falta una variante especializada.

- Riesgo: el schema wrapper rompe compatibilidad con `$ref`.
  Mitigacion: conservar `$defs` en la raiz y no alterar `$ref` dentro de `value`.

- Riesgo: campos no requeridos originalmente quedan forzados.
  Mitigacion: esto es intencional para obtener reasoning/value por campo; el `value` debe respetar null/empty/default semantic segun schema y evidencia.

- Riesgo: el postprocesador oculta errores de razonamiento.
  Mitigacion: guardar output crudo en trazas para inspeccion.

- Riesgo: strict structured outputs puede rechazar detalles del schema original cuando se anida dentro de `value`.
  Mitigacion: testear con schemas reales de `dev_rev`; si falla, aplicar una compatibilizacion minima al schema de generacion sin cambiar el schema final del prompt.

- Riesgo: el FSP aumenta tokens de entrada y puede sesgar estilo/dominio.
  Mitigacion: usar un ejemplo relativamente general, centrado en formato de razonamiento y grounding; mantener `INCLUDE_INLINE_REASONING_FEW_SHOT` para hacer ablations.

- Riesgo: mostrar el schema wrapper en prompt duplica informacion que ya recibe GCD.
  Mitigacion: mantener `INLINE_PROMPT_SCHEMA_FINAL_VALUES` como alternativa rapida si el wrapper visible degrada resultados o coste.

## Decision recomendada

Implementar `inline-reasoning` como experimento de una sola llamada, mas caro que `simple-clean-schema` pero potencialmente mas robusto en tareas con null traps, enums e inferencia semantica.

La clave es mantener el diseno controlado:

1. Razonamiento solo por campo top-level.
2. `value` conserva exactamente el schema original del campo.
3. El prompt puede mostrar el schema final limpio o el wrapper, con preferencia actual por el wrapper visible.
4. El postprocesador devuelve solo los `value`.
5. El FSP se puede activar para ensenar reasonings completos con citas textuales cuando el modelo no lo hace bien zero-shot.

Si mejora campos dificiles sin degradar demasiado listas largas, puede ser una buena tercera variante junto al baseline y `simple-clean-schema`.
