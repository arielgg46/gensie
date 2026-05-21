# cultural_media

Los tasks `cultural_media` piden extraer metadatos y crítica subjetiva desde una reseña cultural, normalmente de cine o series: el modelo debe identificar la obra reseñada entre muchas menciones distractoras, mapear el tipo de medio y el sentimiento global a enums, distinguir datos factuales grounded como director, reparto, año o puntuación de inferencias no soportadas, y resumir pros, cons y veredicto sin inventar información externa.

## Ejemplos revisados

- `data/dev_rev/cultural_media_001.json`
- `data/dev_rev/cultural_media_002.json`
- `data/dev/cultural_media_003.json`
- `data/dev/cultural_media_004.json`
- `data/dev/cultural_media_005.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `work_title` | Requerido, `string`, no nullable. No entra como bit `null`/valor; conviene variar título claramente reseñado vs título rodeado de otras obras comparadas o mencionadas como distractores. |
| `medium` | Requerido, enum `MOVIE | BOOK | TV_SERIES | VIDEO_GAME`. No entra como bit de ausencia, pero los dos cases deberían complementar al menos `MOVIE` vs `TV_SERIES`, que son los medios presentes en los ejemplos revisados. |
| `director` | `string` vs `null`. Bit principal: director explícitamente mencionado frente a texto que menciona creador, showrunner, plataforma o responsables no equivalentes a director. `cultural_media_003` es buen ejemplo de `null` aunque la instrucción pide creador. |
| `main_cast` | `[]` vs lista poblada. Bit principal: reparto/intérpretes mencionados frente a texto centrado en dirección, trama o plataforma sin actores claros. En los tres ejemplos revisados aparece lista poblada, pero el schema permite y necesita cubrir lista vacía. |
| `release_year` | `integer` vs `null`. Bit principal: año de estreno o lanzamiento explícitamente grounded frente a fechas de contexto, períodos históricos, años de otras obras o ausencia de año. `cultural_media_002` cubre `2026`; `001` y `003` cubren `null`. |
| `rating` | `number` vs `null`. Bit principal: nota explícita normalizable a escala 0-10 frente a reseña sin puntuación. Los tres ejemplos revisados tienen `null`, así que uno de los cases nuevos debería incluir una nota numérica clara para enseñar este campo. |
| `sentiment` | Requerido, enum `POSITIVE | NEUTRAL | NEGATIVE`. No entra como ausencia, pero debe variar entre cases: los ejemplos revisados cubren los tres tonos (`NEGATIVE`, `NEUTRAL`, `POSITIVE`). |
| `pros` | `[]` vs lista poblada. Bit principal si el texto es unilateral; en reseñas mixtas suele estar poblado. Conviene cubrir una reseña negativa con algún pro grounded o una reseña sin aspectos positivos claros. |
| `cons` | `[]` vs lista poblada. Bit principal si el texto es unilateral; conviene cubrir una reseña positiva sin defectos claros o una reseña mixta con reservas concretas. |
| `key_verdict` | Requerido, `string`, no nullable. No entra como bit de ausencia; la variación útil es veredicto casi verbatim desde titular/frase final vs síntesis breve a partir de varias frases de cierre. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `work_title` | Película reseñada con título claro desde el encabezado, aunque con comparaciones a otras películas como distractores. | Serie reseñada con título claro, pero rodeada de menciones a otras series/plataformas para obligar a elegir la obra principal. |
| `medium` | `MOVIE`. | `TV_SERIES`. |
| `director` | Valor no null: director mencionado de forma explícita, por ejemplo `Clara Varela`. | `null`: el texto puede mencionar creador, showrunner, guionista o plataforma, pero no una persona que dirija la obra. |
| `main_cast` | `[]`: la reseña no menciona actores o intérpretes concretos, solo personajes, equipo técnico o comparaciones. | Lista poblada: dos o tres intérpretes mencionados explícitamente como protagonistas o reparto principal. |
| `release_year` | `null`: puede haber fechas de contexto, de otras obras o de la saga, pero no año de estreno/lanzamiento de la obra reseñada. | Año no null: año de estreno o lanzamiento explícito, por ejemplo `2025`. |
| `rating` | Número no null: nota explícita normalizable a 0-10, por ejemplo `3.0` a partir de `3/10` o `1,5/5`. | `null`: reseña sin puntuación numérica aunque tenga valoración verbal. |
| `sentiment` | `NEGATIVE`: crítica claramente desfavorable. | `NEUTRAL`: crítica mixta, con elogios claros pero reservas relevantes. |
| `pros` | `[]`: el texto no concede aspectos positivos concretos, o los descarta como insuficientes sin convertirlos en elogios. | Lista poblada con fragmentos preferiblemente verbatim: actuaciones, diálogos, atmósfera o uso del espacio tal como aparecen en el texto. |
| `cons` | Lista poblada con fragmentos preferiblemente verbatim: defectos explícitos como explicaciones torpes, falta de tensión, humor tardío o clímax mecánico. | Lista poblada con fragmentos preferiblemente verbatim: tramo central estirado, subtramas abiertas, repetición o pérdida de ligereza. |
| `key_verdict` | Veredicto casi verbatim desde una frase final contundente, por ejemplo `un intento fallido sin pulso ni personalidad`. | Síntesis breve de balance mixto, por ejemplo `una serie notable en sus personajes, pero irregular en su desarrollo`. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `work_title` | Título de la obra reseñada, no de las comparaciones. Prioriza el título del encabezado y las menciones repetidas como foco del artículo; ignora obras citadas como referentes, plagios, homenajes o distractores. |
| `medium` | Tipo de medio de la obra principal: `MOVIE`, `BOOK`, `TV_SERIES` o `VIDEO_GAME`. Usa pistas como "película", "serie", "episodios", "temporada", "novela" o plataforma, pero no clasifiques por obras mencionadas alrededor. |
| `director` | Persona que dirige la obra, solo si el texto usa evidencia de dirección o "tras las cámaras" para esa obra. No sustituyas por creador, showrunner, guionista, productor ejecutivo, fotografía, plataforma o autor de la novela adaptada. |
| `main_cast` | Actores o intérpretes nombrados como reparto, protagonistas o presencia actoral de la obra reseñada. No incluyas personajes ficticios, directores, creadores, autores ni nombres de otras obras; usa `[]` si el reparto se menciona sin nombres. |
| `release_year` | Año de estreno o lanzamiento de la obra principal. Devuelve `null` si solo hay fechas de otras obras, época en que transcurre la trama, fecha futura ambigua, plataforma actual o contexto histórico sin vínculo explícito al estreno. |
| `rating` | Puntuación explícita del crítico normalizada a 0-10. No inventes nota a partir de adjetivos; si aparece `3/10` usa `3.0`, si aparece una escala distinta conviértela solo cuando la escala esté clara. |
| `sentiment` | Tono global de la reseña: `POSITIVE`, `NEUTRAL` o `NEGATIVE`. Decide por el balance final, no por una frase aislada: elogios con reservas fuertes suelen ser `NEUTRAL`; condena dominante es `NEGATIVE`; recomendación clara es `POSITIVE`. |
| `pros` | Aspectos positivos concretos destacados por el crítico, preferiblemente fragmentos verbatim o casi verbatim. No conviertas premisas atractivas en pros si el texto las presenta como fallidas o insuficientes. |
| `cons` | Defectos concretos mencionados por el crítico, con formulación cercana al texto. Evita críticas genéricas no citadas y separa defectos distintos cuando el texto los enumera claramente. |
| `key_verdict` | Juicio final conciso de la reseña. Suele salir del titular o cierre; puede ser casi verbatim si resume el balance, pero no debe copiar una frase larga con detalles secundarios. |

## Input y output propuestos

### Ejemplo 1

`input_text`:

```text
# 'La noche de los mapas' se estrella como thriller de ciencia ficción: mucho decorado y cero pulso

La noche de los mapas parecía tener todos los ingredientes para levantar una película de intriga espacial: estaciones abandonadas, conspiraciones cartográficas y una ciudad subterránea llena de secretos. También carga con la sombra de mejores aventuras de ciencia ficción, pero esas comparaciones solo dejan más claro lo poco que esta obra encuentra una voz propia. [...] Clara Varela dirige una película empeñada en parecer enorme, aunque casi nunca consigue que sus piezas encajen. El guion anuncia misterios y luego los resuelve con explicaciones torpes, y cada persecución llega sin tensión. La puesta en escena intenta vender urgencia con luces rojas y música insistente, pero todo parece una maqueta de algo que nunca arranca. [...] El reparto se pierde entre frases solemnes y órdenes gritadas, siempre tratado como un bloque sin presencia individual. La película se compara con modas antiguas del género y con sagas conocidas, pero ninguna fecha queda ligada a su lanzamiento. Lo único rotundo es la nota: después de dos horas de ruido, apenas merece un 3 sobre 10. [...] Ni siquiera sus ideas más llamativas funcionan. La ciudad subterránea no tiene personalidad, el humor cae siempre tarde y el clímax final convierte la conspiración en una sucesión de puertas que se abren solas. Al salir queda una sensación simple: La noche de los mapas es un intento fallido sin pulso ni personalidad.
```

`output`:

```json
{
  "work_title": "La noche de los mapas",
  "medium": "MOVIE",
  "director": "Clara Varela",
  "main_cast": [],
  "release_year": null,
  "rating": 3.0,
  "sentiment": "NEGATIVE",
  "pros": [],
  "cons": [
    "explicaciones torpes",
    "cada persecución llega sin tensión",
    "el humor cae siempre tarde",
    "el clímax final convierte la conspiración en una sucesión de puertas que se abren solas"
  ],
  "key_verdict": "un intento fallido sin pulso ni personalidad"
}
```

`reasoning`:

```json
{
  "work_title": {
    "field_asks": "el nombre de la película, libro o serie reseñada.",
    "relevant_fragments": "\"# 'La noche de los mapas' se estrella como thriller de ciencia ficción\" y \"La noche de los mapas parecía tener todos los ingredientes\".",
    "final_value": "La obra principal reseñada es \"La noche de los mapas\"."
  },
  "medium": {
    "field_asks": "el tipo de medio reseñado, mapeado a uno de estos valores: MOVIE, BOOK, TV_SERIES o VIDEO_GAME.",
    "relevant_fragments": "\"levantar una película de intriga espacial\" y \"Clara Varela dirige una película\".",
    "final_value": "Como los fragmentos relevantes describen la obra como \"película\", el valor del enum debe ser \"MOVIE\"."
  },
  "director": {
    "field_asks": "la persona que dirigió la película o serie, o null si no aparece.",
    "relevant_fragments": "\"Clara Varela dirige una película empeñada en parecer enorme\".",
    "final_value": "El texto identifica explícitamente a Clara Varela como directora."
  },
  "main_cast": {
    "field_asks": "los actores o intérpretes principales mencionados en la reseña.",
    "relevant_fragments": "\"El reparto se pierde entre frases solemnes y órdenes gritadas, siempre tratado como un bloque sin presencia individual\".",
    "final_value": "El contexto más cercano habla del reparto como bloque, pero no da nombres de intérpretes; la lista debe ser vacía."
  },
  "release_year": {
    "field_asks": "el año de estreno o lanzamiento de la obra, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"La película se compara con modas antiguas del género y con sagas conocidas, pero ninguna fecha queda ligada a su lanzamiento\".",
    "final_value": "El texto menciona referencias temporales ajenas, pero no un año de estreno o lanzamiento de la película; el valor debe ser null."
  },
  "rating": {
    "field_asks": "la puntuación dada por el crítico, normalizada a escala 0-10.",
    "relevant_fragments": "\"después de dos horas de ruido, apenas merece un 3 sobre 10\".",
    "final_value": "La nota ya está expresada sobre 10, así que el valor normalizado es 3.0."
  },
  "sentiment": {
    "field_asks": "el tono global de la reseña, mapeado a uno de estos valores: POSITIVE, NEUTRAL o NEGATIVE.",
    "relevant_fragments": "\"se estrella\", \"cero pulso\" y \"un intento fallido sin pulso ni personalidad\".",
    "final_value": "Como los fragmentos relevantes expresan una valoración claramente desfavorable, el valor del enum debe ser \"NEGATIVE\"."
  },
  "pros": {
    "field_asks": "aspectos positivos concretos destacados por la crítica.",
    "relevant_fragments": "\"lo poco que esta obra encuentra una voz propia\", \"todo parece una maqueta\" y \"Ni siquiera sus ideas más llamativas funcionan\".",
    "final_value": "El texto revisa los posibles méritos y los formula como fallos; no hay aspectos positivos concretos suficientemente grounded, así que la lista es vacía."
  },
  "cons": {
    "field_asks": "defectos o aspectos negativos mencionados en la reseña.",
    "relevant_fragments": "\"explicaciones torpes\", \"cada persecución llega sin tensión\", \"el humor cae siempre tarde\" y \"el clímax final convierte la conspiración en una sucesión de puertas que se abren solas\".",
    "final_value": "Los defectos deben conservarse como fragmentos verbatim o casi verbatim del texto."
  },
  "key_verdict": {
    "field_asks": "un resumen conciso del juicio final de la reseña.",
    "relevant_fragments": "\"La noche de los mapas es un intento fallido sin pulso ni personalidad\".",
    "final_value": "El veredicto puede copiarse casi verbatim como \"un intento fallido sin pulso ni personalidad\"."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# 'Los días de la estación' confirma a sus protagonistas como un hallazgo, aunque la serie no siempre sabe cerrar lo que abre

Cada temporada aparece una serie pequeña que no pretende cambiar la televisión, pero sí encontrar un tono propio. 'Los días de la estación', estrenada en 2025 en Horizonte Play, pertenece a esa familia: seis episodios sobre una vieja estación de tren convertida en refugio vecinal, con una mirada cálida hacia sus personajes. [...] La serie fue creada por Irene Salvatierra y escrita junto a Pablo León para Horizonte Play. Entre el reparto, Nadia Ríos sostiene la historia con una interpretación contenida, Bruno Castañeda aporta una comicidad seca que evita el sentimentalismo y Laura Otero convierte una subtrama mínima en el momento más delicado de la temporada. [...] Cuando 'Los días de la estación' se concentra en la convivencia, funciona de maravilla. Hay diálogos precisos, una atmósfera melancólica que nunca se vuelve postal y un uso muy bonito del espacio de la estación como memoria compartida. [...] El problema es que el tramo central se estira más de la cuenta. Algunas subtramas familiares quedan abiertas sin verdadera consecuencia y el quinto episodio repite información que ya estaba clara. La serie no se hunde por eso, pero sí pierde parte de la ligereza que había construido. El balance queda en una zona intermedia: una serie notable en sus personajes, pero irregular en su desarrollo.
```

`output`:

```json
{
  "work_title": "Los días de la estación",
  "medium": "TV_SERIES",
  "director": null,
  "main_cast": [
    "Nadia Ríos",
    "Bruno Castañeda",
    "Laura Otero"
  ],
  "release_year": 2025,
  "rating": null,
  "sentiment": "NEUTRAL",
  "pros": [
    "Nadia Ríos sostiene la historia con una interpretación contenida",
    "Bruno Castañeda aporta una comicidad seca que evita el sentimentalismo",
    "Hay diálogos precisos",
    "un uso muy bonito del espacio de la estación como memoria compartida"
  ],
  "cons": [
    "el tramo central se estira más de la cuenta",
    "Algunas subtramas familiares quedan abiertas sin verdadera consecuencia",
    "el quinto episodio repite información que ya estaba clara",
    "pierde parte de la ligereza que había construido"
  ],
  "key_verdict": "una serie notable en sus personajes, pero irregular en su desarrollo"
}
```

`reasoning`:

```json
{
  "work_title": {
    "field_asks": "el nombre de la película, libro o serie reseñada.",
    "relevant_fragments": "\"# 'Los días de la estación' confirma a sus protagonistas\" y \"'Los días de la estación', estrenada en 2025 en Horizonte Play\".",
    "final_value": "La obra principal reseñada es \"Los días de la estación\"."
  },
  "medium": {
    "field_asks": "el tipo de medio reseñado, mapeado a uno de estos valores: MOVIE, BOOK, TV_SERIES o VIDEO_GAME.",
    "relevant_fragments": "\"Cada temporada aparece una serie pequeña\" y \"seis episodios sobre una vieja estación de tren\".",
    "final_value": "Como los fragmentos relevantes presentan la obra como una serie con episodios, el valor del enum debe ser \"TV_SERIES\"."
  },
  "director": {
    "field_asks": "la persona que dirigió la película o serie, o null si no aparece.",
    "relevant_fragments": "\"La serie fue creada por Irene Salvatierra y escrita junto a Pablo León para Horizonte Play\".",
    "final_value": "El contexto más cercano menciona creación y escritura, pero no dirección; por grounding estricto el valor debe ser null."
  },
  "main_cast": {
    "field_asks": "los actores o intérpretes principales mencionados en la reseña.",
    "relevant_fragments": "\"Entre el reparto, Nadia Ríos sostiene la historia\", \"Bruno Castañeda aporta una comicidad seca\" y \"Laura Otero convierte una subtrama mínima\".",
    "final_value": "Los nombres mencionados como reparto son Nadia Ríos, Bruno Castañeda y Laura Otero."
  },
  "release_year": {
    "field_asks": "el año de estreno o lanzamiento de la obra, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"'Los días de la estación', estrenada en 2025 en Horizonte Play\".",
    "final_value": "El año de estreno indicado para la serie es 2025."
  },
  "rating": {
    "field_asks": "la puntuación dada por el crítico, normalizada a escala 0-10, o null si no hay puntuación.",
    "relevant_fragments": "\"El balance queda en una zona intermedia: una serie notable en sus personajes, pero irregular en su desarrollo\".",
    "final_value": "El cierre da una valoración verbal, pero no una nota numérica; el valor debe ser null."
  },
  "sentiment": {
    "field_asks": "el tono global de la reseña, mapeado a uno de estos valores: POSITIVE, NEUTRAL o NEGATIVE.",
    "relevant_fragments": "\"funciona de maravilla\", \"El problema es que el tramo central se estira más de la cuenta\" y \"una zona intermedia\".",
    "final_value": "Como los fragmentos relevantes combinan elogios claros con reservas relevantes y un balance intermedio, el valor del enum debe ser \"NEUTRAL\"."
  },
  "pros": {
    "field_asks": "aspectos positivos concretos destacados por la crítica.",
    "relevant_fragments": "\"Nadia Ríos sostiene la historia con una interpretación contenida\", \"Bruno Castañeda aporta una comicidad seca\", \"Hay diálogos precisos\" y \"un uso muy bonito del espacio de la estación como memoria compartida\".",
    "final_value": "Los pros deben conservarse como fragmentos verbatim o casi verbatim del texto."
  },
  "cons": {
    "field_asks": "defectos o aspectos negativos mencionados en la reseña.",
    "relevant_fragments": "\"el tramo central se estira más de la cuenta\", \"Algunas subtramas familiares quedan abiertas sin verdadera consecuencia\", \"el quinto episodio repite información que ya estaba clara\" y \"pierde parte de la ligereza que había construido\".",
    "final_value": "Los cons deben conservarse como fragmentos verbatim o casi verbatim del texto."
  },
  "key_verdict": {
    "field_asks": "un resumen conciso del juicio final de la reseña.",
    "relevant_fragments": "\"una serie notable en sus personajes, pero irregular en su desarrollo\".",
    "final_value": "El veredicto final puede copiarse verbatim."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados siguen una forma de artículo de crítica: empiezan con un encabezado `#` que suele contener el título de la obra y una valoración editorial fuerte, después alternan párrafos extensos separados a veces por `[...]` y algún subtítulo Markdown, introducen comparaciones con otras obras que funcionan como distractores, incluyen una zona factual con medio, director/creador, reparto, plataforma o fecha, luego un bloque de sinopsis/contexto y finalmente varios párrafos evaluativos con pros, cons y una frase de cierre que puede convertirse en `key_verdict`. El texto rara vez trae una puntuación explícita; cuando hay fechas, pueden referirse al estreno real, al lanzamiento esperado, a la época narrada o a otras obras, así que `release_year` debe salir solo de evidencia directa sobre la obra reseñada.
