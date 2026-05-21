# stem_astronomy_detailed

Los tasks `stem_astronomy_detailed` son extracciones L5 de propiedades físicas y orbitales de cuerpos celestes: el modelo debe identificar nombre oficial y tipo, normalizar magnitudes numéricas en kg, km, días y UA cuando el texto las proporciona, y devolver `null` ante valores aproximados insuficientes, frases comparativas o datos históricos que no corresponden al campo pedido.

## Ejemplos revisados

- `data/dev_rev/stem_astronomy_detailed_001.json`
- `data/dev_rev/stem_astronomy_detailed_002.json`
- `data/dev/stem_astronomy_detailed_003.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `official_name` | Requerido, `string`, no nullable. Dualidad entre nombre directo en encabezado y designación científica en el cuerpo con nombre popular en el título. |
| `body_type` | Enum requerido. Debe mapear a `ASTEROIDE`, `COMETA`, `PLANETA`, `LUNA`, `PLANETA ENANO`, `OBJETO INTERESTELAR` u `OTRO`. Conviene alternar planeta con cometa/asteroide para no fijar el schema a planetas del sistema solar. |
| `mass_kg` | `number` vs `null`. Dualidad entre masa explícita en kg o notación científica y ausencia de masa medible. No inferir desde tamaño o tipo. |
| `diameter_km` | `number` vs `null`. Dualidad entre diámetro medio explícito y descripciones visuales sin medida. |
| `eccentricity` | `number` vs `null`. En Venus se menciona "menos del 1%" y queda null por falta de número exacto; conviene un caso con valor decimal explícito y otro sin dato suficiente. |
| `orbital_period_days` | `number` vs `null`. Dualidad entre periodo dado en días y referencias a años o rotación que no deben confundirse con periodo orbital, salvo que el texto ya dé equivalencia en días. |
| `semi_major_axis_au` | `number` vs `null`. Dualidad entre semieje mayor explícito en UA y distancias vagas como "cerca del Sol" o "órbita inferior". |
| `discovery_date` | `string` `YYYY-MM-DD` vs `null`. Para planetas conocidos desde la antigüedad suele ser `null`; para cometas/asteroides modernos puede normalizarse desde fecha completa. |
| `discoverer` | `string` vs `null`. Dualidad entre descubridor nombrado y objetos conocidos desde tiempos antiguos o sin descubridor individual. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `official_name` | Planeta con nombre directo. | Cometa con nombre oficial en el cuerpo y nombre abreviado en el encabezado. |
| `body_type` | `PLANETA`. | `COMETA`. |
| `mass_kg` | Valor no null en notación científica. | `null`, núcleo no resuelto y sin estimación de masa. |
| `diameter_km` | Valor no null de diámetro medio. | `null`, sin diámetro medido. |
| `eccentricity` | Valor decimal explícito. | Valor decimal explícito o `null`; usaré valor explícito para ejercitar precisión orbital. |
| `orbital_period_days` | Valor explícito en días. | Valor explícito en días. |
| `semi_major_axis_au` | Valor explícito en UA. | Valor explícito en UA. |
| `discovery_date` | `null`, conocido desde la antigüedad. | Fecha completa normalizada. |
| `discoverer` | `null`. | Descubridor nombrado. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Marte

Marte es el cuarto planeta del sistema solar y un planeta rocoso. Las fichas astronómicas modernas le asignan una masa de 6,4171 × 10^23 kg y un diámetro medio de 6779 km. Su órbita alrededor del Sol tiene una excentricidad de 0,0934, un semieje mayor de 1,524 UA y un periodo orbital de 686,98 días terrestres.

El planeta fue observado desde la antigüedad por su brillo rojizo y aparece en catálogos babilónicos y grecorromanos, por lo que no se atribuye a una fecha moderna de descubrimiento. La rotación marciana dura unas 24,6 horas, dato que se menciona aparte de su traslación orbital.
```

`instruction`:

```text
Extrae las propiedades físicas y orbitales del cuerpo celeste descrito en el texto, incluyendo su nombre oficial, tipo, y parámetros orbitales disponibles.
```

`output`:

```json
{
  "official_name": "Marte",
  "body_type": "PLANETA",
  "mass_kg": 6.4171e23,
  "diameter_km": 6779,
  "eccentricity": 0.0934,
  "orbital_period_days": 686.98,
  "semi_major_axis_au": 1.524,
  "discovery_date": null,
  "discoverer": null
}
```

`reasoning`:

```json
{
  "official_name": {
    "field_asks": "el nombre o designación científica principal del cuerpo celeste.",
    "relevant_fragments": "\"# Marte\" y \"Marte es el cuarto planeta del sistema solar\".",
    "final_value": "Como los fragmentos relevantes presentan Marte como el cuerpo descrito, el nombre oficial debe ser \"Marte\"."
  },
  "body_type": {
    "field_asks": "la clasificación del cuerpo celeste, mapeada a uno de estos valores: ASTEROIDE, COMETA, PLANETA, LUNA, PLANETA ENANO, OBJETO INTERESTELAR u OTRO.",
    "relevant_fragments": "\"Marte es el cuarto planeta del sistema solar y un planeta rocoso\".",
    "final_value": "Como el fragmento relevante clasifica Marte como planeta, el valor del enum debe ser \"PLANETA\"."
  },
  "mass_kg": {
    "field_asks": "masa en kilogramos, o null si no hay dato suficiente.",
    "relevant_fragments": "\"una masa de 6,4171 × 10^23 kg\".",
    "final_value": "Como el fragmento relevante da la masa en kg, el valor debe normalizarse a 6.4171e23."
  },
  "diameter_km": {
    "field_asks": "diámetro medio en kilómetros, o null si no hay dato suficiente.",
    "relevant_fragments": "\"un diámetro medio de 6779 km\".",
    "final_value": "Como el fragmento relevante da el diámetro medio en km, el valor debe ser 6779."
  },
  "eccentricity": {
    "field_asks": "excentricidad orbital, o null si no hay valor numérico suficiente.",
    "relevant_fragments": "\"excentricidad de 0,0934\".",
    "final_value": "Como el fragmento relevante da la excentricidad decimal, el valor debe ser 0.0934."
  },
  "orbital_period_days": {
    "field_asks": "tiempo para completar una órbita en días terrestres, o null si no hay dato suficiente.",
    "relevant_fragments": "\"un periodo orbital de 686,98 días terrestres\" y \"La rotación marciana dura unas 24,6 horas\".",
    "final_value": "Como el fragmento relevante distingue traslación orbital de rotación, el periodo orbital debe ser 686.98 días."
  },
  "semi_major_axis_au": {
    "field_asks": "semieje mayor o distancia media al Sol en unidades astronómicas, o null si no hay dato suficiente.",
    "relevant_fragments": "\"un semieje mayor de 1,524 UA\".",
    "final_value": "Como el fragmento relevante da el semieje mayor en UA, el valor debe ser 1.524."
  },
  "discovery_date": {
    "field_asks": "fecha de descubrimiento en formato YYYY-MM-DD, o null si no hay fecha suficiente.",
    "relevant_fragments": "\"fue observado desde la antigüedad\" y \"no se atribuye a una fecha moderna de descubrimiento\".",
    "final_value": "Como los fragmentos relevantes sitúan el conocimiento de Marte en la antigüedad y no dan fecha de descubrimiento, el valor debe ser null."
  },
  "discoverer": {
    "field_asks": "persona u observatorio que descubrió el objeto, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"aparece en catálogos babilónicos y grecorromanos\".",
    "final_value": "El fragmento relevante habla de tradición observacional antigua, pero no identifica un descubridor individual u observatorio; el valor debe ser null."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# Cometa Rivera-Soto

El cometa C/2012 R3 (Rivera-Soto) fue identificado el 14 de septiembre de 2012 por la astrónoma Laura Rivera Soto desde el Observatorio de Calar Alto. La ficha del Minor Planet Center lo clasifica como cometa de periodo largo y cita una órbita con excentricidad 0,742, semieje mayor de 3,86 UA y periodo orbital de 2765 días.

Las imágenes de seguimiento mostraron una coma difusa y una cola débil, pero el núcleo no quedó resuelto. Por eso los informes fotométricos describen actividad cometaria sin publicar masa ni diámetro medio. Una observación de 2014 revisó la inclinación orbital, pero no cambió el nombre oficial.
```

`instruction`:

```text
Extrae las propiedades físicas y orbitales del cuerpo celeste descrito en el texto, incluyendo su nombre oficial, tipo de cuerpo, masa, diámetro, excentricidad orbital, período orbital, semieje mayor, y datos de descubrimiento.
```

`output`:

```json
{
  "official_name": "C/2012 R3 (Rivera-Soto)",
  "body_type": "COMETA",
  "mass_kg": null,
  "diameter_km": null,
  "eccentricity": 0.742,
  "orbital_period_days": 2765,
  "semi_major_axis_au": 3.86,
  "discovery_date": "2012-09-14",
  "discoverer": "Laura Rivera Soto"
}
```

`reasoning`:

```json
{
  "official_name": {
    "field_asks": "el nombre o designación científica principal del cuerpo celeste.",
    "relevant_fragments": "\"El cometa C/2012 R3 (Rivera-Soto)\" y \"no cambió el nombre oficial\".",
    "final_value": "Como el fragmento relevante da la designación completa, el nombre oficial debe ser \"C/2012 R3 (Rivera-Soto)\"."
  },
  "body_type": {
    "field_asks": "la clasificación del cuerpo celeste, mapeada a uno de estos valores: ASTEROIDE, COMETA, PLANETA, LUNA, PLANETA ENANO, OBJETO INTERESTELAR u OTRO.",
    "relevant_fragments": "\"El cometa C/2012 R3 (Rivera-Soto)\" y \"lo clasifica como cometa de periodo largo\".",
    "final_value": "Como los fragmentos relevantes clasifican el objeto como cometa, el valor del enum debe ser \"COMETA\"."
  },
  "mass_kg": {
    "field_asks": "masa en kilogramos, o null si no hay dato suficiente.",
    "relevant_fragments": "\"el núcleo no quedó resuelto\" y \"sin publicar masa ni diámetro medio\".",
    "final_value": "Como los fragmentos relevantes explican que no se publicó masa, el valor debe ser null."
  },
  "diameter_km": {
    "field_asks": "diámetro medio en kilómetros, o null si no hay dato suficiente.",
    "relevant_fragments": "\"el núcleo no quedó resuelto\" y \"sin publicar masa ni diámetro medio\".",
    "final_value": "Como los fragmentos relevantes indican que no se publicó diámetro medio, el valor debe ser null."
  },
  "eccentricity": {
    "field_asks": "excentricidad orbital, o null si no hay valor numérico suficiente.",
    "relevant_fragments": "\"una órbita con excentricidad 0,742\".",
    "final_value": "Como el fragmento relevante da la excentricidad decimal, el valor debe ser 0.742."
  },
  "orbital_period_days": {
    "field_asks": "tiempo para completar una órbita en días terrestres, o null si no hay dato suficiente.",
    "relevant_fragments": "\"periodo orbital de 2765 días\".",
    "final_value": "Como el fragmento relevante da el periodo orbital en días, el valor debe ser 2765."
  },
  "semi_major_axis_au": {
    "field_asks": "semieje mayor o distancia media al Sol en unidades astronómicas, o null si no hay dato suficiente.",
    "relevant_fragments": "\"semieje mayor de 3,86 UA\".",
    "final_value": "Como el fragmento relevante da el semieje mayor en UA, el valor debe ser 3.86."
  },
  "discovery_date": {
    "field_asks": "fecha de descubrimiento en formato YYYY-MM-DD, o null si no hay fecha suficiente.",
    "relevant_fragments": "\"fue identificado el 14 de septiembre de 2012\".",
    "final_value": "Como el fragmento relevante da una fecha completa de identificación, debe normalizarse a \"2012-09-14\"."
  },
  "discoverer": {
    "field_asks": "persona u observatorio que descubrió el objeto, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"por la astrónoma Laura Rivera Soto desde el Observatorio de Calar Alto\".",
    "final_value": "Como el fragmento relevante identifica a Laura Rivera Soto como descubridora, el valor debe ser \"Laura Rivera Soto\"."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son entradas astronómicas en Markdown con encabezado `# <cuerpo>`, descripción de clasificación, observación e historia, y parámetros orbitales o físicos dispersos. Suelen contener números cercanos que no deben confundirse, como periodo de rotación frente a periodo orbital, temperatura o elongación frente a excentricidad, y años de misión frente a fecha de descubrimiento. Los nuevos ejemplos mantienen textos compactos de menos de 1600 caracteres y citas que soportan valores numéricos o `null` sin recurrir a conocimiento externo.
