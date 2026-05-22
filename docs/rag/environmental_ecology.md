# environmental_ecology

Los tasks `environmental_ecology` usan el schema general de noticias L4 para artículos de ecología, clima, conservación o eventos con componente ambiental: el modelo debe copiar el titular, resumir los hechos principales en 1-3 frases, clasificar la noticia en un enum amplio, extraer ubicación y fecha solo si aparecen o se pueden anclar al texto, listar personas y organizaciones mencionadas, y distinguir cifras de muertes, heridos y afectados sin convertir cualquier número ambiental o técnico en conteo humano.

## Ejemplos revisados

- `data/dev_rev/environmental_ecology_001.json`
- `data/dev_rev/environmental_ecology_002.json`
- `data/dev_rev/environmental_ecology_006.json`
- `data/dev/environmental_ecology_007.json`
- `data/dev/environmental_ecology_010.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `headline` | Requerido, `string`, no nullable. Suele salir verbatim del encabezado `# ...`; la dualidad útil es titular descriptivo directo vs titular con una persona o cifra llamativa que no debe contaminar otros campos. |
| `summary` | Requerido, `string`, no nullable. No es verbatim: debe condensar hechos principales en 1-3 frases. Dualidad entre resumen de evento concreto con cifras y resumen de declaración/advertencia pública con menos datos materiales. |
| `category` | Enum requerido. Debe mapear a uno de estos valores: `JUDICIAL`, `DISASTER`, `HEALTH`, `ENVIRONMENT`, `POLITICS`, `ECONOMY`, `SCIENCE`, `CULTURE`, `SPORTS` u `OTHER`. En el prefijo suele ser `ENVIRONMENT`, pero el ejemplo de Carrera Solar muestra que puede ser `SPORTS` o `SCIENCE` según el foco; conviene enseñar que el prefijo no obliga automáticamente al enum. |
| `location` | `string` vs `null`. Dualidad entre ubicación explícita con ciudad/región/país y artículo con declaración global o contexto institucional sin lugar claro del evento. Debe evitar mezclar ubicaciones secundarias que aparecen en párrafos laterales. |
| `date` | `string` vs `null`. Dualidad entre fecha explícita o rango mencionado en el artículo y referencias temporales vagas como `este jueves`, `recientemente`, `últimos días` o `década atrás` cuando no hay fecha absoluta suficiente. |
| `key_people` | `[]` vs lista poblada. En Carrera Solar queda vacío aunque haya equipos; en las notas con declaraciones aparecen nombres como `Megan Ferguson`, `Jay Chadwick` o `Al Gore`. Debe incluir personas nombradas, incluso si alguna aparece en un párrafo secundario, siempre que sea una persona individual. |
| `key_organizations` | `[]` vs lista poblada. Dualidad entre artículos con instituciones, equipos, medios o foros mencionados y artículos sin organizaciones claras. Debe distinguir organizaciones de lugares, especies, fenómenos o cargos. |
| `casualties` | `integer` vs `null`. Normalmente `null` en ecología; conviene un ejemplo con muertes humanas explícitas para enseñar que no se infiere desde animales muertos, daños ecológicos o riesgos. |
| `injured` | `integer` vs `null`. Dualidad entre heridos humanos explícitos y ausencia de lesionados. Debe ignorar animales enfermos, especies afectadas o formulaciones hipotéticas. |
| `affected_count` | `integer` vs `null`. Dualidad entre número de personas afectadas, desplazadas o evacuadas y números ecológicos no humanos, como animales, kilómetros, hectáreas o concentraciones, que no deberían poblar este campo salvo que el texto lo formule como personas afectadas. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `headline` | Titular principal del artículo, normalmente el encabezado `#`. Cópialo sin el marcador Markdown y no incorpores subtítulos, primeras frases ni nombres secundarios que aparezcan después. |
| `summary` | Resumen breve en 1-3 oraciones de los hechos principales. Debe sintetizar evento, causa, actores y consecuencias cuando estén en el texto, sin copiar todo ni inventar contexto ambiental no mencionado. |
| `category` | Categoría temática del enum: `JUDICIAL`, `DISASTER`, `HEALTH`, `ENVIRONMENT`, `POLITICS`, `ECONOMY`, `SCIENCE`, `CULTURE`, `SPORTS` u `OTHER`. En este prefijo suele ser `ENVIRONMENT`, pero usa `SPORTS` para competencias, `SCIENCE` para estudios como foco central, y no fuerces ambiente si la noticia trata principalmente otro ámbito. |
| `location` | Lugar principal del hecho noticioso. Extrae ciudad, región o país cuando el evento esté ubicado; devuelve `null` ante declaraciones globales o listados de lugares secundarios sin un sitio central. |
| `date` | Fecha explícita del hecho o rango claramente fechado. Devuelve `null` para expresiones temporales poco concretas o relativas como `este jueves`, `en las próximas horas`, `recientemente`, `últimos días` o periodos históricos sin fecha absoluta suficiente. |
| `key_people` | Nombres propios de personas individuales mencionadas, aunque aparezcan en párrafos laterales. No incluyas cargos, equipos, comunidades, animales ni grupos anónimos. |
| `key_organizations` | Organizaciones, instituciones, empresas, gobiernos, medios o equipos con nombre propio. No confundas lugares, fenómenos naturales, especies o cargos genéricos. No incluyas instalaciones genéricas, equipos sin nombre propio, o países (a menos que se hable expresamente de su gobierno) como si fueran organizaciones. |
| `casualties` | Número de muertes humanas mencionadas. Devuelve `null` si solo hay animales muertos, daños ecológicos, riesgos o cifras de especies. |
| `injured` | Número de personas heridas o lesionadas. Devuelve `null` si el texto solo menciona enfermedades animales, exposición ambiental sin lesión cuantificada o medidas preventivas. |
| `affected_count` | Número de personas afectadas, evacuadas, atendidas o sin servicios. No uses cifras ambientales, animales, hectáreas, kilómetros, muestras, focos o toneladas, cuando no haya conversión segura a cantidad de personas. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `headline` | Titular de evento ambiental con cifra territorial o de personas afectadas. | Titular de informe científico con persona nombrada y cifras técnicas como distractores. |
| `summary` | Resumen de derrame, sequía o contaminación con medidas tomadas y población afectada. | Resumen de estudio ambiental con hallazgos, método y consecuencias humanas explícitas. |
| `category` | `ENVIRONMENT`, porque el foco es contaminación, conservación o daño ecológico. | `SCIENCE`, porque el foco es un estudio nuevo y sus hallazgos, aunque el tema sea ambiental. |
| `location` | Valor no null, por ejemplo una bahía, provincia o parque nacional explícito. | `null` si el artículo habla de un informe global o de una comparecencia sin ubicar un evento ambiental concreto. |
| `date` | Valor no null: fecha textual explícita o rango anclado en el texto. | `null`: solo expresiones relativas o referencias vagas. |
| `key_people` | `[]`: autoridades o brigadas nombradas por cargo, sin nombres individuales. | Lista poblada con científicos, portavoces o activistas nombrados. |
| `key_organizations` | Lista poblada con ministerio, municipalidad, universidad, ONG o empresa. | `[]` si el texto solo nombra cargos, grupos genéricos o lugares; alternativamente lista mínima si aparece una institución central. |
| `casualties` | `null`: daño ambiental y personas afectadas, pero sin muertes. | Entero no null: el texto menciona muertes humanas contabilizadas por el estudio. |
| `injured` | `null`: evacuados o afectados sin heridos. | Entero no null: el texto menciona personas heridas o atendidas por lesiones. |
| `affected_count` | Entero no null: personas evacuadas, afectadas o sin agua potable. | `null`: cifras de especies, muestras, hectáreas o temperatura, pero no personas afectadas. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Declaran alerta ambiental por derrame de relaves en la cuenca del río San Juan

El Ministerio del Ambiente declaró el 18 de abril de 2026 una alerta ambiental en la cuenca del río San Juan, en Pasco, Perú, después de que una poza de relaves de la mina Santa Isidora cediera durante las lluvias y tiñera de gris varios tramos del cauce.
Técnicos de la Autoridad Nacional del Agua midieron alta turbidez en doce kilómetros del río y recomendaron suspender el uso de las acequias hasta recibir nuevos análisis.

Brigadas de la Municipalidad Provincial de Pasco repartieron bidones y pastillas potabilizadoras a 1 200 vecinos de Huayllay, Rancas y San Miguel. La Cooperativa Río Claro, operadora de la mina, informó que instaló tres barreras de contención, mientras comuneros reclamaron que el olor metálico llegó a los canales de riego antes del amanecer.

La Universidad Nacional Daniel Alcides Carrión tomó muestras de agua, suelo y peces para comparar los resultados con registros de 2023. El reporte preliminar también menciona la mortandad de truchas en dos criaderos familiares y lodo rojizo cerca de una bocatoma.
```

`instruction`:

```text
Extrae la información estructurada de este artículo de noticias sobre un evento medioambiental, incluyendo el titular, resumen, categoría, ubicación, personas y organizaciones clave mencionadas, y cualquier cifra de víctimas o afectados si se menciona.
```

`output`:

```json
{
  "headline": "Declaran alerta ambiental por derrame de relaves en la cuenca del río San Juan",
  "summary": "El Ministerio del Ambiente declaró una alerta ambiental en la cuenca del río San Juan, en Pasco, Perú, tras el derrame de relaves de la mina Santa Isidora durante lluvias. Autoridades ambientales detectaron alta turbidez, suspendieron el uso de acequias y distribuyeron agua y pastillas potabilizadoras a 1 200 vecinos de tres comunidades. La Cooperativa Río Claro instaló barreras de contención y la Universidad Nacional Daniel Alcides Carrión tomó muestras para comparar el daño con registros previos.",
  "category": "ENVIRONMENT",
  "location": "cuenca del río San Juan, Pasco, Perú",
  "date": "18 de abril de 2026",
  "key_people": [],
  "key_organizations": [
    "Ministerio del Ambiente",
    "Autoridad Nacional del Agua",
    "Municipalidad Provincial de Pasco",
    "Cooperativa Río Claro",
    "Universidad Nacional Daniel Alcides Carrión"
  ],
  "casualties": null,
  "injured": null,
  "affected_count": 1200
}
```

`reasoning`:

```json
{
  "headline": {
    "field_asks": "el titular principal del artículo de noticias.",
    "relevant_fragments": "\"# Declaran alerta ambiental por derrame de relaves en la cuenca del río San Juan\".",
    "final_value": "Como el fragmento relevante es el encabezado principal, el titular debe ser \"Declaran alerta ambiental por derrame de relaves en la cuenca del río San Juan\"."
  },
  "summary": {
    "field_asks": "un resumen breve de los hechos principales reportados, en 1-3 oraciones.",
    "relevant_fragments": "\"El Ministerio del Ambiente declaró el 18 de abril de 2026 una alerta ambiental en la cuenca del río San Juan, en Pasco, Perú, después de que una poza de relaves de la mina Santa Isidora cediera durante las lluvias\", \"Brigadas de la Municipalidad Provincial de Pasco repartieron bidones y pastillas potabilizadoras a 1 200 vecinos de Huayllay, Rancas y San Miguel\" y \"La Universidad Nacional Daniel Alcides Carrión tomó muestras de agua, suelo y peces para comparar los resultados con registros de 2023\".",
    "final_value": "Como los fragmentos relevantes cubren el hecho principal, las medidas inmediatas, la población afectada y el monitoreo, el resumen debe condensarlos en tres oraciones."
  },
  "category": {
    "field_asks": "la categoría temática de la noticia, mapeada a uno de estos valores: JUDICIAL, DISASTER, HEALTH, ENVIRONMENT, POLITICS, ECONOMY, SCIENCE, CULTURE, SPORTS u OTHER.",
    "relevant_fragments": "\"alerta ambiental\", \"derrame de relaves\" y \"alta turbidez en doce kilómetros del río\".",
    "final_value": "Como los fragmentos relevantes tratan contaminación y respuesta ambiental, el valor del enum debe ser \"ENVIRONMENT\"."
  },
  "location": {
    "field_asks": "la ubicación geográfica donde ocurrió el evento, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"en la cuenca del río San Juan, en Pasco, Perú\".",
    "final_value": "Como el fragmento relevante ubica el evento en la cuenca del río San Juan, Pasco, Perú, el valor debe ser \"cuenca del río San Juan, Pasco, Perú\"."
  },
  "date": {
    "field_asks": "la fecha mencionada en el artículo, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"declaró el 18 de abril de 2026 una alerta ambiental\".",
    "final_value": "Como el fragmento relevante da una fecha completa para la declaración de alerta, el valor debe ser \"18 de abril de 2026\"."
  },
  "key_people": {
    "field_asks": "nombres de personas individuales clave mencionadas en el artículo.",
    "relevant_fragments": "\"Técnicos de la Autoridad Nacional del Agua\", \"Brigadas de la Municipalidad Provincial de Pasco\" y \"comuneros reclamaron\".",
    "final_value": "Los fragmentos relevantes mencionan cargos, brigadas y grupos, pero no nombres de personas individuales; la lista debe ser vacía."
  },
  "key_organizations": {
    "field_asks": "nombres de organizaciones, empresas, instituciones o gobiernos mencionados.",
    "relevant_fragments": "\"Ministerio del Ambiente\", \"Autoridad Nacional del Agua\", \"Municipalidad Provincial de Pasco\", \"Cooperativa Río Claro\" y \"Universidad Nacional Daniel Alcides Carrión\".",
    "final_value": "Como los fragmentos relevantes nombran instituciones y una empresa operadora, la lista debe incluir esas cinco organizaciones."
  },
  "casualties": {
    "field_asks": "número de muertes mencionadas, o null si no se menciona ninguna cifra de muertes humanas.",
    "relevant_fragments": "\"repartieron bidones y pastillas potabilizadoras a 1 200 vecinos\" y \"mortandad de truchas en dos criaderos familiares\".",
    "final_value": "Los fragmentos relevantes dan población atendida y muerte de peces, pero no muertes humanas; el valor debe ser null."
  },
  "injured": {
    "field_asks": "número de personas heridas mencionadas, o null si no se menciona ninguna cifra de heridos humanos.",
    "relevant_fragments": "\"repartieron bidones y pastillas potabilizadoras a 1 200 vecinos\".",
    "final_value": "El fragmento relevante describe asistencia, pero no personas heridas; el valor debe ser null."
  },
  "affected_count": {
    "field_asks": "número de personas afectadas o desplazadas, o null si no aplica o no hay cifra suficiente.",
    "relevant_fragments": "\"repartieron bidones y pastillas potabilizadoras a 1 200 vecinos de Huayllay, Rancas y San Miguel\".",
    "final_value": "Como el fragmento relevante cuantifica a los vecinos atendidos por el evento, el valor debe ser 1200."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# Científicos vinculan incendios de turberas con daños respiratorios duraderos

La investigadora Lara Méndez presentó este martes un estudio sobre incendios de turberas ante una red internacional de salud ambiental. El trabajo, coordinado con Rui Tanaka y difundido como preprint revisado por pares, comparó 3 400 muestras de humo y suelo tomadas en humedales boreales y tropicales durante los últimos cinco años.

El equipo revisó partes médicos, sensores de partículas finas y registros de viento asociados a 620 focos de combustión lenta. Según la base consolidada, esos episodios estuvieron vinculados con 18 muertes y 146 personas heridas por inhalación de humo denso, sobre todo en turnos de extinción y traslados de emergencia.

Un laboratorio universitario aportó modelos de dispersión para separar el humo de turberas del producido por incendios forestales de superficie. Los autores calculan que una hectárea de turba seca puede liberar hasta tres veces más carbono que un bosque joven, pero advierten que la cifra cambia con la profundidad del suelo y la humedad previa.
```

`instruction`:

```text
Extrae la información estructurada de este artículo de noticias sobre medio ambiente y crisis climática, siguiendo el esquema proporcionado. Devuelve null para los campos que no se mencionan en el texto.
```

`output`:

```json
{
  "headline": "Científicos vinculan incendios de turberas con daños respiratorios duraderos",
  "summary": "La investigadora Lara Méndez presentó un estudio sobre incendios de turberas coordinado con Rui Tanaka y difundido como preprint revisado por pares. El equipo analizó 3 400 muestras, registros médicos, sensores de partículas y datos de viento asociados a 620 focos de combustión lenta, vinculando esos episodios con 18 muertes y 146 personas heridas por inhalación de humo. El artículo distingue el humo de turberas del de incendios forestales de superficie y explica que una hectárea de turba seca puede liberar hasta tres veces más carbono que un bosque joven.",
  "category": "SCIENCE",
  "location": null,
  "date": null,
  "key_people": [
    "Lara Méndez",
    "Rui Tanaka"
  ],
  "key_organizations": [],
  "casualties": 18,
  "injured": 146,
  "affected_count": null
}
```

`reasoning`:

```json
{
  "headline": {
    "field_asks": "el titular principal del artículo de noticias.",
    "relevant_fragments": "\"# Científicos vinculan incendios de turberas con daños respiratorios duraderos\".",
    "final_value": "Como el fragmento relevante es el encabezado principal, el titular debe ser \"Científicos vinculan incendios de turberas con daños respiratorios duraderos\"."
  },
  "summary": {
    "field_asks": "un resumen breve de los hechos principales reportados, en 1-3 oraciones.",
    "relevant_fragments": "\"La investigadora Lara Méndez presentó este martes un estudio sobre incendios de turberas ante una red internacional de salud ambiental\", \"El trabajo, coordinado con Rui Tanaka y difundido como preprint revisado por pares, comparó 3 400 muestras de humo y suelo tomadas en humedales boreales y tropicales durante los últimos cinco años\", \"Según la base consolidada, esos episodios estuvieron vinculados con 18 muertes y 146 personas heridas por inhalación de humo denso\" y \"Los autores calculan que una hectárea de turba seca puede liberar hasta tres veces más carbono que un bosque joven\".",
    "final_value": "Como los fragmentos relevantes cubren autoría del estudio, método, consecuencias humanas y hallazgos técnicos, el resumen debe sintetizar esos hechos en tres oraciones."
  },
  "category": {
    "field_asks": "la categoría temática de la noticia, mapeada a uno de estos valores: JUDICIAL, DISASTER, HEALTH, ENVIRONMENT, POLITICS, ECONOMY, SCIENCE, CULTURE, SPORTS u OTHER.",
    "relevant_fragments": "\"presentó este martes un estudio\", \"El equipo revisó partes médicos, sensores de partículas finas y registros de viento\" y \"Un laboratorio universitario aportó modelos de dispersión\".",
    "final_value": "Como los fragmentos relevantes se centran en un estudio, datos y modelos científicos, el valor del enum debe ser \"SCIENCE\"."
  },
  "location": {
    "field_asks": "la ubicación geográfica donde ocurrió el evento, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"comparó 3 400 muestras de humo y suelo tomadas en humedales boreales y tropicales\".",
    "final_value": "El fragmento relevante describe un ámbito de estudio amplio y genérico, pero no una ubicación concreta del evento noticioso; el valor debe ser null."
  },
  "date": {
    "field_asks": "la fecha mencionada en el artículo, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"presentó este martes\" y \"durante los últimos cinco años\".",
    "final_value": "Los fragmentos relevantes solo dan una referencia relativa y un periodo de estudio, no una fecha absoluta; el valor debe ser null."
  },
  "key_people": {
    "field_asks": "nombres de personas individuales clave mencionadas en el artículo.",
    "relevant_fragments": "\"La investigadora Lara Méndez\" y \"coordinado con Rui Tanaka\".",
    "final_value": "Como los fragmentos relevantes nombran a dos personas individuales vinculadas al estudio, la lista debe incluir \"Lara Méndez\" y \"Rui Tanaka\"."
  },
  "key_organizations": {
    "field_asks": "nombres de organizaciones, empresas, instituciones o gobiernos mencionados.",
    "relevant_fragments": "\"una red internacional de salud ambiental\", \"preprint revisado por pares\" y \"Un laboratorio universitario\".",
    "final_value": "Los fragmentos relevantes describen espacios o tipos institucionales, pero no dan nombres propios de organizaciones, empresas, instituciones o gobiernos; la lista debe ser vacía."
  },
  "casualties": {
    "field_asks": "número de muertes mencionadas, o null si no se menciona ninguna cifra de muertes humanas.",
    "relevant_fragments": "\"esos episodios estuvieron vinculados con 18 muertes\".",
    "final_value": "Como el fragmento relevante menciona 18 muertes humanas asociadas a los episodios analizados, el valor debe ser 18."
  },
  "injured": {
    "field_asks": "número de personas heridas mencionadas, o null si no se menciona ninguna cifra de heridos humanos.",
    "relevant_fragments": "\"esos episodios estuvieron vinculados con [...] 146 personas heridas por inhalación de humo denso\".",
    "final_value": "Como el fragmento relevante cuantifica a las personas heridas por inhalación, el valor debe ser 146."
  },
  "affected_count": {
    "field_asks": "número de personas afectadas o desplazadas, o null si no aplica o no hay cifra suficiente.",
    "relevant_fragments": "\"comparó 3 400 muestras de humo y suelo tomadas en humedales boreales y tropicales\", \"620 focos de combustión lenta\" y \"18 muertes y 146 personas heridas por inhalación de humo denso\".",
    "final_value": "Los fragmentos relevantes dan muestras, focos, muertes y heridos, pero no una cifra separada de personas afectadas o desplazadas; el valor debe ser null."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son artículos de noticia en Markdown: encabezado `# <titular>`, una entradilla que resume el hecho, varios párrafos con citas o atribuciones, y a veces párrafos laterales con otros actores o contextos políticos que pueden meter personas y lugares secundarios. Para los nuevos ejemplos conviene mantener esa forma periodística breve, con menos de 1600 caracteres, cifras ambientales y humanas bien separadas, entidades naturales que no se confundan con organizaciones, y ausencias expresadas de forma natural por el foco del artículo, no mediante frases que digan explícitamente que un campo no aparece.
