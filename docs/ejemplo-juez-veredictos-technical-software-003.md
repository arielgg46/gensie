# Ejemplo de prompt y schema de generación: `technical_software_003`

Este documento muestra cómo podría verse una llamada al juez con veredictos por
candidato para `data/dev_rev/technical_software_003.json`.

Es un ejemplo de visualización, no una traza real. Para que se vea el formato
completo, se asume que todos los campos del schema original están disputados y
que los candidatos vienen de tres trials válidos. En una ejecución real, el
`JudgeScope` reduciría el prompt y el schema solo a los campos efectivamente
disputados.

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
No inventes candidatos, no omitas slots requeridos y no uses conocimiento externo.
Cada candidate_value debe copiar exactamente el literal fijado por el schema.
```

### User

```text
TAREA DEL JUEZ:
Evalúa los candidatos observados para cada campo disputado y emite un veredicto estructurado.
Los conteos indican estabilidad entre trials, pero no reemplazan al grounding textual.
En `field`, explica qué pide el campo; no decidas el valor ahí.
En cada `candidate_value`, copia exactamente el valor del slot correspondiente.
En cada `evidence`, habla de la evidencia o ausencia de evidencia de ese candidato. Cita fragmentos verbatim con contexto. Usa `[...]` solo para marcar texto intermedio omitido dentro de una cita; no lo uses como prefijo o sufijo decorativo. No cites solo el literal del candidato: muestra el contexto donde se justifica aceptarlo o rechazarlo, y razona ahí mismo si el candidato debe ser el valor final, en campos simples, o si debe incluirse en el array final, en campos array.
Para arrays, decide `include=true` si el item debe entrar en el array final, o `false` si debe descartarse.
Los candidatos se presentan como slots obligatorios `#1`, `#2`, etc.; conserva esos nombres y no agregues slots.
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

# candidates es un objeto JSON con claves "#1", "#2", ...
# Cada slot corresponde a un candidato listado en VALORES CANDIDATOS POR CAMPO.
class SingleCandidate[T](BaseModel):
    candidate_value: T
    evidence: str

class ArrayCandidate[T](BaseModel):
    candidate_value: T
    evidence: str
    include: bool

class SingleVerdict[T](BaseModel):
    field: str
    candidates: dict[str, SingleCandidate[T]]
    value: T

class ArrayVerdict[T](BaseModel):
    field: str
    candidates: dict[str, ArrayCandidate[T]]

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
Valores candidatos:
- #1 (3/3): "VLC media player"
- #2 (1/3): "VLC"

CAMPO `app_category`
Formato: SingleVerdict[SoftwareType]
Valores candidatos:
- #1 (3/3): "MEDIA_PLAYER"
- #2 (1/3): "OTHER"

CAMPO `license`
Formato: SingleVerdict[str]
Valores candidatos:
- #1 (2/3): "GPLv2.1+"
- #2 (1/3): "GPL"

CAMPO `platforms` (lista)
Formato: ArrayVerdict[str]
Elementos candidatos:
- #1 (3/3): "GNU/Linux"
- #2 (3/3): "macOS"
- #3 (3/3): "Microsoft Windows"
- #4 (2/3): "BSD"
- #5 (2/3): "Solaris"
- #6 (2/3): "iOS"
- #7 (2/3): "Android"
- #8 (1/3): "Linux"
- #9 (1/3): "Windows"

CAMPO `primary_developer`
Formato: SingleVerdict[str]
Valores candidatos:
- #1 (2/3): "proyecto VideoLAN"
- #2 (1/3): "VideoLAN"

CAMPO `features` (lista)
Formato: ArrayVerdict[str]
Elementos candidatos:
- #1 (3/3): "Reproductor y framework multimedia"
- #2 (3/3): "Reproducir casi cualquier formato de vídeo sin necesidad de instalar códecs externos"
- #3 (2/3): "Reproducir vídeos en formatos DVD, Bluray, a resoluciones normales, en alta definición o incluso en ultra alta definición o 4K"
- #4 (2/3): "Capacidad de streaming"
- #5 (1/3): "Software libre"

CAMPO `exact_release_date`
Formato: SingleVerdict[Nullable[str]]
Valores candidatos:
- #1 (2/3): null
- #2 (1/3): "2001"

CAMPO `latest_stable_version_sha256`
Formato: SingleVerdict[Nullable[str]]
Valores candidatos:
- #1 (3/3): null
- #2 (1/3): "not mentioned"

CAMPO `current_ceo_name`
Formato: SingleVerdict[Nullable[str]]
Valores candidatos:
- #1 (3/3): null
- #2 (1/3): "Jean-Baptiste Kempf"
```

## Schema de generación

Este es el `response_format["json_schema"]["schema"]` para los candidatos
anteriores. Usa slots requeridos `"#1"`, `"#2"`, etc. y `enum` singleton en cada
`candidate_value`.

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "official_name": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "#1": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "string", "enum": ["VLC media player"] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            },
            "#2": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "string", "enum": ["VLC"] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            }
          },
          "required": ["#1", "#2"]
        },
        "value": {
          "type": "string",
          "enum": ["VLC media player", "VLC"]
        }
      },
      "required": ["field", "candidates", "value"]
    },
    "app_category": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "#1": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "string", "enum": ["MEDIA_PLAYER"] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            },
            "#2": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "string", "enum": ["OTHER"] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            }
          },
          "required": ["#1", "#2"]
        },
        "value": {
          "type": "string",
          "enum": ["MEDIA_PLAYER", "OTHER"]
        }
      },
      "required": ["field", "candidates", "value"]
    },
    "license": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "#1": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "string", "enum": ["GPLv2.1+"] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            },
            "#2": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "string", "enum": ["GPL"] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            }
          },
          "required": ["#1", "#2"]
        },
        "value": {
          "type": "string",
          "enum": ["GPLv2.1+", "GPL"]
        }
      },
      "required": ["field", "candidates", "value"]
    },
    "platforms": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "#1": { "$ref": "#/$defs/platform_GNU_Linux" },
            "#2": { "$ref": "#/$defs/platform_macOS" },
            "#3": { "$ref": "#/$defs/platform_Microsoft_Windows" },
            "#4": { "$ref": "#/$defs/platform_BSD" },
            "#5": { "$ref": "#/$defs/platform_Solaris" },
            "#6": { "$ref": "#/$defs/platform_iOS" },
            "#7": { "$ref": "#/$defs/platform_Android" },
            "#8": { "$ref": "#/$defs/platform_Linux" },
            "#9": { "$ref": "#/$defs/platform_Windows" }
          },
          "required": ["#1", "#2", "#3", "#4", "#5", "#6", "#7", "#8", "#9"]
        }
      },
      "required": ["field", "candidates"]
    },
    "primary_developer": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "#1": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "string", "enum": ["proyecto VideoLAN"] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            },
            "#2": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "string", "enum": ["VideoLAN"] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            }
          },
          "required": ["#1", "#2"]
        },
        "value": {
          "type": "string",
          "enum": ["proyecto VideoLAN", "VideoLAN"]
        }
      },
      "required": ["field", "candidates", "value"]
    },
    "features": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "#1": { "$ref": "#/$defs/feature_multimedia_framework" },
            "#2": { "$ref": "#/$defs/feature_no_external_codecs" },
            "#3": { "$ref": "#/$defs/feature_dvd_bluray_4k" },
            "#4": { "$ref": "#/$defs/feature_streaming" },
            "#5": { "$ref": "#/$defs/feature_free_software" }
          },
          "required": ["#1", "#2", "#3", "#4", "#5"]
        }
      },
      "required": ["field", "candidates"]
    },
    "exact_release_date": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "#1": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "null", "enum": [null] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            },
            "#2": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "string", "enum": ["2001"] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            }
          },
          "required": ["#1", "#2"]
        },
        "value": {
          "anyOf": [
            { "type": "null", "enum": [null] },
            { "type": "string", "enum": ["2001"] }
          ]
        }
      },
      "required": ["field", "candidates", "value"]
    },
    "latest_stable_version_sha256": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "#1": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "null", "enum": [null] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            },
            "#2": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "string", "enum": ["not mentioned"] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            }
          },
          "required": ["#1", "#2"]
        },
        "value": {
          "anyOf": [
            { "type": "null", "enum": [null] },
            { "type": "string", "enum": ["not mentioned"] }
          ]
        }
      },
      "required": ["field", "candidates", "value"]
    },
    "current_ceo_name": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "field": { "type": "string" },
        "candidates": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "#1": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "null", "enum": [null] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            },
            "#2": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "candidate_value": { "type": "string", "enum": ["Jean-Baptiste Kempf"] },
                "evidence": { "type": "string" }
              },
              "required": ["candidate_value", "evidence"]
            }
          },
          "required": ["#1", "#2"]
        },
        "value": {
          "anyOf": [
            { "type": "null", "enum": [null] },
            { "type": "string", "enum": ["Jean-Baptiste Kempf"] }
          ]
        }
      },
      "required": ["field", "candidates", "value"]
    }
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
    "platform_GNU_Linux": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["GNU/Linux"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "platform_macOS": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["macOS"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "platform_Microsoft_Windows": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["Microsoft Windows"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "platform_BSD": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["BSD"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "platform_Solaris": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["Solaris"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "platform_iOS": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["iOS"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "platform_Android": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["Android"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "platform_Linux": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["Linux"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "platform_Windows": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["Windows"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "feature_multimedia_framework": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["Reproductor y framework multimedia"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "feature_no_external_codecs": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["Reproducir casi cualquier formato de vídeo sin necesidad de instalar códecs externos"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "feature_dvd_bluray_4k": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["Reproducir vídeos en formatos DVD, Bluray, a resoluciones normales, en alta definición o incluso en ultra alta definición o 4K"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "feature_streaming": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["Capacidad de streaming"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    },
    "feature_free_software": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "candidate_value": { "type": "string", "enum": ["Software libre"] },
        "evidence": { "type": "string" },
        "include": { "type": "boolean" }
      },
      "required": ["candidate_value", "evidence", "include"]
    }
  }
}
```

## Forma esperada de respuesta

La respuesta tendría esta forma. Los textos de `evidence` son ilustrativos, pero
buscan enseñar el nivel deseado para un FSP: fragmento contextualizado,
`[...]` solo cuando se omite texto intermedio, y razonamiento explícito de
aceptación o rechazo.

```json
{
  "official_name": {
    "field": "El campo pide el nombre oficial completo del software descrito.",
    "candidates": {
      "#1": {
        "candidate_value": "VLC media player",
        "evidence": "Fragmentos: \"# VLC media player\" y \"VLC media player es un reproductor y framework multimedia\". El título y la oración inicial usan el literal completo para identificar el software descrito; por eso este candidato es el nombre oficial completo y debe ser el valor final."
      },
      "#2": {
        "candidate_value": "VLC",
        "evidence": "Fragmentos: \"# VLC media player\" y \"VLC es un reproductor de audio y vídeo\". El texto sí usa \"VLC\", pero lo hace después de presentar el nombre completo en el título; por eso este candidato funciona como abreviatura y no es tan fiel como nombre oficial completo."
      }
    },
    "value": "VLC media player"
  },
  "app_category": {
    "field": "El campo pide la categoría funcional principal de la aplicación.",
    "candidates": {
      "#1": {
        "candidate_value": "MEDIA_PLAYER",
        "evidence": "Fragmentos: \"VLC media player es un reproductor y framework multimedia\" y \"VLC es un reproductor de audio y vídeo\". Ambos pasajes describen la función principal como reproducción multimedia; por eso MEDIA_PLAYER captura la categoría funcional central."
      },
      "#2": {
        "candidate_value": "OTHER",
        "evidence": "Fragmentos revisados: \"VLC media player es un reproductor y framework multimedia\" y \"VLC es un reproductor de audio y vídeo\". El texto ya justifica una categoría específica de reproductor multimedia, así que OTHER sería una degradación innecesaria y debe rechazarse."
      }
    },
    "value": "MEDIA_PLAYER"
  }
}
```

En una salida real aparecerían todos los campos requeridos por el schema de
generación de arriba.
