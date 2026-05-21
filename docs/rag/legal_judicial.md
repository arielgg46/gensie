# legal_judicial

Los tasks `legal_judicial` usan el schema general de noticias L4 para procesos judiciales, condenas, operativos policiales y hechos penales: el modelo debe copiar el titular, resumir el fallo o intervención, clasificar como noticia judicial, extraer ubicación y fecha si están grounded, listar personas y organizaciones nombradas, y distinguir cifras jurídicas como años de prisión, detenidos o armas incautadas de cifras humanas de fallecidos, heridos o afectados.

## Ejemplos revisados

- `data/dev_rev/legal_judicial_001.json`
- `data/dev_rev/legal_judicial_002.json`
- `data/dev/legal_judicial_003.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `headline` | Requerido, `string`, no nullable. Sale verbatim del encabezado; conviene variar sentencia judicial frente a operativo policial. |
| `summary` | Requerido, `string`, no nullable. Debe condensar decisión judicial, acusación, personas clave y consecuencias sin convertir toda la crónica en lista de nombres. |
| `category` | Enum requerido. Debe mapear a uno de estos valores: `JUDICIAL`, `DISASTER`, `HEALTH`, `ENVIRONMENT`, `POLITICS`, `ECONOMY`, `SCIENCE`, `CULTURE`, `SPORTS` u `OTHER`. En este prefijo debe ser `JUDICIAL` cuando el foco sea condena, investigación, operativo o persecución penal. |
| `location` | `string` vs `null`. Dualidad entre tribunal o ciudad explícita y textos con instituciones nacionales o barrios genéricos sin ubicación completa. |
| `date` | `string` vs `null`. Dualidad entre fecha absoluta de sentencia u operativo y referencias relativas como `hoy`, `esta madrugada` o `durante la audiencia`. |
| `key_people` | `[]` vs lista poblada. Incluye condenados, fiscales, jueces o víctimas nombradas; no incluye cargos sin nombre propio. |
| `key_organizations` | `[]` vs lista poblada. Incluye tribunales, fiscalías, policías, bandas, empresas o entidades afectadas; debe preservar nombres oficiales y alias organizacionales. |
| `casualties` | `integer` vs `null`. Solo muertes humanas del hecho narrado; no años de cárcel, condenados, fallecidos históricos no ligados al evento o bajas hipotéticas. |
| `injured` | `integer` vs `null`. Solo personas heridas; no detenidos, imputados, evacuados ni perjudicados económicos. |
| `affected_count` | `integer` vs `null`. Puede poblarse con víctimas o perjudicados si el texto los cuantifica; no debe usarse para años de condena, armas, detenidos o sospechosos. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `headline` | Sentencia por estafa digital con afectados económicos. | Redada policial contra una banda armada. |
| `summary` | Tres oraciones con condena, cuantía procesal y víctimas afectadas. | Dos o tres oraciones con operativo, fallecidos, heridos y detenciones. |
| `category` | `JUDICIAL`. | `JUDICIAL`. |
| `location` | Valor no null: Valencia, España. | Valor no null: Rosario, Argentina. |
| `date` | Valor no null: 15 de marzo de 2026. | `null`: referencia relativa `esta madrugada`. |
| `key_people` | Lista poblada: acusada y fiscal nombrados. | `[]`: cargos, agentes y sospechosos sin nombres individuales. |
| `key_organizations` | Lista poblada: tribunal, fiscalía, banco y plataforma. | Lista poblada: policía, fiscalía y banda. |
| `casualties` | `null`: hay condena y víctimas económicas, no muertes. | `2`: dos agentes muertos. |
| `injured` | `null`: hay perjudicados económicos, no lesionados. | `5`: cinco personas heridas. |
| `affected_count` | `3600`: clientes perjudicados por la estafa. | `null`: detenidos y armas no son personas afectadas o desplazadas. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Condenan a Sofía Ledesma por la estafa digital de Cuenta Clara

La Audiencia Provincial de Valencia condenó el 15 de marzo de 2026 a Sofía Ledesma a nueve años de prisión por dirigir una red que copiaba credenciales bancarias mediante la falsa plataforma Cuenta Clara. La sentencia sitúa la causa en Valencia, España, y describe transferencias pequeñas realizadas durante seis meses desde cuentas del Banco Marisma.

El fiscal Rafael Orts sostuvo que la acusada coordinó dominios web, mensajes de verificación y monederos virtuales usados para retirar el dinero. El fallo reconoce 3 600 clientes perjudicados y ordena indemnizaciones individuales, además del decomiso de equipos informáticos. La Fiscalía Provincial de Valencia anunció que estudiará recurrir la absolución de dos colaboradores técnicos.
```

`instruction`:

```text
Extrae la información estructurada de este artículo de noticias judiciales, identificando personas clave, organizaciones involucradas y cifras humanas mencionadas.
```

`output`:

```json
{
  "headline": "Condenan a Sofía Ledesma por la estafa digital de Cuenta Clara",
  "summary": "La Audiencia Provincial de Valencia condenó el 15 de marzo de 2026 a Sofía Ledesma a nueve años de prisión por dirigir una red que copiaba credenciales bancarias mediante la plataforma falsa Cuenta Clara. El fiscal Rafael Orts sostuvo que la acusada coordinó dominios, mensajes y monederos virtuales usados para retirar dinero de cuentas del Banco Marisma. El fallo reconoce 3 600 clientes perjudicados, ordena indemnizaciones y la Fiscalía Provincial de Valencia estudiará recurrir la absolución de dos colaboradores técnicos.",
  "category": "JUDICIAL",
  "location": "Valencia, España",
  "date": "15 de marzo de 2026",
  "key_people": [
    "Sofía Ledesma",
    "Rafael Orts"
  ],
  "key_organizations": [
    "Audiencia Provincial de Valencia",
    "Cuenta Clara",
    "Banco Marisma",
    "Fiscalía Provincial de Valencia"
  ],
  "casualties": null,
  "injured": null,
  "affected_count": 3600
}
```

`reasoning`:

```json
{
  "headline": {
    "field_asks": "el titular principal del artículo de noticias.",
    "relevant_fragments": "\"# Condenan a Sofía Ledesma por la estafa digital de Cuenta Clara\".",
    "final_value": "Como el fragmento relevante es el encabezado principal, el titular debe ser \"Condenan a Sofía Ledesma por la estafa digital de Cuenta Clara\"."
  },
  "summary": {
    "field_asks": "un resumen breve de los hechos principales reportados, en 1-3 oraciones.",
    "relevant_fragments": "\"condenó el 15 de marzo de 2026 a Sofía Ledesma a nueve años de prisión\", \"copiaba credenciales bancarias mediante la falsa plataforma Cuenta Clara\" y \"reconoce 3 600 clientes perjudicados\".",
    "final_value": "Como los fragmentos relevantes cubren condena, mecanismo de estafa y cantidad de perjudicados, el resumen debe sintetizar esos hechos y la posible apelación."
  },
  "category": {
    "field_asks": "la categoría temática de la noticia, mapeada a uno de estos valores: JUDICIAL, DISASTER, HEALTH, ENVIRONMENT, POLITICS, ECONOMY, SCIENCE, CULTURE, SPORTS u OTHER.",
    "relevant_fragments": "\"condenó [...] a nueve años de prisión\", \"La sentencia\" y \"La Fiscalía Provincial de Valencia\".",
    "final_value": "Como los fragmentos relevantes tratan una condena, una sentencia y actuación fiscal, el valor del enum debe ser \"JUDICIAL\"."
  },
  "location": {
    "field_asks": "la ubicación geográfica donde ocurrió el evento, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"La sentencia sitúa la causa en Valencia, España\".",
    "final_value": "Como el fragmento relevante ubica la causa en Valencia, España, el valor debe ser \"Valencia, España\"."
  },
  "date": {
    "field_asks": "la fecha mencionada en el artículo, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"condenó el 15 de marzo de 2026\".",
    "final_value": "Como el fragmento relevante da una fecha completa de la condena, el valor debe ser \"15 de marzo de 2026\"."
  },
  "key_people": {
    "field_asks": "nombres de personas individuales clave mencionadas en el artículo.",
    "relevant_fragments": "\"Sofía Ledesma\" y \"El fiscal Rafael Orts\".",
    "final_value": "Como los fragmentos relevantes nombran a la condenada y al fiscal, la lista debe incluir \"Sofía Ledesma\" y \"Rafael Orts\"."
  },
  "key_organizations": {
    "field_asks": "nombres de organizaciones, empresas, instituciones o gobiernos mencionados.",
    "relevant_fragments": "\"Audiencia Provincial de Valencia\", \"Cuenta Clara\", \"Banco Marisma\" y \"Fiscalía Provincial de Valencia\".",
    "final_value": "Como los fragmentos relevantes nombran tribunal, plataforma, banco y fiscalía, la lista debe incluir esas organizaciones o entidades."
  },
  "casualties": {
    "field_asks": "número de muertes mencionadas, o null si no se menciona ninguna cifra de muertes humanas.",
    "relevant_fragments": "\"a nueve años de prisión\" y \"3 600 clientes perjudicados\".",
    "final_value": "Los fragmentos relevantes dan una pena y perjudicados económicos, pero no muertes humanas; el valor debe ser null."
  },
  "injured": {
    "field_asks": "número de personas heridas mencionadas, o null si no se menciona ninguna cifra de heridos humanos.",
    "relevant_fragments": "\"copiaba credenciales bancarias\" y \"ordena indemnizaciones individuales\".",
    "final_value": "Los fragmentos relevantes describen fraude económico e indemnizaciones, pero no lesiones personales; el valor debe ser null."
  },
  "affected_count": {
    "field_asks": "número de personas afectadas, perjudicadas o desplazadas, o null si no aplica o no hay cifra suficiente.",
    "relevant_fragments": "\"El fallo reconoce 3 600 clientes perjudicados\".",
    "final_value": "Como el fragmento relevante cuantifica clientes perjudicados por la estafa, el valor debe ser 3600."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# Dos agentes mueren en una redada contra la banda Los Cobres

Una redada realizada esta madrugada en el barrio Las Canteras, en Rosario, Argentina, terminó con dos agentes muertos y cinco personas heridas, entre ellas un vecino alcanzado por esquirlas. La Policía Federal Argentina informó que el operativo buscaba capturar a integrantes de Los Cobres, una banda investigada por extorsiones a transportistas y lavado de dinero.

La Fiscalía de Rosario señaló que se incautaron nueve armas, tres vehículos y cuadernos con anotaciones de cobros semanales. Ocho sospechosos fueron detenidos y trasladados a dependencias judiciales, mientras peritos revisaban una vivienda usada como depósito. El jefe del operativo declaró ante la prensa que la pesquisa continuará con el análisis de teléfonos y cámaras de seguridad de la zona.
```

`instruction`:

```text
Extrae la información estructurada de este artículo de noticias sobre un operativo policial, incluyendo el titular, resumen, categoría, ubicación, organizaciones clave, y cualquier cifra de víctimas o heridos mencionada.
```

`output`:

```json
{
  "headline": "Dos agentes mueren en una redada contra la banda Los Cobres",
  "summary": "Una redada realizada esta madrugada en el barrio Las Canteras, en Rosario, Argentina, terminó con dos agentes muertos y cinco personas heridas. La Policía Federal Argentina informó que el operativo buscaba capturar a integrantes de Los Cobres, investigada por extorsiones y lavado de dinero. La Fiscalía de Rosario señaló que se incautaron armas, vehículos y cuadernos, y ocho sospechosos fueron detenidos.",
  "category": "JUDICIAL",
  "location": "barrio Las Canteras, Rosario, Argentina",
  "date": null,
  "key_people": [],
  "key_organizations": [
    "Policía Federal Argentina",
    "Los Cobres",
    "Fiscalía de Rosario"
  ],
  "casualties": 2,
  "injured": 5,
  "affected_count": null
}
```

`reasoning`:

```json
{
  "headline": {
    "field_asks": "el titular principal del artículo de noticias.",
    "relevant_fragments": "\"# Dos agentes mueren en una redada contra la banda Los Cobres\".",
    "final_value": "Como el fragmento relevante es el encabezado principal, el titular debe ser \"Dos agentes mueren en una redada contra la banda Los Cobres\"."
  },
  "summary": {
    "field_asks": "un resumen breve de los hechos principales reportados, en 1-3 oraciones.",
    "relevant_fragments": "\"redada realizada esta madrugada [...] terminó con dos agentes muertos y cinco personas heridas\", \"buscaba capturar a integrantes de Los Cobres\" y \"Ocho sospechosos fueron detenidos\".",
    "final_value": "Como los fragmentos relevantes cubren operativo, víctimas, objetivo policial e incautaciones/detenciones, el resumen debe condensar esos puntos."
  },
  "category": {
    "field_asks": "la categoría temática de la noticia, mapeada a uno de estos valores: JUDICIAL, DISASTER, HEALTH, ENVIRONMENT, POLITICS, ECONOMY, SCIENCE, CULTURE, SPORTS u OTHER.",
    "relevant_fragments": "\"redada\", \"operativo\", \"banda investigada por extorsiones\" y \"dependencias judiciales\".",
    "final_value": "Como los fragmentos relevantes tratan un operativo policial y una investigación penal, el valor del enum debe ser \"JUDICIAL\"."
  },
  "location": {
    "field_asks": "la ubicación geográfica donde ocurrió el evento, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"en el barrio Las Canteras, en Rosario, Argentina\".",
    "final_value": "Como el fragmento relevante ubica la redada en el barrio Las Canteras, Rosario, Argentina, el valor debe ser \"barrio Las Canteras, Rosario, Argentina\"."
  },
  "date": {
    "field_asks": "la fecha mencionada en el artículo, o null si no hay evidencia suficiente.",
    "relevant_fragments": "\"esta madrugada\".",
    "final_value": "El fragmento relevante da una referencia temporal relativa, pero no una fecha absoluta; el valor debe ser null."
  },
  "key_people": {
    "field_asks": "nombres de personas individuales clave mencionadas en el artículo.",
    "relevant_fragments": "\"dos agentes\", \"un vecino\" y \"El jefe del operativo\".",
    "final_value": "Los fragmentos relevantes mencionan roles o personas genéricas sin nombres individuales; la lista debe ser vacía."
  },
  "key_organizations": {
    "field_asks": "nombres de organizaciones, empresas, instituciones o gobiernos mencionados.",
    "relevant_fragments": "\"Policía Federal Argentina\", \"Los Cobres\" y \"Fiscalía de Rosario\".",
    "final_value": "Como los fragmentos relevantes nombran una fuerza policial, una banda y una fiscalía, la lista debe incluir esas organizaciones."
  },
  "casualties": {
    "field_asks": "número de muertes mencionadas, o null si no se menciona ninguna cifra de muertes humanas.",
    "relevant_fragments": "\"terminó con dos agentes muertos\".",
    "final_value": "Como el fragmento relevante cuantifica dos muertes humanas, el valor debe ser 2."
  },
  "injured": {
    "field_asks": "número de personas heridas mencionadas, o null si no se menciona ninguna cifra de heridos humanos.",
    "relevant_fragments": "\"cinco personas heridas, entre ellas un vecino alcanzado por esquirlas\".",
    "final_value": "Como el fragmento relevante cuantifica cinco personas heridas, el valor debe ser 5."
  },
  "affected_count": {
    "field_asks": "número de personas afectadas, perjudicadas o desplazadas, o null si no aplica o no hay cifra suficiente.",
    "relevant_fragments": "\"Ocho sospechosos fueron detenidos\" y \"se incautaron nueve armas, tres vehículos\".",
    "final_value": "Los fragmentos relevantes dan detenidos e incautaciones, pero no una cifra de personas afectadas, perjudicadas o desplazadas; el valor debe ser null."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son noticias judiciales en Markdown: encabezado `# <titular>`, párrafos con condena, operativo o enfrentamiento, menciones a tribunales, fiscalías, policías, organizaciones criminales, víctimas y autoridades, y cifras que pueden ser penales, humanas o logísticas. Para los nuevos ejemplos conviene mantener crónicas breves de menos de 1600 caracteres, con cifras de distinta naturaleza para enseñar que años de prisión, detenidos, armas o vehículos no deben llenar automáticamente los campos de muertos, heridos o afectados.
