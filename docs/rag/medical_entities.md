# medical_entities

Los tasks `medical_entities` son extracciones L5 de menciones nombradas en fragmentos de fichas técnicas farmacéuticas, especialmente medicamentos CIMA. El modelo debe devolver una única lista `entities` con menciones verbatim y etiqueta semántica, tratando medicamentos, principios activos, excipientes, formas farmacéuticas y códigos como `MISCELLANEOUS`, laboratorios y agencias como `ORGANIZATION`, direcciones o países como `LOCATION`, y meses/fechas de autorización o revisión como `DATE`.

## Ejemplos revisados

- `data/dev_rev/medical_entities_001.json`
- `data/dev_rev/medical_entities_002.json`
- `data/dev/medical_entities_001.json`
- `data/dev/medical_entities_002.json`

Solo existen dos ejemplos del prefijo en `dev_rev` y los dos archivos de `data/dev` repiten esas instancias con salidas menos curadas; no hay cinco ejemplos disponibles sin salir del prefijo.

## Dualidad por campo

| Campo | Opinion sobre dualidad |
| --- | --- |
| `entities` | Array de objetos. Dualidad principal entre lista densa de sustancias farmacéuticas, todas `MISCELLANEOUS`, y lista mixta con medicamento, laboratorio, ubicaciones, fechas y organismo regulador. En los ejemplos revisados siempre hay entidades; no conviene forzar `[]` porque el prefijo se construye sobre fragmentos ricos de ficha técnica. |
| `entities[].text` | Debe conservar la mención verbatim, incluyendo dosis, forma farmacéutica, códigos E, paréntesis y dirección si forman parte de la mención. Dualidad entre sustancias simples (`Cafeína`) y menciones largas con concentración o paréntesis (`sorbitol líquido no cristalizable (E-420)`). |
| `entities[].label` | Enum requerido. En este prefijo los valores naturales revisados son `MISCELLANEOUS`, `ORGANIZATION`, `LOCATION` y `DATE`. `PERSON` y `EVENT` existen en el schema genérico, pero no aparecen en las fichas técnicas revisadas; forzarlos cambiaría el estilo del prefijo. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `entities` | Lista única de menciones nombradas explícitas en la ficha técnica. Incluye medicamentos, principios activos, excipientes, códigos, laboratorios, agencias, direcciones, países y fechas cuando aparecen; evita extraer encabezados, números de sección, enlaces genéricos o entidades inferidas desde conocimiento externo. |
| `entities[].text` | Mención verbatim tomada del texto, con tildes, mayúsculas/minúsculas, dosis, barras, paréntesis, códigos E, siglas y formas legales tal como figuran. Prefiere la mención completa curada, por ejemplo medicamento con concentración, excipiente con código o organismo con sigla; no atomices direcciones o nombres técnicos salvo que la fuente los presente separados. |
| `entities[].label` | Etiqueta del enum completo: `PERSON`, `ORGANIZATION`, `LOCATION`, `DATE`, `EVENT` o `MISCELLANEOUS`. En fichas CIMA, medicamentos, sustancias, formas farmacéuticas y códigos suelen ser `MISCELLANEOUS`; laboratorios y agencias `ORGANIZATION`; direcciones, localidades y países `LOCATION`; meses o fechas de autorización/revisión `DATE`. Usa `PERSON` o `EVENT` solo si una persona o evento aparece explícitamente, no por forzar cobertura. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `entities` | Lista densa de medicamento, principios activos, excipientes y analgésico comparador; casi todo `MISCELLANEOUS`. | Lista administrativa con medicamento, laboratorio, dirección, localidad/país, fechas y agencia reguladora. |
| `entities[].text` | Menciones con unidades y códigos E, manteniendo paréntesis y concentraciones. | Menciones largas de dirección y organismo con sigla, más fechas mes-año. |
| `entities[].label` | Contraste entre nombre completo de medicamento y sustancias, todas como `MISCELLANEOUS`. | Contraste `ORGANIZATION`, `LOCATION`, `DATE` y `MISCELLANEOUS`. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
FICHA TECNICA ACETILSALICILICO/ CAFEINA ROVI 500 mg + 30 mg COMPRIMIDOS EFERVESCENTES [...] # 1. NOMBRE DEL MEDICAMENTO

Acetilsalicílico/cafeína Rovi 500 mg + 30 mg comprimidos efervescentes.

# 2. COMPOSICIÓN CUALITATIVA Y CUANTITATIVA

Cada comprimido efervescente contiene:

Principios activos:

Ácido acetilsalicílico........................................ 500 mg.

Cafeína........................................................ 30 mg.

### 2.2.1. Excipiente(s) con efecto conocido

Sodio hidrogenocarbonato (E-500) (410 mg), ácido cítrico anhidro (320 mg), sacarina sódica (E-954)(8 mg), sorbitol líquido no cristalizable (E-420)(25 mg) y aroma de limón.

Para consultar la lista completa de excipientes ver sección 6.1.

# 3. FORMA FARMACÉUTICA

Comprimido efervescente. Comprimidos blancos, redondos, con olor característico a limón.

# 4. DATOS CLÍNICOS

## 4.1. Indicaciones terapéuticas

Tratamiento sintomático del dolor ocasional leve o moderado cuando no se considere suficiente el uso de paracetamol en monofármaco.
```

`instruction`:

```text
Identifica las entidades nombradas (nombres de medicamentos, sustancias, marcas y otros) mencionadas en este fragmento de ficha técnica farmacéutica.
```

`output`:

```json
{
  "entities": [
    {
      "text": "Acetilsalicílico/cafeína Rovi 500 mg + 30 mg comprimidos efervescentes",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Ácido acetilsalicílico",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Cafeína",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Sodio hidrogenocarbonato (E-500)",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "ácido cítrico anhidro",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "sacarina sódica (E-954)",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "sorbitol líquido no cristalizable (E-420)",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "aroma de limón",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "paracetamol",
      "label": "MISCELLANEOUS"
    }
  ]
}
```

`reasoning`:

```json
{
  "entities": {
    "field_asks": "lista de menciones nombradas de medicamentos, sustancias, marcas y otros elementos farmacéuticos, con texto verbatim y etiqueta del enum permitido.",
    "relevant_fragments": "\"Acetilsalicílico/cafeína Rovi 500 mg + 30 mg comprimidos efervescentes\", \"Ácido acetilsalicílico\", \"Cafeína\", \"Sodio hidrogenocarbonato (E-500)\", \"ácido cítrico anhidro\", \"sacarina sódica (E-954)\", \"sorbitol líquido no cristalizable (E-420)\", \"aroma de limón\" y \"paracetamol\".",
    "final_value": "Como los fragmentos relevantes son el nombre del medicamento, principios activos, excipientes y un analgésico comparador, todas esas menciones deben conservarse verbatim y etiquetarse como MISCELLANEOUS."
  }
}
```

### Ejemplo 2

`input_text`:

```text
FICHA TECNICA OMEPRAZOL NORTE 20 mg CAPSULAS DURAS GASTRORRESISTENTES EFG

Pulse aquí
                        
                        para ver el documento en formato PDF.

# 1. NOMBRE DEL MEDICAMENTO

omeprazol norte 20 mg cápsulas duras gastrorresistentes EFG

# 2. COMPOSICIÓN CUALITATIVA Y CUANTITATIVA [...] # 7. TITULAR DE LA AUTORIZACIÓN DE COMERCIALIZACIÓN

Norte Pharma, S.L.

Avenida de los Ensayos, 24. Parque Tecnológico del Ebro

50197-Zaragoza (Aragón) – España

# 8. NÚMERO(S) DE AUTORIZACIÓN DE COMERCIALIZACIÓN

72.184

# 9. FECHA DE LA PRIMERA AUTORIZACIÓN/ RENOVACIÓN DE LA AUTORIZACIÓN

Mayo 2011.

# 10. FECHA DE LA REVISIÓN DEL TEXTO

Enero 2026

La información detallada y actualizada de este medicamento está disponible en la página web de la Agencia Española de Medicamentos y Productos Sanitarios (AEMPS) http://www.aemps.gob.es/
```

`instruction`:

```text
Extrae los nombres de medicamentos, laboratorios, ubicaciones, fechas y organizaciones mencionados en este fragmento técnico.
```

`output`:

```json
{
  "entities": [
    {
      "text": "omeprazol norte 20 mg cápsulas duras gastrorresistentes EFG",
      "label": "MISCELLANEOUS"
    },
    {
      "text": "Norte Pharma, S.L.",
      "label": "ORGANIZATION"
    },
    {
      "text": "Avenida de los Ensayos, 24. Parque Tecnológico del Ebro",
      "label": "LOCATION"
    },
    {
      "text": "Zaragoza (Aragón)",
      "label": "LOCATION"
    },
    {
      "text": "España",
      "label": "LOCATION"
    },
    {
      "text": "Mayo 2011",
      "label": "DATE"
    },
    {
      "text": "Enero 2026",
      "label": "DATE"
    },
    {
      "text": "Agencia Española de Medicamentos y Productos Sanitarios (AEMPS)",
      "label": "ORGANIZATION"
    }
  ]
}
```

`reasoning`:

```json
{
  "entities": {
    "field_asks": "lista de menciones nombradas de medicamento, laboratorio, ubicaciones, fechas y organizaciones en un fragmento técnico farmacéutico.",
    "relevant_fragments": "\"omeprazol norte 20 mg cápsulas duras gastrorresistentes EFG\", \"Norte Pharma, S.L.\", \"Avenida de los Ensayos, 24. Parque Tecnológico del Ebro\", \"50197-Zaragoza (Aragón) – España\", \"Mayo 2011\", \"Enero 2026\" y \"Agencia Española de Medicamentos y Productos Sanitarios (AEMPS)\".",
    "final_value": "Como los fragmentos relevantes incluyen el medicamento, el titular, ubicaciones administrativas, fechas de autorización/revisión y la agencia reguladora, la lista debe conservar esas menciones verbatim con etiquetas MISCELLANEOUS, ORGANIZATION, LOCATION y DATE."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son fragmentos de fichas técnicas CIMA en Markdown, sin línea `Source:`, con encabezado inicial en mayúsculas, la frase de enlace al PDF, secciones `# 1. NOMBRE DEL MEDICAMENTO`, `# 2. COMPOSICIÓN CUALITATIVA Y CUANTITATIVA`, `# 3. FORMA FARMACÉUTICA` o secciones administrativas `# 7` a `# 10`. Usan `[...]` para omitir secciones intermedias y mezclan nombres completos de medicamentos, principios activos, excipientes con códigos E, laboratorios, direcciones, fechas de autorización y organismos reguladores. Las salidas curadas prefieren menciones completas y contextuales, por ejemplo una dirección completa o el organismo con sigla, antes que fragmentos excesivamente atomizados.
