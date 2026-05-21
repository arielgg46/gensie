# legal_legislation

Los tasks `legal_legislation` son extracciones L7 de metadatos dispersos sobre normas españolas: el modelo debe reconstruir el título oficial completo aunque el encabezado use un nombre popular, mapear el rango jurídico y la jurisdicción a enums cerrados, normalizar la fecha de sanción cuando exista, detectar si el texto afirma derogación o sustitución, y listar artículos, disposiciones o apartados mencionados como modificados o relevantes sin mezclar referencias históricas ajenas a la norma principal.

## Ejemplos revisados

- `data/dev_rev/legal_legislation_001.json`
- `data/dev_rev/legal_legislation_002.json`
- `data/dev/legal_legislation_003.json`
- `data/dev/legal_legislation_004.json`
- `data/dev/legal_legislation_005.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `official_title` | Requerido, `string`, no nullable. Dualidad entre título oficial explícito en la primera oración y encabezado con nombre popular o genérico que obliga a elegir el título formal del cuerpo. Debe preferirse el título completo de la norma principal, no títulos de reformas, antecedentes o leyes comparadas. |
| `law_range` | Enum requerido. Debe mapear a uno de estos valores: `LEY ORGÁNICA`, `LEY ORDINARIA`, `REAL DECRETO`, `REAL DECRETO-LEY`, `CONSTITUCIÓN` u `OTRA`. En los revisados predominan leyes ordinarias, pero conviene alternar con `REAL DECRETO-LEY`, `REAL DECRETO` u `OTRA` para no fijar el prefijo a `LEY ORDINARIA`. |
| `sanction_date` | `string` normalizado `YYYY-MM-DD` vs `null`. Dualidad entre fecha formal completa de sanción o aprobación y textos con solo entrada en vigor, publicación, propuesta o rango temporal histórico. La fecha de publicación en boletín no debe usarse si el campo pide sanción y no se afirma equivalencia. |
| `jurisdiction` | Enum requerido. Debe mapear a uno de estos valores: `NACIONAL`, `AUTONÓMICO`, `LOCAL` o `EUROPEO`. Dualidad principal entre normas estatales y autonómicas; los ejemplos revisados incluyen ambas, y las referencias a la Unión Europea o a municipios no deberían arrastrar el valor si la norma principal es estatal o autonómica. |
| `is_repealed` | `boolean`. En los ejemplos revisados aparece siempre `false`, pero para FSP conviene un caso `true` cuando el texto diga que la norma fue derogada, sustituida o perdió vigencia por otra. No basta con que haya recursos, suspensiones parciales, reformas o debates de derogación. |
| `affected_articles` | `[]` vs lista poblada. Dualidad entre artículos o disposiciones concretas mencionadas como modificadas/relevantes y textos que solo describen objeto, exposición de motivos o debate político sin citar artículos específicos. Debe preservar formas como `artículo 2`, `artículo 9.3` o `Disposición Transitoria Segunda` cuando aparecen con valor jurídico. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `official_title` | Título oficial completo de la norma principal, aunque el encabezado use un nombre popular. Prefiere la formulación formal en la introducción; no confundas reformas, normas citadas como contexto, leyes futuras ni títulos de secciones con la norma principal. |
| `law_range` | Rango jurídico de la norma principal; enum completo: `LEY ORGÁNICA`, `LEY ORDINARIA`, `REAL DECRETO`, `REAL DECRETO-LEY`, `CONSTITUCIÓN` u `OTRA`. Usa el tipo explícito del título formal y no arrastres el rango de reglamentos, decretos, artículos constitucionales o normas supletorias citadas. |
| `sanction_date` | Fecha de sanción, promulgación o aprobación formal de la norma, normalizada como `YYYY-MM-DD`. No uses la fecha de publicación, entrada en vigor, recursos, suspensiones o reformas si el texto no las identifica como fecha formal de la norma principal. |
| `jurisdiction` | Ámbito de la norma principal; enum completo: `NACIONAL`, `AUTONÓMICO`, `LOCAL` o `EUROPEO`. Decide por la institución que aprueba la norma y su ámbito, no por referencias a Constitución, Unión Europea, ayuntamientos o administraciones citadas como contexto. |
| `is_repealed` | `true` solo si el texto dice que la norma fue derogada, anulada íntegramente, sustituida o perdió vigencia. Suspensiones parciales, recursos, modificaciones, propuestas de derogación o artículos inconstitucionales no bastan por sí solos. |
| `affected_articles` | Artículos, disposiciones o apartados concretos citados como relevantes, modificados, desarrollados o anulados. Conserva la forma del texto (`artículo 92`, `artículo 149.1.32`, `Disposición Transitoria Segunda`) y no incluyas leyes completas, secciones genéricas ni referencias históricas sin función normativa directa. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `official_title` | Encabezado con nombre breve, primera oración con título oficial completo de la norma principal. | Encabezado popular o temático, título oficial completo disperso en una sección posterior para forzar agregación. |
| `law_range` | `REAL DECRETO-LEY`, para variar frente a las leyes ordinarias revisadas. | `LEY ORDINARIA` autonómica o `OTRA` si se trata de una ley de bases/delegación; elegir una que contraste claramente con el ejemplo 1. |
| `sanction_date` | Valor no null: fecha formal completa en español, normalizada a `YYYY-MM-DD`. | `null`: texto con publicación, entrada en vigor o debate parlamentario, pero sin fecha formal de sanción/aprobación de la norma principal. |
| `jurisdiction` | `NACIONAL`, por norma estatal aprobada por el Gobierno o las Cortes Generales. | `AUTONÓMICO`, por norma aprobada por un parlamento o gobierno autonómico, aunque mencione Estado, Constitución o Unión Europea como contexto. |
| `is_repealed` | `false`: texto vigente, modificado o con debate, pero sin derogación. | `true`: texto afirma que la norma fue derogada o sustituida por otra posterior. |
| `affected_articles` | Lista poblada con dos o tres artículos/disposiciones modificados o relevantes. | `[]`: la descripción habla de finalidad, entrada en vigor y derogación, pero no cita artículos concretos de la norma principal. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Real decreto-ley de ahorro energético de 2022

Source: https://es.wikipedia.org/wiki/Real_Decreto-ley_14/2022

El Real Decreto-ley 14/2022, de 1 de agosto, de medidas de sostenibilidad económica en el ámbito del transporte, en materia de becas y ayudas al estudio, así como de medidas de ahorro, eficiencia energética y de reducción de la dependencia energética del gas natural, fue aprobado por el Consejo de Ministros el 1 de agosto de 2022. La norma se dictó con alcance estatal tras la subida del precio del gas y fue convalidada semanas después por el Congreso de los Diputados.

Contenido y tramitación
La exposición de motivos relaciona el paquete con el plan europeo de reducción de demanda energética, pero el texto se presenta como norma española de urgencia. Entre las medidas de mayor eco, el artículo 29 fijó límites de climatización para recintos administrativos, comercios y estaciones; el artículo 30 exigió sistemas automáticos de cierre en edificios con acceso desde la calle; y la disposición adicional tercera prorrogó ayudas al transporte colectivo.

La edición consolidada incorpora correcciones menores y remisiones a órdenes ministeriales posteriores. No obstante, el sumario del BOE mantiene la disposición como vigente y solo marca algunos apartados como modificados.
```

`instruction`:

```text
Extrae el resumen del contrato o acto legislativo.
```

`output`:

```json
{
  "official_title": "Real Decreto-ley 14/2022, de 1 de agosto, de medidas de sostenibilidad económica en el ámbito del transporte, en materia de becas y ayudas al estudio, así como de medidas de ahorro, eficiencia energética y de reducción de la dependencia energética del gas natural",
  "law_range": "REAL DECRETO-LEY",
  "sanction_date": "2022-08-01",
  "jurisdiction": "NACIONAL",
  "is_repealed": false,
  "affected_articles": [
    "artículo 29",
    "artículo 30",
    "disposición adicional tercera"
  ]
}
```

`reasoning`:

```json
{
  "official_title": {
    "field_asks": "el título oficial completo de la norma.",
    "relevant_fragments": "\"El Real Decreto-ley 14/2022, de 1 de agosto, de medidas de sostenibilidad económica en el ámbito del transporte, en materia de becas y ayudas al estudio, así como de medidas de ahorro, eficiencia energética y de reducción de la dependencia energética del gas natural\".",
    "final_value": "Como el fragmento relevante da el título formal completo de la norma principal, el valor debe ser ese título íntegro."
  },
  "law_range": {
    "field_asks": "el rango jurídico de la norma, mapeado a uno de estos valores: LEY ORGÁNICA, LEY ORDINARIA, REAL DECRETO, REAL DECRETO-LEY, CONSTITUCIÓN u OTRA.",
    "relevant_fragments": "\"El Real Decreto-ley 14/2022\" y \"norma española de urgencia\".",
    "final_value": "Como los fragmentos relevantes identifican la norma como real decreto-ley, el valor del enum debe ser \"REAL DECRETO-LEY\"."
  },
  "sanction_date": {
    "field_asks": "la fecha de sanción o aprobación de la norma en formato YYYY-MM-DD, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"fue aprobado por el Consejo de Ministros el 1 de agosto de 2022\".",
    "final_value": "Como el fragmento relevante da una fecha completa de aprobación, debe normalizarse a \"2022-08-01\"."
  },
  "jurisdiction": {
    "field_asks": "el ámbito de aplicación, mapeado a uno de estos valores: NACIONAL, AUTONÓMICO, LOCAL o EUROPEO.",
    "relevant_fragments": "\"La norma se dictó con alcance estatal\" y \"norma española de urgencia\".",
    "final_value": "Como los fragmentos relevantes sitúan la norma en el ámbito estatal español, el valor del enum debe ser \"NACIONAL\"."
  },
  "is_repealed": {
    "field_asks": "true si el texto menciona que la norma ya no está en vigor, fue derogada o fue sustituida; false en caso contrario.",
    "relevant_fragments": "\"el sumario del BOE mantiene la disposición como vigente\" y \"solo marca algunos apartados como modificados\".",
    "final_value": "Como los fragmentos relevantes hablan de vigencia y modificaciones parciales, no de derogación de la norma, el valor debe ser false."
  },
  "affected_articles": {
    "field_asks": "lista de artículos, disposiciones o apartados concretos mencionados como modificados o relevantes.",
    "relevant_fragments": "\"el artículo 29 fijó límites de climatización\", \"el artículo 30 exigió sistemas automáticos de cierre\" y \"la disposición adicional tercera prorrogó ayudas al transporte colectivo\".",
    "final_value": "Como los fragmentos relevantes mencionan esas unidades normativas concretas como relevantes, la lista debe incluir \"artículo 29\", \"artículo 30\" y \"disposición adicional tercera\"."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# Ley de patios verdes valenciana

Source: https://es.wikipedia.org/wiki/Ley_de_patios_verdes_valenciana

La llamada ley de patios verdes fue citada en prensa durante años como una iniciativa escolar de la Generalitat. En la ficha consolidada aparece con su título formal, Ley 6/2009, de huertos escolares y educación ambiental de la Comunitat Valenciana, una ley autonómica ordinaria tramitada por Les Corts tras varias campañas municipales de compostaje. La crónica parlamentaria sitúa su aprobación en la primavera de 2009, mientras que la publicación oficial se produjo el 14 de julio de ese año.

Objeto y aplicación
El texto creó una red de huertos escolares, reguló convenios con ayuntamientos y encargó a la conselleria educativa preparar guías para centros públicos y concertados. También citaba programas europeos de sostenibilidad urbana y una orden estatal sobre residuos orgánicos, pero esas referencias funcionaban como contexto técnico, no como rango de la norma.

Vigencia
La Ley 3/2018, de educación ambiental y sostenibilidad escolar, derogó íntegramente la ley de patios verdes y sustituyó sus programas por planes de centro. La exposición de motivos de la norma nueva conservó la memoria de los huertos piloto, aunque los expedientes pasaron a tramitarse bajo el marco de 2018.
```

`instruction`:

```text
Extrae el resumen del contrato o acto legislativo.
```

`output`:

```json
{
  "official_title": "Ley 6/2009, de huertos escolares y educación ambiental de la Comunitat Valenciana",
  "law_range": "LEY ORDINARIA",
  "sanction_date": null,
  "jurisdiction": "AUTONÓMICO",
  "is_repealed": true,
  "affected_articles": []
}
```

`reasoning`:

```json
{
  "official_title": {
    "field_asks": "el título oficial completo de la norma.",
    "relevant_fragments": "\"La llamada ley de patios verdes\" y \"aparece con su título formal, Ley 6/2009, de huertos escolares y educación ambiental de la Comunitat Valenciana\".",
    "final_value": "Como los fragmentos relevantes distinguen el nombre periodístico del título formal, el valor debe ser \"Ley 6/2009, de huertos escolares y educación ambiental de la Comunitat Valenciana\"."
  },
  "law_range": {
    "field_asks": "el rango jurídico de la norma, mapeado a uno de estos valores: LEY ORGÁNICA, LEY ORDINARIA, REAL DECRETO, REAL DECRETO-LEY, CONSTITUCIÓN u OTRA.",
    "relevant_fragments": "\"Ley 6/2009\" y \"una ley autonómica ordinaria tramitada por Les Corts\".",
    "final_value": "Como los fragmentos relevantes la describen como ley ordinaria, el valor del enum debe ser \"LEY ORDINARIA\"."
  },
  "sanction_date": {
    "field_asks": "la fecha de sanción o aprobación de la norma en formato YYYY-MM-DD, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"sitúa su aprobación en la primavera de 2009\" y \"la publicación oficial se produjo el 14 de julio de ese año\".",
    "final_value": "Los fragmentos relevantes dan una estación aproximada para la aprobación y una fecha de publicación, pero no una fecha completa de sanción o aprobación; el valor debe ser null."
  },
  "jurisdiction": {
    "field_asks": "el ámbito de aplicación, mapeado a uno de estos valores: NACIONAL, AUTONÓMICO, LOCAL o EUROPEO.",
    "relevant_fragments": "\"iniciativa escolar de la Generalitat\", \"Comunitat Valenciana\" y \"ley autonómica ordinaria tramitada por Les Corts\".",
    "final_value": "Como los fragmentos relevantes sitúan la norma en instituciones y ámbito valencianos, el valor del enum debe ser \"AUTONÓMICO\"."
  },
  "is_repealed": {
    "field_asks": "true si el texto menciona que la norma ya no está en vigor, fue derogada o fue sustituida; false en caso contrario.",
    "relevant_fragments": "\"La Ley 3/2018, de educación ambiental y sostenibilidad escolar, derogó íntegramente la ley de patios verdes\" y \"sustituyó sus programas por planes de centro\".",
    "final_value": "Como los fragmentos relevantes afirman derogación íntegra y sustitución por una norma posterior, el valor debe ser true."
  },
  "affected_articles": {
    "field_asks": "lista de artículos, disposiciones o apartados concretos mencionados como modificados o relevantes.",
    "relevant_fragments": "\"creó una red de huertos escolares\", \"reguló convenios con ayuntamientos\" y \"encargó a la conselleria educativa preparar guías\".",
    "final_value": "Los fragmentos relevantes describen contenidos de la norma, pero no citan artículos, disposiciones o apartados concretos; la lista debe ser vacía."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son entradas enciclopédicas largas en Markdown: encabezado con `# <nombre común>`, línea de `Source`, una introducción con el título formal y fechas, y después secciones como antecedentes, contenido, modificaciones, sanciones, debate público o derecho supletorio. Suelen contener muchos distractores jurídicos: leyes anteriores modificadas, leyes futuras, artículos constitucionales, fechas de publicación o entrada en vigor, organizaciones políticas y citas doctrinales. Para los nuevos ejemplos conviene mantener una entrada de noticia/enciclopedia legislativa, pero con menos de 1600 caracteres, dejando claro qué norma es la principal y qué referencias son contexto.
