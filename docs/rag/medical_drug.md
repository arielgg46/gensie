# medical_drug

Los tasks `medical_drug` son extracciones L8 desde fichas técnicas de medicamentos: el modelo debe agregar nombre común, nombre oficial, forma farmacéutica, dosis o concentraciones disponibles, aptitud pediátrica y una lista anidada de reacciones adversas; además debe mapear frecuencias textuales a enums (`HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`) e inferir impacto clínico (`MILD`, `MODERATE`, `SEVERE`, `CRITICAL`) a partir de la reacción, sin confundir posología, advertencias o composición con efectos adversos de la sección 4.8.

## Ejemplos revisados

- `data/dev_rev/medical_drug_001.json`
- `data/dev_rev/medical_drug_002.json`
- `data/dev/medical_drug_002.json`
- `data/dev/medical_drug_003.json`
- `data/dev/medical_drug_005.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `common_name` | Requerido, `string`, no nullable. Dualidad útil entre principio activo único (`Paracetamol`) y combinación de principios activos (`Paracetamol / Codeína`). Debe salir de la composición o del nombre del medicamento, no de una indicación terapéutica. |
| `official_name` | Requerido, `string`, no nullable. Dualidad entre un nombre oficial único y una ficha que menciona varias presentaciones o concentraciones; el valor debe corresponder a la presentación principal pedida o descrita, no a todos los nombres listados. |
| `pharmaceutical_format` | Requerido, `string`, no nullable. Dualidad entre forma simple (`Comprimido`, `Solución oral`) y forma más específica (`Comprimido recubierto con película`, `Solución para perfusión`). Conviene copiar el literal de la sección 3 cuando exista. |
| `standard_doses` | Array no requerido en `required`, pero muy informativo. Dualidad entre una sola dosis/concentración y varias dosis, incluyendo concentraciones por ml o combinaciones con principio activo. Puede ser `[]` si la ficha no da dosis estándar claras, pero en los ejemplos revisados siempre aparece poblado. |
| `is_pediatric` | `boolean`. Dualidad principal: `true` cuando la ficha da posología pediátrica para niños o adolescentes con uso permitido, frente a `false` cuando restringe o contraindica el uso en menores aunque mencione adolescentes. Hay que distinguir "población pediátrica" como sección de "indicado para niños". |
| `side_effects` | Array anidado. Puede variar en longitud y granularidad, pero cuando el input recorta una sección 4.8 pequeña conviene extraer todas las reacciones de ese recorte y no solo una muestra. Para cada item, `reaction` debe ser el nombre del efecto adverso, `system_organ_class` puede ser `string` o `null`, `probability` debe mapear frecuencia textual al enum y `impact` se infiere clínicamente. |
| `side_effects[].reaction` | Requerido dentro del item. Dualidad entre reacciones simples (`Malestar`, `Hipotensión`) y reacciones complejas o compuestas (`Reacciones de hipersensibilidad`, `Acidosis metabólica con déficit aniónico elevado`). Preferir literal o fragmento fiel del texto. |
| `side_effects[].system_organ_class` | `string` vs `null`. En los ejemplos revisados casi siempre es `string` porque las reacciones aparecen bajo encabezados de sistema; conviene incluir un caso donde una reacción aparece en una frase general de perfil de seguridad sin clase clara, para enseñar `null`. |
| `side_effects[].probability` | Enum requerido. Debe mapear a uno de estos valores: `HIGH`, `MEDIUM`, `LOW` o `UNKNOWN`. Dualidad importante: `Raras`/`Muy raras` suelen ir a `LOW`; `Frecuentes` a `HIGH`; `Poco frecuentes` o algunos usos del dataset pueden ir a `MEDIUM`; `Frecuencia no conocida` debe ir a `UNKNOWN`. |
| `side_effects[].impact` | Enum requerido. Debe mapear a uno de estos valores: `MILD`, `MODERATE`, `SEVERE` o `CRITICAL`. Dualidad entre reacciones leves como malestar/náuseas, moderadas como transaminasas o hipotensión, severas como hepatotoxicidad o reacciones cutáneas graves, y críticas como shock anafiláctico o depresión respiratoria. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `common_name` | Principio activo o combinación de principios activos. Extráelo del nombre o de la composición; normaliza combinaciones como `Paracetamol / Codeína` y no uses indicaciones terapéuticas ni excipientes. |
| `official_name` | Nombre completo de la presentación en `# 1. NOMBRE DEL MEDICAMENTO`. Si aparecen varias presentaciones, conserva la presentación principal del recorte y no mezcles dosis de otras fichas. |
| `pharmaceutical_format` | Forma farmacéutica literal de `# 3. FORMA FARMACÉUTICA`, por ejemplo `Comprimido`, `Comprimido recubierto con película`, `Solución oral` o `Solución para perfusión`. No la infieras desde la vía ni desde la posología si la sección 3 está presente. |
| `standard_doses` | Lista de concentraciones o dosis estándar de la composición y del nombre oficial. Incluye unidades y principio activo cuando haya combinación; no conviertas pautas de administración, máximos diarios ni intervalos horarios en dosis estándar. |
| `is_pediatric` | `true` si el texto permite uso o da pauta para niños/adolescentes concretos; `false` si contraindica menores o solo menciona población pediátrica para advertir restricciones. Distingue adolescentes permitidos de niños excluidos cuando el medicamento no es apto para la población pediátrica general. |
| `side_effects` | Lista de reacciones adversas de `## 4.8. Reacciones adversas`, preferiblemente todas las del recorte. No extraigas efectos desde indicaciones, advertencias, sobredosis o composición; conserva clase de órgano, frecuencia e impacto por cada reacción. |
| `side_effects[].reaction` | Nombre de la reacción adversa, literal o muy fiel al texto. Divide listas separadas por comas cuando sean reacciones distintas (`Trombocitopenia`, `agranulocitosis`) y conserva expresiones clínicas compuestas cuando forman una entidad. |
| `side_effects[].system_organ_class` | Clase de órgano o sistema bajo la que aparece la reacción; usa `null` si la reacción se menciona en una frase general sin encabezado claro. No confundas principio activo (`Paracetamol`, `Codeína`) con clase de órgano. |
| `side_effects[].probability` | Frecuencia mapeada al enum completo: `HIGH`, `MEDIUM`, `LOW` o `UNKNOWN`. `Frecuentes` suele ser `HIGH`, `Poco frecuentes` `MEDIUM`, `Raras`/`Muy raras` `LOW`, y `Frecuencia no conocida` o casos aislados sin frecuencia tabulada `UNKNOWN`. |
| `side_effects[].impact` | Impacto clínico inferido y mapeado al enum completo: `MILD`, `MODERATE`, `SEVERE` o `CRITICAL`. Síntomas leves como malestar o náuseas son `MILD`; alteraciones que requieren valoración suelen ser `MODERATE`; hepatotoxicidad, broncoespasmo o reacciones cutáneas graves son `SEVERE`; shock anafiláctico, depresión respiratoria o agranulocitosis pueden ser `CRITICAL`. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `common_name` | Monofármaco, por ejemplo `Ibuprofeno` o `Paracetamol`. | Combinación de principios activos, por ejemplo `Paracetamol / Codeína`, para contrastar con nombre único. |
| `official_name` | Nombre oficial único con dosis, sin varias presentaciones competidoras. | Nombre oficial de una solución oral combinada, con concentración de ambos principios activos. |
| `pharmaceutical_format` | Forma específica sólida, por ejemplo `Comprimido recubierto con película`. | Forma líquida, por ejemplo `Solución oral`, para contrastar formato. |
| `standard_doses` | Lista de un solo elemento, por ejemplo `400 mg`. | Lista de dos elementos con concentración y principio activo, por ejemplo `24 mg/ml paracetamol` y `2,40 mg/ml codeína`. |
| `is_pediatric` | `true`: posología explícita para niños por peso o edad. | `false`: sección pediátrica menciona adolescentes o menores, pero contraindica menores de 12 años o limita el uso de forma que no es apto para niños. |
| `side_effects` | Lista corta, 3-4 items, incluyendo una reacción sin clase de órgano clara para usar `system_organ_class: null`. | Lista más rica, 8 items, extrayendo todas las reacciones del recorte de 4.8 y no solo una selección. |
| `side_effects[].probability` | Mezcla de `HIGH`, `MEDIUM` y `LOW` si el texto tiene frecuentes/poco frecuentes/raras. | `LOW` y `UNKNOWN`, siguiendo el patrón de paracetamol/codeína y frecuencia no conocida. |
| `side_effects[].impact` | Incluir al menos `MILD`, `MODERATE` y `SEVERE`. | Incluir `CRITICAL` para una reacción como depresión respiratoria o shock anafiláctico. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
FICHA TÉCNICA IBUPROFENO LUMEN 400 mg COMPRIMIDOS RECUBIERTOS CON PELÍCULA EFG

Pulse aquí
                        
                        para ver el documento en formato PDF.

# 1. NOMBRE DEL MEDICAMENTO

Ibuprofeno Lumen 400 mg comprimidos recubiertos con película EFG. [...] 

# 2. COMPOSICIÓN CUALITATIVA Y CUANTITATIVA

Cada comprimido recubierto contiene 400 mg de ibuprofeno. Excipiente con efecto conocido: cada comprimido contiene lactosa monohidrato. [...] 

# 3. FORMA FARMACÉUTICA

Comprimido recubierto con película. Comprimidos blancos, oblongos y ranurados por una cara. La ranura no debe utilizarse para fraccionar dosis iguales. [...] 

## 4.2. Posología y forma de administración

Posología

Adultos: 1 comprimido cada 6-8 horas, si fuera necesario. No superar 1.200 mg al día sin supervisión médica.

Población pediátrica:

Niños a partir de 12 años y peso igual o superior a 40 kg: 1 comprimido cada 6-8 horas, con un máximo de 3 comprimidos al día. En menores de 12 años se recomiendan otras presentaciones ajustadas al peso. [...] 

## 4.8. Reacciones adversas

Las reacciones adversas se agrupan por frecuencia y sistema orgánico. Frecuentes (>=1/100 a <1/10), poco frecuentes (>=1/1.000 a <1/100), raras (>=1/10.000 a <1/1.000).

Trastornos gastrointestinales:
Frecuentes: Náuseas.

Trastornos del sistema nervioso:
Poco frecuentes: Mareo.

Trastornos de la piel y del tejido subcutáneo:
Raras: Reacciones cutáneas graves.

Tras la comercialización también se han comunicado casos aislados de edema facial.
```

`instruction`:

```text
Extrae la descripción estructurada del medicamento, incluyendo su uso en población pediátrica y la lista detallada de efectos adversos.
```

`output`:

```json
{
  "common_name": "Ibuprofeno",
  "official_name": "Ibuprofeno Lumen 400 mg comprimidos recubiertos con película EFG",
  "pharmaceutical_format": "Comprimido recubierto con película",
  "standard_doses": [
    "400 mg"
  ],
  "is_pediatric": true,
  "side_effects": [
    {
      "reaction": "Náuseas",
      "system_organ_class": "Trastornos gastrointestinales",
      "probability": "HIGH",
      "impact": "MILD"
    },
    {
      "reaction": "Mareo",
      "system_organ_class": "Trastornos del sistema nervioso",
      "probability": "MEDIUM",
      "impact": "MILD"
    },
    {
      "reaction": "Reacciones cutáneas graves",
      "system_organ_class": "Trastornos de la piel y del tejido subcutáneo",
      "probability": "LOW",
      "impact": "SEVERE"
    },
    {
      "reaction": "edema facial",
      "system_organ_class": null,
      "probability": "UNKNOWN",
      "impact": "MODERATE"
    }
  ]
}
```

`reasoning`:

```json
{
  "common_name": {
    "field_asks": "el nombre genérico del principio activo.",
    "relevant_fragments": "\"Ibuprofeno Lumen 400 mg\" y \"Cada comprimido recubierto contiene 400 mg de ibuprofeno\".",
    "final_value": "Como los fragmentos relevantes identifican ibuprofeno como principio activo, el nombre común debe ser \"Ibuprofeno\"."
  },
  "official_name": {
    "field_asks": "el nombre comercial u oficial completo del medicamento.",
    "relevant_fragments": "\"# 1. NOMBRE DEL MEDICAMENTO\" y \"Ibuprofeno Lumen 400 mg comprimidos recubiertos con película EFG\".",
    "final_value": "Como el fragmento relevante de la sección 1 da el nombre completo de la presentación, el valor debe ser \"Ibuprofeno Lumen 400 mg comprimidos recubiertos con película EFG\"."
  },
  "pharmaceutical_format": {
    "field_asks": "la forma farmacéutica física del medicamento.",
    "relevant_fragments": "\"# 3. FORMA FARMACÉUTICA\" y \"Comprimido recubierto con película\".",
    "final_value": "Como la sección 3 da la forma farmacéutica, el valor debe ser \"Comprimido recubierto con película\"."
  },
  "standard_doses": {
    "field_asks": "lista de dosis o concentraciones estándar mencionadas.",
    "relevant_fragments": "\"Ibuprofeno Lumen 400 mg\" y \"Cada comprimido recubierto contiene 400 mg de ibuprofeno\".",
    "final_value": "Como los fragmentos relevantes mencionan una única concentración por comprimido, la lista debe contener \"400 mg\"."
  },
  "is_pediatric": {
    "field_asks": "true si el medicamento está indicado o tiene posología para niños o adolescentes; false si no lo está.",
    "relevant_fragments": "\"Población pediátrica: Niños a partir de 12 años y peso igual o superior a 40 kg: 1 comprimido cada 6-8 horas\".",
    "final_value": "Como el fragmento relevante da una pauta pediátrica permitida para niños a partir de 12 años, el valor debe ser true."
  },
  "side_effects": {
    "field_asks": "lista estructurada de reacciones adversas de la sección 4.8; cada item debe incluir reacción, clase de órgano o null, probabilidad mapeada a HIGH, MEDIUM, LOW o UNKNOWN, e impacto mapeado a MILD, MODERATE, SEVERE o CRITICAL.",
    "relevant_fragments": "\"Trastornos gastrointestinales: Frecuentes: Náuseas\", \"Trastornos del sistema nervioso: Poco frecuentes: Mareo\", \"Trastornos de la piel y del tejido subcutáneo: Raras: Reacciones cutáneas graves\" y \"casos aislados de edema facial\".",
    "final_value": "Como los fragmentos relevantes dan las reacciones y sus frecuencias, \"Frecuentes\" se mapea a HIGH, \"Poco frecuentes\" a MEDIUM, \"Raras\" a LOW y los casos aislados sin frecuencia tabulada a UNKNOWN; los impactos se asignan según gravedad clínica: náuseas y mareo MILD, reacciones cutáneas graves SEVERE y edema facial MODERATE."
  }
}
```

### Ejemplo 2

`input_text`:

```text
FICHA TÉCNICA PARACETAMOL/ CODEÍNA NOVA 24mg/ml +2,40mg/ml SOLUCIÓN ORAL

Pulse aquí
                        
                        para ver el documento en formato PDF.

# 1. NOMBRE DEL MEDICAMENTO

Paracetamol/codeína Nova 24 mg/ml + 2,40 mg/ml solución oral. [...] 

# 2. COMPOSICIÓN CUALITATIVA Y CUANTITATIVA

Cada ml de solución contiene 24 mg de paracetamol y 2,40 mg de codeína fosfato hemihidrato. [...] 

# 3. FORMA FARMACÉUTICA

Solución oral. Líquido transparente de color rojo con aroma a fresa. [...] 

## 4.1. Indicaciones terapéuticas

Indicado en pacientes mayores de 12 años para dolor agudo moderado no aliviado por otros analgésicos. [...] 

## 4.2. Posología y forma de administración

Población pediátrica:

- Adolescentes de 12 a 18 años: de 10 a 15 ml cada 6 horas.

- Niños menores de 12 años: no se debe utilizar codeína debido al riesgo de toxicidad opioide por metabolismo variable a morfina. [...] 

## 4.8. Reacciones adversas

Las reacciones adversas son raras, muy raras o de frecuencia no conocida.

Paracetamol
Trastornos del metabolismo y de la nutrición:
Muy raras: Hipoglucemia.
Frecuencia no conocida: Acidosis metabólica con déficit aniónico elevado.

Codeína
Trastornos del sistema nervioso:
Raras: Somnolencia.

Trastornos gastrointestinales:
Raras: Estreñimiento, náuseas.

Trastornos respiratorios:
Raras: Broncoespasmo, depresión respiratoria.

Trastornos del sistema inmunológico:
Muy raras: Reacciones de hipersensibilidad que pueden llegar a shock anafiláctico.
```

`instruction`:

```text
Extrae la información completa del medicamento, incluyendo nombre, indicación pediátrica y efectos adversos con su frecuencia e impacto.
```

`output`:

```json
{
  "common_name": "Paracetamol / Codeína",
  "official_name": "Paracetamol/codeína Nova 24 mg/ml + 2,40 mg/ml solución oral",
  "pharmaceutical_format": "Solución oral",
  "standard_doses": [
    "24 mg/ml paracetamol",
    "2,40 mg/ml codeína"
  ],
  "is_pediatric": false,
  "side_effects": [
    {
      "reaction": "Hipoglucemia",
      "system_organ_class": "Trastornos del metabolismo y de la nutrición",
      "probability": "LOW",
      "impact": "MODERATE"
    },
    {
      "reaction": "Acidosis metabólica con déficit aniónico elevado",
      "system_organ_class": "Trastornos del metabolismo y de la nutrición",
      "probability": "UNKNOWN",
      "impact": "MODERATE"
    },
    {
      "reaction": "Somnolencia",
      "system_organ_class": "Trastornos del sistema nervioso",
      "probability": "LOW",
      "impact": "MILD"
    },
    {
      "reaction": "Estreñimiento",
      "system_organ_class": "Trastornos gastrointestinales",
      "probability": "LOW",
      "impact": "MILD"
    },
    {
      "reaction": "náuseas",
      "system_organ_class": "Trastornos gastrointestinales",
      "probability": "LOW",
      "impact": "MILD"
    },
    {
      "reaction": "Broncoespasmo",
      "system_organ_class": "Trastornos respiratorios",
      "probability": "LOW",
      "impact": "SEVERE"
    },
    {
      "reaction": "depresión respiratoria",
      "system_organ_class": "Trastornos respiratorios",
      "probability": "LOW",
      "impact": "CRITICAL"
    },
    {
      "reaction": "Reacciones de hipersensibilidad que pueden llegar a shock anafiláctico",
      "system_organ_class": "Trastornos del sistema inmunológico",
      "probability": "LOW",
      "impact": "CRITICAL"
    }
  ]
}
```

`reasoning`:

```json
{
  "common_name": {
    "field_asks": "el nombre genérico del principio activo o de los principios activos.",
    "relevant_fragments": "\"Paracetamol/codeína Nova\" y \"contiene 24 mg de paracetamol y 2,40 mg de codeína fosfato hemihidrato\".",
    "final_value": "Como los fragmentos relevantes identifican dos principios activos, el nombre común debe ser \"Paracetamol / Codeína\"."
  },
  "official_name": {
    "field_asks": "el nombre comercial u oficial completo del medicamento.",
    "relevant_fragments": "\"# 1. NOMBRE DEL MEDICAMENTO\" y \"Paracetamol/codeína Nova 24 mg/ml + 2,40 mg/ml solución oral\".",
    "final_value": "Como el fragmento relevante de la sección 1 da el nombre completo de la presentación, el valor debe ser \"Paracetamol/codeína Nova 24 mg/ml + 2,40 mg/ml solución oral\"."
  },
  "pharmaceutical_format": {
    "field_asks": "la forma farmacéutica física del medicamento.",
    "relevant_fragments": "\"# 3. FORMA FARMACÉUTICA\" y \"Solución oral\".",
    "final_value": "Como la sección 3 da la forma farmacéutica, el valor debe ser \"Solución oral\"."
  },
  "standard_doses": {
    "field_asks": "lista de dosis o concentraciones estándar mencionadas.",
    "relevant_fragments": "\"Cada ml de solución contiene 24 mg de paracetamol y 2,40 mg de codeína fosfato hemihidrato\".",
    "final_value": "Como el fragmento relevante da concentraciones por ml para los dos principios activos, la lista debe incluir \"24 mg/ml paracetamol\" y \"2,40 mg/ml codeína\"."
  },
  "is_pediatric": {
    "field_asks": "true si el medicamento está indicado o tiene posología para niños o adolescentes; false si no lo está.",
    "relevant_fragments": "\"Adolescentes de 12 a 18 años\" y \"Niños menores de 12 años: no se debe utilizar codeína debido al riesgo de toxicidad opioide\".",
    "final_value": "Como los fragmentos relevantes limitan el uso a adolescentes y excluyen a niños menores de 12 años por riesgo opioide, el valor debe ser false."
  },
  "side_effects": {
    "field_asks": "lista estructurada de reacciones adversas de la sección 4.8; cada item debe incluir reacción, clase de órgano o null, probabilidad mapeada a HIGH, MEDIUM, LOW o UNKNOWN, e impacto mapeado a MILD, MODERATE, SEVERE o CRITICAL.",
    "relevant_fragments": "\"Trastornos del metabolismo y de la nutrición: Muy raras: Hipoglucemia. Frecuencia no conocida: Acidosis metabólica con déficit aniónico elevado\", \"Trastornos gastrointestinales: Raras: Estreñimiento, náuseas\", \"Trastornos respiratorios: Raras: Broncoespasmo, depresión respiratoria\" y \"Trastornos del sistema inmunológico: Muy raras: Reacciones de hipersensibilidad que pueden llegar a shock anafiláctico\".",
    "final_value": "Como los fragmentos relevantes cubren todo el recorte de la sección 4.8, deben salir las ocho reacciones listadas: \"Muy raras\" y \"Raras\" se mapean a LOW y \"Frecuencia no conocida\" a UNKNOWN. El impacto queda apoyado en la naturaleza clínica de cada reacción: somnolencia, estreñimiento y náuseas son MILD por ser síntomas habitualmente reversibles; hipoglucemia y acidosis metabólica son MODERATE porque implican alteraciones metabólicas que requieren valoración; Broncoespasmo es SEVERE por compromiso respiratorio; depresión respiratoria y las reacciones de hipersensibilidad que pueden llegar a shock anafiláctico son CRITICAL por riesgo vital directo."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son extractos de ficha técnica CIMA en Markdown, a veces con texto omitido mediante `[...]`: sección `# 1. NOMBRE DEL MEDICAMENTO`, sección `# 2. COMPOSICIÓN CUALITATIVA Y CUANTITATIVA` si hace falta para dosis o principios activos, sección `# 3. FORMA FARMACÉUTICA`, fragmentos de `## 4.2. Posología y forma de administración` para decidir `is_pediatric`, y sección `## 4.8. Reacciones adversas` para construir la lista anidada. Los nuevos ejemplos deben seguir esa estructura, mantener menos de 1600 caracteres, usar fragmentos clínicos naturales y evitar frases escritas para anunciar la ausencia de un campo.
