# technical_extraction

Los tasks `technical_extraction` son extracciones L1 de un único fragmento verbatim desde textos técnicos: el modelo debe localizar la oración o subfrase que responde directamente a la pregunta, copiarla sin normalizar ni resumir, y evitar fragmentos cercanos que mencionan tecnologías, licencias, versiones o desarrolladores relacionados pero no responden exactamente la instrucción.

## Ejemplos revisados

- `data/dev_rev/technical_extraction_001.json`
- `data/dev_rev/technical_extraction_002.json`
- `data/dev_rev/technical_extraction_003.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `answer` | Requerido, `string`, no nullable. La dualidad útil es fragmento de oración frente a oración completa; en ambos casos debe ser verbatim. Conviene incluir distractores con tecnologías del mismo dominio para enseñar que la respuesta sale del contexto semántico pedido, no de cualquier término técnico destacado. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `answer` | Subfrase verbatim que responde el algoritmo de deduplicación, separada de otros algoritmos mencionados para compresión. | Oración completa verbatim que responde el motor de consultas, con un motor legado como distractor cercano. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# ArcZip

ArcZip es un archivador experimental para copias incrementales en servidores pequeños. La versión 4.2 cambió su índice de bloques y añadió verificación paralela de contenedores .azp. El manual aclara que LZMA queda reservado para la compresión final y que Zstandard se usa solo en paquetes temporales de red. En la sección de almacenamiento se lee: el motor deduplica bloques mediante el algoritmo BLAKE3-Rolling antes de escribir el contenedor definitivo. La herramienta también conserva un modo ZIP clásico para interoperar con clientes antiguos.
```

`instruction`:

```text
¿Qué algoritmo usa ArcZip para deduplicar bloques?
```

`output`:

```json
{
  "answer": "el motor deduplica bloques mediante el algoritmo BLAKE3-Rolling"
}
```

`reasoning`:

```json
{
  "answer": {
    "field_asks": "un único fragmento verbatim del texto que responda directamente la pregunta.",
    "relevant_fragments": "\"LZMA queda reservado para la compresión final\", \"Zstandard se usa solo en paquetes temporales de red\" y \"el motor deduplica bloques mediante el algoritmo BLAKE3-Rolling antes de escribir el contenedor definitivo\".",
    "final_value": "Como el fragmento relevante sobre deduplicación identifica BLAKE3-Rolling y los otros algoritmos se asignan a compresión o paquetes temporales, la respuesta debe copiar la subfrase \"el motor deduplica bloques mediante el algoritmo BLAKE3-Rolling\"."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# DeltaDB

DeltaDB es una base de datos embebida para series temporales industriales. Sus primeras versiones dependían de AtlasQL para ejecutar filtros simples, pero ese componente quedó limitado al importador de migraciones. Desde la versión 2.7, DeltaDB usa el motor QuasarSQL para planificar consultas sobre índices temporales. La capa de almacenamiento sigue escrita en Rust y el conector OPC-UA se publica como paquete separado para fabricantes que necesitan integración con sensores antiguos.
```

`instruction`:

```text
¿Qué motor usa DeltaDB para planificar consultas sobre índices temporales?
```

`output`:

```json
{
  "answer": "Desde la versión 2.7, DeltaDB usa el motor QuasarSQL para planificar consultas sobre índices temporales."
}
```

`reasoning`:

```json
{
  "answer": {
    "field_asks": "un único fragmento verbatim del texto que responda directamente la pregunta.",
    "relevant_fragments": "\"Sus primeras versiones dependían de AtlasQL para ejecutar filtros simples\" y \"Desde la versión 2.7, DeltaDB usa el motor QuasarSQL para planificar consultas sobre índices temporales.\".",
    "final_value": "Como el fragmento relevante distingue el motor legado AtlasQL del motor usado para planificar consultas, la respuesta debe copiar la oración completa sobre QuasarSQL."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son entradas técnicas en Markdown con encabezado `# <software>`, una definición breve, una o varias frases con desarrollador, motor, licencia, formato o características, y secciones de historia o características con tecnologías distractoras. Para los nuevos ejemplos conviene mantener textos compactos de menos de 1600 caracteres, introducir al menos un distractor técnico cercano y formular preguntas que se respondan con un fragmento verbatim inequívoco.
