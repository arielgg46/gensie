# stem_astronomy_detailed

Los tasks `stem_astronomy_detailed` son extracciones L5 de propiedades físicas y orbitales de cuerpos celestes: el modelo debe identificar nombre oficial y tipo, normalizar magnitudes numéricas en kg, km, días y UA cuando el texto las proporciona, y devolver `null` ante valores aproximados insuficientes, frases comparativas o datos históricos que no corresponden al campo pedido.

## Ejemplos revisados

- `data/dev_rev/stem_astronomy_detailed_001.json`
- `data/dev_rev/stem_astronomy_detailed_002.json`
- `data/dev/stem_astronomy_detailed_004.json`
- `data/dev/stem_astronomy_detailed_008.json`
- `data/dev/stem_astronomy_detailed_009.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `official_name` | Requerido, `string`, no nullable. Dualidad entre nombre directo del encabezado (`Marte`) y designación científica principal en el cuerpo (`(134340) Pluto`). |
| `body_type` | Enum requerido. Debe mapear a `ASTEROIDE`, `COMETA`, `PLANETA`, `LUNA`, `PLANETA ENANO`, `OBJETO INTERESTELAR` u `OTRO`. Aquí conviene alternar `PLANETA` y `PLANETA ENANO` para no fijar el ejemplo a planetas clásicos. |
| `mass_kg` | `number` vs `null`. Revisando los `input_text` de `data/dev` y `data/dev_rev`, no vi una masa del cuerpo expresada en kg: aparecen masas relativas (`diecisiete veces la de la Tierra`, `un tercio de la masa...`) y un caso de `380 kg` de rocas lunares, que no es la masa de la Luna. El schema sí permite número en kg, incluida notación científica; para cubrir la dualidad se usa un positivo explícito en kg en un ejemplo y una masa solo comparativa o contextual en el otro. |
| `diameter_km` | `number` vs `null`. Dualidad entre diámetro medio explícito en km y comparaciones de tamaño sin cifra normalizable. |
| `eccentricity` | `number` vs `null`. Revisando los `input_text`, Venus menciona `excentricidad de menos del 1 %` y Eris habla de objetos de `alta excentricidad`, pero no aparece una excentricidad decimal exacta directamente extraíble. Para cubrir dualidad se usa un valor decimal explícito frente a una órbita descrita como excéntrica sin número. |
| `orbital_period_days` | `number` vs `null`. Dualidad entre duración de la traslación/revolución alrededor del primario expresada en días terrestres y otros datos orbitales que no son periodo, como distancia media en UA. |
| `semi_major_axis_au` | `number` vs `null`. Dualidad entre semieje mayor o distancia orbital media explícita en UA y una descripción orbital sin UA. |
| `discovery_date` | `string` `YYYY-MM-DD` vs `null`. Para cuerpos conocidos desde la antigüedad o sin fecha explícita queda `null`; para objetos con hallazgo documentado se normaliza desde fecha completa. |
| `discoverer` | `string` vs `null`. Dualidad entre descubridor nombrado y objetos sin descubridor individual en el texto. No basta con mencionar astrónomos que estudiaron órbitas o misiones que exploraron el cuerpo. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `official_name` | Nombre directo del encabezado: `Marte`. | Designación científica del cuerpo: `(134340) Pluto`, aunque el encabezado sea popular. |
| `body_type` | `PLANETA`. | `PLANETA ENANO`. |
| `mass_kg` | Valor no null en kg: `6.4171e23`. | `null`, con comparaciones generales pero sin kg. |
| `diameter_km` | Valor no null: `6779`. | `null`, sin diámetro medio en km. |
| `eccentricity` | Valor decimal explícito: `0.0934`. | `null`, órbita descrita como excéntrica sin cifra. |
| `orbital_period_days` | Valor no null: `686.98`, a partir de la duración del año marciano. | `null`, sin periodo de revolución en días. |
| `semi_major_axis_au` | `null`, sin semieje ni distancia media en UA. | Valor no null: `39.5`, como distancia media al Sol en UA. |
| `discovery_date` | `null`, observado desde la antigüedad sin fecha de descubrimiento. | `1930-02-18`, fecha completa de descubrimiento. |
| `discoverer` | `null`, sin descubridor individual. | `Clyde William Tombaugh`, nombrado como descubridor. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Marte

Marte es el cuarto planeta en orden de distancia al Sol y el segundo más pequeño del sistema solar, después de Mercurio. Recibió su nombre en homenaje al dios romano de la guerra, y también es conocido como el planeta rojo por el óxido de hierro predominante en su superficie.

Las fichas astronómicas modernas le asignan una masa de 6,4171 × 10^23 kg y un diámetro medio de 6779 km. Su órbita alrededor del Sol tiene una excentricidad de 0,0934. El año marciano dura 686,98 días terrestres, mientras que el periodo de rotación del planeta ronda las 24,6 horas y se cita aparte al hablar de sus ciclos diarios.

Marte se observa fácilmente a simple vista desde la Tierra y aparece en tradiciones astronómicas antiguas. Sus casquetes polares, las tormentas de polvo y el Monte Olimpo han sido temas recurrentes en la exploración mediante sondas. La presencia de Fobos y Deimos se menciona a menudo como posible captura de cuerpos menores, aunque esa hipótesis pertenece a la historia de sus satélites.

Tycho Brahe midió con gran precisión su movimiento aparente, y los datos de esos lazos permitieron a Kepler formular sus leyes del movimiento planetario. Las observaciones telescópicas terrestres han estado limitadas por la atmósfera, por lo que varias misiones modernas se centraron en cartografiar la superficie y estudiar su habitabilidad pasada.
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
  "semi_major_axis_au": null,
  "discovery_date": null,
  "discoverer": null
}
```

`reasoning`:

```json
{
  "official_name": {
    "field_asks": "el nombre o designación científica principal del cuerpo celeste.",
    "relevant_fragments": "\"# Marte\" y \"Marte es el cuarto planeta\".",
    "final_value": "Como los fragmentos relevantes presentan Marte como el cuerpo descrito, el nombre oficial debe ser \"Marte\"."
  },
  "body_type": {
    "field_asks": "la clasificación del cuerpo celeste, mapeada a uno de estos valores: ASTEROIDE, COMETA, PLANETA, LUNA, PLANETA ENANO, OBJETO INTERESTELAR u OTRO.",
    "relevant_fragments": "\"Marte es el cuarto planeta en orden de distancia al Sol\".",
    "final_value": "Como el fragmento relevante clasifica Marte como planeta, el valor del enum debe ser \"PLANETA\"."
  },
  "mass_kg": {
    "field_asks": "masa en kilogramos, o null si el texto no da masa en kg o una cantidad directamente normalizable a kg.",
    "relevant_fragments": "\"una masa de 6,4171 × 10^23 kg\".",
    "final_value": "Como el fragmento relevante da una masa explícita en kg, el valor debe normalizarse como 6.4171e23."
  },
  "diameter_km": {
    "field_asks": "diámetro medio en kilómetros, o null si no hay dato numérico suficiente.",
    "relevant_fragments": "\"un diámetro medio de 6779 km\".",
    "final_value": "Como el fragmento relevante da diámetro medio en km, el valor debe ser 6779."
  },
  "eccentricity": {
    "field_asks": "excentricidad orbital, o null si no hay valor numérico suficiente.",
    "relevant_fragments": "\"Su órbita alrededor del Sol tiene una excentricidad de 0,0934\".",
    "final_value": "Como el fragmento relevante da excentricidad decimal explícita, el valor debe ser 0.0934."
  },
  "orbital_period_days": {
    "field_asks": "tiempo que tarda el cuerpo en completar una órbita alrededor de su primario, expresado en días terrestres; no debe confundirse con periodo de rotación, duración del día, fecha de misión ni ciclo estacional.",
    "relevant_fragments": "\"El año marciano dura 686,98 días terrestres\" y \"el periodo de rotación del planeta ronda las 24,6 horas\".",
    "final_value": "Como el primer fragmento relevante da la duración de la traslación alrededor del Sol y el segundo separa la rotación diaria, el periodo orbital debe ser 686.98."
  },
  "semi_major_axis_au": {
    "field_asks": "semieje mayor o distancia orbital media al Sol en unidades astronómicas, o null si no hay dato en UA suficiente.",
    "relevant_fragments": "\"Marte es el cuarto planeta en orden de distancia al Sol\" y \"Su órbita alrededor del Sol tiene una excentricidad de 0,0934\".",
    "final_value": "Como los fragmentos relevantes hablan de orden orbital y excentricidad, pero no dan semieje mayor ni distancia media en UA, el valor debe ser null."
  },
  "discovery_date": {
    "field_asks": "fecha de descubrimiento en formato YYYY-MM-DD, o null si no hay fecha completa de descubrimiento.",
    "relevant_fragments": "\"Marte se observa fácilmente a simple vista desde la Tierra y aparece en tradiciones astronómicas antiguas\".",
    "final_value": "Como el fragmento relevante sitúa a Marte en observación antigua y no da fecha completa de descubrimiento, el valor debe ser null."
  },
  "discoverer": {
    "field_asks": "persona u observatorio que descubrió el objeto, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"Tycho Brahe midió con gran precisión su movimiento aparente\" y \"permitieron a Kepler formular sus leyes\".",
    "final_value": "Como los fragmentos relevantes mencionan astrónomos que estudiaron el movimiento de Marte, pero no los presentan como descubridores del planeta, el valor debe ser null."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# Plutón (planeta enano)

Plutón, designado (134340) Pluto, es un planeta enano del sistema solar ubicado en el cinturón de Kuiper, situado a continuación de la órbita de Neptuno. Fue descubierto por Clyde William Tombaugh el 18 de febrero de 1930 y recibió su nombre del dios mitológico romano Plutón.

Durante décadas fue considerado el noveno planeta, hasta que la Unión Astronómica Internacional redefinió la categoría de planeta en 2006. Desde entonces se clasifica como planeta enano y plutoide. Su trayectoria es inclinada y excéntrica, y en la ficha orbital resumida se conserva una distancia media al Sol de 39.5 ua.

La descripción histórica comenta su recatalogación, la existencia de Caronte y otras lunas menores, y comparaciones generales de tamaño con la Luna y con otros objetos transneptunianos. También recuerda que las primeras imágenes eran puntos débiles en placas fotográficas, por lo que su naturaleza se discutió durante años antes de quedar integrada en el estudio del cinturón de Kuiper.

Las campañas fotográficas de Lowell sirvieron de base para el hallazgo de Tombaugh. Más tarde, las observaciones de ocultaciones estelares y la visita de una sonda permitieron estudiar su atmósfera tenue y su geología helada, pero la reseña se centra sobre todo en su descubrimiento y reclasificación.
```

`instruction`:

```text
Extrae las propiedades físicas y orbitales del cuerpo celeste descrito en el texto, incluyendo su nombre oficial, clasificación, distancia orbital media y datos de descubrimiento.
```

`output`:

```json
{
  "official_name": "(134340) Pluto",
  "body_type": "PLANETA ENANO",
  "mass_kg": null,
  "diameter_km": null,
  "eccentricity": null,
  "orbital_period_days": null,
  "semi_major_axis_au": 39.5,
  "discovery_date": "1930-02-18",
  "discoverer": "Clyde William Tombaugh"
}
```

`reasoning`:

```json
{
  "official_name": {
    "field_asks": "el nombre o designación científica principal del cuerpo celeste.",
    "relevant_fragments": "\"Plutón, designado (134340) Pluto\".",
    "final_value": "Como el fragmento relevante da la designación científica junto al nombre común, el nombre oficial debe ser \"(134340) Pluto\"."
  },
  "body_type": {
    "field_asks": "la clasificación del cuerpo celeste, mapeada a uno de estos valores: ASTEROIDE, COMETA, PLANETA, LUNA, PLANETA ENANO, OBJETO INTERESTELAR u OTRO.",
    "relevant_fragments": "\"es un planeta enano\" y \"se clasifica como planeta enano y plutoide\".",
    "final_value": "Como los fragmentos relevantes clasifican Plutón como planeta enano, el valor del enum debe ser \"PLANETA ENANO\"."
  },
  "mass_kg": {
    "field_asks": "masa en kilogramos, o null si el texto no da masa en kg o una cantidad directamente normalizable a kg.",
    "relevant_fragments": "\"comparaciones generales de tamaño con la Luna y con otros objetos transneptunianos\".",
    "final_value": "Como el fragmento relevante solo alude a comparaciones generales y no da masa en kilogramos, el valor debe ser null."
  },
  "diameter_km": {
    "field_asks": "diámetro medio en kilómetros, o null si no hay dato numérico suficiente.",
    "relevant_fragments": "\"comparaciones generales de tamaño con la Luna y con otros objetos transneptunianos\".",
    "final_value": "Como el fragmento relevante no proporciona diámetro medio en km, el valor debe ser null."
  },
  "eccentricity": {
    "field_asks": "excentricidad orbital, o null si no hay valor numérico suficiente.",
    "relevant_fragments": "\"Su trayectoria es inclinada y excéntrica\".",
    "final_value": "Como el fragmento relevante describe la órbita como excéntrica pero no da un valor numérico, el valor debe ser null."
  },
  "orbital_period_days": {
    "field_asks": "tiempo que tarda el cuerpo en completar una órbita alrededor de su primario, expresado en días terrestres; no debe confundirse con periodo de rotación, duración del día, fecha de misión ni ciclo estacional.",
    "relevant_fragments": "\"Su trayectoria es inclinada y excéntrica\" y \"se conserva una distancia media al Sol de 39.5 ua\".",
    "final_value": "Como los fragmentos relevantes describen rasgos orbitales y distancia media, pero no duración de una revolución en días terrestres, el valor debe ser null."
  },
  "semi_major_axis_au": {
    "field_asks": "semieje mayor o distancia orbital media al Sol en unidades astronómicas, o null si no hay dato en UA suficiente.",
    "relevant_fragments": "\"se conserva una distancia media al Sol de 39.5 ua\".",
    "final_value": "Como el fragmento relevante da distancia orbital media en unidades astronómicas, el valor debe ser 39.5."
  },
  "discovery_date": {
    "field_asks": "fecha de descubrimiento en formato YYYY-MM-DD, o null si no hay fecha completa de descubrimiento.",
    "relevant_fragments": "\"Fue descubierto por Clyde William Tombaugh el 18 de febrero de 1930\".",
    "final_value": "Como el fragmento relevante da una fecha completa de descubrimiento, debe normalizarse a \"1930-02-18\"."
  },
  "discoverer": {
    "field_asks": "persona u observatorio que descubrió el objeto, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"Fue descubierto por Clyde William Tombaugh\" y \"base para el hallazgo de Tombaugh\".",
    "final_value": "Como los fragmentos relevantes identifican a Clyde William Tombaugh como descubridor, el valor debe ser \"Clyde William Tombaugh\"."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son entradas astronómicas en Markdown con encabezado `# <cuerpo>` y párrafos enciclopédicos continuos, sin línea `Source:` y casi siempre sin secciones internas. Suelen mezclar clasificación, observación histórica, misiones, rasgos físicos y parámetros orbitales dispersos. Los ejemplos reales contienen cantidades cercanas que no deben confundirse: periodo de rotación frente a periodo de traslación, masa relativa frente a masa en kg, ranking o comparación de tamaño frente a diámetro en km, distancia media en UA frente a periodo orbital, y fecha de descubrimiento frente a años de misión o estudio. En este prefijo, si queremos cubrir todos los campos con dos FSP, hay que aceptar al menos un positivo sintético para `mass_kg` y `eccentricity`, porque los `input_text` revisados no traen una masa del cuerpo en kg ni una excentricidad decimal exacta.
