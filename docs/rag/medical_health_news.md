# medical_health_news

Los tasks `medical_health_news` usan el schema general de noticias L4 para notas de salud pública, investigaciones médicas, alertas sanitarias o programas de atención: el modelo debe copiar el titular, resumir el hecho principal, clasificar la categoría, extraer ubicación y fecha si están grounded, listar personas y organizaciones nombradas, y distinguir muertes, hospitalizaciones o afectados reales de cifras de muestras, dosis, ventas, contratos o participantes de estudio.

## Ejemplos revisados

- `data/dev_rev/medical_health_news_001.json`
- `data/dev/medical_health_news_002.json`
- `data/dev/medical_health_news_003.json`
- `data/dev/medical_health_news_009.json`
- `data/dev/medical_health_news_010.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `headline` | Requerido, `string`, no nullable. Sale verbatim del encabezado; conviene variar alerta sanitaria frente a divulgación o investigación médica. |
| `summary` | Requerido, `string`, no nullable. Debe condensar hallazgo, respuesta institucional y cifras relevantes en 1-3 frases. |
| `category` | Enum requerido. Debe mapear a uno de estos valores: `JUDICIAL`, `DISASTER`, `HEALTH`, `ENVIRONMENT`, `POLITICS`, `ECONOMY`, `SCIENCE`, `CULTURE`, `SPORTS` u `OTHER`. En este prefijo suele ser `HEALTH`, aunque algunos estudios podrían rozar `SCIENCE`; conviene mantener el foco sanitario. |
| `location` | `string` vs `null`. Dualidad entre brote o alerta localizada y estudio sin lugar del evento noticioso. |
| `date` | `string` vs `null`. Dualidad entre fecha absoluta de alerta/retiro y referencias relativas como `este martes` o periodos de estudio. |
| `key_people` | `[]` vs lista poblada. Incluye médicos, investigadores o autoridades nombradas; no incluye pacientes anónimos ni cargos sin nombre. |
| `key_organizations` | `[]` vs lista poblada. Incluye ministerios, hospitales, revistas, farmacéuticas o programas sanitarios nombrados; no incluye grupos genéricos. |
| `casualties` | `integer` vs `null`. Debe ser muertes humanas explícitas; no ventas, dosis, años, pacientes estudiados o casos sin desenlace fatal. |
| `injured` | `integer` vs `null`. Puede usarse para personas hospitalizadas, intoxicadas o lesionadas cuando el texto las cuantifica como afectadas clínicamente; no para participantes de un estudio. |
| `affected_count` | `integer` vs `null`. Debe poblarse con personas afectadas, desplazadas o perjudicadas; no con frascos, muestras, hospitales, municipios o participantes analizados si no se presentan como afectados. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `headline` | Titular principal de la noticia, normalmente el encabezado `#`. Cópialo de forma literal, conservando nombres de enfermedades, organismos y cifras si aparecen en el titular. |
| `summary` | Resumen breve en 1-3 oraciones con alerta, hallazgo, medida sanitaria, organismos y cifras humanas relevantes. No conviertas detalles secundarios como ventas, dosis, vuelos o contratos en el centro si no son el hecho principal. |
| `category` | Categoría temática del enum completo: `JUDICIAL`, `DISASTER`, `HEALTH`, `ENVIRONMENT`, `POLITICS`, `ECONOMY`, `SCIENCE`, `CULTURE`, `SPORTS` u `OTHER`. Usa `HEALTH` para alertas sanitarias, brotes, estudios clínicos, programas médicos, medicamentos, vacunas o decisiones de salud pública, aunque haya elementos políticos o económicos. |
| `location` | Lugar principal de la alerta, estudio o evento sanitario. Extrae país, ciudad o región cuando el texto lo sitúe; devuelve `null` si solo hay muestras multicéntricas, instituciones genéricas o contexto internacional sin ubicación del evento. |
| `date` | Fecha explícita de la alerta, medida sanitaria, publicación o evento. Devuelve `null` para `este martes`, `ayer`, periodos de seguimiento, años de programas o aniversarios si no hay fecha absoluta suficiente. |
| `key_people` | Personas individuales nombradas: médicos, investigadores, ministros, directores o autoridades sanitarias. No incluyas pacientes anónimos, grupos de trabajadores, cargos sin nombre ni autores colectivos. |
| `key_organizations` | Organizaciones sanitarias, ministerios, hospitales, revistas, farmacéuticas, programas o medios nombrados. No incluyas grupos genéricos como “el equipo”, “centros de salud” o “autoridades” si no tienen nombre propio. |
| `casualties` | Número de muertes humanas mencionadas por el evento sanitario. No uses ventas, dosis, contratos, muestras, participantes, infectados o muertes históricas si no son el balance relevante de la noticia. |
| `injured` | Número de personas heridas, intoxicadas, hospitalizadas o clínicamente afectadas de forma aguda cuando el texto lo cuantifica. No uses participantes de estudio, personas vacunadas, médicos desplazados o infectados si el campo se reserva para hospitalizados/lesionados y no hay equivalencia clara. |
| `affected_count` | Número de personas afectadas, infectadas, damnificadas, desplazadas o perjudicadas si el texto las presenta como tal. No uses frascos, dosis, ventas, municipios, vuelos, hospitales, muestras o participantes analizados si no se describen como afectados. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `headline` | Alerta sanitaria por suplemento contaminado. | Estudio médico sobre turnos nocturnos y glucosa. |
| `summary` | Tres oraciones con retiro, fallecidos, hospitalizados y respuesta. | Dos o tres oraciones con hallazgo, muestra y recomendación clínica. |
| `category` | `HEALTH`. | `HEALTH`. |
| `location` | Valor no null: Villa Mar. | `null`: no hay ciudad o país del evento, solo muestra multicéntrica genérica. |
| `date` | Valor no null: 4 de julio de 2026. | `null`: referencia relativa `este martes` y periodo de seguimiento. |
| `key_people` | `[]`: autoridades por cargo, sin nombres individuales. | Lista poblada con investigadora nombrada. |
| `key_organizations` | Lista poblada con secretaría, hospital y laboratorio. | `[]`: equipo, congreso y centros descritos de forma genérica. |
| `casualties` | `4`. | `null`. |
| `injured` | `23`. | `null`. |
| `affected_count` | `null`: se cuantifican frascos retirados, no personas afectadas totales. | `null`: los 860 son participantes del estudio, no afectados. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Retiran un suplemento tras intoxicaciones vinculadas a daño hepático en Villa Mar

La Secretaría de Salud de Villa Mar ordenó el 4 de julio de 2026 retirar el suplemento EnerPlus Forte después de que varios pacientes llegaran al Hospital General del Puerto con insuficiencia hepática aguda. La investigación preliminar relaciona los cuadros con un lote producido por Laboratorios NovaFit y vendido en gimnasios y tiendas naturistas de la ciudad.

El balance sanitario confirmó 4 fallecidos y 23 personas hospitalizadas con síntomas compatibles, entre ellos ictericia intensa, dolor abdominal y alteración de enzimas hepáticas. La autoridad local inmovilizó 9 500 frascos, abrió una línea telefónica para reportes y pidió conservar los envases comprados durante las últimas seis semanas para rastrear el lote contaminado.
```

`instruction`:

```text
Extrae la información estructurada de este artículo de noticias sobre salud pública, siguiendo el esquema proporcionado. Devuelve null para los campos que no se mencionan en el texto.
```

`output`:

```json
{
  "headline": "Retiran un suplemento tras intoxicaciones vinculadas a daño hepático en Villa Mar",
  "summary": "La Secretaría de Salud de Villa Mar ordenó el 4 de julio de 2026 retirar el suplemento EnerPlus Forte tras casos de insuficiencia hepática aguda atendidos en el Hospital General del Puerto. La investigación preliminar vinculó los cuadros con un lote producido por Laboratorios NovaFit y vendido en gimnasios y tiendas naturistas de la ciudad. El balance sanitario confirmó 4 fallecidos y 23 personas hospitalizadas, mientras la autoridad inmovilizó 9 500 frascos y abrió una línea de reportes.",
  "category": "HEALTH",
  "location": "Villa Mar",
  "date": "4 de julio de 2026",
  "key_people": [],
  "key_organizations": [
    "Secretaría de Salud de Villa Mar",
    "Hospital General del Puerto",
    "Laboratorios NovaFit"
  ],
  "casualties": 4,
  "injured": 23,
  "affected_count": null
}
```

`reasoning`:

```json
{
  "headline": {
    "field_asks": "el titular principal del artículo de noticias.",
    "relevant_fragments": "\"# Retiran un suplemento tras intoxicaciones vinculadas a daño hepático en Villa Mar\".",
    "final_value": "Como el fragmento relevante es el encabezado principal, el titular debe ser \"Retiran un suplemento tras intoxicaciones vinculadas a daño hepático en Villa Mar\"."
  },
  "summary": {
    "field_asks": "un resumen breve de los hechos principales reportados, en 1-3 oraciones.",
    "relevant_fragments": "\"La Secretaría de Salud de Villa Mar ordenó el 4 de julio de 2026 retirar el suplemento EnerPlus Forte después de que varios pacientes llegaran al Hospital General del Puerto con insuficiencia hepática aguda\", \"La investigación preliminar relaciona los cuadros con un lote producido por Laboratorios NovaFit y vendido en gimnasios y tiendas naturistas de la ciudad\" y \"El balance sanitario confirmó 4 fallecidos y 23 personas hospitalizadas con síntomas compatibles\".",
    "final_value": "Como los fragmentos relevantes cubren retiro, causa investigada, organizaciones y balance sanitario, el resumen debe condensar esos hechos."
  },
  "category": {
    "field_asks": "la categoría temática de la noticia, mapeada a uno de estos valores: JUDICIAL, DISASTER, HEALTH, ENVIRONMENT, POLITICS, ECONOMY, SCIENCE, CULTURE, SPORTS u OTHER.",
    "relevant_fragments": "\"intoxicaciones vinculadas a daño hepático\", \"insuficiencia hepática aguda\" y \"balance sanitario\".",
    "final_value": "Como los fragmentos relevantes tratan una alerta de salud pública y cuadros clínicos, el valor del enum debe ser \"HEALTH\"."
  },
  "location": {
    "field_asks": "la ubicación geográfica donde ocurrió el evento, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"La Secretaría de Salud de Villa Mar\" y \"tiendas naturistas de la ciudad\".",
    "final_value": "Como los fragmentos relevantes sitúan la alerta en Villa Mar, el valor debe ser \"Villa Mar\"."
  },
  "date": {
    "field_asks": "la fecha mencionada en el artículo, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"ordenó el 4 de julio de 2026 retirar el suplemento\".",
    "final_value": "Como el fragmento relevante da una fecha completa para la orden de retiro, el valor debe ser \"4 de julio de 2026\"."
  },
  "key_people": {
    "field_asks": "nombres de personas individuales clave mencionadas en el artículo.",
    "relevant_fragments": "\"La Secretaría de Salud de Villa Mar\", \"La autoridad local\" y \"varios pacientes\".",
    "final_value": "Los fragmentos relevantes mencionan instituciones, autoridad genérica y pacientes sin nombres individuales; la lista debe ser vacía."
  },
  "key_organizations": {
    "field_asks": "nombres de organizaciones, empresas, instituciones o gobiernos mencionados.",
    "relevant_fragments": "\"Secretaría de Salud de Villa Mar\", \"Hospital General del Puerto\" y \"Laboratorios NovaFit\".",
    "final_value": "Como los fragmentos relevantes nombran instituciones sanitarias y un laboratorio, la lista debe incluir esas tres organizaciones."
  },
  "casualties": {
    "field_asks": "número de muertes mencionadas, o null si no se menciona ninguna cifra de muertes humanas.",
    "relevant_fragments": "\"confirmó 4 fallecidos\".",
    "final_value": "Como el fragmento relevante cuantifica fallecidos humanos, el valor debe ser 4."
  },
  "injured": {
    "field_asks": "número de personas heridas, lesionadas u hospitalizadas por el evento, o null si no se menciona ninguna cifra clínica equivalente.",
    "relevant_fragments": "\"23 personas hospitalizadas con síntomas compatibles\".",
    "final_value": "Como el fragmento relevante cuantifica personas hospitalizadas por la intoxicación, el valor debe ser 23."
  },
  "affected_count": {
    "field_asks": "número de personas afectadas, perjudicadas o desplazadas, o null si no aplica o no hay cifra suficiente.",
    "relevant_fragments": "\"La autoridad local inmovilizó 9 500 frascos\" y \"pidió conservar los envases comprados durante las últimas seis semanas para rastrear el lote contaminado\".",
    "final_value": "Los fragmentos relevantes cuantifican productos y envases, pero no una cifra total de personas afectadas; el valor debe ser null."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# Un estudio relaciona los turnos nocturnos con peor control de glucosa

La endocrinóloga Mara Céspedes presentó este martes un análisis sobre 860 trabajadores con seguimiento metabólico durante dieciocho meses. El equipo comparó horarios de sueño, comidas fuera de turno y mediciones continuas de glucosa en personal de hospitales y fábricas, con especial atención a quienes rotaban entre madrugada y mañana.

Según la revisión, los turnos nocturnos frecuentes se asociaron con picos de glucosa más prolongados y mayor dificultad para ajustar la medicación en personas con diabetes tipo 2. Céspedes recomendó que las consultas laborales incluyan diarios de sueño y horarios de comida antes de cambiar tratamientos. El informe se discutió en una mesa clínica de medicina del trabajo y será enviado a una revista especializada.
```

`instruction`:

```text
Extrae la información estructurada de este artículo de noticias de salud siguiendo el esquema proporcionado.
```

`output`:

```json
{
  "headline": "Un estudio relaciona los turnos nocturnos con peor control de glucosa",
  "summary": "La endocrinóloga Mara Céspedes presentó un análisis de 860 trabajadores con seguimiento metabólico durante dieciocho meses. El estudio asoció los turnos nocturnos frecuentes con picos de glucosa más prolongados y mayor dificultad para ajustar la medicación en personas con diabetes tipo 2. Céspedes recomendó incorporar diarios de sueño y horarios de comida en las consultas laborales antes de cambiar tratamientos.",
  "category": "HEALTH",
  "location": null,
  "date": null,
  "key_people": [
    "Mara Céspedes"
  ],
  "key_organizations": [],
  "casualties": null,
  "injured": null,
  "affected_count": null
}
```

`reasoning`:

```json
{
  "headline": {
    "field_asks": "el titular principal del artículo de noticias.",
    "relevant_fragments": "\"# Un estudio relaciona los turnos nocturnos con peor control de glucosa\".",
    "final_value": "Como el fragmento relevante es el encabezado principal, el titular debe ser \"Un estudio relaciona los turnos nocturnos con peor control de glucosa\"."
  },
  "summary": {
    "field_asks": "un resumen breve de los hechos principales reportados, en 1-3 oraciones.",
    "relevant_fragments": "\"La endocrinóloga Mara Céspedes presentó este martes un análisis sobre 860 trabajadores con seguimiento metabólico durante dieciocho meses\", \"Según la revisión, los turnos nocturnos frecuentes se asociaron con picos de glucosa más prolongados y mayor dificultad para ajustar la medicación en personas con diabetes tipo 2\" y \"Céspedes recomendó que las consultas laborales incluyan diarios de sueño y horarios de comida antes de cambiar tratamientos\".",
    "final_value": "Como los fragmentos relevantes cubren autoría, muestra, hallazgo y recomendación, el resumen debe sintetizar esos puntos."
  },
  "category": {
    "field_asks": "la categoría temática de la noticia, mapeada a uno de estos valores: JUDICIAL, DISASTER, HEALTH, ENVIRONMENT, POLITICS, ECONOMY, SCIENCE, CULTURE, SPORTS u OTHER.",
    "relevant_fragments": "\"seguimiento metabólico\", \"mediciones continuas de glucosa\" y \"personas con diabetes tipo 2\".",
    "final_value": "Como los fragmentos relevantes tratan salud metabólica y diabetes, el valor del enum debe ser \"HEALTH\"."
  },
  "location": {
    "field_asks": "la ubicación geográfica donde ocurrió el evento, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"personal de hospitales y fábricas\" y \"una mesa clínica de medicina del trabajo\".",
    "final_value": "Los fragmentos relevantes describen tipos de centros y un espacio clínico, pero no nombran una ciudad, país o región del evento; el valor debe ser null."
  },
  "date": {
    "field_asks": "la fecha mencionada en el artículo, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"presentó este martes\" y \"durante dieciocho meses\".",
    "final_value": "Los fragmentos relevantes dan una referencia relativa y un periodo de seguimiento, pero no una fecha absoluta; el valor debe ser null."
  },
  "key_people": {
    "field_asks": "nombres de personas individuales clave mencionadas en el artículo.",
    "relevant_fragments": "\"La endocrinóloga Mara Céspedes\".",
    "final_value": "Como el fragmento relevante nombra a una persona individual, la lista debe incluir \"Mara Céspedes\"."
  },
  "key_organizations": {
    "field_asks": "nombres de organizaciones, empresas, instituciones o gobiernos mencionados.",
    "relevant_fragments": "\"El equipo\", \"personal de hospitales y fábricas\", \"una mesa clínica de medicina del trabajo\" y \"una revista especializada\".",
    "final_value": "Los fragmentos relevantes describen grupos o espacios genéricos, pero no organizaciones con nombre propio; la lista debe ser vacía."
  },
  "casualties": {
    "field_asks": "número de muertes mencionadas, o null si no se menciona ninguna cifra de muertes humanas.",
    "relevant_fragments": "\"un análisis sobre 860 trabajadores con seguimiento metabólico durante dieciocho meses\" y \"personas con diabetes tipo 2\".",
    "final_value": "Los fragmentos relevantes describen una muestra de estudio y población clínica, pero no muertes humanas; el valor debe ser null."
  },
  "injured": {
    "field_asks": "número de personas heridas, lesionadas u hospitalizadas por el evento, o null si no se menciona ninguna cifra clínica equivalente.",
    "relevant_fragments": "\"picos de glucosa más prolongados\" y \"mayor dificultad para ajustar la medicación\".",
    "final_value": "Los fragmentos relevantes describen resultados metabólicos, pero no personas heridas u hospitalizadas por un evento; el valor debe ser null."
  },
  "affected_count": {
    "field_asks": "número de personas afectadas, perjudicadas o desplazadas, o null si no aplica o no hay cifra suficiente.",
    "relevant_fragments": "\"un análisis sobre 860 trabajadores con seguimiento metabólico durante dieciocho meses\".",
    "final_value": "Los fragmentos relevantes cuantifican participantes analizados, pero no personas afectadas o desplazadas; el valor debe ser null."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son noticias de salud en Markdown: encabezado `# <titular>`, párrafos sobre informes, declaraciones médicas, organismos sanitarios, farmacéuticas, programas públicos o estudios, y cifras que pueden referirse a ventas, dosis, participantes, vuelos, municipios o pacientes. Para los nuevos ejemplos conviene mantener textos compactos de menos de 1600 caracteres, con contexto sanitario natural y suficientes números distractores para enseñar que solo las cifras humanas explícitamente afectadas, heridas, hospitalizadas o fallecidas deben poblar los campos correspondientes.
