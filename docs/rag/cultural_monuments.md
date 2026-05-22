# cultural_monuments

Los tasks `cultural_monuments` son extracciones L3 de fichas breves del registro BIC español: el modelo debe leer una entrada semiestructurada en Markdown, recuperar el nombre oficial y municipio, mapear la categoría legal al enum del schema, normalizar códigos y fechas, y decidir si el bien está declarado o solo incoado; los ejemplos revisados muestran además mucho ruido de extracción, con coordenadas donde debería aparecer un código, campos desplazados entre `Municipality`, `Category` y `Declaration Date`, fechas vacías, y líneas de relleno sin valor.

## Ejemplos revisados

- `data/dev_rev/cultural_monuments_1.json`
- `data/dev/cultural_monuments_2.json`
- `data/dev/cultural_monuments_3.json`
- `data/dev/cultural_monuments_4.json`
- `data/dev/cultural_monuments_5.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `official_name` | Requerido, `string`, no nullable. La dualidad útil es nombre oficial directo en el encabezado vs nombre popular o alias en el encabezado con el nombre oficial en una línea de ficha. No conviene enseñar `null`; sí conviene enseñar a no confundir nombres entre paréntesis de coordenadas o nombres de partes del registro. |
| `municipality` | Requerido, `string`, no nullable. Dualidad entre municipio limpio en `Municipality:` y municipio con ruido cercano de localización, comarca o paraje. Si aparece `Location:` o un paraje, debe distinguirse del municipio salvo que el propio campo venga fusionado como en algunos ejemplos del dataset. |
| `bic_category` | Enum requerido. Debe mapear a uno de estos valores: `MONUMENTO`, `JARDÍN HISTÓRICO`, `CONJUNTO HISTÓRICO`, `SITIO HISTÓRICO`, `ZONA ARQUEOLÓGICA` u `OTRO`. Dualidad entre categoría legal directa, por ejemplo `Monumento`, y una etiqueta no perteneciente al enum, por ejemplo `Arte Rupestre`, que en los ejemplos revisados se resuelve como `OTRO`. |
| `registration_code` | Requerido, `string`, con patrón de mayúsculas, números y guiones. Dualidad principal: código BIC válido tipo `RI-51-0009449` vs ausencia de código válido, coordenadas o campo vacío. Como el schema no permite `null`, los ejemplos revisados usan `NONE` cuando no hay un código registral extraíble. |
| `declaration_date` | `string` normalizado `YYYY-MM-DD` vs `null`. Dualidad entre fecha textual española explícita, por ejemplo `29 de septiembre de 2011`, y campo vacío o contenido que no es una fecha, como un código BIC colocado por error en `Declaration Date:`. |
| `is_declared` | `boolean`, con default `true`. Dualidad entre estado `Declarado` y estado `Incoado` o pendiente. En los ejemplos revisados casi todo acaba en `true`, pero para complementar conviene crear un caso con `Status: Incoado` que fuerce `false` sin depender de inferencias vagas. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `official_name` | Nombre oficial directo en el encabezado y repetido en la ficha. | Encabezado con nombre popular o abreviado; línea `Official Name:` con el nombre que debe extraerse. |
| `municipality` | Municipio limpio en `Municipality:`. | Municipio limpio pero con `Location:` o paraje cercano como distractor, para no concatenarlo. |
| `bic_category` | Categoría directa `Monumento`, mapeada a `MONUMENTO`. | Tipo `Arte Rupestre` o etiqueta no legal, mapeada a `OTRO`. |
| `registration_code` | Código válido explícito en `Registration Code: RI-51-...`. | Campo vacío o coordenadas en `Registration Code:`, por lo que el valor debe ser `NONE`. |
| `declaration_date` | Fecha textual española explícita, normalizada a `YYYY-MM-DD`. | Campo de fecha vacío o con contenido no fechable, por lo que debe ser `null`. |
| `is_declared` | `Status: Declarado`, por lo que debe ser `true`. | `Status: Incoado`, por lo que debe ser `false`. |

En este schema la alternancia de `null` solo aplica directamente a `declaration_date`; `registration_code` no acepta `null`, así que el contraste equivalente es código válido frente a `NONE` cuando el texto solo ofrece coordenadas o deja el campo sin código registral.

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `official_name` | Nombre del bien protegido, normalmente el encabezado `#`. Si aparece `Official Name`, úsalo como nombre oficial; no mezcles coordenadas, alias entre paréntesis ni líneas de fuente. |
| `municipality` | Municipio o localidad del bien. En estos registros los campos pueden estar desplazados: a veces `Municipality` contiene la categoría y `Category` contiene el municipio; elige el valor que sea lugar, aunque esté en otra línea. |
| `bic_category` | Categoría legal mapeada al enum. `Monumento` -> `MONUMENTO`; `Arte Rupestre` o etiquetas fuera del enum -> `OTRO`; no uses municipios, coordenadas ni códigos como categoría. |
| `registration_code` | Código registral BIC con patrón de mayúsculas, números y guiones, por ejemplo `RI-51-0009449`. Si solo hay coordenadas, campo vacío o nada que cumpla el patrón, usa `NONE`; si el código aparece desplazado en `Declaration Date` u otro, extráelo igualmente. |
| `declaration_date` | Fecha legal de declaración normalizada a `YYYY-MM-DD`. Devuelve `null` si el campo está vacío, contiene coordenadas, contiene un código BIC o solo hay líneas de relleno sin fecha. |
| `is_declared` | `true` si el estado es declarado o si el registro solo muestra ficha BIC sin indicio de incoación. `false` solo cuando aparezca `Incoado`, pendiente u otra señal explícita de no declarado. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Puente de San Miguel

Municipality: Teruel
Category: Monumento
Registration Code: RI-51-0012386
Declaration Date: 12 de marzo de 1998
Status: Declarado
Source: Wikipedia Annex List

No detailed article available.
Additional detail line 1.
Additional detail line 2.
Additional detail line 3.
Coordinates: 40°20′45″N 1°06′22″O / 40.3458, -1.1061 (Puente Viejo)
```

`instruction`:

```text
Extrae la información del monumento o bien de interés cultural a partir del texto proporcionado, siguiendo el esquema indicado.
```

`output`:

```json
{
  "official_name": "Puente de San Miguel",
  "municipality": "Teruel",
  "bic_category": "MONUMENTO",
  "registration_code": "RI-51-0012386",
  "declaration_date": "1998-03-12",
  "is_declared": true
}
```

`reasoning`:

```json
{
  "official_name": {
    "field_asks": "el nombre oficial del monumento o sitio protegido.",
    "relevant_fragments": "\"# Puente de San Miguel\" y \"Coordinates: 40°20′45″N 1°06′22″O / 40.3458, -1.1061 (Puente Viejo)\".",
    "final_value": "Como el encabezado da \"Puente de San Miguel\" como bien principal y \"Puente Viejo\" aparece solo entre paréntesis dentro de las coordenadas, el valor debe ser \"Puente de San Miguel\"."
  },
  "municipality": {
    "field_asks": "el municipio o ciudad donde se encuentra el bien.",
    "relevant_fragments": "\"Municipality: Teruel\".",
    "final_value": "Como el fragmento relevante etiqueta \"Teruel\" como municipio, el valor debe ser \"Teruel\"."
  },
  "bic_category": {
    "field_asks": "la categoría legal de protección, mapeada a uno de estos valores: MONUMENTO, JARDÍN HISTÓRICO, CONJUNTO HISTÓRICO, SITIO HISTÓRICO, ZONA ARQUEOLÓGICA u OTRO.",
    "relevant_fragments": "\"Category: Monumento\".",
    "final_value": "Como el fragmento relevante da la categoría \"Monumento\", el valor del enum debe ser \"MONUMENTO\"."
  },
  "registration_code": {
    "field_asks": "el código oficial de registro con patrón de mayúsculas, números y guiones; si no hay código válido extraíble, usar NONE.",
    "relevant_fragments": "\"Registration Code: RI-51-0012386\" y \"Coordinates: 40°20′45″N 1°06′22″O / 40.3458, -1.1061 (Puente Viejo)\".",
    "final_value": "Como el fragmento relevante contiene el código registral válido y las coordenadas están en otro campo, el valor debe ser \"RI-51-0012386\"."
  },
  "declaration_date": {
    "field_asks": "la fecha de declaración legal normalizada en formato YYYY-MM-DD, o null si no hay fecha suficiente.",
    "relevant_fragments": "\"Declaration Date: 12 de marzo de 1998\".",
    "final_value": "Como el fragmento relevante da una fecha completa, debe normalizarse a \"1998-03-12\"."
  },
  "is_declared": {
    "field_asks": "true si el estado es Declarado; false si el estado es Incoado o pendiente.",
    "relevant_fragments": "\"Status: Declarado\".",
    "final_value": "Como el fragmento relevante indica estado \"Declarado\", el valor debe ser true."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# Abrigos de la Solana

Municipality: Ares del Maestrat
Type: Arte Rupestre
Location: Barranco de la Gasulla; Mas de la Solana
Registration Code: 40°27′11″N 0°06′52″O / 40.4531, -0.1144 (Abrigos de la Solana)
Declaration Date:
Status: Incoado
Source: Wikipedia Annex List

No detailed article available.
Additional detail line 1.
Additional detail line 2.
Official Name: Abrigos rupestres de la Solana del Molino
```

`instruction`:

```text
Extrae la información del monumento o bien de interés cultural a partir del texto proporcionado, siguiendo el esquema indicado.
```

`output`:

```json
{
  "official_name": "Abrigos rupestres de la Solana del Molino",
  "municipality": "Ares del Maestrat",
  "bic_category": "OTRO",
  "registration_code": "NONE",
  "declaration_date": null,
  "is_declared": false
}
```

`reasoning`:

```json
{
  "official_name": {
    "field_asks": "el nombre oficial del monumento o sitio protegido.",
    "relevant_fragments": "\"# Abrigos de la Solana\" y \"Official Name: Abrigos rupestres de la Solana del Molino\".",
    "final_value": "Como el fragmento relevante diferencia el encabezado abreviado del nombre oficial añadido en la ficha, el valor debe ser \"Abrigos rupestres de la Solana del Molino\"."
  },
  "municipality": {
    "field_asks": "el municipio o ciudad donde se encuentra el bien.",
    "relevant_fragments": "\"Municipality: Ares del Maestrat\" y \"Location: Barranco de la Gasulla; Mas de la Solana\".",
    "final_value": "Como el fragmento relevante etiqueta \"Ares del Maestrat\" como municipio y deja barranco y masía como localización, el valor debe ser \"Ares del Maestrat\"."
  },
  "bic_category": {
    "field_asks": "la categoría legal de protección, mapeada a uno de estos valores: MONUMENTO, JARDÍN HISTÓRICO, CONJUNTO HISTÓRICO, SITIO HISTÓRICO, ZONA ARQUEOLÓGICA u OTRO.",
    "relevant_fragments": "\"Type: Arte Rupestre\".",
    "final_value": "Como \"Arte Rupestre\" no coincide con las categorías legales enumeradas, el valor del enum debe ser \"OTRO\"."
  },
  "registration_code": {
    "field_asks": "el código oficial de registro con patrón de mayúsculas, números y guiones; si no hay código válido extraíble, usar NONE.",
    "relevant_fragments": "\"Registration Code: 40°27′11″N 0°06′52″O / 40.4531, -0.1144 (Abrigos de la Solana)\".",
    "final_value": "Como el fragmento relevante contiene coordenadas y no un código registral válido, el valor debe ser \"NONE\"."
  },
  "declaration_date": {
    "field_asks": "la fecha de declaración legal normalizada en formato YYYY-MM-DD, o null si no hay fecha suficiente.",
    "relevant_fragments": "\"Declaration Date:\" y \"Status: Incoado\".",
    "final_value": "Como el fragmento relevante deja la fecha vacía y solo aporta un estado pendiente, el valor debe ser null."
  },
  "is_declared": {
    "field_asks": "true si el estado es Declarado; false si el estado es Incoado o pendiente.",
    "relevant_fragments": "\"Status: Incoado\".",
    "final_value": "Como el fragmento relevante indica estado \"Incoado\", el valor debe ser false."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados tienen forma de ficha Markdown muy corta: encabezado `# <bien>`, varias líneas clave-valor (`Municipality`, `Category` o `Type`, `Location`, `Registration Code`, `Declaration Date`, `Source`) y después una cola genérica como `No detailed article available.` con `Additional detail line N`. El rasgo más importante es el ruido de extracción: a veces `Municipality` contiene la categoría, `Category` contiene el municipio fusionado con un paraje, `Registration Code` contiene coordenadas y `Declaration Date` contiene un código BIC. Para los nuevos ejemplos conviene mantener esa estructura de anexo o registro, añadir como máximo una línea `Status:` para hacer observable `is_declared`, y meter ruido realista alrededor de coordenadas, parajes o líneas de fuente, sin escribir frases que expliquen artificialmente qué campo falta.
