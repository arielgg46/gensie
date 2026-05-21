# medical_extraction

Los tasks `medical_extraction` son extracciones literales L1 sobre fragmentos de fichas médicas o farmacéuticas, casi siempre de secciones CIMA de composición cualitativa y cuantitativa: el modelo recibe una pregunta puntual y debe copiar exactamente el fragmento que la responde, preservando unidades, comas decimales, dos puntos, punto final y formulaciones como aparecen en el texto, sin normalizar cantidades ni resumirlas.

## Ejemplos revisados

- `data/dev_rev/medical_extraction_001.json`
- `data/dev_rev/medical_extraction_002.json`
- `data/dev_rev/medical_extraction_003.json`

Solo existen tres ejemplos del prefijo en `dev_rev` y `data/dev` contiene las
mismas instancias; no hay más fuentes disponibles del prefijo para llegar a
cinco.

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `answer` | Campo requerido, `string`, no nullable. No hay dualidad `null`/valor ni `[]`/lista; la dualidad útil es tipo de fragmento verbatim: frase introductoria corta con dos puntos vs oración completa con cantidad y unidad; fragmento único claro vs fragmento elegido entre líneas casi repetidas; cantidad de principio activo vs cantidad de excipiente; mantener literal con coma decimal, unidad y puntuación vs tentación de normalizar o recortar. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `answer` | Frase introductoria corta que termina en dos puntos, por ejemplo una línea tipo `Cada ampolla de 2 ml contiene:`. El texto debería incluir otra línea parecida para otra presentación o concentración, de modo que el modelo tenga que seleccionar la frase exacta pedida. | Oración completa con cantidad, unidad y punto final, por ejemplo una línea de excipiente tipo `Cada comprimido contiene 18 mg de lactosa monohidrato.`. El texto debería incluir cantidades de principio activo cercanas para evitar que el modelo devuelva solo el número o la sustancia equivocada. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `answer` | Fragmento literal que responde la pregunta. Copia la línea completa y exacta, incluyendo dos puntos, punto final, coma decimal, unidad y nombre de la presentación o sustancia; no normalices cantidades, no devuelvas solo el número y no confundas presentaciones cercanas como 500 mg vs 650 mg o principio activo vs excipiente. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# 1. NOMBRE DEL MEDICAMENTO

Glucosal 50 mg/ml solución inyectable

Glucosal 100 mg/ml solución inyectable

# 2. COMPOSICIÓN CUALITATIVA Y CUANTITATIVA

Cada ampolla de 2 ml de Glucosal 50 mg/ml contiene:

Glucosa monohidrato ............... 110 mg (equivalentes a 100 mg de glucosa).

Cada ampolla de 5 ml de Glucosal 100 mg/ml contiene:

Glucosa monohidrato ............... 550 mg (equivalentes a 500 mg de glucosa).

Excipientes: cloruro de sodio, agua para preparaciones inyectables y ácido clorhídrico para ajuste de pH.

Para consultar la lista completa de excipientes, ver sección 6.1.
```

`instruction`:

```text
¿Qué frase inicia la composición de la ampolla de 5 ml de Glucosal 100 mg/ml?
```

`output`:

```json
{
  "answer": "Cada ampolla de 5 ml de Glucosal 100 mg/ml contiene:"
}
```

`reasoning`:

```json
{
  "answer": {
    "field_asks": "el fragmento verbatim del texto que responde a la pregunta.",
    "relevant_fragments": "\"Cada ampolla de 5 ml de Glucosal 100 mg/ml contiene:\"",
    "final_value": "Como el fragmento relevante coincide con la presentación preguntada, debe copiarse verbatim: \"Cada ampolla de 5 ml de Glucosal 100 mg/ml contiene:\"."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# 2. COMPOSICIÓN CUALITATIVA Y CUANTITATIVA

Cada comprimido recubierto contiene 500 mg de metamizol magnésico.

Excipientes con efecto conocido

Cada comprimido contiene 18 mg de lactosa monohidrato.

Cada comprimido contiene 0,45 mg de amarillo anaranjado S (E-110).

Para consultar la lista completa de excipientes, ver sección 6.1.

# 3. FORMA FARMACÉUTICA

Comprimido recubierto con película.

Comprimidos redondos, biconvexos, de color amarillo pálido y con ranura por una cara.
```

`instruction`:

```text
¿Cuánta lactosa monohidrato contiene cada comprimido?
```

`output`:

```json
{
  "answer": "Cada comprimido contiene 18 mg de lactosa monohidrato."
}
```

`reasoning`:

```json
{
  "answer": {
    "field_asks": "el fragmento verbatim del texto que responde a la pregunta.",
    "relevant_fragments": "\"# 2. COMPOSICIÓN CUALITATIVA Y CUANTITATIVA [...] Cada comprimido contiene 18 mg de lactosa monohidrato.\"",
    "final_value": "Como el fragmento relevante da la cantidad de lactosa monohidrato pedida, debe copiarse la oración completa verbatim: \"Cada comprimido contiene 18 mg de lactosa monohidrato.\"."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados tienen forma de ficha técnica en Markdown: encabezados numerados como `# 1. NOMBRE DEL MEDICAMENTO`, `# 2. COMPOSICIÓN CUALITATIVA Y CUANTITATIVA` o `# 3. FORMA FARMACÉUTICA`; líneas de composición separadas por saltos de línea; nombres de medicamentos o presentaciones similares; cantidades con unidades (`mg`, `ml`, `g`) y coma decimal; y frases repetidas del tipo `Cada comprimido... contiene:` o `Cada mililitro... contiene:`. La respuesta debe ser un fragmento literal suficiente para responder la pregunta, normalmente una línea completa, no una normalización ni una explicación.
