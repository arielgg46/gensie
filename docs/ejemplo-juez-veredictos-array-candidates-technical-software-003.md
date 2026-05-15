# Ejemplo de prompt y schema de generación con `candidates` como array: `technical_software_003`

Este documento muestra cómo podría verse una llamada al juez con veredictos por
candidato para `data/dev_rev/technical_software_003.json`, usando un enfoque más
compacto que representa `candidates` como un array de objetos.

Es un ejemplo de visualización, no una traza real. Para que se vea el formato
completo, se asume que todos los campos del schema original están disputados y
que los candidatos vienen de tres trials válidos. En una ejecución real, el
`JudgeScope` reduciría el prompt y el schema solo a los campos efectivamente
disputados.

La diferencia principal frente al enfoque con slots `"#1"`, `"#2"`, etc. es que
el schema de generación ya no enumera cada candidato. La lista exacta de
candidatos vive en el prompt, y el validador local comprueba después que el
modelo devolvió la misma cantidad, en el mismo orden y con los mismos
`candidate_value`.

## Instancia base

`id`: `technical_software_003`

`instruction`:

```text
Resume los datos técnicos de VLC, centrándote en su tipo de software, desarrollador y plataformas soportadas.
```

`input_text`:

```text
# VLC media player

VLC media player es un reproductor y framework multimedia, libre y de código abierto desarrollado por el proyecto VideoLAN. Es un programa multiplataforma con versiones disponibles para muchos sistemas operativos, es capaz de reproducir casi cualquier formato de vídeo sin necesidad de instalar códecs externos y puede reproducir vídeos en formatos DVD, Bluray, a resoluciones normales, en alta definición o incluso en ultra alta definición o 4K.
VLC es un reproductor de audio y vídeo capaz de reproducir muchos códecs y formatos de audio y vídeo, además de capacidad de streaming. Es software libre, distribuido bajo la licencia GPLv2.1+.​ [...] Es un reproductor portable y multiplataforma, con versiones para GNU/Linux, macOS, Microsoft Windows, BSD, Solaris, iOS y Android, entre otros.​​
```

## Candidatos supuestos

Estos candidatos son plausibles para ilustrar el formato:

- `official_name`: `"VLC media player"`, `"VLC"`
- `app_category`: `"MEDIA_PLAYER"`, `"OTHER"`
- `license`: `"GPLv2.1+"`, `"GPL"`
- `platforms`: `"GNU/Linux"`, `"macOS"`, `"Microsoft Windows"`, `"BSD"`, `"Solaris"`, `"iOS"`, `"Android"`, `"Linux"`, `"Windows"`
- `primary_developer`: `"proyecto VideoLAN"`, `"VideoLAN"`
- `features`: `"Reproductor y framework multimedia"`, `"Reproducir casi cualquier formato de vídeo sin necesidad de instalar códecs externos"`, `"Reproducir vídeos en formatos DVD, Bluray, a resoluciones normales, en alta definición o incluso en ultra alta definición o 4K"`, `"Capacidad de streaming"`, `"Software libre"`
- `exact_release_date`: `null`, `"2001"`
- `latest_stable_version_sha256`: `null`, `"not mentioned"`
- `current_ceo_name`: `null`, `"Jean-Baptiste Kempf"`

## Prompt

### System

```text
Eres un juez experto de extracción de información en español.
Recibes varios intentos de extracción, campos disputados y candidatos observados.
Devuelve veredictos estructurados por candidato usando solo el texto fuente.
No inventes candidatos, no omitas candidatos y no uses conocimiento externo.
Cada candidate_value debe copiar exactamente el literal indicado en el prompt,
en el mismo orden en que aparece para su campo.
```

### User

```text
TAREA DEL JUEZ:
Evalúa los candidatos observados para cada campo disputado y emite un veredicto estructurado.
Los conteos indican estabilidad entre trials, pero no reemplazan al grounding textual.
En `field`, explica qué pide el campo; no decidas el valor ahí.
En cada `candidates`, devuelve un array con exactamente un objeto por candidato listado, en el mismo orden.
En cada `candidate_value`, copia exactamente el valor candidato correspondiente.
En cada `evidence`, habla de la evidencia o ausencia de evidencia de ese candidato. Cita fragmentos verbatim con contexto. Usa `[...]` solo para marcar texto intermedio omitido dentro de una cita; no lo uses como prefijo o sufijo decorativo. No cites solo el literal del candidato: muestra el contexto donde se justifica aceptarlo o rechazarlo, y razona ahí mismo si el candidato debe ser el valor final, en campos simples, o si debe incluirse en el array final, en campos array.
Para campos simples, después de `candidates` decide `value` con el valor final.
Para campos array, decide `include=true` si el item debe entrar en el array final, o `false` si debe descartarse.
El schema de generación solo valida la forma; la lista de candidatos válida está en este prompt y será validada después de la llamada.
Si la mayoría contradice el texto fuente o inventa información, corrige hacia el texto o usa null cuando el schema lo permita.

INSTRUCCIÓN ORIGINAL:
Resume los datos técnicos de VLC, centrándote en su tipo de software, desarrollador y plataformas soportadas.

INSTRUCCIÓN DEL JUEZ:
Emite veredictos solo para estos campos: `official_name`, `app_category`, `license`, `platforms`, `primary_developer`, `features`, `exact_release_date`, `latest_stable_version_sha256`, `current_ceo_name`.

SCHEMA PYDANTIC DE VEREDICTOS:
Nullable[T] = T | None

class SoftwareType(str, Enum):
    ARCHIVER = "ARCHIVER"
    WEB_BROWSER = "WEB_BROWSER"
    OFFICE_SUITE = "OFFICE_SUITE"
    IDE_EDITOR = "IDE_EDITOR"
    GRAPHICS_EDITOR = "GRAPHICS_EDITOR"
    MEDIA_PLAYER = "MEDIA_PLAYER"
    SYSTEM_TOOL = "SYSTEM_TOOL"
    OTHER = "OTHER"

# candidates es una lista ordenada.
# Debe tener exactamente un item por candidato listado en VALORES CANDIDATOS POR CAMPO.
class SingleCandidate[T](BaseModel):
    candidate_value: T
    evidence: str

class ArrayCandidate[T](BaseModel):
    candidate_value: T
    evidence: str
    include: bool

class SingleVerdict[T](BaseModel):
    field: str
    candidates: list[SingleCandidate[T]]
    value: T

class ArrayVerdict[T](BaseModel):
    field: str
    candidates: list[ArrayCandidate[T]]

class Output(BaseModel):
    official_name: SingleVerdict[str] = Field(
        description="The full official name of the software"
    )
    app_category: SingleVerdict[SoftwareType] = Field(
        description="The primary functional category of the app"
    )
    license: SingleVerdict[str] = Field(
        description="The specific license mentioned (e.g., GPL, Proprietary)"
    )
    platforms: ArrayVerdict[str] = Field(
        description="Operating systems mentioned as supported (e.g., Windows, macOS, Linux)"
    )
    primary_developer: SingleVerdict[str] = Field(
        description="The individual or organization that developed the software"
    )
    features: ArrayVerdict[str] = Field(
        description="List of specific technical capabilities or features mentioned"
    )
    exact_release_date: SingleVerdict[Nullable[str]] = Field(
        description="The EXACT date (DD/MM/YYYY) of the first release. RETURN NULL IF ONLY THE YEAR IS MENTIONED."
    )
    latest_stable_version_sha256: SingleVerdict[Nullable[str]] = Field(
        description="The SHA256 checksum of the latest installer. RETURN NULL IF NOT EXPLICITLY IN THE TEXT."
    )
    current_ceo_name: SingleVerdict[Nullable[str]] = Field(
        description="The name of the current CEO of the developing organization. RETURN NULL IF NOT IN TEXT."
    )

TEXTO FUENTE:
# VLC media player

VLC media player es un reproductor y framework multimedia, libre y de código abierto desarrollado por el proyecto VideoLAN. Es un programa multiplataforma con versiones disponibles para muchos sistemas operativos, es capaz de reproducir casi cualquier formato de vídeo sin necesidad de instalar códecs externos y puede reproducir vídeos en formatos DVD, Bluray, a resoluciones normales, en alta definición o incluso en ultra alta definición o 4K.
VLC es un reproductor de audio y vídeo capaz de reproducir muchos códecs y formatos de audio y vídeo, además de capacidad de streaming. Es software libre, distribuido bajo la licencia GPLv2.1+.​ [...] Es un reproductor portable y multiplataforma, con versiones para GNU/Linux, macOS, Microsoft Windows, BSD, Solaris, iOS y Android, entre otros.​​

VALORES CANDIDATOS POR CAMPO:
Trials válidos: 3

CAMPO `official_name`
Formato: SingleVerdict[str]
Valores candidatos, en este orden:
1. (3/3): "VLC media player"
2. (1/3): "VLC"

CAMPO `app_category`
Formato: SingleVerdict[SoftwareType]
Valores candidatos, en este orden:
1. (3/3): "MEDIA_PLAYER"
2. (1/3): "OTHER"

CAMPO `license`
Formato: SingleVerdict[str]
Valores candidatos, en este orden:
1. (2/3): "GPLv2.1+"
2. (1/3): "GPL"

CAMPO `platforms` (lista)
Formato: ArrayVerdict[str]
Elementos candidatos, en este orden:
1. (3/3): "GNU/Linux"
2. (3/3): "macOS"
3. (3/3): "Microsoft Windows"
4. (2/3): "BSD"
5. (2/3): "Solaris"
6. (2/3): "iOS"
7. (2/3): "Android"
8. (1/3): "Linux"
9. (1/3): "Windows"

CAMPO `primary_developer`
Formato: SingleVerdict[str]
Valores candidatos, en este orden:
1. (2/3): "proyecto VideoLAN"
2. (1/3): "VideoLAN"

CAMPO `features` (lista)
Formato: ArrayVerdict[str]
Elementos candidatos, en este orden:
1. (3/3): "Reproductor y framework multimedia"
2. (3/3): "Reproducir casi cualquier formato de vídeo sin necesidad de instalar códecs externos"
3. (2/3): "Reproducir vídeos en formatos DVD, Bluray, a resoluciones normales, en alta definición o incluso en ultra alta definición o 4K"
4. (2/3): "Capacidad de streaming"
5. (1/3): "Software libre"

CAMPO `exact_release_date`
Formato: SingleVerdict[Nullable[str]]
Valores candidatos, en este orden:
1. (2/3): null
2. (1/3): "2001"

CAMPO `latest_stable_version_sha256`
Formato: SingleVerdict[Nullable[str]]
Valores candidatos, en este orden:
1. (3/3): null
2. (1/3): "not mentioned"

CAMPO `current_ceo_name`
Formato: SingleVerdict[Nullable[str]]
Valores candidatos, en este orden:
1. (3/3): null
2. (1/3): "Jean-Baptiste Kempf"
```

## Schema de generación

Este es el `response_format["json_schema"]["schema"]` para la misma instancia,
pero sin codificar los candidatos concretos dentro del schema. No usa
`prefixItems`, `const`, `minItems` ni `maxItems`.

La versión está escrita con `$defs` para enseñar la forma compacta. Si un
backend no resolviera `$ref`/`$defs`, estas definiciones se podrían inlinear de
forma mecánica y seguiría siendo mucho más pequeño que el diseño con slots por
candidato.

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "official_name": { "$ref": "#/$defs/SingleStringVerdict" },
    "app_category": { "$ref": "#/$defs/SingleSoftwareTypeVerdict" },
    "license": { "$ref": "#/$defs/SingleStringVerdict" },
    "platforms": { "$ref": "#/$defs/ArrayStringVerdict" },
    "primary_developer": { "$ref": "#/$defs/SingleStringVerdict" },
    "features": { "$ref": "#/$defs/ArrayStringVerdict" },
    "exact_release_date": { "$ref": "#/$defs/SingleNullableStringVerdict" },
    "latest_stable_version_sha256": { "$ref": "#/$defs/SingleNullableStringVerdict" },
    "current_ceo_name": { "$ref": "#/$defs/SingleNullableStringVerdict" }
  },
  "required": [
    "official_name",
    "app_category",
    "license",
    "platforms",
    "primary_developer",
    "features",
    "exact_release_date",
    "latest_stable_version_sha256",
    "current_ceo_name"
  ],
  "$defs": {
    "SingleStringVerdict": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "array",
          "items": { "$ref": "#/$defs/SingleStringCandidate" }
        },
        "value": { "type": "string" }
      },
      "required": ["field", "candidates", "value"]
    },
    "SingleNullableStringVerdict": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "array",
          "items": { "$ref": "#/$defs/SingleNullableStringCandidate" }
        },
        "value": {
          "anyOf": [
            { "type": "string" },
            { "type": "null" }
          ]
        }
      },
      "required": ["field", "candidates", "value"]
    },
    "SingleSoftwareTypeVerdict": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "array",
          "items": { "$ref": "#/$defs/SingleSoftwareTypeCandidate" }
        },
        "value": { "$ref": "#/$defs/SoftwareType" }
      },
      "required": ["field", "candidates", "value"]
    },
    "ArrayStringVerdict": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "array",
          "items": { "$ref": "#/$defs/ArrayStringCandidate" }
        }
      },
      "required": ["field", "candidates"]
    },
    "SingleStringCandidate": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string" },
        "evidence": { "type": "string" }
      },
      "required": ["candidate_value", "evidence"]
    },
    "SingleNullableStringCandidate": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": {
          "anyOf": [
            { "type": "string" },
            { "type": "null" }
          ]
        },
        "evidence": { "type": "string" }
      },
      "required": ["candidate_value", "evidence"]
    },
    "SingleSoftwareTypeCandidate": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "$ref": "#/$defs/SoftwareType" },
        "evidence": { "type": "string" }
      },
      "required": ["candidate_value", "evidence"]
    },
    "ArrayStringCandidate": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string" },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "SoftwareType": {
      "type": "string",
      "enum": [
        "ARCHIVER",
        "WEB_BROWSER",
        "OFFICE_SUITE",
        "IDE_EDITOR",
        "GRAPHICS_EDITOR",
        "MEDIA_PLAYER",
        "SYSTEM_TOOL",
        "OTHER"
      ]
    }
  }
}
```

## Validación posterior necesaria

Como el schema no fija los candidatos concretos, el parser local debe validar
cada campo contra la lista del prompt:

1. `len(response[field].candidates)` debe ser igual a la cantidad esperada.
2. Cada `candidate_value` debe coincidir exactamente con el candidato esperado
   en la misma posición.
3. En campos `SingleVerdict[T]`, `value` debe coincidir exactamente con uno de
   los candidatos esperados para ese campo.
4. En campos `ArrayVerdict[T]`, el valor final se reconstruye con los candidatos
   que tengan `include=true`.
5. Si alguna regla falla, se puede hacer retry con un prompt de reparación o
   caer al agregador anterior.

Este enfoque sacrifica la garantía dura del decoder sobre cantidad, orden y
valores concretos, pero reduce mucho el tamaño del schema. La restricción pasa
de generación a validación local.

## Forma esperada de respuesta

La respuesta tendría esta forma. Los textos de `evidence` son ilustrativos, pero
buscan enseñar el nivel deseado para un FSP: fragmento contextualizado,
`[...]` solo cuando se omite texto intermedio, y razonamiento explícito de
aceptación o rechazo.

```json
{
  "official_name": {
    "field": "El campo pide el nombre oficial completo del software descrito.",
    "candidates": [
      {
        "candidate_value": "VLC media player",
        "evidence": "Fragmentos: \"# VLC media player\" y \"VLC media player es un reproductor y framework multimedia\". El título y la oración inicial usan el literal completo para identificar el software descrito; por eso este candidato es el nombre oficial completo y debe ser el valor final."
      },
      {
        "candidate_value": "VLC",
        "evidence": "Fragmentos: \"# VLC media player\" y \"VLC es un reproductor de audio y vídeo\". El texto sí usa \"VLC\", pero lo hace después de presentar el nombre completo en el título; por eso este candidato funciona como abreviatura y no es tan fiel como nombre oficial completo."
      }
    ],
    "value": "VLC media player"
  },
  "app_category": {
    "field": "El campo pide la categoría funcional principal de la aplicación.",
    "candidates": [
      {
        "candidate_value": "MEDIA_PLAYER",
        "evidence": "Fragmentos: \"VLC media player es un reproductor y framework multimedia\" y \"VLC es un reproductor de audio y vídeo\". Ambos pasajes describen la función principal como reproducción multimedia; por eso MEDIA_PLAYER captura la categoría funcional central."
      },
      {
        "candidate_value": "OTHER",
        "evidence": "Fragmentos revisados: \"VLC media player es un reproductor y framework multimedia\" y \"VLC es un reproductor de audio y vídeo\". El texto ya justifica una categoría específica de reproductor multimedia, así que OTHER sería una degradación innecesaria y debe rechazarse."
      }
    ],
    "value": "MEDIA_PLAYER"
  },
  "platforms": {
    "field": "El campo pide los sistemas operativos mencionados como soportados.",
    "candidates": [
      {
        "candidate_value": "GNU/Linux",
        "evidence": "Fragmento: \"VLC [...] Es un reproductor portable y multiplataforma, con versiones para GNU/Linux, macOS, Microsoft Windows, BSD, Solaris, iOS y Android, entre otros\". GNU/Linux aparece dentro de la enumeración explícita de plataformas con versiones disponibles; debe incluirse.",
        "include": true
      },
      {
        "candidate_value": "macOS",
        "evidence": "Fragmento: \"VLC [...] Es un reproductor portable y multiplataforma, con versiones para [...] macOS [...]\". macOS aparece en la lista de sistemas con versiones disponibles, así que pertenece al array final.",
        "include": true
      },
      {
        "candidate_value": "Microsoft Windows",
        "evidence": "Fragmento: \"VLC [...] Es un reproductor portable y multiplataforma, con versiones para [...] Microsoft Windows [...]\". Microsoft Windows aparece explícitamente en la lista de plataformas con versiones disponibles; debe incluirse.",
        "include": true
      },
      {
        "candidate_value": "BSD",
        "evidence": "Fragmento: \"VLC [...] Es un reproductor portable y multiplataforma, con versiones para [...] BSD [...]\". BSD aparece como uno de los sistemas con versiones disponibles y debe incluirse.",
        "include": true
      },
      {
        "candidate_value": "Solaris",
        "evidence": "Fragmento: \"VLC [...] Es un reproductor portable y multiplataforma, con versiones para [...] Solaris [...]\". Solaris aparece explícitamente en la enumeración de plataformas; debe incluirse.",
        "include": true
      },
      {
        "candidate_value": "iOS",
        "evidence": "Fragmento: \"VLC [...] Es un reproductor portable y multiplataforma, con versiones para [...] iOS [...]\". iOS aparece en la lista de versiones disponibles y debe incluirse.",
        "include": true
      },
      {
        "candidate_value": "Android",
        "evidence": "Fragmento: \"VLC [...] Es un reproductor portable y multiplataforma, con versiones para [...] Android, entre otros\". Android aparece en la enumeración de plataformas soportadas y debe incluirse.",
        "include": true
      },
      {
        "candidate_value": "Linux",
        "evidence": "Fragmento revisado: \"VLC [...] con versiones para GNU/Linux, macOS, Microsoft Windows, BSD, Solaris, iOS y Android, entre otros\". La evidencia textual da el literal \"GNU/Linux\", no \"Linux\" aislado; incluir ambos duplicaría la misma plataforma y reduciría la fidelidad literal, así que este candidato debe descartarse.",
        "include": false
      },
      {
        "candidate_value": "Windows",
        "evidence": "Fragmento revisado: \"VLC [...] con versiones para GNU/Linux, macOS, Microsoft Windows, BSD, Solaris, iOS y Android, entre otros\". La mención explícita es \"Microsoft Windows\"; \"Windows\" es una normalización más corta, pero el candidato más fiel ya está presente, así que este item debe descartarse para evitar duplicación.",
        "include": false
      }
    ]
  }
}
```

En una salida real aparecerían todos los campos requeridos por el schema de
generación de arriba.
