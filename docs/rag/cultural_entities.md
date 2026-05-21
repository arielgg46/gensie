# cultural_entities

Los tasks `cultural_entities` son extracciones L5 de menciones nombradas en recortes culturales, casi siempre criticas o avances de cine y television. El modelo debe devolver una unica lista `entities` con menciones verbatim y etiqueta semantica, sin separar por categorias en campos distintos y sin normalizar titulos, fechas ni nombres.

## Ejemplos revisados

- `data/dev_rev/cultural_entities_001.json`
- `data/dev_rev/cultural_entities_002.json`
- `data/dev/cultural_entities_001.json`
- `data/dev/cultural_entities_002.json`

Solo existen dos ejemplos del prefijo en `dev_rev` y los dos archivos de `data/dev` repiten esas instancias; no hay cinco ejemplos disponibles sin salir del prefijo.

## Dualidad por campo

| Campo | Opinion sobre dualidad |
| --- | --- |
| `entities` | Array de objetos, no requerido en `required` pero central para la tarea. La dualidad util es lista corta frente a lista mas densa, y cobertura de etiquetas distintas: `PERSON`, `ORGANIZATION`, `LOCATION`, `DATE`, `EVENT` y `MISCELLANEOUS`. En este prefijo conviene mantener titulos de peliculas/series como `MISCELLANEOUS`, personas reales y personajes como `PERSON`, estudios o medios como `ORGANIZATION`, lugares culturales como `LOCATION`, fechas completas como `DATE` y festivales/premios como `EVENT`. |
| `entities[].text` | Debe ser la mencion verbatim, respetando comillas, signos y articulos cuando forman parte del titulo. Dualidad entre menciones simples (`Sofía Galán`) y titulos con puntuacion o articulo (`El jardín orbital`, `La casa de las mareas`). No debe traducirse ni abreviarse. |
| `entities[].label` | Enum requerido. Dualidad entre entidades culturales que no son personas (`MISCELLANEOUS`) y organizaciones/lugares/fechas reales que aparecen cerca. La etiqueta debe depender de la mencion en el texto, no de conocimiento externo ampliado. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `entities` | Lista única de menciones nombradas del recorte cultural. Extrae películas, series, actores, personajes, estudios, medios, lugares, fechas y eventos si aparecen; no agrupes por categoría ni añadas entidades inferidas desde conocimiento externo. |
| `entities[].text` | Mención verbatim tal como aparece en el texto. Conserva tildes, signos de exclamación, comillas internas, artículos y fechas completas; no traduzcas, normalices ni fusiones variantes de un título si el texto las menciona por separado. |
| `entities[].label` | Etiqueta del enum completo: `PERSON`, `ORGANIZATION`, `LOCATION`, `DATE`, `EVENT` o `MISCELLANEOUS`. Actores, directoras y personajes suelen ser `PERSON`; estudios, plataformas y medios `ORGANIZATION`; ciudades, barrios o lugares culturales `LOCATION`; fechas de estreno `DATE`; festivales o premios `EVENT`; películas, series y obras culturales `MISCELLANEOUS`. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `entities` | Lista corta con persona, personaje, lugares y titulos culturales. Sin fechas, organizaciones ni eventos. | Lista mas poblada con persona, organizacion, lugar, fecha, evento/festival y varios titulos culturales. |
| `entities[].text` | Menciones breves y titulos limpios extraidos del encabezado y primer parrafo. | Menciones con signos, articulos y fecha completa dentro de un recorte con `[...]`. |
| `entities[].label` | Contraste `PERSON`, `LOCATION` y `MISCELLANEOUS`. | Cobertura completa incluyendo `ORGANIZATION`, `DATE` y `EVENT`. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# 'El jardín orbital' confirma que la animación española puede mirar a las estrellas sin perder el pulso doméstico [...] Desde que 'Robot Dreams' abrió una puerta inesperada, cada nuevo estreno animado español parece obligado a cargar con una comparación injusta. 'El jardín orbital' sale bastante bien parada: cuenta la historia de Nora, una niña que imagina una estación espacial sobre Madrid para escapar del ruido de su casa, y lo hace sin convertir la melancolía en una postal. La directora Sofía Galán filma los pasillos de la estación como si fueran habitaciones infantiles, mientras el barrio de Lavapiés aparece convertido en mapa emocional. Hay ecos de 'Wall-E', claro, pero también una ternura propia que no necesita pedir permiso a Pixar.
```

`instruction`:

```text
Extrae los nombres de películas, personas, personajes y lugares mencionados en la introducción de la crítica.
```

`output`:

```json
{
  "entities": [
    {
      "text": "El jardín orbital",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Robot Dreams",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Nora",
      "label": "PERSON"
    },
    {
      "text": "Madrid",
      "label": "LOCATION"
    },
    {
      "text": "Sofía Galán",
      "label": "PERSON"
    },
    {
      "text": "Lavapiés",
      "label": "LOCATION"
    },
    {
      "text": "Wall-E",
      "label": "MISCELLANEOUS"
    }
  ]
}
```

`reasoning`:

```json
{
  "entities": {
    "field_asks": "lista de menciones nombradas del recorte cultural, cada una con texto verbatim y etiqueta PERSON, ORGANIZATION, LOCATION, DATE, EVENT o MISCELLANEOUS.",
    "relevant_fragments": "\"'El jardín orbital'\", \"'Robot Dreams'\", \"Nora\", \"Madrid\", \"la directora Sofía Galán\", \"Lavapiés\" y \"'Wall-E'\".",
    "final_value": "Como los fragmentos relevantes contienen titulos culturales, personas/personajes y lugares, la lista debe incluir esas siete menciones verbatim con sus etiquetas: titulos como MISCELLANEOUS, Nora y Sofía Galán como PERSON, y Madrid y Lavapiés como LOCATION."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# 'La casa de las mareas' ya tiene fecha en cines tras conquistar San Sebastián, y A24 prepara su salto internacional [...] Pocas películas españolas llegan con una conversación tan rara alrededor: primero fue el premio en el Festival de San Sebastián, luego las comparaciones con 'Alcarràs' y ahora el anuncio de que A24 moverá la cinta fuera de Europa. La película de Iker Valcárcel, rodada entre Getaria y Zumaia, se estrenará en salas el 17 de abril de 2026. El tráiler vende una historia de herencias, silencios y tormentas familiares, con Marta Etura como madre que vuelve al caserío y Eneko Sagardoy interpretando al hermano que nunca se marchó. Netflix tanteó sus derechos, pero la distribuidora Bruma Films ha preferido mantener primero el recorrido en cines.
```

`instruction`:

```text
Identifica las películas, estudios, personas, lugares, fechas y eventos mencionados en la noticia cultural.
```

`output`:

```json
{
  "entities": [
    {
      "text": "La casa de las mareas",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "San Sebastián",
      "label": "LOCATION"
    },
    {
      "text": "A24",
      "label": "ORGANIZATION"
    },
    {
      "text": "Festival de San Sebastián",
      "label": "EVENT"
    },
    {
      "text": "Alcarràs",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Iker Valcárcel",
      "label": "PERSON"
    },
    {
      "text": "Getaria",
      "label": "LOCATION"
    },
    {
      "text": "Zumaia",
      "label": "LOCATION"
    },
    {
      "text": "17 de abril de 2026",
      "label": "DATE"
    },
    {
      "text": "Marta Etura",
      "label": "PERSON"
    },
    {
      "text": "Eneko Sagardoy",
      "label": "PERSON"
    },
    {
      "text": "Netflix",
      "label": "ORGANIZATION"
    },
    {
      "text": "Bruma Films",
      "label": "ORGANIZATION"
    }
  ]
}
```

`reasoning`:

```json
{
  "entities": {
    "field_asks": "lista de menciones nombradas de peliculas, estudios, personas, lugares, fechas y eventos, con texto verbatim y etiqueta del enum permitido.",
    "relevant_fragments": "\"'La casa de las mareas'\", \"San Sebastián\", \"A24\", \"Festival de San Sebastián\", \"'Alcarràs'\", \"Iker Valcárcel\", \"Getaria y Zumaia\", \"17 de abril de 2026\", \"Marta Etura\", \"Eneko Sagardoy\", \"Netflix\" y \"Bruma Films\".",
    "final_value": "Como el recorte menciona una pelicula principal, otra pelicula comparada, organizaciones, lugares, personas, una fecha completa y un festival, la lista debe conservar esas menciones verbatim. \"Festival de San Sebastián\" se etiqueta como EVENT, mientras \"San Sebastián\" aislado en el encabezado funciona como LOCATION."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son recortes muy compactos de articulos culturales en Markdown, sin linea `Source:`, con encabezado `#` largo, tono periodistico/opinativo y el marcador `[...]` para saltar del titular al cuerpo. No usan secciones internas. Suelen mezclar titulos entre comillas, actores, personajes, estudios, medios, lugares de la industria y fechas de estreno. La salida no agrupa por tipo: todo va en `entities` como una lista unica de menciones verbatim. Los ejemplos nuevos mantienen esa forma de recorte, con distractores naturales de critica cultural, y evitan inventar categorias fuera del enum o normalizar titulos y fechas.
