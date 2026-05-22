# legal_entities

Los tasks `legal_entities` son extracciones L5 de entidades nombradas en textos legales españoles, normalmente encabezados, preámbulos o disposiciones en estilo BOE. El modelo debe devolver una única lista `entities` con menciones verbatim y etiqueta semántica, sin normalizar mayúsculas, sin expandir instituciones que no aparecen así en el texto y evitando duplicar la misma entidad cuando la repetición no aporta una mención distinta.

## Ejemplos revisados

- `data/dev_rev/legal_entities_001.json`
- `data/dev/legal_entities_001.json`

Solo existe una instancia del prefijo en `dev_rev` y `data/dev` contiene la misma instancia con una mencion repetida adicional; no hay cinco ejemplos disponibles del prefijo sin salir de el.

## Dualidad por campo

| Campo | Opinion sobre dualidad |
| --- | --- |
| `entities` | Array de objetos. Dualidad principal entre texto solemne de encabezado/preámbulo, con persona, institución, pueblo/nación y lugares, frente a disposición administrativa con órgano, norma, fechas y territorio. En el ejemplo curado se evita duplicar `España` y se conserva la primera mención completa. |
| `entities[].text` | Debe ser la mención verbatim, respetando mayúsculas y artículos cuando forman parte de la frase legal (`DON JUAN CARLOS I`, `LAS CORTES`, `La Nación española`). Dualidad entre menciones institucionales en mayúsculas y menciones mixtas con fecha o título de norma. |
| `entities[].label` | Enum requerido. En este prefijo aparecen naturalmente `PERSON`, `ORGANIZATION`, `LOCATION`, `DATE` y `MISCELLANEOUS`. `EVENT` no se observa en el ejemplo revisado; se puede cubrir en un caso administrativo solo si el texto nombra un acto o proceso como evento, pero no conviene forzarlo si la instrucción pide personas, organizaciones y lugares. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `entities` | Lista única de menciones nombradas explícitas del texto legal. Extrae personas, órganos, instituciones, territorios, países, fechas, normas, boletines y sujetos jurídicos cuando aparecen; evita duplicar una entidad repetida sin una mención distinta útil y no expandas instituciones con palabras que el texto no contiene. |
| `entities[].text` | Mención verbatim, preservando mayúsculas, tildes, artículos, tratamientos, numeración normativa, comillas españolas y frases institucionales completas. No normalices `DON`, `LAS CORTES` o `EL PUEBLO ESPAÑOL`, y no conviertas conceptos legales en nombres inventados. |
| `entities[].label` | Etiqueta del enum completo: `PERSON`, `ORGANIZATION`, `LOCATION`, `DATE`, `EVENT` o `MISCELLANEOUS`. Personas reales son `PERSON`; Cortes, ministerios, direcciones generales y boletines oficiales son `ORGANIZATION`; países, territorios y lugares son `LOCATION`; fechas son `DATE`; actos o procesos nombrados explícitamente pueden ser `EVENT`; constituciones, reales decretos, leyes, pueblos o nación como sujeto jurídico suelen ser `MISCELLANEOUS`. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `entities` | Texto de promulgación/preámbulo con persona, reino/lugar, cortes, pueblo y nación como entidad conceptual. Sin fechas. | Texto de real decreto/disposición con ministerio, comunidad autónoma, boletín, fechas y norma mencionada. |
| `entities[].text` | Menciones en mayúsculas y fórmulas solemnes, evitando repetir el mismo lugar si reaparece en minúsculas. | Menciones administrativas largas, incluyendo fechas verbatim y órganos con nombre completo. |
| `entities[].label` | Contraste `PERSON`, `ORGANIZATION`, `LOCATION` y `MISCELLANEOUS`. | Cobertura de `ORGANIZATION`, `LOCATION`, `DATE` y `MISCELLANEOUS`. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
DOÑA ISABEL II, REINA DE ESPAÑA, A TODOS LOS QUE LA PRESENTE VIEREN Y ENTENDIEREN,

SABED: QUE LAS CORTES GENERALES HAN APROBADO Y EL PUEBLO ESPAÑOL RATIFICADO LA SIGUIENTE LEY FUNDAMENTAL:

**PREÁMBULO**

La Nación española, deseando asegurar la libertad civil, la justicia y la concordia entre los territorios que la integran, proclama su voluntad de:

Garantizar la convivencia democrática dentro de la Ley Fundamental y de las normas que emanen de la voluntad popular.

Proteger a todos los españoles y pueblos de España en el ejercicio de sus derechos, culturas, lenguas e instituciones.

Promover el progreso de la cultura y de la economía para asegurar una digna calidad de vida.

Colaborar en el fortalecimiento de unas relaciones pacíficas entre todos los pueblos de Europa.
```

`instruction`:

```text
Extrae las entidades nombradas (personas, organizaciones, lugares) mencionadas en el encabezado y preámbulo de la Ley Fundamental.
```

`output`:

```json
{
  "entities": [
    {
      "text": "DOÑA ISABEL II",
      "label": "PERSON"
    },
    {
      "text": "ESPAÑA",
      "label": "LOCATION"
    },
    {
      "text": "LAS CORTES GENERALES",
      "label": "ORGANIZATION"
    },
    {
      "text": "EL PUEBLO ESPAÑOL",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "LEY FUNDAMENTAL",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "La Nación española",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Europa",
      "label": "LOCATION"
    }
  ]
}
```

`reasoning`:

```json
{
  "entities": {
    "field_asks": "lista de entidades nombradas del encabezado y preámbulo legal, con menciones verbatim y etiquetas PERSON, ORGANIZATION, LOCATION, DATE, EVENT o MISCELLANEOUS.",
    "relevant_fragments": "\"DOÑA ISABEL II, REINA DE ESPAÑA\" (persona titular y país/reino nombrado), \"SABED: QUE LAS CORTES GENERALES HAN APROBADO Y EL PUEBLO ESPAÑOL RATIFICADO LA SIGUIENTE LEY FUNDAMENTAL\" (órgano legislativo, sujeto jurídico y norma), \"La Nación española [...] proclama su voluntad\" (sujeto constitucional/conceptual) y \"relaciones pacíficas entre todos los pueblos de Europa\" (lugar o región nombrada).",
    "final_value": "Como los fragmentos relevantes nombran una persona, un lugar, una organización institucional, sujetos constitucionales y una norma, la lista debe conservar esas menciones verbatim. La repetición posterior de España dentro de \"pueblos de España\" no se incluye de nuevo porque ya aparece como primera mención completa en mayúsculas."
  }
}
```

### Ejemplo 2

`input_text`:

```text
REAL DECRETO 48/2026, de 15 de enero, por el que se regula la concesión directa de subvenciones para la restauración de archivos municipales afectados por inundaciones.

El Ministerio de Cultura, a propuesta de la Comunidad Autónoma de Aragón, considera necesario articular un procedimiento extraordinario para proteger fondos documentales dañados en diversos municipios de Zaragoza.

La presente disposición se dicta al amparo de la Ley 16/1985, de 25 de junio, del Patrimonio Histórico Español, y será publicada en el «Boletín Oficial del Estado».

Artículo 1. Objeto.

Se autoriza la concesión directa de ayudas a los ayuntamientos incluidos en el anexo, de acuerdo con las disponibilidades presupuestarias y con los informes técnicos emitidos por la Dirección General de Patrimonio Cultural.
```

`instruction`:

```text
Identifica las entidades nombradas (normas, organismos, lugares y fechas) mencionadas en el fragmento del real decreto.
```

`output`:

```json
{
  "entities": [
    {
      "text": "REAL DECRETO 48/2026",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "15 de enero",
      "label": "DATE"
    },
    {
      "text": "Ministerio de Cultura",
      "label": "ORGANIZATION"
    },
    {
      "text": "Comunidad Autónoma de Aragón",
      "label": "ORGANIZATION"
    },
    {
      "text": "Zaragoza",
      "label": "LOCATION"
    },
    {
      "text": "Ley 16/1985",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "25 de junio",
      "label": "DATE"
    },
    {
      "text": "Patrimonio Histórico Español",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Boletín Oficial del Estado",
      "label": "ORGANIZATION"
    },
    {
      "text": "Dirección General de Patrimonio Cultural",
      "label": "ORGANIZATION"
    }
  ]
}
```

`reasoning`:

```json
{
  "entities": {
    "field_asks": "lista de entidades nombradas en el fragmento legal, incluyendo normas, organismos, lugares y fechas con texto verbatim.",
    "relevant_fragments": "\"REAL DECRETO 48/2026, de 15 de enero\" (norma y fecha), \"El Ministerio de Cultura, a propuesta de la Comunidad Autónoma de Aragón\" (órganos o administraciones), \"municipios de Zaragoza\" (lugar), \"Ley 16/1985, de 25 de junio, del Patrimonio Histórico Español\" (norma, fecha y materia jurídica), \"será publicada en el «Boletín Oficial del Estado»\" (boletín oficial como organización) y \"informes técnicos emitidos por la Dirección General de Patrimonio Cultural\" (órgano administrativo).",
    "final_value": "Como los fragmentos relevantes nombran normas, fechas, órganos administrativos, un territorio y el boletín oficial, la lista debe conservar esas menciones verbatim con etiquetas MISCELLANEOUS para normas o conceptos legales, DATE para fechas, ORGANIZATION para órganos y boletín, y LOCATION para Zaragoza."
  }
}
```

## Estructura de los input_text

El `input_text` revisado es un fragmento legal BOE en Markdown, sin línea `Source:`, con fórmula solemne en mayúsculas, preámbulo destacado con `**PREÁMBULO**`, párrafos normativos y menciones institucionales. La salida curada conserva menciones verbatim como `DON JUAN CARLOS I`, `LAS CORTES`, `EL PUEBLO ESPAÑOL` y `La Nación española`, y evita duplicar `España` cuando reaparece más adelante con la misma función. Los nuevos ejemplos mantienen el tono jurídico formal, la puntuación y las mayúsculas propias del BOE, y proponen un segundo estilo administrativo de real decreto para cubrir fechas, órganos y normas sin abandonar el registro legal.
