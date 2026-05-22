# technical_software

Los tasks `technical_software` son extracciones L9 de descripciones de aplicaciones con trampas adversariales de null: el modelo debe identificar nombre oficial, tipo funcional, licencia, plataformas, desarrollador y rasgos técnicos, pero abstenerse en campos como fecha exacta de primer lanzamiento, SHA256 del instalador o CEO actual si el texto solo da años, versiones, roles no equivalentes o conocimiento externo.

## Ejemplos revisados

- `data/dev_rev/technical_software_003.json`
- `data/dev_rev/technical_software_006.json`
- `data/dev/technical_software_008.json`
- `data/dev/technical_software_010.json`
- `data/dev/technical_software_013.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `official_name` | Requerido, `string`, no nullable. Dualidad entre título directo en encabezado y nombre oficial desarrollado en el cuerpo con alias o abreviatura. |
| `app_category` | Enum requerido. Debe mapear a uno de estos valores: `ARCHIVER`, `WEB_BROWSER`, `OFFICE_SUITE`, `IDE_EDITOR`, `GRAPHICS_EDITOR`, `MEDIA_PLAYER`, `SYSTEM_TOOL` u `OTHER`. Conviene alternar categorías frecuentes como reproductor/editor con otras menos vistas como archivador o herramienta de sistema. |
| `license` | Requerido, `string`, no nullable. En los ejemplos revisados predominan licencias libres nombradas (`GPLv2.1+`, `GPL`, `GNU LGPL`, `MPL` o nombre completo de GPL); la dualidad más fiel a `dev` es entre abreviatura y nombre explícito de licencia. Aunque el schema admite `Proprietary`, no vi un task similar de `dev` donde el output use "software propietario"; conviene reservarlo para un caso futuro si aparece en ejemplos curados. |
| `platforms` | `[]` vs lista poblada. En los ejemplos revisados suele estar poblada con sistemas operativos. Conviene un caso con plataformas explícitas y otro donde se mencionen instaladores o dispositivos sin nombrar sistemas operativos. |
| `primary_developer` | Requerido, `string`, no nullable. Dualidad entre organización desarrolladora y persona fundadora/líder cuando el texto la presenta como responsable principal. |
| `features` | `[]` vs lista poblada. Debe incluir capacidades técnicas mencionadas, preferentemente verbatim o casi verbatim; si el texto solo da historia, licencia y checksum, puede quedar vacío. |
| `exact_release_date` | `string` `DD/MM/YYYY` vs `null`. Trampa central: si solo aparece año, mes o fecha de versión posterior, debe ser `null`; si aparece fecha exacta de primer lanzamiento, se normaliza. |
| `latest_stable_version_sha256` | `string` vs `null`. Solo debe poblarse si el texto da explícitamente un SHA256 del instalador estable más reciente; hashes de commit, firmas PGP o checksum de versión beta no aplican. |
| `current_ceo_name` | `string` vs `null`. Solo debe poblarse si el texto dice explícitamente que alguien es CEO actual de la organización desarrolladora; fundador, mantenedor, creador o líder del proyecto no basta. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `official_name` | Nombre oficial del software. Usa el encabezado si ya es el nombre formal, o el nombre completo del cuerpo cuando el encabezado sea una abreviatura o alias; no mezcles siglas históricas con el nombre actual. |
| `app_category` | Categoría funcional principal; enum completo: `ARCHIVER`, `WEB_BROWSER`, `OFFICE_SUITE`, `IDE_EDITOR`, `GRAPHICS_EDITOR`, `MEDIA_PLAYER`, `SYSTEM_TOOL` u `OTHER`. Decide por la función descrita (archivador, navegador, suite ofimática, editor/IDE, editor gráfico, reproductor, herramienta de sistema) y usa `OTHER` solo si no encaja claramente. |
| `license` | Licencia específica mencionada, preferiblemente literal (`GPLv2.1+`, `GNU LGPL`, `MPL 2.0`). No inventes licencia desde “software libre” si no aparece una formulación suficiente, y no uses licencias de plugins, formatos o proyectos relacionados como licencia de la aplicación principal. |
| `platforms` | Sistemas operativos o plataformas soportadas nombradas explícitamente. No pobles la lista con “instaladores”, “paquetes”, repositorios, dispositivos genéricos o historia de desarrollo si no se nombran sistemas como GNU/Linux, macOS, Windows, BSD, iOS, Android, etc. |
| `primary_developer` | Persona, comunidad, proyecto u organización que desarrolla el software. Diferencia creador histórico, coordinador, organización sin ánimo de lucro y empresa; elige quien el texto presenta como responsable principal del desarrollo. |
| `features` | Capacidades técnicas mencionadas, en frases breves y fieles al texto. Extrae funciones como reproducción, streaming, compresión, edición, formatos o herramientas; no incluyas historia, licencia, plataformas, checksum ni cargos corporativos como features. |
| `exact_release_date` | Fecha exacta del primer lanzamiento en `DD/MM/YYYY`. Devuelve `null` SI SOLO HAY año, versión posterior, fecha de liberación de código distinta del primer lanzamiento o referencias relativas sin día/mes/año completos. |
| `latest_stable_version_sha256` | SHA256 del instalador estable más reciente, solo si el texto lo dice explícitamente. Devuelve `null` para hashes de commit, firmas PGP, checksums de nightly/beta, identificadores cortos o valores sin relación con el instalador estable. |
| `current_ceo_name` | Nombre del CEO actual de la organización desarrolladora, solo si se afirma explícitamente. Fundador, creador, mantenedor, líder del proyecto, presidente de fundación o coordinador técnico no necesariamente equivalen a CEO actual. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `official_name` | Nombre oficial directo en encabezado y primera oración. | Encabezado abreviado con nombre oficial completo en el cuerpo. |
| `app_category` | `IDE_EDITOR`, por editor de código. | `ARCHIVER`, por compresor/gestor de archivos. |
| `license` | Licencia libre específica, por ejemplo `MPL 2.0`. | Otra licencia libre nombrada, por ejemplo `GNU LGPL`, para seguir el estilo observado en `dev`. |
| `platforms` | Lista poblada con varios sistemas operativos. | `[]`, con instaladores mencionados sin sistemas operativos concretos. |
| `primary_developer` | Organización o comunidad desarrolladora. | Empresa desarrolladora con CEO explícito. |
| `features` | Lista poblada con capacidades técnicas. | `[]`, si el texto habla de release, distribución y checksum pero no enumera capacidades. |
| `exact_release_date` | `null`, porque solo aparece el año de origen o una versión posterior. | Valor no null, fecha exacta de primer lanzamiento normalizada a `DD/MM/YYYY`. |
| `latest_stable_version_sha256` | `null`, por ausencia de checksum explícito o por hash no aplicable. | Valor no null con SHA256 explícito del instalador estable. |
| `current_ceo_name` | `null`, porque hay fundador/mantenedor pero no CEO actual. | Valor no null con CEO actual nombrado explícitamente. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Lince Editor

Lince Editor es un editor de código y entorno ligero de desarrollo creado por la comunidad Lince Tools. El proyecto nació en 2017 como complemento para revisar scripts y las primeras compilaciones públicas circularon al año siguiente en el repositorio de extensiones.

Es software libre distribuido bajo la licencia MPL 2.0 y cuenta con versiones para GNU/Linux, macOS y Microsoft Windows. El sitio de descargas conserva firmas PGP de paquetes antiguos y el identificador de commit 8f4c9e2 de una compilación nightly.

== Características ==
Entre sus características se citan resaltado de sintaxis, terminal integrada, búsqueda por expresiones regulares y sincronización de espacios de trabajo mediante archivos de configuración.

== Historia ==
La página histórica atribuye la idea original a Mateo Salvat, que revisa cambios mayores, y señala que la coordinación cotidiana corresponde al equipo de Lince Tools.
```

`instruction`:

```text
Analiza la descripción del software para extraer detalles técnicos, desarrolladores y licencias.
```

`output`:

```json
{
  "official_name": "Lince Editor",
  "app_category": "IDE_EDITOR",
  "license": "MPL 2.0",
  "platforms": [
    "GNU/Linux",
    "macOS",
    "Microsoft Windows"
  ],
  "primary_developer": "Lince Tools",
  "features": [
    "resaltado de sintaxis",
    "terminal integrada",
    "búsqueda por expresiones regulares",
    "sincronización de espacios de trabajo mediante archivos de configuración"
  ],
  "exact_release_date": null,
  "latest_stable_version_sha256": null,
  "current_ceo_name": null
}
```

`reasoning`:

```json
{
  "official_name": {
    "field_asks": "el nombre oficial completo del software.",
    "relevant_fragments": "\"# Lince Editor\" y \"Lince Editor es un editor de código\".",
    "final_value": "Como los fragmentos relevantes presentan \"Lince Editor\" como nombre principal del software, el valor debe ser \"Lince Editor\"."
  },
  "app_category": {
    "field_asks": "la categoría funcional principal de la aplicación, mapeada a uno de estos valores: ARCHIVER, WEB_BROWSER, OFFICE_SUITE, IDE_EDITOR, GRAPHICS_EDITOR, MEDIA_PLAYER, SYSTEM_TOOL u OTHER.",
    "relevant_fragments": "\"es un editor de código y entorno ligero de desarrollo\".",
    "final_value": "Como el fragmento relevante describe un editor de código y entorno de desarrollo, el valor del enum debe ser \"IDE_EDITOR\"."
  },
  "license": {
    "field_asks": "la licencia específica mencionada para el software.",
    "relevant_fragments": "\"Es software libre distribuido bajo la licencia MPL 2.0\".",
    "final_value": "Como el fragmento relevante nombra explícitamente la licencia, el valor debe ser \"MPL 2.0\"."
  },
  "platforms": {
    "field_asks": "sistemas operativos mencionados como soportados.",
    "relevant_fragments": "\"cuenta con versiones para GNU/Linux, macOS y Microsoft Windows\".",
    "final_value": "Como el fragmento relevante enumera sistemas operativos soportados, la lista debe incluir \"GNU/Linux\", \"macOS\" y \"Microsoft Windows\"."
  },
  "primary_developer": {
    "field_asks": "la persona u organización que desarrolló el software.",
    "relevant_fragments": "\"creado por la comunidad Lince Tools\" y \"la coordinación cotidiana corresponde al equipo de Lince Tools\".",
    "final_value": "Como los fragmentos relevantes atribuyen el desarrollo a Lince Tools, el desarrollador principal debe ser \"Lince Tools\"."
  },
  "features": {
    "field_asks": "capacidades técnicas o funciones específicas mencionadas.",
    "relevant_fragments": "\"== Características ==\nEntre sus características se citan resaltado de sintaxis, terminal integrada, búsqueda por expresiones regulares y sincronización de espacios de trabajo mediante archivos de configuración\".",
    "final_value": "Como el fragmento relevante introduce una sección de características y enumera capacidades técnicas concretas, la lista debe conservar los cuatro rasgos verbatim: \"resaltado de sintaxis\", \"terminal integrada\", \"búsqueda por expresiones regulares\" y \"sincronización de espacios de trabajo mediante archivos de configuración\"."
  },
  "exact_release_date": {
    "field_asks": "la fecha exacta del primer lanzamiento en formato DD/MM/YYYY, o null si solo se menciona el año.",
    "relevant_fragments": "\"El proyecto nació en 2017\" y \"las primeras compilaciones públicas circularon al año siguiente\".",
    "final_value": "Como los fragmentos relevantes solo dan un año de inicio y una referencia relativa al año siguiente, sin día y mes del primer lanzamiento, el valor debe ser null."
  },
  "latest_stable_version_sha256": {
    "field_asks": "el checksum SHA256 del instalador estable más reciente, o null si no está explícitamente en el texto.",
    "relevant_fragments": "\"firmas PGP de paquetes antiguos\" y \"el identificador de commit 8f4c9e2 de una compilación nightly\".",
    "final_value": "Como los fragmentos relevantes apuntan a firmas PGP antiguas y a un identificador de commit de una compilación nightly, no a un SHA256 del instalador estable más reciente, el valor debe ser null."
  },
  "current_ceo_name": {
    "field_asks": "el nombre del CEO actual de la organización desarrolladora, o null si no está explícitamente en el texto.",
    "relevant_fragments": "\"atribuye la idea original a Mateo Salvat\" y \"la coordinación cotidiana corresponde al equipo de Lince Tools\".",
    "final_value": "Como los fragmentos relevantes presentan a Mateo Salvat como autor de la idea y al equipo como coordinador, sin nombrar CEO actual de Lince Tools, el valor debe ser null."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# QPack

QPack es el nombre abreviado usado en foros para QuantaPack Pro, un archivador de ficheros desarrollado por Aster Labs. El formato QPK fue diseñado por Bruno Kehl y se popularizó en repositorios internos de documentación técnica.

== Historia ==
El primer lanzamiento público de QuantaPack Pro se realizó el 04 de marzo de 2019 durante la feria DataTools. Desde la rama 5.4, Aster Labs distribuye el programa bajo la licencia GNU LGPL. El portal de clientes agrupa instaladores firmados, notas de migración y paquetes antiguos en un archivo de descargas.

Para verificar la descarga estable 5.4, la ficha publica el SHA256 del instalador: 9f2a7b1c4d6e8f00112233445566778899aabbccddeeff001122334455667788. En el aviso corporativo de 2024, Aster Labs identifica a Marina Soler como CEO actual de la compañía desarrolladora.
```

`instruction`:

```text
Resume los datos técnicos de QPack, centrándote en su tipo de software, desarrollador y plataformas soportadas.
```

`output`:

```json
{
  "official_name": "QuantaPack Pro",
  "app_category": "ARCHIVER",
  "license": "GNU LGPL",
  "platforms": [],
  "primary_developer": "Aster Labs",
  "features": [],
  "exact_release_date": "04/03/2019",
  "latest_stable_version_sha256": "9f2a7b1c4d6e8f00112233445566778899aabbccddeeff001122334455667788",
  "current_ceo_name": "Marina Soler"
}
```

`reasoning`:

```json
{
  "official_name": {
    "field_asks": "el nombre oficial completo del software.",
    "relevant_fragments": "\"QPack es el nombre abreviado usado en foros para QuantaPack Pro\".",
    "final_value": "Como el fragmento relevante distingue la abreviatura del nombre completo, el nombre oficial debe ser \"QuantaPack Pro\"."
  },
  "app_category": {
    "field_asks": "la categoría funcional principal de la aplicación, mapeada a uno de estos valores: ARCHIVER, WEB_BROWSER, OFFICE_SUITE, IDE_EDITOR, GRAPHICS_EDITOR, MEDIA_PLAYER, SYSTEM_TOOL u OTHER.",
    "relevant_fragments": "\"QuantaPack Pro, un archivador de ficheros\".",
    "final_value": "Como el fragmento relevante describe el software como archivador, el valor del enum debe ser \"ARCHIVER\"."
  },
  "license": {
    "field_asks": "la licencia específica mencionada para el software.",
    "relevant_fragments": "\"Aster Labs distribuye el programa bajo la licencia GNU LGPL\".",
    "final_value": "Como el fragmento relevante nombra explícitamente la licencia, el valor debe ser \"GNU LGPL\"."
  },
  "platforms": {
    "field_asks": "sistemas operativos mencionados como soportados.",
    "relevant_fragments": "\"El portal de clientes agrupa instaladores firmados, notas de migración y paquetes antiguos en un archivo de descargas\".",
    "final_value": "Como el fragmento relevante habla de instaladores y descargas, pero no nombra ningún sistema operativo soportado como Windows, macOS o Linux, la lista debe ser vacía."
  },
  "primary_developer": {
    "field_asks": "la persona u organización que desarrolló el software.",
    "relevant_fragments": "\"un archivador de ficheros desarrollado por Aster Labs\".",
    "final_value": "Como el fragmento relevante atribuye el desarrollo a Aster Labs, el desarrollador principal debe ser \"Aster Labs\"."
  },
  "features": {
    "field_asks": "capacidades técnicas o funciones específicas mencionadas.",
    "relevant_fragments": "\"un archivador de ficheros desarrollado por Aster Labs\", \"El formato QPK fue diseñado por Bruno Kehl\" y \"El portal de clientes agrupa instaladores firmados, notas de migración y paquetes antiguos\".",
    "final_value": "Como los fragmentos relevantes permiten clasificar la aplicación y ubicar su formato, distribución e historia, pero no enumeran capacidades técnicas específicas como compresión, cifrado, integración con el sistema o formatos soportados, la lista debe ser vacía."
  },
  "exact_release_date": {
    "field_asks": "la fecha exacta del primer lanzamiento en formato DD/MM/YYYY, o null si solo se menciona el año.",
    "relevant_fragments": "\"El primer lanzamiento público de QuantaPack Pro se realizó el 04 de marzo de 2019\".",
    "final_value": "Como el fragmento relevante da una fecha exacta de primer lanzamiento, debe normalizarse a \"04/03/2019\"."
  },
  "latest_stable_version_sha256": {
    "field_asks": "el checksum SHA256 del instalador estable más reciente, o null si no está explícitamente en el texto.",
    "relevant_fragments": "\"Para verificar la descarga estable 5.4, la ficha publica el SHA256 del instalador: 9f2a7b1c4d6e8f00112233445566778899aabbccddeeff001122334455667788\".",
    "final_value": "Como el fragmento relevante da explícitamente el SHA256 del instalador estable, el valor debe ser \"9f2a7b1c4d6e8f00112233445566778899aabbccddeeff001122334455667788\"."
  },
  "current_ceo_name": {
    "field_asks": "el nombre del CEO actual de la organización desarrolladora, o null si no está explícitamente en el texto.",
    "relevant_fragments": "\"Aster Labs identifica a Marina Soler como CEO actual de la compañía desarrolladora\".",
    "final_value": "Como el fragmento relevante identifica explícitamente a Marina Soler como CEO actual, el valor debe ser \"Marina Soler\"."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son entradas técnicas en Markdown de estilo enciclopédico, normalmente con encabezado `# <software>`, párrafos descriptivos y, en algunos casos, secciones como `== Historia ==` o `== Características ==`; los casos curados más cortos usan recortes con `[...]`. Suelen mezclar definición funcional, licencia, desarrollador, plataformas y capacidades con trampas de ausencia como años sin fecha exacta, hashes que no son SHA256 de instalador estable, fundadores que no son CEO y plataformas no nombradas. En los ejemplos revisados no aparece un output propietario, sino licencias libres nombradas, por lo que los nuevos ejemplos mantienen esa línea y evitan frases que anuncien la ausencia de un campo.
