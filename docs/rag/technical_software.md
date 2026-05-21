# technical_software

Los tasks `technical_software` son extracciones L9 de descripciones de aplicaciones con trampas adversariales de null: el modelo debe identificar nombre oficial, tipo funcional, licencia, plataformas, desarrollador y rasgos técnicos, pero abstenerse en campos como fecha exacta de primer lanzamiento, SHA256 del instalador o CEO actual si el texto solo da años, versiones, roles no equivalentes o conocimiento externo.

## Ejemplos revisados

- `data/dev_rev/technical_software_003.json`
- `data/dev_rev/technical_software_006.json`
- `data/dev/technical_software_008.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `official_name` | Requerido, `string`, no nullable. Dualidad entre título directo en encabezado y nombre oficial desarrollado en el cuerpo con alias o abreviatura. |
| `app_category` | Enum requerido. Debe mapear a uno de estos valores: `ARCHIVER`, `WEB_BROWSER`, `OFFICE_SUITE`, `IDE_EDITOR`, `GRAPHICS_EDITOR`, `MEDIA_PLAYER`, `SYSTEM_TOOL` u `OTHER`. Conviene alternar categorías frecuentes como reproductor/editor con otras menos vistas como archivador o herramienta de sistema. |
| `license` | Requerido, `string`, no nullable. Dualidad entre licencia libre específica (`GPLv2.1+`, `MPL 2.0`, `MIT`) y licencia propietaria explícita. No debe inferirse desde "gratuito" o "código abierto" sin nombre de licencia si el campo pide licencia específica. |
| `platforms` | `[]` vs lista poblada. En los ejemplos revisados suele estar poblada con sistemas operativos. Conviene un caso con plataformas explícitas y otro donde se mencionen instaladores o dispositivos sin nombrar sistemas operativos. |
| `primary_developer` | Requerido, `string`, no nullable. Dualidad entre organización desarrolladora y persona fundadora/líder cuando el texto la presenta como responsable principal. |
| `features` | `[]` vs lista poblada. Debe incluir capacidades técnicas mencionadas, preferentemente verbatim o casi verbatim; si el texto solo da historia, licencia y checksum, puede quedar vacío. |
| `exact_release_date` | `string` `DD/MM/YYYY` vs `null`. Trampa central: si solo aparece año, mes o fecha de versión posterior, debe ser `null`; si aparece fecha exacta de primer lanzamiento, se normaliza. |
| `latest_stable_version_sha256` | `string` vs `null`. Solo debe poblarse si el texto da explícitamente un SHA256 del instalador estable más reciente; hashes de commit, firmas PGP o checksum de versión beta no aplican. |
| `current_ceo_name` | `string` vs `null`. Solo debe poblarse si el texto dice explícitamente que alguien es CEO actual de la organización desarrolladora; fundador, mantenedor, creador o líder del proyecto no basta. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `official_name` | Nombre oficial directo en encabezado y primera oración. | Encabezado abreviado con nombre oficial completo en el cuerpo. |
| `app_category` | `IDE_EDITOR`, por editor de código. | `ARCHIVER`, por compresor/gestor de archivos. |
| `license` | Licencia libre específica, por ejemplo `MPL 2.0`. | Licencia propietaria explícita. |
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

Lince Editor es un editor de código y entorno ligero de desarrollo creado por la comunidad Lince Tools. El proyecto comenzó en 2017 como un complemento para revisar scripts, pero la primera versión pública solo se describe en las notas como "la serie inicial de 2018".

El programa se distribuye como software libre bajo la licencia MPL 2.0. Tiene versiones para GNU/Linux, macOS y Microsoft Windows. Entre sus capacidades se mencionan resaltado de sintaxis, terminal integrada, búsqueda por expresiones regulares y sincronización de espacios de trabajo mediante archivos de configuración.

La página histórica atribuye la idea original a Mateo Salvat y señala que sigue revisando cambios mayores, aunque la gestión diaria depende del equipo de Lince Tools. El sitio de descargas muestra firmas PGP para algunos paquetes antiguos y un hash de commit de la rama nightly, pero no publica SHA256 del instalador estable.
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
    "relevant_fragments": "\"se distribuye como software libre bajo la licencia MPL 2.0\".",
    "final_value": "Como el fragmento relevante nombra explícitamente la licencia, el valor debe ser \"MPL 2.0\"."
  },
  "platforms": {
    "field_asks": "sistemas operativos mencionados como soportados.",
    "relevant_fragments": "\"Tiene versiones para GNU/Linux, macOS y Microsoft Windows\".",
    "final_value": "Como el fragmento relevante enumera sistemas operativos soportados, la lista debe incluir \"GNU/Linux\", \"macOS\" y \"Microsoft Windows\"."
  },
  "primary_developer": {
    "field_asks": "la persona u organización que desarrolló el software.",
    "relevant_fragments": "\"creado por la comunidad Lince Tools\" y \"la gestión diaria depende del equipo de Lince Tools\".",
    "final_value": "Como los fragmentos relevantes atribuyen el desarrollo a Lince Tools, el desarrollador principal debe ser \"Lince Tools\"."
  },
  "features": {
    "field_asks": "capacidades técnicas o funciones específicas mencionadas.",
    "relevant_fragments": "\"resaltado de sintaxis, terminal integrada, búsqueda por expresiones regulares y sincronización de espacios de trabajo mediante archivos de configuración\".",
    "final_value": "Como el fragmento relevante enumera capacidades técnicas, la lista debe conservar esos cuatro rasgos."
  },
  "exact_release_date": {
    "field_asks": "la fecha exacta del primer lanzamiento en formato DD/MM/YYYY, o null si solo se menciona el año.",
    "relevant_fragments": "\"comenzó en 2017\" y \"la primera versión pública solo se describe [...] como \\\"la serie inicial de 2018\\\"\".",
    "final_value": "Los fragmentos relevantes dan años y una serie inicial, pero no una fecha exacta de primer lanzamiento; el valor debe ser null."
  },
  "latest_stable_version_sha256": {
    "field_asks": "el checksum SHA256 del instalador estable más reciente, o null si no está explícitamente en el texto.",
    "relevant_fragments": "\"firmas PGP para algunos paquetes antiguos\" y \"un hash de commit de la rama nightly\".",
    "final_value": "Los fragmentos relevantes mencionan firmas PGP y un hash de commit nightly, pero no un SHA256 del instalador estable más reciente; el valor debe ser null."
  },
  "current_ceo_name": {
    "field_asks": "el nombre del CEO actual de la organización desarrolladora, o null si no está explícitamente en el texto.",
    "relevant_fragments": "\"atribuye la idea original a Mateo Salvat\" y \"sigue revisando cambios mayores\".",
    "final_value": "Los fragmentos relevantes presentan a Mateo Salvat como creador o revisor, no como CEO actual; el valor debe ser null."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# QPack

QPack es el nombre abreviado usado en foros para QuantaPack Pro, un archivador comercial desarrollado por Aster Labs. La ficha técnica de la versión estable 5.4 lo describe como software propietario y recuerda que su primer lanzamiento público se hizo el 04 de marzo de 2019 durante la feria DataTools.

La nota de publicación no enumera sistemas operativos: solo indica que los instaladores se entregan desde el portal de clientes y que los paquetes antiguos quedaron en el archivo privado. Tampoco detalla funciones nuevas, más allá de corregir errores de la rama 5.3.

Para verificar la descarga estable, Aster Labs publicó el SHA256 del instalador: 9f2a7b1c4d6e8f00112233445566778899aabbccddeeff001122334455667788. En el mismo aviso corporativo se identifica a Marina Soler como CEO actual de Aster Labs y a Bruno Kehl como responsable histórico del formato QPK.
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
  "license": "software propietario",
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
    "relevant_fragments": "\"QuantaPack Pro, un archivador comercial\".",
    "final_value": "Como el fragmento relevante describe el software como archivador, el valor del enum debe ser \"ARCHIVER\"."
  },
  "license": {
    "field_asks": "la licencia específica mencionada para el software.",
    "relevant_fragments": "\"lo describe como software propietario\".",
    "final_value": "Como el fragmento relevante da la licencia o régimen de distribución explícito, el valor debe ser \"software propietario\"."
  },
  "platforms": {
    "field_asks": "sistemas operativos mencionados como soportados.",
    "relevant_fragments": "\"La nota de publicación no enumera sistemas operativos\" y \"los instaladores se entregan desde el portal de clientes\".",
    "final_value": "Los fragmentos relevantes hablan de instaladores, pero no nombran sistemas operativos soportados; la lista debe ser vacía."
  },
  "primary_developer": {
    "field_asks": "la persona u organización que desarrolló el software.",
    "relevant_fragments": "\"un archivador comercial desarrollado por Aster Labs\".",
    "final_value": "Como el fragmento relevante atribuye el desarrollo a Aster Labs, el desarrollador principal debe ser \"Aster Labs\"."
  },
  "features": {
    "field_asks": "capacidades técnicas o funciones específicas mencionadas.",
    "relevant_fragments": "\"Tampoco detalla funciones nuevas, más allá de corregir errores de la rama 5.3\".",
    "final_value": "El fragmento relevante no enumera capacidades técnicas del software, solo una corrección genérica de errores; la lista debe ser vacía."
  },
  "exact_release_date": {
    "field_asks": "la fecha exacta del primer lanzamiento en formato DD/MM/YYYY, o null si solo se menciona el año.",
    "relevant_fragments": "\"su primer lanzamiento público se hizo el 04 de marzo de 2019\".",
    "final_value": "Como el fragmento relevante da una fecha exacta de primer lanzamiento, debe normalizarse a \"04/03/2019\"."
  },
  "latest_stable_version_sha256": {
    "field_asks": "el checksum SHA256 del instalador estable más reciente, o null si no está explícitamente en el texto.",
    "relevant_fragments": "\"Aster Labs publicó el SHA256 del instalador: 9f2a7b1c4d6e8f00112233445566778899aabbccddeeff001122334455667788\".",
    "final_value": "Como el fragmento relevante da explícitamente el SHA256 del instalador estable, el valor debe ser \"9f2a7b1c4d6e8f00112233445566778899aabbccddeeff001122334455667788\"."
  },
  "current_ceo_name": {
    "field_asks": "el nombre del CEO actual de la organización desarrolladora, o null si no está explícitamente en el texto.",
    "relevant_fragments": "\"se identifica a Marina Soler como CEO actual de Aster Labs\".",
    "final_value": "Como el fragmento relevante identifica explícitamente a Marina Soler como CEO actual, el valor debe ser \"Marina Soler\"."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son entradas técnicas breves en Markdown, con encabezado `# <software>`, uno o varios párrafos descriptivos y a veces fragmentos elididos con `[...]`; suelen mezclar definición funcional, licencia, desarrollador, plataformas y capacidades con trampas de ausencia como años sin fecha exacta, hashes que no son SHA256 de instalador estable, fundadores que no son CEO y plataformas no nombradas. Los nuevos ejemplos mantienen esa forma, con textos de menos de 1600 caracteres y evidencia natural para decidir cuándo extraer y cuándo devolver `null` o `[]`.
