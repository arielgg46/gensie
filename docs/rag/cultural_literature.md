# cultural_literature

Los tasks `cultural_literature` son extracciones L2 de metadatos bibliográficos y temas desde entradas enciclopédicas o descripciones de obras literarias: el modelo debe distinguir el título oficial de nombres populares o títulos de partes, extraer autor y año solo cuando estén grounded, listar géneros y temas explícitamente mencionados, y devolver `null` cuando el texto no afirma datos como lengua original o año exacto aunque puedan inferirse por conocimiento externo.

## Ejemplos revisados

- `data/dev_rev/cultural_literature_001.json`
- `data/dev_rev/cultural_literature_002.json`
- `data/dev_rev/cultural_literature_006.json`
- `data/dev_rev/cultural_literature_009.json`
- `data/dev_rev/cultural_literature_010.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `title` | Requerido, `string`, no nullable. La dualidad útil es título oficial directo vs título popular/distractor: en Quijote hay títulos de partes, y en Celestina el nombre popular no coincide con el título oficial esperado. |
| `author` | Requerido, `string`, no nullable. Conviene variar autor nombrado directamente vs atribución o autoría especial, por ejemplo `Anónimo` cuando el texto lo dice; no debe inventarse null porque el schema no lo permite. |
| `publication_year` | `integer` vs `null`. Bit principal: año exacto de primera publicación frente a referencias vagas como siglo, últimos años de un siglo, premios o ediciones posteriores. |
| `genres` | `[]` vs lista poblada. En los ejemplos revisados siempre aparece alguna etiqueta de género, pero el schema permite lista vacía si el texto no da géneros literarios explícitos. Cuando haya lista, preferir fragmentos verbatim o casi verbatim. |
| `key_themes` | `[]` vs lista poblada. Bit principal: temas explícitos frente a una descripción que solo da datos bibliográficos o recepción. Cuando haya lista, debe salir de conceptos nombrados en el texto, no de interpretación externa. |
| `original_language` | `string` vs `null`. Bit principal: lengua original explícitamente afirmada frente a nacionalidad del autor, literatura nacional o país de publicación, que no bastan por grounding estricto. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `title` | Case nuevo, no Quijote. Título oficial directo desde encabezado y primera oración, con títulos de partes internas como distractores menores. | Case nuevo con alias o título popular en el encabezado y título oficial en el cuerpo; el output debe elegir el título oficial afirmado por el texto. |
| `author` | Autor nombrado directamente con nombre propio. | Autoría especial: texto que diga explícitamente `Anónimo` o una atribución controlada, para no enseñar solo nombres propios de autor. |
| `publication_year` | Valor no null: año exacto de primera publicación explícito. | `null`: texto con siglo, fecha de composición, premio o edición posterior, pero sin año exacto de primera publicación. |
| `genres` | Lista poblada con uno o dos géneros verbatim o casi verbatim. | `[]`: el texto describe recepción, lengua y temas, pero no nombra géneros literarios explícitos. |
| `key_themes` | `[]`: el texto da metadatos y género, pero no temas principales explícitos. | Lista poblada con temas textuales, por ejemplo `exilio`, `memoria familiar` o `pobreza urbana`, no interpretaciones amplias. |
| `original_language` | `null`: el texto habla de país, literatura nacional o autora, pero no afirma lengua original. | Valor no null: lengua original mencionada de forma explícita, por ejemplo `gallego`, `catalán` o `español`. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `title` | Título oficial de la obra descrita. Prioriza el título presentado como obra principal; no confundas encabezados populares, alias, títulos de partes, continuaciones, ediciones o estudios críticos con el título oficial esperado. |
| `author` | Autor o creador principal explícitamente atribuido a la obra. Si el texto dice `Anónimo`, usa ese valor; no confundas copistas, editores, traductores, críticos, personajes o autores de obras comparadas con autoría. |
| `publication_year` | Año exacto de primera publicación de la obra. Devuelve `null` si solo hay siglo, fecha de composición, éxito editorial, premio, reedición, continuación, edición escolar o estudio posterior. |
| `genres` | Géneros o clasificaciones literarias explícitas en el texto, como `novela`, `tragicomedia` o `comedia humanística`. Usa `[]` si solo aparecen forma material, argumento, recepción o temas sin etiqueta de género clara. |
| `key_themes` | Temas principales nombrados por el texto, no interpretaciones externas. Extrae conceptos como injusticia social, tradición caballeresca, pobreza o memoria solo cuando el fragmento los presenta como asuntos de la obra. |
| `original_language` | Lengua original de redacción, solo si el texto la afirma o da evidencia textual fuerte sobre la lengua de la obra. Nacionalidad del autor, país, literatura nacional o traducciones no bastan por sí solos. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# La ciudad de los espejos

## Introducción

La ciudad de los espejos es una novela breve de la escritora argentina Elena Márquez. Fue publicada por primera vez en 1978 por Editorial Sur. El volumen salió dividido en dos partes, "El barrio de la lluvia" y "Las habitaciones repetidas"; la edición escolar de 1991 añadió una nota de la autora y un apéndice crítico. En reseñas de la época se la situó entre la narrativa fantástica rioplatense, aunque también se subrayó su tono urbano y su prosa contenida. Recibió el Premio Municipal de Literatura en 1980 y volvió a circular en una colección dedicada a escritoras del Cono Sur. La ficha de esa colección la presentaba como novela breve; otros paratextos destacaban sus cambios de narrador y su estructura de episodios encadenados.
```

`instruction`:

```text
Extrae los metadatos bibliográficos y temas principales de la obra literaria descrita.
```

`output`:

```json
{
  "title": "La ciudad de los espejos",
  "author": "Elena Márquez",
  "publication_year": 1978,
  "genres": [
    "novela breve",
    "narrativa fantástica rioplatense"
  ],
  "key_themes": [],
  "original_language": null
}
```

`reasoning`:

```json
{
  "title": {
    "field_asks": "el título oficial de la obra literaria.",
    "relevant_fragments": "\"# La ciudad de los espejos\" y \"El volumen salió dividido en dos partes, \\\"El barrio de la lluvia\\\" y \\\"Las habitaciones repetidas\\\"\".",
    "final_value": "Como los fragmentos relevantes presentan \"La ciudad de los espejos\" como obra principal y los otros títulos solo como partes internas del volumen, el título debe ser \"La ciudad de los espejos\"."
  },
  "author": {
    "field_asks": "el autor o creador principal de la obra.",
    "relevant_fragments": "\"La ciudad de los espejos es una novela breve de la escritora argentina Elena Márquez\".",
    "final_value": "Como el fragmento relevante atribuye la obra a Elena Márquez, el autor debe ser \"Elena Márquez\"."
  },
  "publication_year": {
    "field_asks": "el año en que la obra fue publicada por primera vez, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"Fue publicada por primera vez en 1978 por Editorial Sur\" y \"la edición escolar de 1991 añadió una nota de la autora\".",
    "final_value": "Como el fragmento relevante afirma la primera publicación en 1978, el valor debe ser 1978."
  },
  "genres": {
    "field_asks": "los géneros literarios asociados con la obra, como lista vacía si no hay géneros explícitos.",
    "relevant_fragments": "\"La ficha de esa colección la presentaba como novela breve\" y \"se la situó entre la narrativa fantástica rioplatense\".",
    "final_value": "Como los fragmentos relevantes nombran géneros o clasificaciones literarias explícitas, la lista debe incluir \"novela breve\" y \"narrativa fantástica rioplatense\"."
  },
  "key_themes": {
    "field_asks": "los temas principales explorados en la obra, como lista vacía si el texto no los menciona explícitamente.",
    "relevant_fragments": "\"se subrayó su tono urbano y su prosa contenida\" y \"otros paratextos destacaban sus cambios de narrador y su estructura de episodios encadenados\".",
    "final_value": "Los fragmentos relevantes describen tono, prosa, narrador y estructura, pero no enumeran temas principales de la obra; la lista debe ser vacía."
  },
  "original_language": {
    "field_asks": "la lengua en que la obra fue escrita originalmente, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"escritora argentina Elena Márquez\" y \"escritoras del Cono Sur\".",
    "final_value": "Los fragmentos relevantes indican nacionalidad y región literaria, pero no afirman la lengua original; el valor debe ser null."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# La balada del puerto

## Introducción

La balada del puerto es el nombre con que se conoce popularmente el Libro de la niebla, obra anónima conservada en tres manuscritos de finales del siglo XIV. La tradición manuscrita más antigua lo transmite en gallego, con rúbricas latinas añadidas al margen y una nota de copista firmada por Xil Pérez. Sus pasajes centrales tratan el exilio, la memoria familiar y la pobreza urbana de los barrios portuarios; otras secciones reúnen plegarias, listas de deudas y nombres de embarcaciones. La copia más citada lleva una miniatura añadida en el siglo XV. Un estudio de 1923 la difundió con su alias moderno, pero los catálogos conservan el título Libro de la niebla.
```

`instruction`:

```text
Extrae los metadatos bibliográficos y temas principales de la obra literaria descrita.
```

`output`:

```json
{
  "title": "Libro de la niebla",
  "author": "Anónimo",
  "publication_year": null,
  "genres": [],
  "key_themes": [
    "exilio",
    "memoria familiar",
    "pobreza urbana"
  ],
  "original_language": "gallego"
}
```

`reasoning`:

```json
{
  "title": {
    "field_asks": "el título oficial de la obra literaria.",
    "relevant_fragments": "\"La balada del puerto es el nombre con que se conoce popularmente el Libro de la niebla\" y \"los catálogos conservan el título Libro de la niebla\".",
    "final_value": "Como los fragmentos relevantes distinguen el alias popular del título conservado en catálogos, el título debe ser \"Libro de la niebla\"."
  },
  "author": {
    "field_asks": "el autor o creador principal de la obra.",
    "relevant_fragments": "\"Libro de la niebla, obra anónima\" y \"una nota de copista firmada por Xil Pérez\".",
    "final_value": "Como los fragmentos relevantes identifican la obra como anónima y presentan a Xil Pérez solo como copista, el autor debe ser \"Anónimo\"."
  },
  "publication_year": {
    "field_asks": "el año en que la obra fue publicada por primera vez, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"conservada en tres manuscritos de finales del siglo XIV\" y \"Un estudio de 1923 la difundió con su alias moderno\".",
    "final_value": "Los fragmentos relevantes dan un periodo de transmisión y un estudio moderno, pero no un año exacto de primera publicación; el valor debe ser null."
  },
  "genres": {
    "field_asks": "los géneros literarios asociados con la obra, como lista vacía si no hay géneros explícitos.",
    "relevant_fragments": "\"obra anónima conservada en tres manuscritos\" y \"otras secciones reúnen plegarias, listas de deudas y nombres de embarcaciones\".",
    "final_value": "Los fragmentos relevantes aportan soporte material y contenido interno, pero no nombran géneros literarios explícitos; la lista debe ser vacía."
  },
  "key_themes": {
    "field_asks": "los temas principales explorados en la obra, como lista vacía si el texto no los menciona explícitamente.",
    "relevant_fragments": "\"Sus pasajes centrales tratan el exilio, la memoria familiar y la pobreza urbana de los barrios portuarios\".",
    "final_value": "Como el fragmento relevante enumera temas centrales, la lista debe incluir \"exilio\", \"memoria familiar\" y \"pobreza urbana\"."
  },
  "original_language": {
    "field_asks": "la lengua en que la obra fue escrita originalmente, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"La tradición manuscrita más antigua lo transmite en gallego, con rúbricas latinas añadidas al margen\".",
    "final_value": "Como el fragmento relevante sitúa el texto principal de la tradición más antigua en gallego y deja el latín para rúbricas marginales, la lengua original debe ser \"gallego\"."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados siguen una entrada enciclopédica en Markdown: encabezado con `# <obra>`, sección `## Introducción`, una primera oración que define la obra y autoría, varias frases con publicación/composición/recepción, y a veces una sección `## Argumento` extensa con personajes, trama y temas. Pueden ser breves, como `La Celestina`, o muy largos, como `Cien años de soledad`; para FSP conviene mantenerlos compactos pero con la misma textura enciclopédica. Suelen contener distractores fuertes: títulos alternativos o populares, títulos de partes, fechas de continuación, premios o ediciones posteriores, estudios críticos, argumento detallado y datos de literatura nacional que no siempre prueban la lengua original. Los nuevos ejemplos deben mantener esa estructura, con textos de menos de 1600 caracteres y evidencia natural para cada campo.
