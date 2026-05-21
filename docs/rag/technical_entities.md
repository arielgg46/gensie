# technical_entities

Los tasks `technical_entities` son extracciones L5 de entidades nombradas en textos técnicos, normalmente descripciones de software, formatos, motores, protocolos o proyectos: el modelo debe devolver una sola lista de menciones verbatim con su etiqueta, distinguir personas y organizaciones de productos o tecnologías, reconocer fechas y lugares cuando aparecen, y evitar convertir términos genéricos como "biblioteca", "repositorio" o "sistema operativo" en entidades si no son nombres propios.

## Ejemplos revisados

- `data/dev_rev/technical_entities_001.json`
- `data/dev_rev/technical_entities_002.json`
- `data/dev_rev/technical_entities_003.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `entities` | Array requerido de objetos `{text, label}`. La dualidad principal es lista amplia con varias categorías frente a lista más técnica dominada por `MISCELLANEOUS`. Puede incluir o no personas, organizaciones, fechas, lugares y eventos; no conviene forzar `[]` porque el task se define precisamente como reconocimiento de entidades nombradas. |
| `entities[].text` | Requerido, `string`, debe ser una mención verbatim del texto. Dualidad entre nombre completo, sigla, versión, protocolo o alias; se debe evitar normalizar, traducir o fusionar menciones diferentes. |
| `entities[].label` | Enum requerido. Debe mapear a uno de estos valores: `PERSON`, `ORGANIZATION`, `LOCATION`, `DATE`, `EVENT` o `MISCELLANEOUS`. En textos técnicos, software, formatos, motores, protocolos, versiones y nombres de módulos suelen caer en `MISCELLANEOUS`, mientras proyectos o fundaciones pueden ser `ORGANIZATION`. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `entities` | Lista de entidades nombradas presentes en el texto técnico. Extrae menciones concretas y propias; no incluyas términos genéricos como “biblioteca”, “formato”, “repositorio”, “sistema operativo” o “motor” salvo que formen parte de un nombre propio. |
| `entities[].text` | Mención verbatim tal como aparece en el texto. Conserva mayúsculas, tildes, números, versiones, guiones y siglas; no traduzcas, normalices, expandas ni fusiones menciones distintas como nombre completo y alias si aparecen separadas. |
| `entities[].label` | Etiqueta de la entidad; enum completo: `PERSON`, `ORGANIZATION`, `LOCATION`, `DATE`, `EVENT` o `MISCELLANEOUS`. Personas individuales son `PERSON`; proyectos, fundaciones y empresas son `ORGANIZATION`; ciudades o lugares son `LOCATION`; fechas explícitas son `DATE`; conferencias o eventos nombrados son `EVENT`; software, protocolos, formatos, motores, módulos, versiones y algoritmos suelen ser `MISCELLANEOUS`. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `entities` | Lista rica: persona, organización, fechas, evento, ubicación y tecnologías. | Lista sin personas, fechas ni eventos; organización, ubicación y tecnologías como contraste. |
| `entities[].text` | Menciones verbatim con versiones y nombres propios: `Nube Clara 2.0`, `Inés Lobo`, `Fundación BitÁgora`, `12 de junio de 2025`, etc. | Menciones verbatim de controlador, empresa, firmware, protocolos y herramientas: `Sierra-IX`, `DeltaBus`, `Modbus TCP`, etc. |
| `entities[].label` | Cubre los seis labels del enum, incluyendo `EVENT` para una conferencia nombrada. | Predominan `MISCELLANEOUS`, con `ORGANIZATION` y `LOCATION`, para no enseñar que siempre deben aparecer personas o fechas. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Nube Clara 2.0

Nube Clara 2.0 es una biblioteca de sincronización de archivos creada por Inés Lobo y mantenida por la Fundación BitÁgora. En 2024 reemplazó su cola interna por PostgreSQL y añadió un operador para Kubernetes. Durante la OpenInfra Summit celebrada en Madrid el 12 de junio de 2025, la ponente presentó Río, un módulo compatible con S3 y WebDAV para copias incrementales. La nota también menciona GitLab como repositorio espejo, pero aclara que el paquete principal se publica con firma Ed25519.
```

`instruction`:

```text
Extrae las entidades nombradas del texto técnico y clasifícalas por tipo.
```

`output`:

```json
{
  "entities": [
    {
      "text": "Nube Clara 2.0",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Inés Lobo",
      "label": "PERSON"
    },
    {
      "text": "Fundación BitÁgora",
      "label": "ORGANIZATION"
    },
    {
      "text": "2024",
      "label": "DATE"
    },
    {
      "text": "PostgreSQL",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Kubernetes",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "OpenInfra Summit",
      "label": "EVENT"
    },
    {
      "text": "Madrid",
      "label": "LOCATION"
    },
    {
      "text": "12 de junio de 2025",
      "label": "DATE"
    },
    {
      "text": "Río",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "S3",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "WebDAV",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "GitLab",
      "label": "ORGANIZATION"
    },
    {
      "text": "Ed25519",
      "label": "MISCELLANEOUS"
    }
  ]
}
```

`reasoning`:

```json
{
  "entities": {
    "field_asks": "lista de menciones de entidades nombradas con su etiqueta, usando exactamente uno de estos valores para cada label: PERSON, ORGANIZATION, LOCATION, DATE, EVENT o MISCELLANEOUS.",
    "relevant_fragments": "\"Nube Clara 2.0 [...] creada por Inés Lobo y mantenida por la Fundación BitÁgora\", \"En 2024 reemplazó su cola interna por PostgreSQL y añadió un operador para Kubernetes\", \"Durante la OpenInfra Summit celebrada en Madrid el 12 de junio de 2025\" y \"presentó Río, un módulo compatible con S3 y WebDAV [...] GitLab [...] Ed25519\".",
    "final_value": "Como los fragmentos relevantes nombran una persona, una organización mantenedora, dos fechas, un evento, una ubicación y varios productos, protocolos o identificadores técnicos, la lista debe conservar esas menciones verbatim y etiquetarlas con el enum correspondiente."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# Controlador Sierra-IX

El controlador Sierra-IX de Orbis Automation se usa en estaciones de bombeo y ejecuta el firmware DeltaBus sobre Linux o FreeRTOS. La guía técnica describe perfiles Modbus TCP, exportación a Prometheus y plantillas de despliegue para Ansible. En el banco de pruebas de Valencia, el equipo instaló el paquete Hydra-Bridge para traducir mensajes entre MQTT y CANopen. El texto compara el modelo ACME-R2 como hardware anterior, pero lo trata como referencia de compatibilidad.
```

`instruction`:

```text
Extrae las entidades nombradas del texto técnico y clasifícalas por tipo.
```

`output`:

```json
{
  "entities": [
    {
      "text": "Sierra-IX",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Orbis Automation",
      "label": "ORGANIZATION"
    },
    {
      "text": "DeltaBus",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Linux",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "FreeRTOS",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Modbus TCP",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Prometheus",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Ansible",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Valencia",
      "label": "LOCATION"
    },
    {
      "text": "Hydra-Bridge",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "MQTT",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "CANopen",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "ACME-R2",
      "label": "MISCELLANEOUS"
    }
  ]
}
```

`reasoning`:

```json
{
  "entities": {
    "field_asks": "lista de menciones de entidades nombradas con su etiqueta, usando exactamente uno de estos valores para cada label: PERSON, ORGANIZATION, LOCATION, DATE, EVENT o MISCELLANEOUS.",
    "relevant_fragments": "\"Sierra-IX de Orbis Automation [...] firmware DeltaBus sobre Linux o FreeRTOS\", \"perfiles Modbus TCP, exportación a Prometheus y plantillas de despliegue para Ansible\" y \"banco de pruebas de Valencia [...] Hydra-Bridge [...] MQTT y CANopen [...] ACME-R2\".",
    "final_value": "Como los fragmentos relevantes nombran una empresa, una ubicación y varias tecnologías, firmwares, protocolos o modelos, la lista debe incluir esas menciones verbatim; al no haber nombres de personas, fechas absolutas ni eventos nombrados, no se añaden entidades de esos labels."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son fragmentos enciclopédicos o resúmenes técnicos en Markdown: encabezado `# <software o tecnología>`, una primera frase definitoria, mención de desarrolladores, proyectos u organizaciones, y después formatos, motores, protocolos, sistemas operativos o fechas históricas. Para los nuevos ejemplos conviene mantener textos breves de menos de 1600 caracteres, con nombres propios mezclados con términos genéricos, versiones y siglas técnicas, de modo que el modelo aprenda a extraer solo menciones nombradas y a etiquetar tecnologías como `MISCELLANEOUS` cuando no son personas, organizaciones, lugares, fechas ni eventos.
