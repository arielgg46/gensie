# general_disasters

Los tasks `general_disasters` usan el schema general de noticias L4 para fenómenos meteorológicos, deslizamientos, terremotos u otros desastres: el modelo debe copiar el titular, resumir los hechos principales en 1-3 frases, clasificar la noticia, extraer ubicación y fecha cuando estén grounded, listar personas y organizaciones nombradas, y separar cifras humanas de víctimas, heridos o afectados de números físicos como velocidad del viento, distancia, oleaje o intensidad.

## Ejemplos revisados

- `data/dev_rev/general_disasters_001.json`
- `data/dev_rev/general_disasters_002.json`
- `data/dev/general_disasters_003.json`
- `data/dev/general_disasters_009.json`
- `data/dev/general_disasters_010.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `headline` | Requerido, `string`, no nullable. Suele salir verbatim del encabezado `# ...`; conviene variar titular de impacto local frente a titular de seguimiento meteorológico. |
| `summary` | Requerido, `string`, no nullable. Debe condensar hecho, ubicación, consecuencias y respuesta, sin copiar listas completas de velocidades o distancias salvo que sean centrales. |
| `category` | Enum requerido. Debe mapear a uno de estos valores: `JUDICIAL`, `DISASTER`, `HEALTH`, `ENVIRONMENT`, `POLITICS`, `ECONOMY`, `SCIENCE`, `CULTURE`, `SPORTS` u `OTHER`. En este prefijo normalmente debe ser `DISASTER`, incluso si el texto incluye autoridades o alertas. |
| `location` | `string` vs `null`. Dualidad entre ubicación concreta de impacto y seguimiento en aguas abiertas o zona genérica sin lugar geográfico suficiente. |
| `date` | `string` vs `null`. Dualidad entre fecha absoluta completa y referencias relativas como `este jueves`, `en las próximas horas` o temporada sin fecha concreta. |
| `key_people` | `[]` vs lista poblada. Las autoridades por cargo no bastan; deben aparecer nombres individuales. |
| `key_organizations` | `[]` vs lista poblada. Incluye centros de huracanes, defensa civil, bomberos, hospitales o gobiernos nombrados; no incluye grupos genéricos sin nombre propio. |
| `casualties` | `integer` vs `null`. Debe ser muertes humanas explícitas, no animales muertos, viviendas destruidas ni desaparecidos si no se reportan como fallecidos. |
| `injured` | `integer` vs `null`. Debe ser personas heridas o atendidas por lesiones, no personas evacuadas o expuestas. |
| `affected_count` | `integer` vs `null`. Debe ser personas evacuadas, damnificadas o desplazadas; no velocidades, distancias, barrios, viviendas o hectáreas. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `headline` | Titular principal de la noticia, normalmente el encabezado `#`. Cópialo sin el marcador Markdown y no añadas contexto del cuerpo ni cifras que no estén en el titular. |
| `summary` | Resumen breve en 1-3 oraciones con fenómeno, ubicación, consecuencias humanas y respuesta cuando aparezcan. No conviertas listas largas de velocidades, distancias o daños materiales en el foco si las víctimas o afectados son el hecho central. |
| `category` | Categoría temática del enum completo: `JUDICIAL`, `DISASTER`, `HEALTH`, `ENVIRONMENT`, `POLITICS`, `ECONOMY`, `SCIENCE`, `CULTURE`, `SPORTS` u `OTHER`. Para huracanes, temporales, aludes, terremotos, inundaciones y emergencias similares usa `DISASTER`, aunque el texto cite gobiernos, policía o centros meteorológicos. |
| `location` | Lugar principal del evento o impacto. Extrae ciudad, región, país o zona marítima concreta si está grounded; devuelve `null` si solo hay aguas abiertas, direcciones, puertos genéricos o referencias demasiado amplias sin lugar nombrado. |
| `date` | Fecha explícita del hecho o periodo cuando el texto la da. Devuelve `null` para `este jueves`, `en las próximas horas`, `temporada`, duración del temporal o fechas de boletines si no son una fecha absoluta del evento. |
| `key_people` | Personas individuales nombradas y relevantes. No incluyas cargos sin nombre, grupos, equipos de rescate ni organismos; sí incluye autoridades, especialistas o testigos con nombre propio. |
| `key_organizations` | Organizaciones, gobiernos, centros meteorológicos, medios, hospitales o agencias nombradas. No incluyas instalaciones genéricas, equipos sin nombre propio, países donantes como si fueran organizaciones ni fenómenos meteorológicos. |
| `casualties` | Número de muertes humanas reportadas. No uses desaparecidos, animales muertos, viviendas destruidas, balances aproximados del titular si el cuerpo da una cifra más precisa, ni muertes no confirmadas. |
| `injured` | Número de personas heridas o lesionadas. No uses evacuados, damnificados, personas expuestas, desaparecidos ni atendidos preventivamente si no se describen como heridos. |
| `affected_count` | Número de personas afectadas, damnificadas, evacuadas o desplazadas. No uses velocidades del viento, kilómetros, alturas de oleaje, casas, rutas, toneladas, dinero ni familias si el schema espera personas y no hay conversión segura. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `headline` | Titular de alud con impacto humano local. | Titular de tifón que pierde fuerza mar adentro. |
| `summary` | Tres oraciones con hecho, cifras humanas y respuesta. | Dos o tres oraciones de seguimiento preventivo y condiciones marítimas. |
| `category` | `DISASTER`. | `DISASTER`. |
| `location` | Valor no null: Santa Lidia, Nariño, Colombia. | `null`: solo aguas abiertas y referencias genéricas a puertos del norte. |
| `date` | Valor no null: 9 de febrero de 2026. | `null`: referencia relativa `este jueves`. |
| `key_people` | Lista poblada con una autoridad nombrada. | Lista poblada con una meteoróloga nombrada, para no ligar personas solo a autoridades políticas. |
| `key_organizations` | Lista poblada con organismos de respuesta y hospital. | `[]`: servicios o equipos genéricos sin nombre propio. |
| `casualties` | `7`. | `null`. |
| `injured` | `43`. | `null`. |
| `affected_count` | `1800`. | `null`. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Un alud arrasa dos barrios de Santa Lidia tras tres días de lluvias

Un deslizamiento de lodo bajó por la quebrada El Pinar el 9 de febrero de 2026 y golpeó los barrios La Esperanza y San Roque, en Santa Lidia, departamento de Nariño, Colombia. El alcalde Mateo Rojas dijo que la ladera ya venía agrietándose desde la madrugada, pero el corte de la carretera impidió llegar a todas las viviendas antes del desprendimiento.

Bomberos Voluntarios de Santa Lidia, la Defensa Civil Colombiana y cuadrillas del Hospital San Gabriel trabajaron durante la noche con maquinaria ligera. El primer balance oficial reportó 7 fallecidos, 43 heridos y 1 800 personas evacuadas hacia escuelas y coliseos. La Unidad Nacional para la Gestión del Riesgo anunció carpas, agua y una evaluación geológica para decidir si los vecinos podrán regresar a la zona baja del valle.
```

`instruction`:

```text
Extrae la información estructurada de este artículo de noticias sobre un desastre natural, siguiendo el esquema proporcionado. Devuelve null para los campos que no se mencionan en el texto.
```

`output`:

```json
{
  "headline": "Un alud arrasa dos barrios de Santa Lidia tras tres días de lluvias",
  "summary": "Un deslizamiento de lodo bajó por la quebrada El Pinar el 9 de febrero de 2026 y golpeó dos barrios de Santa Lidia, en Nariño, Colombia. El balance oficial reportó 7 fallecidos, 43 heridos y 1 800 personas evacuadas, mientras equipos de bomberos, defensa civil y hospital trabajaron durante la noche. La Unidad Nacional para la Gestión del Riesgo anunció asistencia y una evaluación geológica antes de permitir el regreso a la zona baja del valle.",
  "category": "DISASTER",
  "location": "Santa Lidia, Nariño, Colombia",
  "date": "9 de febrero de 2026",
  "key_people": [
    "Mateo Rojas"
  ],
  "key_organizations": [
    "Bomberos Voluntarios de Santa Lidia",
    "Defensa Civil Colombiana",
    "Hospital San Gabriel",
    "Unidad Nacional para la Gestión del Riesgo"
  ],
  "casualties": 7,
  "injured": 43,
  "affected_count": 1800
}
```

`reasoning`:

```json
{
  "headline": {
    "field_asks": "el titular principal del artículo de noticias.",
    "relevant_fragments": "\"# Un alud arrasa dos barrios de Santa Lidia tras tres días de lluvias\".",
    "final_value": "Como el fragmento relevante es el encabezado principal, el titular debe ser \"Un alud arrasa dos barrios de Santa Lidia tras tres días de lluvias\"."
  },
  "summary": {
    "field_asks": "un resumen breve de los hechos principales reportados, en 1-3 oraciones.",
    "relevant_fragments": "\"Un deslizamiento de lodo bajó por la quebrada El Pinar\", \"El primer balance oficial reportó 7 fallecidos, 43 heridos y 1 800 personas evacuadas\" y \"anunció carpas, agua y una evaluación geológica\".",
    "final_value": "Como los fragmentos relevantes cubren el evento, las cifras humanas y la respuesta institucional, el resumen debe condensar esos hechos en tres oraciones."
  },
  "category": {
    "field_asks": "la categoría temática de la noticia, mapeada a uno de estos valores: JUDICIAL, DISASTER, HEALTH, ENVIRONMENT, POLITICS, ECONOMY, SCIENCE, CULTURE, SPORTS u OTHER.",
    "relevant_fragments": "\"Un deslizamiento de lodo\" y \"un alud arrasa dos barrios\".",
    "final_value": "Como los fragmentos relevantes describen un desastre natural con impacto humano, el valor del enum debe ser \"DISASTER\"."
  },
  "location": {
    "field_asks": "la ubicación geográfica donde ocurrió el evento, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"en Santa Lidia, departamento de Nariño, Colombia\".",
    "final_value": "Como el fragmento relevante ubica el alud en Santa Lidia, Nariño, Colombia, el valor debe ser \"Santa Lidia, Nariño, Colombia\"."
  },
  "date": {
    "field_asks": "la fecha mencionada en el artículo, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"el 9 de febrero de 2026\".",
    "final_value": "Como el fragmento relevante da una fecha completa del deslizamiento, el valor debe ser \"9 de febrero de 2026\"."
  },
  "key_people": {
    "field_asks": "nombres de personas individuales clave mencionadas en el artículo.",
    "relevant_fragments": "\"El alcalde Mateo Rojas dijo\".",
    "final_value": "Como el fragmento relevante nombra a una persona individual, la lista debe incluir \"Mateo Rojas\"."
  },
  "key_organizations": {
    "field_asks": "nombres de organizaciones, empresas, instituciones o gobiernos mencionados.",
    "relevant_fragments": "\"Bomberos Voluntarios de Santa Lidia\", \"Defensa Civil Colombiana\", \"Hospital San Gabriel\" y \"Unidad Nacional para la Gestión del Riesgo\".",
    "final_value": "Como los fragmentos relevantes nombran organismos de respuesta e instituciones, la lista debe incluir esas cuatro organizaciones."
  },
  "casualties": {
    "field_asks": "número de muertes mencionadas, o null si no se menciona ninguna cifra de muertes humanas.",
    "relevant_fragments": "\"El primer balance oficial reportó 7 fallecidos\".",
    "final_value": "Como el fragmento relevante cuantifica fallecidos humanos, el valor debe ser 7."
  },
  "injured": {
    "field_asks": "número de personas heridas mencionadas, o null si no se menciona ninguna cifra de heridos humanos.",
    "relevant_fragments": "\"43 heridos\".",
    "final_value": "Como el fragmento relevante cuantifica heridos, el valor debe ser 43."
  },
  "affected_count": {
    "field_asks": "número de personas afectadas, evacuadas o desplazadas, o null si no aplica o no hay cifra suficiente.",
    "relevant_fragments": "\"1 800 personas evacuadas hacia escuelas y coliseos\".",
    "final_value": "Como el fragmento relevante cuantifica personas evacuadas, el valor debe ser 1800."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# El tifón Luma pierde fuerza mar adentro tras activar avisos costeros

El tifón Luma avanzó este jueves sobre aguas abiertas con rachas de viento cada vez menos organizadas y oleaje cercano a cuatro metros. La meteoróloga Ana Kei explicó en una rueda técnica que el sistema se aleja de las rutas de ferry y que los modelos reducen la probabilidad de impacto directo durante la noche.

Los puertos pesqueros del norte mantuvieron bandera amarilla, suspendieron salidas pequeñas y revisaron amarres en los muelles expuestos. En las próximas horas se esperan bandas de lluvia irregulares y corrientes fuertes, aunque el núcleo del tifón continuará mar adentro. Equipos de puerto retiraron boyas sueltas y pidieron a las embarcaciones deportivas esperar el boletín de la mañana antes de volver al agua.
```

`instruction`:

```text
Extrae la información estructurada de este artículo de noticias sobre un fenómeno meteorológico, incluyendo el titular, resumen, categoría, ubicación, organizaciones clave, y cualquier cifra de víctimas o afectados mencionada.
```

`output`:

```json
{
  "headline": "El tifón Luma pierde fuerza mar adentro tras activar avisos costeros",
  "summary": "El tifón Luma avanzó este jueves sobre aguas abiertas con rachas menos organizadas y oleaje cercano a cuatro metros. Ana Kei explicó que el sistema se aleja de las rutas de ferry y que los modelos reducen la probabilidad de impacto directo durante la noche. Los puertos pesqueros del norte mantuvieron avisos preventivos, suspendieron salidas pequeñas y revisaron amarres.",
  "category": "DISASTER",
  "location": null,
  "date": null,
  "key_people": [
    "Ana Kei"
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
    "relevant_fragments": "\"# El tifón Luma pierde fuerza mar adentro tras activar avisos costeros\".",
    "final_value": "Como el fragmento relevante es el encabezado principal, el titular debe ser \"El tifón Luma pierde fuerza mar adentro tras activar avisos costeros\"."
  },
  "summary": {
    "field_asks": "un resumen breve de los hechos principales reportados, en 1-3 oraciones.",
    "relevant_fragments": "\"El tifón Luma avanzó este jueves sobre aguas abiertas\", \"el sistema se aleja de las rutas de ferry\" y \"mantuvieron bandera amarilla, suspendieron salidas pequeñas y revisaron amarres\".",
    "final_value": "Como los fragmentos relevantes cubren evolución del tifón, menor riesgo directo y medidas preventivas, el resumen debe sintetizar esos puntos en tres oraciones."
  },
  "category": {
    "field_asks": "la categoría temática de la noticia, mapeada a uno de estos valores: JUDICIAL, DISASTER, HEALTH, ENVIRONMENT, POLITICS, ECONOMY, SCIENCE, CULTURE, SPORTS u OTHER.",
    "relevant_fragments": "\"El tifón Luma\" y \"avisos costeros\".",
    "final_value": "Como los fragmentos relevantes tratan un fenómeno meteorológico peligroso, el valor del enum debe ser \"DISASTER\"."
  },
  "location": {
    "field_asks": "la ubicación geográfica donde ocurrió el evento, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"sobre aguas abiertas\", \"mar adentro\" y \"Los puertos pesqueros del norte\".",
    "final_value": "Los fragmentos relevantes describen el desplazamiento y avisos de forma genérica, sin ciudad, país, región nombrada o ubicación geográfica suficientemente específica; el valor debe ser null."
  },
  "date": {
    "field_asks": "la fecha mencionada en el artículo, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"este jueves\", \"durante la noche\" y \"el boletín de la mañana\".",
    "final_value": "Los fragmentos relevantes dan referencias relativas y momentos del día, pero no una fecha absoluta; el valor debe ser null."
  },
  "key_people": {
    "field_asks": "nombres de personas individuales clave mencionadas en el artículo.",
    "relevant_fragments": "\"La meteoróloga Ana Kei explicó\".",
    "final_value": "Como el fragmento relevante nombra a una persona individual, la lista debe incluir \"Ana Kei\"."
  },
  "key_organizations": {
    "field_asks": "nombres de organizaciones, empresas, instituciones o gobiernos mencionados.",
    "relevant_fragments": "\"Los puertos pesqueros del norte\" y \"Equipos de puerto\".",
    "final_value": "Los fragmentos relevantes mencionan instalaciones y equipos genéricos, pero no organizaciones con nombre propio; la lista debe ser vacía."
  },
  "casualties": {
    "field_asks": "número de muertes mencionadas, o null si no se menciona ninguna cifra de muertes humanas.",
    "relevant_fragments": "\"mantuvieron bandera amarilla, suspendieron salidas pequeñas y revisaron amarres\".",
    "final_value": "El fragmento relevante describe medidas preventivas portuarias, pero no cifras de muertes humanas; el valor debe ser null."
  },
  "injured": {
    "field_asks": "número de personas heridas mencionadas, o null si no se menciona ninguna cifra de heridos humanos.",
    "relevant_fragments": "\"se aleja de las rutas de ferry\" y \"Equipos de puerto retiraron boyas sueltas\".",
    "final_value": "Los fragmentos relevantes tratan reducción de riesgo y preparación, pero no personas heridas; el valor debe ser null."
  },
  "affected_count": {
    "field_asks": "número de personas afectadas, evacuadas o desplazadas, o null si no aplica o no hay cifra suficiente.",
    "relevant_fragments": "\"oleaje cercano a cuatro metros\" y \"suspendieron salidas pequeñas\".",
    "final_value": "Los fragmentos relevantes dan una medida de oleaje y una suspensión operativa, pero no una cifra de personas afectadas, evacuadas o desplazadas; el valor debe ser null."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son noticias breves en Markdown: encabezado `# <titular>`, un primer párrafo con el fenómeno y su evolución, atribución a centros meteorológicos u organismos de respuesta, ubicación relativa respecto a costas o ciudades, y cifras físicas como vientos, distancia o velocidad. Para los nuevos ejemplos conviene mantener esa forma periodística compacta, separar con claridad cifras meteorológicas de cifras humanas, y dejar que los `null` salgan de contextos naturales de monitoreo, alerta o prevención sin frases fabricadas para anunciar ausencias.
