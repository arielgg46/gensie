# Propuesta: juez con veredictos por candidato

## Objetivo

Crear una variante del juez de self-consistency donde el modelo no devuelva
directamente `{reasoning, value}` por campo. En su lugar, para cada campo
disputado de primer nivel el juez debe producir un veredicto estructurado que:

- explique qué pide el campo;
- evalúe explícitamente cada candidato observado en los trials válidos dentro de
  `evidence`;
- copie el valor literal de cada candidato en `candidate_value`;
- permita reconstruir el output final fuera de la llamada al juez.

Esta variante no sustituye necesariamente al juez actual. Puede convivir como
otro `AggregationMode` o como una opción de `AggregationSpec`, por ejemplo
`judge_variant="candidate_verdicts"`.

## Dirección actual

La dirección propuesta es que `candidates` sea un array de objetos, no un objeto
con claves de slot.

Para campos simples:

```python
class SingleCandidate[T](BaseModel):
    candidate_value: T
    evidence: str

class SingleVerdict[T](BaseModel):
    field: str
    candidates: list[SingleCandidate[T]]
    value: T
```

Para campos array/lista:

```python
class ArrayCandidate[T](BaseModel):
    candidate_value: T
    evidence: str
    include: bool

class ArrayVerdict[T](BaseModel):
    field: str
    candidates: list[ArrayCandidate[T]]
```

La lista de candidatos concretos vive en el prompt, no en el JSON Schema de
generación. El schema solo valida la forma y los tipos base. Después de la
llamada, el código local valida y, por defecto, reporta como warning que el
modelo devolvió:

- exactamente la misma cantidad de candidatos esperada;
- en el mismo orden;
- con cada `candidate_value` copiado exactamente;
- con `value` igual a uno de los candidatos esperados en campos simples.

Este enfoque sacrifica la garantía dura del decoder sobre cantidad, orden y
valores literales, pero evita que el schema de generación crezca con cada
candidato. Dado que el schema sí cuenta para consumo de tokens en el backend del
challenge, esta es la opción más razonable para no quemar presupuesto ni chocar
con límites de tamaño. La validación puede hacerse estricta por configuración si
se prefiere fallback ante cualquier desviación.

Antes de construir el prompt del juez, los candidatos string se compactan por una
clave normalizada: se decodifican escapes Unicode literales completos cuando
aparezcan como texto, se normaliza Unicode, se eliminan marcas diacríticas
incluida la tilde de `ñ`, se colapsan espacios y se compara con `casefold()`. De
cada grupo se conserva como representante el candidato con más soporte, y el
soporte mostrado pasa a ser `min(total_trials, suma_de_soportes_del_grupo)`.

La salida del juez también queda acotada por prompt: `evidence` debe ser breve.
El schema puede incluir `maxLength` si se activa
`GENSIE_SC_VERDICT_JUDGE_USE_EVIDENCE_MAX_LENGTH=1`, pero queda apagado por
defecto porque Cerebras rechaza ese keyword en `response_format`. Además, el
prompt exige escribir caracteres Unicode reales en español y no secuencias
escapadas `\uXXXX`. Como defensa general, las salidas JSON ya parseadas se
normalizan a Unicode NFC y se decodifican escapes Unicode literales completos si
quedaron dentro de strings. Esto no intenta reparar JSON truncado o escapes
corruptos: la mitigación central es reducir candidatos duplicados y tamaño de
`evidence`.

## Decisión de compatibilidad

La forma ideal para expresar "un candidato por posición, con valor literal
fijado" habría sido usar JSON Schema moderno:

- `prefixItems` para fijar el schema del elemento 1, elemento 2, etc.;
- `const` para forzar que cada `candidate_value` sea exactamente el candidato
  observado;
- `minItems` y `maxItems` para obligar a que el array tenga exactamente todos
  los candidatos.

Esa forma es natural porque `candidates` seguiría siendo un array y el backend
podría forzar cada posición:

```json
{
  "candidates": [
    {
      "candidate_value": "Ceres",
      "evidence": "Fragmento: \"Ceres es un planeta enano [...] situado en el cinturón de asteroides\". El fragmento identifica a Ceres como el objeto descrito y lo presenta como el sujeto principal de la descripción; por eso este candidato sí puede ser el valor real del campo."
    },
    {
      "candidate_value": "1 Ceres",
      "evidence": "Fragmento revisado: \"Ceres es un planeta enano [...] situado en el cinturón de asteroides\". El texto identifica al objeto como Ceres, pero no contiene la designación numerada \"1 Ceres\"; por tanto este candidato no debe elegirse si la extracción debe limitarse al texto fuente."
    }
  ],
  "value": "Ceres"
}
```

Pero no es una base suficientemente portable para GenSIE:

- la descripción del challenge dice que el `target_schema` es un JSON Schema en
  subconjunto OpenAPI 3.0;
- OpenAPI 3.0 no incluye `prefixItems` ni `const`;
- una prueba local con Cerebras rechazó `minItems` y `maxItems` dentro de
  `response_format`;
- por tanto no conviene diseñar el juez sobre keywords que podrían fallar en el
  backend oficial o en proveedores compatibles.

La alternativa anterior con slots `"#1"`, `"#2"`, etc. evitaba esas keywords y
podía forzar presencia y literales usando propiedades requeridas y `enum`
singleton. Sin embargo, también duplicaba todos los candidatos dentro del schema
de generación. Como el schema consume tokens, esa variante puede volverse
demasiado cara o superar límites de tamaño en instancias con muchos candidatos,
arrays largos u objetos grandes.

Por eso se adopta esta regla:

- el prompt enumera candidatos y sus conteos;
- el JSON Schema de generación describe solo la forma de los veredictos y los
  tipos base, con `maxLength` en `evidence` solo si se activa por entorno;
- la validación local garantiza cantidad, orden, copia exacta y pertenencia.

No se cambia el contrato a índices de candidatos. Los índices reducirían la
repetición de `candidate_value`, pero hacen más fácil razonar sobre el candidato
equivocado y no solucionan que `evidence` pueda contener tildes o eñes. La
compatibilidad se mantiene con candidatos literales en el prompt, schema compacto
y defensas de tamaño/normalización.

Existe una variante experimental `candidate_layout="slots"` para proveedores que
no aceptan `minItems`/`maxItems`. En esa variante `candidates` deja de ser array
y pasa a ser un objeto con propiedades requeridas `"1"`, `"2"`, ... hasta `N`,
sin `additionalProperties`. Cada slot sigue conteniendo `candidate_value`,
`evidence` y, en arrays, `include`; por tanto el juez no decide por un índice
opaco sino por el valor literal del candidato. Para ahorrar tokens, los `$defs`
del schema generado usan nombres de un solo carácter en esta variante.

## Contratos de salida

La transformación del schema reducido del juez depende del tipo del campo
original.

### Campo simple

Todo campo de primer nivel que no sea array/lista se transforma en
`SingleVerdict[T]`.

Semántica:

- `field`: razonamiento breve sobre qué pide el campo, a partir del
  `description`, `title`, schema e instrucción original. No debe decidir el
  valor. Debe reformular el objetivo del campo de manera pensada.
- `candidates`: array ordenado con exactamente un objeto por candidato observado.
- `candidate_value`: valor literal del candidato. Debe copiarse exactamente del
  listado del prompt.
- `evidence`: análisis de la evidencia o ausencia de evidencia para ese
  candidato. Debe citar fragmentos verbatim con suficiente contexto. Si omite
  texto intermedio dentro de una cita, debe marcar esa omisión con `[...]`; no
  debe usar `[...]` como prefijo o sufijo decorativo. No basta con citar solo el
  literal del `candidate_value`: la evidencia debe mostrar la oración o contexto
  donde ese literal adquiere sentido, y luego razonar naturalmente si ese
  candidato debe o no ser el valor real del campo.
- `value`: valor final elegido. Debe ser exactamente uno de los
  `candidate_value` esperados para ese campo.

Ejemplo de salida para `official_name`:

```json
{
  "official_name": {
    "field": "El campo pide la denominación o nombre oficial del cuerpo celeste descrito.",
    "candidates": [
      {
        "candidate_value": "Ceres",
        "evidence": "Fragmento: \"Ceres es un planeta enano [...] situado en el cinturón de asteroides\". El fragmento identifica a Ceres como el objeto descrito y lo presenta como el sujeto principal de la descripción; por eso este candidato sí corresponde al nombre que debe extraerse para el campo."
      },
      {
        "candidate_value": "1 Ceres",
        "evidence": "Fragmento revisado: \"Ceres es un planeta enano [...] situado en el cinturón de asteroides\". El texto identifica al objeto como Ceres, pero no contiene la designación numerada \"1 Ceres\"; aunque esa forma pueda ser conocida externamente, no debe elegirse si la extracción debe limitarse al texto fuente."
      }
    ],
    "value": "Ceres"
  }
}
```

### Campo array/lista

Todo campo de primer nivel cuyo schema sea array/lista se transforma en
`ArrayVerdict[T]`, donde `T` es el tipo de cada item del array original.

Semántica:

- `field`: explica qué pide el campo, no qué items deben incluirse.
- `candidates`: array ordenado con exactamente un objeto por item candidato
  observado en los arrays de los trials válidos.
- `candidate_value`: item literal candidato, copiado exactamente.
- `evidence`: análisis de la evidencia o ausencia de evidencia para ese item
  candidato. Debe citar fragmentos verbatim con suficiente contexto. Si omite
  texto intermedio dentro de una cita, debe marcar esa omisión con `[...]`; no
  debe usar `[...]` como prefijo o sufijo decorativo. No basta con citar solo el
  literal del `candidate_value`: la evidencia debe mostrar por qué el item
  pertenece o no al conjunto pedido por el campo.
- `include`: `true` si el item debe incluirse en el array final, `false` si debe
  descartarse.

El array final no lo devuelve el juez directamente. Se reconstruye fuera de la
llamada con todos los `candidate_value` cuyo `include` sea `true`, conservando el
orden de la lista de candidatos del prompt.

Ejemplo:

```json
{
  "key_topics": {
    "field": "El campo pide los temas tratados explícitamente por la obra descrita.",
    "candidates": [
      {
        "candidate_value": "tradición caballeresca",
        "evidence": "Fragmento: \"la obra desmitifica la tradición caballeresca y cortesana\". El contexto no solo menciona el literal, sino que lo presenta como algo tratado por la obra; por eso este item sí corresponde a un tema y debe incluirse.",
        "include": true
      },
      {
        "candidate_value": "narrativa europea",
        "evidence": "Fragmento: \"tuvo una enorme influencia en la narrativa europea posterior\". La narrativa europea aparece como ámbito de recepción o influencia, no como tema interno tratado por la obra; por eso este item debe descartarse para un campo de temas.",
        "include": false
      }
    ]
  }
}
```

## Schema de generación compacto

El schema que se envía en `response_format` no debe listar candidatos concretos.
Su trabajo es validar la estructura general:

- cada campo disputado aparece como `SingleVerdict` o `ArrayVerdict`;
- `candidates` es un array de objetos;
- `candidate_value` conserva el tipo base del campo o del item;
- `evidence` es string;
- `include` existe solo para candidatos de campos array;
- `value` existe solo para campos simples.

En JSON Schema no existen genéricos reales, así que `SingleVerdict[T]` y
`ArrayVerdict[T]` deben materializarse por tipo/forma de valor usado. La regla
de tamaño es importante:

- no crear una definición por candidato;
- no crear una definición por campo si varios campos comparten forma;
- reutilizar `$defs` por tipo estructural: string, nullable string, enum,
  objeto, item de array, etc.;
- si un backend no aceptara `$ref`/`$defs`, inlinear esas definiciones de forma
  mecánica.

Ejemplo compacto para un schema con strings, nullable strings, enum y arrays de
strings:

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "official_name": { "$ref": "#/$defs/SingleStringVerdict" },
    "app_category": { "$ref": "#/$defs/SingleSoftwareTypeVerdict" },
    "license": { "$ref": "#/$defs/SingleStringVerdict" },
    "platforms": { "$ref": "#/$defs/ArrayStringVerdict" },
    "features": { "$ref": "#/$defs/ArrayStringVerdict" },
    "exact_release_date": { "$ref": "#/$defs/SingleNullableStringVerdict" }
  },
  "required": [
    "official_name",
    "app_category",
    "license",
    "platforms",
    "features",
    "exact_release_date"
  ],
  "$defs": {
    "SingleStringVerdict": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "array",
          "items": { "$ref": "#/$defs/SingleStringCandidate" }
        },
        "value": { "type": "string" }
      },
      "required": ["field", "candidates", "value"]
    },
    "SingleNullableStringVerdict": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "array",
          "items": { "$ref": "#/$defs/SingleNullableStringCandidate" }
        },
        "value": {
          "anyOf": [
            { "type": "string" },
            { "type": "null" }
          ]
        }
      },
      "required": ["field", "candidates", "value"]
    },
    "SingleSoftwareTypeVerdict": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "array",
          "items": { "$ref": "#/$defs/SingleSoftwareTypeCandidate" }
        },
        "value": { "$ref": "#/$defs/SoftwareType" }
      },
      "required": ["field", "candidates", "value"]
    },
    "ArrayStringVerdict": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "array",
          "items": { "$ref": "#/$defs/ArrayStringCandidate" }
        }
      },
      "required": ["field", "candidates"]
    },
    "SingleStringCandidate": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string" },
        "evidence": { "type": "string" }
      },
      "required": ["candidate_value", "evidence"]
    },
    "SingleNullableStringCandidate": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": {
          "anyOf": [
            { "type": "string" },
            { "type": "null" }
          ]
        },
        "evidence": { "type": "string" }
      },
      "required": ["candidate_value", "evidence"]
    },
    "SingleSoftwareTypeCandidate": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "$ref": "#/$defs/SoftwareType" },
        "evidence": { "type": "string" }
      },
      "required": ["candidate_value", "evidence"]
    },
    "ArrayStringCandidate": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string" },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "SoftwareType": {
      "type": "string",
      "enum": [
        "ARCHIVER",
        "WEB_BROWSER",
        "OFFICE_SUITE",
        "IDE_EDITOR",
        "GRAPHICS_EDITOR",
        "MEDIA_PLAYER",
        "SYSTEM_TOOL",
        "OTHER"
      ]
    }
  }
}
```

Este schema no impide que el modelo omita un candidato, cambie el orden o escriba
un string distinto. Eso se valida localmente contra `VALORES CANDIDATOS POR
CAMPO`. La ganancia es que el schema ya no crece con cada candidato literal.

### Candidatos no escalares

El contrato deseado sigue siendo que `candidate_value` conserve el tipo real del
candidato:

- strings como strings;
- números como números;
- booleanos como booleanos;
- `null` como `null`;
- objetos como objetos;
- items de array como su tipo real, incluido objeto si el array original es un
  array de objetos.

Para campos simples cuyo valor sea objeto, `SingleCandidate[T].candidate_value` y
`SingleVerdict[T].value` usan el schema estructural de ese objeto. Para campos
array de objetos, `ArrayCandidate[T].candidate_value` usa el schema estructural
del item.

Ejemplo para un campo array de objetos:

```json
{
  "ArrayPersonCandidate": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "candidate_value": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "name": { "type": "string" },
          "role": { "type": "string" }
        },
        "required": ["name", "role"]
      },
      "evidence": { "type": "string" },
      "include": { "type": "boolean" }
    },
    "required": ["candidate_value", "evidence", "include"]
  }
}
```

No se usa `enum` singleton para fijar el objeto completo, porque eso vuelve a
meter candidatos literales en el schema. La igualdad exacta del objeto candidato
se comprueba después con comparación JSON canónica.

Resultado de compatibilidad observado con Cerebras:

- arrays de objetos como salida estructurada funcionan cuando el schema incluye
  `items` y objeto estructural;
- `enum` singleton de objetos y arrays también funcionó si se acompaña con
  schema estructural, pero ya no es una dependencia central de esta propuesta;
- `prefixItems`, `const`, `minItems` y `maxItems` no deben usarse en esta
  variante.

Hay que validar con el backend oficial final que acepta:

- `$defs`/`$ref` en `response_format`;
- arrays de objetos en `candidates`;
- `anyOf` para tipos nullable;
- `additionalProperties: false` en objetos anidados.

## Schema Pydantic en el prompt

El prompt del juez no debe mostrar el JSON Schema de generación tal cual. Ese
schema contiene detalles de constrained decoding que no aportan razonamiento y
puede hacer el prompt más pesado.

Tampoco debe crear clases por campo ni clases por lista de candidatos. El prompt
solo debe tener los wrappers genéricos y la clase `Output`; cualquier clase
adicional debe venir de `$defs` del schema original. Eso evita que el prompt
crezca por cada campo y por cada candidato.

La vista del prompt debe ser compacta e informativa. Debe mezclar:

- el estilo de `enriched-schema`;
- las clases `SingleCandidate`, `ArrayCandidate`, `SingleVerdict` y
  `ArrayVerdict`, declaradas una sola vez;
- solo las clases derivadas de `$defs` que sean necesarias para los campos
  disputados;
- los `description`/`title` de los campos como información semántica;
- los tipos finales del schema original;
- sin listar en esa vista todos los valores candidatos literales.

Ejemplo compacto:

```python
Nullable[T] = T | None

# candidates es una lista ordenada.
# Debe tener exactamente un item por candidato listado en VALORES CANDIDATOS POR CAMPO.
class SingleCandidate[T](BaseModel):
    candidate_value: T
    evidence: str

class ArrayCandidate[T](BaseModel):
    candidate_value: T
    evidence: str
    include: bool

class SingleVerdict[T](BaseModel):
    field: str
    candidates: list[SingleCandidate[T]]
    value: T

class ArrayVerdict[T](BaseModel):
    field: str
    candidates: list[ArrayCandidate[T]]

class Discovery(BaseModel):
    year: Nullable[int] = Field(description="Año del descubrimiento si está en el texto.")
    description: str = Field(description="Descripción breve del descubrimiento.")

class Output(BaseModel):
    official_name: SingleVerdict[str] = Field(
        description="Nombre oficial del cuerpo celeste."
    )
    discoveries: ArrayVerdict[Discovery] = Field(
        description="Descubrimientos explícitamente atribuidos al objeto."
    )
```

Si el schema original contiene `$defs`, se deben renderizar solo las defs
alcanzables desde los campos disputados. Por ejemplo, si solo `discoveries`
usa `Discovery`, se incluye `Discovery`; no se renderiza todo `$defs` por
costumbre.

Los candidatos específicos se muestran aparte:

```text
CAMPO `official_name`
Formato: SingleVerdict[str]
Valores candidatos, en este orden:
1. (2/3): "Ceres"
2. (1/3): "1 Ceres"

CAMPO `discoveries` (lista)
Formato: ArrayVerdict[Discovery]
Elementos candidatos, en este orden:
1. (2/3): {"year": 1801, "description": "primer avistamiento"}
2. (1/3): {"year": null, "description": "clasificación posterior"}
```

La vista Pydantic no necesita enseñar los literals de cada candidato. Esos
literals aparecen en `VALORES CANDIDATOS POR CAMPO` y se validan localmente tras
la respuesta.

Regla de tamaño: la vista Pydantic debe crecer con el número de campos
disputados y tipos referenciados, no con el número de candidatos. El número de
candidatos solo debe afectar la sección `VALORES CANDIDATOS POR CAMPO` y la
salida del modelo.

## Prompt del juez

La instrucción debe cambiar de "elige el valor final" a "emite veredictos
estructurados por candidato".

Secciones propuestas:

- `TAREA DEL JUEZ`
- `INSTRUCCIÓN ORIGINAL`
- `INSTRUCCIÓN DEL JUEZ`
- `SCHEMA PYDANTIC DE VEREDICTOS`
- `TEXTO FUENTE`
- `VALORES CANDIDATOS POR CAMPO`

Reglas clave:

- En `field`, explica qué pide el campo. No decidas el valor ahí.
- En cada `candidates`, devuelve un array con exactamente un objeto por candidato
  listado, en el mismo orden.
- En cada `candidate_value`, copia exactamente el valor candidato
  correspondiente.
- En cada `evidence`, habla de la evidencia o ausencia de evidencia de ese
  candidato. Cita fragmentos verbatim con contexto. Usa `[...]` solo para marcar
  texto intermedio omitido dentro de una cita; no lo uses como prefijo o sufijo
  decorativo. No cites solo el literal del candidato: muestra el contexto donde
  se justifica aceptarlo o rechazarlo, y razona ahí mismo si el candidato debe
  ser el valor final, en campos simples, o si debe incluirse en el array final,
  en campos array.
- En cada `include`, para arrays, decide si el candidato debe formar parte del
  array final.
- Para campos simples, `value` debe ser exactamente uno de los
  `candidate_value`.
- No inventes candidatos nuevos.
- No omitas candidatos.
- No uses conocimiento externo.

El resumen de candidatos debe ser posicional:

```text
CAMPO `official_name`
Valores candidatos, en este orden:
1. (2/3): "Ceres"
2. (1/3): "1 Ceres"

CAMPO `key_topics` (lista)
Elementos candidatos, en este orden:
1. (3/3): "tradición caballeresca"
2. (1/3): "narrativa europea"
```

El prompt puede seguir usando los knobs actuales:

- `GENSIE_SC_JUDGE_INCLUDE_SUPPORT_COUNTS`
- `GENSIE_SC_JUDGE_INCLUDE_STABLE_FIELDS`
- `GENSIE_SC_JUDGE_INCLUDE_SCALAR_REASONINGS`
- `GENSIE_SC_JUDGE_INCLUDE_ARRAY_REASONINGS`

Pero el schema de salida no necesita incluir soporte como propiedad generada. El
soporte puede aparecer solo en el resumen de candidatos del prompt.

## Insights sobre citas en `evidence`

Estos son aprendizajes para diseñar buenos ejemplos FSP y, más adelante, reglas
de prompt. No son todavía una versión final del prompt.

- La cita debe probar la decisión sobre ese candidato, no demostrar que el
  modelo encontró una frase cualquiera donde aparece el literal.
- La cita debe ser tan corta como sea posible, pero incluir el contexto semántico
  que hace útil al candidato: definición, relación, lista, negación, condición o
  ausencia relevante.
- `[...]` solo debe usarse para omitir texto intermedio dentro de una cita. No
  debe usarse al inicio o final como marcador de "hay más texto alrededor".
- Si una cita corta ya contiene lo necesario, no se usa `[...]`.
- El `evidence` no debe explicar la mecánica de la cita. No debe decir "la cita
  omite..." ni "no hace falta usar elipsis...". Debe razonar sobre el candidato.
- Para aceptar un candidato, la cita debe mostrar por qué pertenece al campo
  pedido, no solo que el string aparece.
- Para rechazar un candidato, la cita debe mostrar la diferencia relevante:
  abreviatura vs nombre completo, forma normalizada vs literal textual, tema vs
  género, evidencia contextual insuficiente, o ausencia de una afirmación
  explícita.
- Para arrays, no hace falta repetir la lista completa en cada candidato. Se
  puede citar la lista completa una vez cuando aporta recall, y en candidatos
  posteriores comprimir alrededor del item: `"con versiones para [...] macOS [...]"`.
- Para variantes duplicadas, la evidencia debe preferir el literal más fiel al
  texto y explicar por qué la variante alternativa duplicaría o normalizaría de
  más.
- Para `null`, la evidencia debe citar el contexto más cercano revisado y
  explicar qué afirmación falta. No debe limitarse a decir "no aparece".

Ejemplos de la diferencia:

```text
Demasiado largo para `official_name`:
"VLC media player es un reproductor y framework multimedia [...] desarrollado por el proyecto VideoLAN"

Mejor:
"# VLC media player" y "VLC media player es un reproductor y framework multimedia"
```

```text
Demasiado largo para rechazar `VLC` como nombre oficial:
"VLC es un reproductor de audio y vídeo capaz de reproducir muchos códecs [...] además de capacidad de streaming"

Mejor:
"# VLC media player" y "VLC es un reproductor de audio y vídeo"
```

```text
Útil para plataformas cuando se quiere conservar recall:
"VLC [...] Es un reproductor portable y multiplataforma, con versiones para GNU/Linux, macOS, Microsoft Windows, BSD, Solaris, iOS y Android, entre otros"

Útil para un candidato individual posterior:
"VLC [...] con versiones para [...] macOS [...]"
```

## FSP fijo recomendado

Esta variante debe tener un FSP propio, no reutilizar la salida `{reasoning,
value}` del juez actual.

El FSP debe usar el task del Quijote, como el juez actual, pero adaptado a
veredictos. Debe enseñar:

- `field` como explicación del objetivo del campo, no como decisión;
- `candidates` como array ordenado;
- `candidate_value` copiado literalmente;
- `evidence` como micro-veredicto: fragmentos verbatim con contexto, `[...]`
  solo para omisiones internas, evidencia ausente cuando aplique, y razonamiento
  de aceptación/rechazo del candidato;
- `include` para arrays;
- `value` solo para campos simples;
- un caso nullable.

Ejemplo completo:

```json
{
  "title": {
    "field": "El campo pide el título principal de la obra literaria descrita.",
    "candidates": [
      {
        "candidate_value": "Don Quijote de la Mancha",
        "evidence": "Fragmentos: \"# Don Quijote de la Mancha\" y \"Don Quijote de la Mancha es una novela de Miguel de Cervantes [...] publicada en dos partes\". El encabezado y la oración principal presentan este literal como título y sujeto de la obra completa; por eso este candidato debe ser el valor final."
      },
      {
        "candidate_value": "El ingenioso hidalgo don Quijote de la Mancha",
        "evidence": "Fragmento: \"la primera parte se publicó con el título El ingenioso hidalgo don Quijote de la Mancha [...] la segunda parte apareció como El ingenioso caballero don Quijote de la Mancha\". El fragmento ubica este literal como título de la primera parte, no como título general de la obra completa; por eso no debe elegirse como valor final."
      }
    ],
    "value": "Don Quijote de la Mancha"
  },
  "publication_year": {
    "field": "El campo pide el año de primera publicación de la obra.",
    "candidates": [
      {
        "candidate_value": 1605,
        "evidence": "Fragmento: \"Publicada su primera parte [...] a comienzos de 1605\". El campo pide la primera publicación; 1605 aparece asociado a la primera parte publicada y debe ser el valor final."
      },
      {
        "candidate_value": 1615,
        "evidence": "Fragmento: \"En 1615 apareció su continuación con el título de Segunda parte [...]\". La cita sitúa 1615 como año de la continuación, no de la primera publicación de la obra; por eso este candidato no debe elegirse."
      },
      {
        "candidate_value": null,
        "evidence": "Fragmento: \"Publicada su primera parte [...] a comienzos de 1605\". Sí hay evidencia explícita para el año de primera publicación, así que null sería demasiado conservador y debe rechazarse."
      }
    ],
    "value": 1605
  },
  "genres": {
    "field": "El campo pide los géneros literarios asociados explícitamente con la obra.",
    "candidates": [
      {
        "candidate_value": "novela",
        "evidence": "Fragmento: \"Don Quijote de la Mancha es una novela de Miguel de Cervantes\". La palabra \"novela\" aparece en una oración definitoria sobre la obra, por lo que funciona como género o forma literaria y debe incluirse.",
        "include": true
      },
      {
        "candidate_value": "novela moderna",
        "evidence": "Fragmento: \"Representa la primera novela moderna y la primera novela polifónica\". El texto clasifica explícitamente la obra como novela moderna, así que este candidato pertenece al array final.",
        "include": true
      },
      {
        "candidate_value": "novela polifónica",
        "evidence": "Fragmento: \"Representa la primera novela moderna y la primera novela polifónica\". La expresión aparece como clasificación literaria de la obra; por eso debe incluirse.",
        "include": true
      },
      {
        "candidate_value": "tradición caballeresca",
        "evidence": "Fragmento: \"desmitificadora de la tradición caballeresca y cortés por su tratamiento burlesco\". El contexto presenta la tradición caballeresca como tradición desmitificada, no como género formal de la obra; por eso no debe incluirse en géneros.",
        "include": false
      }
    ]
  },
  "key_themes": {
    "field": "El campo pide los temas principales explorados o tratados por la obra.",
    "candidates": [
      {
        "candidate_value": "tratamiento burlesco",
        "evidence": "Fragmento: \"desmitificadora de la tradición caballeresca y cortés por su tratamiento burlesco\". El texto identifica el tratamiento burlesco como modo central con que la obra aborda esas tradiciones, así que debe incluirse como tema.",
        "include": true
      },
      {
        "candidate_value": "tradición caballeresca",
        "evidence": "Fragmento: \"desmitificadora de la tradición caballeresca y cortés [...]\". La tradición caballeresca es uno de los objetos temáticos que la obra desmitifica, por lo que debe incluirse.",
        "include": true
      },
      {
        "candidate_value": "tradición cortés",
        "evidence": "Fragmento: \"desmitificadora de la tradición caballeresca y cortés por su tratamiento burlesco\". La tradición cortés aparece junto a la caballeresca como objeto del tratamiento burlesco, así que también debe incluirse.",
        "include": true
      },
      {
        "candidate_value": "narrativa europea",
        "evidence": "Fragmento: \"ejerció un enorme influjo en toda la narrativa europea\". La narrativa europea aparece como ámbito de impacto posterior, no como tema explorado por la obra; por eso no debe incluirse.",
        "include": false
      }
    ]
  },
  "original_language": {
    "field": "El campo pide la lengua original de la obra si el texto la afirma explícitamente.",
    "candidates": [
      {
        "candidate_value": null,
        "evidence": "Fragmento revisado: \"Don Quijote de la Mancha es una novela de Miguel de Cervantes [...] una de las obras más destacadas de la literatura española y universal\". El fragmento da contexto autoral y literario, pero no afirma de forma explícita la lengua original; como el campo exige evidencia textual directa, null es el valor más seguro."
      },
      {
        "candidate_value": "español",
        "evidence": "Fragmento revisado: \"Don Quijote de la Mancha es una novela de Miguel de Cervantes [...] una de las obras más destacadas de la literatura española y universal\". La frase permite inferir contexto cultural, pero no dice \"lengua original: español\" ni equivalente; elegir \"español\" requeriría conocimiento externo o una inferencia no solicitada, así que este candidato debe rechazarse."
      },
      {
        "candidate_value": "castellano",
        "evidence": "Fragmento revisado: \"novela escrita por el español Miguel de Cervantes Saavedra [...] literatura española y universal\". El texto permite reconocer contexto español, pero no afirma que la lengua original sea castellano; este candidato requiere conocimiento externo y debe rechazarse."
      }
    ],
    "value": null
  },
  "literary_impact_evidence": {
    "field": "El campo pide un fragmento verbatim completo que evidencie la importancia o impacto literario de la obra.",
    "candidates": [
      {
        "candidate_value": "Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea.",
        "evidence": "Fragmento: \"Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea\". La cita es verbatim y cubre tanto la innovación formal como el influjo literario, por lo que debe ser el valor final."
      },
      {
        "candidate_value": "primera novela moderna y la primera novela polifónica",
        "evidence": "Fragmento: \"Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea\". Este candidato copia solo una parte del fragmento y pierde la consecuencia sobre el influjo europeo; por eso no satisface el campo completo."
      },
      {
        "candidate_value": "El Quijote influyó mucho en la narrativa europea.",
        "evidence": "Fragmento fuente: \"ejerció un enorme influjo en toda la narrativa europea\". El candidato es una paráfrasis, no una copia verbatim del texto, y además omite la parte sobre novela moderna y polifónica; debe rechazarse."
      }
    ],
    "value": "Representa la primera novela moderna y la primera novela polifónica; como tal, ejerció un enorme influjo en toda la narrativa europea."
  }
}
```

## Reconstrucción del output final

Después de la llamada:

1. Parsear el output del juez contra el schema de veredictos.
2. Para cada campo simple:
   - validar que `candidates` es una lista;
   - validar que su longitud coincide con la cantidad esperada;
   - validar que cada `candidate_value` coincide exactamente con el candidato
     esperado en la misma posición;
   - tomar `judge_output[field].value`;
   - validar que `value` coincide con uno de los candidatos esperados.
3. Para cada campo array:
   - validar que `candidates` es una lista;
   - validar longitud y `candidate_value` por posición;
   - incluir `candidate_value` si `include == true`;
   - conservar el orden del listado de candidatos.
4. Mezclar con `scope.stable_fields` igual que el juez actual.
5. Si falla la llamada, el parseo o la validación, intentar un retry de
   reparación o usar el fallback actual: primer trial válido.

Para objetos y arrays, la comparación exacta debe hacerse por JSON canónico, no
por stringificación ad hoc.

### Validación configurable

La validación estricta protege contra errores obvios, pero también puede
descartar todo el trabajo del juez por un fallo local de formato. Por defecto,
esta variante funciona en modo warning-only:

- `GENSIE_SC_VERDICT_JUDGE_ENFORCE_VALIDATION=0` por defecto.
  - Si está en `1`, cualquier fallo de validación fuerza fallback igual que el
    juez estricto inicial.
  - Si está en `0`, se intenta reconstruir el output de forma tolerante y se
    conserva el trabajo del juez siempre que sea posible.
- `GENSIE_SC_VERDICT_JUDGE_REPORT_VALIDATION=1` por defecto.
  - Si está en `1`, los fallos de validación quedan registrados como warnings
    en metadata/trace.
  - Si está en `0`, no se reportan esos warnings, aunque la reconstrucción
    siga haciendo las comprobaciones mínimas necesarias.

En modo tolerante:

- si un array llega reordenado pero con `candidate_value` reconocibles, se
  aplican los `include` y se reconstruye el array final en el orden esperado de
  candidatos;
- si un campo simple devuelve `value` fuera de los candidatos esperados, se
  registra el warning y se usa el valor del juez;
- si falta un veredicto completo o `candidates` no es una lista, ese campo cae
  al valor del primer trial válido, sin invalidar necesariamente los demás
  campos.

## Módulos propuestos

Propuesta de organización:

- `aggregation/verdict_schema.py`
  - construye el schema de generación compacto;
  - crea `$defs` por tipo/forma de valor, no por candidato;
  - conserva tipos originales de candidatos;
  - reconstruye output final desde veredictos;
  - valida cantidad, orden y copia exacta contra el listado del prompt.

- `aggregation/verdict_prompt.py`
  - construye prompt para esta variante;
  - renderiza la vista Pydantic informativa;
  - incluye solo `$defs` alcanzables y descriptions;
  - renderiza el resumen de candidatos como listas numeradas.

- `aggregation/verdict_fsp.py`
  - FSP fijo para esta variante;
  - basado en el task del Quijote;
  - enseña `field`, `candidates`, `candidate_value`, `evidence`, `include` y
    `value`.

- `aggregation/verdict_judge.py`
  - orquesta la llamada al juez;
  - parsea veredictos;
  - reconstruye output final;
  - aplica retries/fallbacks.

Alternativa:

- extender `JudgeAggregator` con `variant="reasoned_output | candidate_verdicts"`.

Esa alternativa reduce clases, pero puede ensuciar `judge.py`. Por organización,
conviene separar esta variante si el schema, prompt y FSP quedan suficientemente
distintos.

## Tests necesarios

Tests unitarios:

- schema de `SingleVerdict` usa `candidates` como array;
- schema de `ArrayVerdict` usa `candidates` como array;
- schema de generación no contiene candidatos literales cuando no son enums del
  schema original;
- schema reutiliza `$defs` para campos con la misma forma;
- schema de `SingleVerdict.value` usa el tipo original del campo;
- schema de `ArrayVerdict.candidate_value` usa el tipo original del item;
- reconstrucción de output simple toma `value`;
- reconstrucción de output array toma candidatos con `include=true`;
- reconstrucción valida longitud exacta de `candidates`;
- reconstrucción valida que cada `candidate_value` coincide con el literal
  esperado en la misma posición;
- reconstrucción valida que `value` pertenece a los candidatos del campo simple;
- por defecto, los fallos de validación se reportan como warnings y no fuerzan
  fallback;
- modo estricto opcional fuerza fallback ante fallos de validación;
- campos estables se mezclan igual que en el juez actual;
- fallback si falla la llamada, el parseo, o la validación en modo estricto;
- FSP no usa `Reasoned`;
- FSP evalúa candidatos explícitamente dentro de `evidence`;
- FSP muestra `evidence` con fragmentos verbatim contextualizados y usa `[...]`
  solo para omisiones internas, no como marcador al inicio o final de la cita;
- vista Pydantic incluye `$defs` alcanzables y descriptions, pero no crea clases
  por campo ni por lista de candidatos.

Tests de compatibilidad con backend:

- array de objetos en `candidates`;
- objeto candidato como `candidate_value`;
- item array candidato como `candidate_value`;
- nullable con `anyOf`;
- enum original de campo con `$ref` o `enum`;
- `$defs`/`$ref` en schema de generación;
- confirmar que no se usan `prefixItems`, `const`, `minItems` ni `maxItems`.

Tests de integración:

- pipeline con dos o tres trials que produzcan candidatos distintos;
- campo simple disputado;
- campo array disputado;
- campo nullable disputado;
- array de objetos disputado;
- caso sin campos disputados no llama al juez;
- caso de un solo trial válido no llama al juez;
- caso donde el modelo cambia el orden de candidatos registra warnings sin
  fallback por defecto;
- caso con validación estricta activa usa fallback ante el mismo fallo.

## Riesgos

- El schema ya no fuerza cantidad, orden ni valores concretos. La robustez pasa a
  depender de validación local, warnings y fallback configurable.
- Si el backend oficial no acepta `$defs`/`$ref` en `response_format`, habrá que
  inlinear definiciones. Aun así, el schema seguirá sin crecer por candidato.
- Repetir `candidate_value` aumenta tokens de salida; esto también habría pasado
  con `prefixItems`/`const` si queríamos que el juez copiara el valor literal.
- Para arrays de objetos, `candidate_value` puede ser grande; habrá que limitar
  candidatos o usar fallback si la salida esperada se vuelve demasiado costosa.
- `field` puede volverse demasiado largo o empezar a razonar sobre el valor. El
  prompt y el FSP deben enseñar que `field` solo interpreta qué pide el campo.
- Si el modelo omite candidatos o altera el orden con frecuencia, puede hacer
  falta un prompt de reparación específico o activar validación estricta.
- Los escapes Unicode corruptos o JSON truncado no se pueden reparar de forma
  fiable después de la llamada. Las defensas principales son reducir candidatos,
  limitar `evidence`, normalizar salidas válidas y evitar `\uXXXX` desde el
  prompt.

## Decisiones pendientes

- Límite máximo de candidatos por campo, además de la compactación normalizada.
- Si la validación estricta debe activarse por defecto o seguir como opción.
- Validar soporte real de `$defs`/`$ref`, arrays de objetos y `anyOf` con el
  backend oficial antes de implementarla como default.
