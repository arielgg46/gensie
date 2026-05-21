# medical_diseases

Los tasks `medical_diseases` son extracciones L5 de perfiles patológicos: el modelo debe identificar nombre de enfermedad, tipo etiológico, descripción causal, síntomas agrupados con severidad e importancia primaria, métodos diagnósticos y cronicidad, separando síntomas definitorios de complicaciones o manifestaciones secundarias.

## Ejemplos revisados

- `data/dev_rev/medical_diseases_01.json`
- `data/dev_rev/medical_diseases_02.json`
- `data/dev/medical_diseases_03.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `pathology_name` | Requerido, `string`, no nullable. Dualidad entre nombre directo en encabezado y sinónimo en primera frase. |
| `etiology_type` | Enum requerido. Debe mapear a `INFECTIOUS`, `GENETIC`, `AUTOIMMUNE`, `DEGENERATIVE`, `UNKNOWN` u `OTHER`. Conviene alternar infecciosa, degenerativa/desconocida y reacciones inmunológicas que caen en `OTHER` o `AUTOIMMUNE` según el texto. |
| `etiology_description` | `string` vs `null`. Debe resumir causa si el texto la explica; si solo describe hipótesis o factores asociados sin causa clara, `null`. |
| `symptoms` | Array de objetos. Dualidad entre lista amplia con síntomas primarios/secundarios y lista corta; `severity_level` puede ser `null` o una severidad textual si el texto la califica. |
| `symptoms[].is_primary` | `true` vs `false`. Síntomas de definición clínica van `true`; complicaciones, signos tardíos o manifestaciones por extensión pueden ir `false`. |
| `diagnosis_methods` | `[]` vs lista poblada. Debe contener pruebas o métodos clínicos nombrados, no secciones genéricas de diagnóstico sin método concreto. |
| `is_chronic` | `boolean` vs `null`. `true` cuando el texto define enfermedad crónica o persistente; `false` cuando define cuadro agudo/autolimitado; `null` si no caracteriza duración. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `pathology_name` | Nombre directo: faringitis estreptocócica. | Nombre directo: migraña crónica. |
| `etiology_type` | `INFECTIOUS`, por bacteria nombrada. | `UNKNOWN`, por mecanismos propuestos sin causa única. |
| `etiology_description` | Texto no null con causa bacteriana. | `null`, hipótesis sin etiología definida. |
| `symptoms` | Síntomas con primarios y un signo de alarma secundario. | Síntomas con severidad explícita y algunos secundarios. |
| `diagnosis_methods` | Lista poblada con test rápido y cultivo. | `[]`, descripción clínica sin pruebas o métodos nombrados. |
| `is_chronic` | `false`, cuadro agudo. | `true`, definido como crónico. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Faringitis estreptocócica

La faringitis estreptocócica es una infección aguda de la faringe causada con mayor frecuencia por Streptococcus pyogenes del grupo A. Suele comenzar de forma brusca con dolor de garganta, fiebre, amígdalas con exudado y ganglios cervicales dolorosos. La tos y la rinorrea orientan más a cuadros virales, pero pueden coexistir en niños.

El diagnóstico se apoya en la exploración clínica y se confirma con test rápido de antígeno o cultivo faríngeo cuando la sospecha es alta. La dificultad para tragar saliva y la desviación de la úvula se describen como signos de alarma por posible absceso periamigdalino, no como manifestaciones habituales del cuadro simple.
```

`instruction`:

```text
Extrae el perfil de la enfermedad.
```

`output`:

```json
{
  "pathology_name": "Faringitis estreptocócica",
  "etiology_type": "INFECTIOUS",
  "etiology_description": "Infección aguda de la faringe causada con mayor frecuencia por Streptococcus pyogenes del grupo A.",
  "symptoms": [
    {
      "name": "dolor de garganta",
      "severity_level": null,
      "is_primary": true
    },
    {
      "name": "fiebre",
      "severity_level": null,
      "is_primary": true
    },
    {
      "name": "amígdalas con exudado",
      "severity_level": null,
      "is_primary": true
    },
    {
      "name": "ganglios cervicales dolorosos",
      "severity_level": null,
      "is_primary": true
    },
    {
      "name": "dificultad para tragar saliva",
      "severity_level": "Severe",
      "is_primary": false
    },
    {
      "name": "desviación de la úvula",
      "severity_level": "Severe",
      "is_primary": false
    }
  ],
  "diagnosis_methods": [
    "exploración clínica",
    "test rápido de antígeno",
    "cultivo faríngeo"
  ],
  "is_chronic": false
}
```

`reasoning`:

```json
{
  "pathology_name": {
    "field_asks": "el nombre médico de la enfermedad o trastorno.",
    "relevant_fragments": "\"# Faringitis estreptocócica\".",
    "final_value": "Como el fragmento relevante es el encabezado del perfil, el nombre debe ser \"Faringitis estreptocócica\"."
  },
  "etiology_type": {
    "field_asks": "el origen principal de la enfermedad, mapeado a uno de estos valores: INFECTIOUS, GENETIC, AUTOIMMUNE, DEGENERATIVE, UNKNOWN u OTHER.",
    "relevant_fragments": "\"es una infección aguda\" y \"causada con mayor frecuencia por Streptococcus pyogenes\".",
    "final_value": "Como los fragmentos relevantes describen una infección bacteriana, el valor del enum debe ser \"INFECTIOUS\"."
  },
  "etiology_description": {
    "field_asks": "resumen breve de cómo se causa la enfermedad, o null si no hay causa explicada.",
    "relevant_fragments": "\"infección aguda de la faringe causada con mayor frecuencia por Streptococcus pyogenes del grupo A\".",
    "final_value": "Como el fragmento relevante explica la causa, la descripción debe resumir esa infección por Streptococcus pyogenes."
  },
  "symptoms": {
    "field_asks": "lista estructurada de síntomas, con severidad si se menciona y marca de si son definitorios o secundarios.",
    "relevant_fragments": "\"dolor de garganta, fiebre, amígdalas con exudado y ganglios cervicales dolorosos\" y \"signos de alarma por posible absceso periamigdalino\".",
    "final_value": "Como el primer fragmento enumera manifestaciones habituales, esos síntomas son primarios; dificultad para tragar saliva y desviación de la úvula se tratan como secundarios y severos por aparecer como signos de alarma."
  },
  "diagnosis_methods": {
    "field_asks": "pruebas clínicas o métodos mencionados para identificar la patología.",
    "relevant_fragments": "\"exploración clínica\" y \"test rápido de antígeno o cultivo faríngeo\".",
    "final_value": "Como los fragmentos relevantes nombran métodos diagnósticos, la lista debe incluir exploración clínica, test rápido de antígeno y cultivo faríngeo."
  },
  "is_chronic": {
    "field_asks": "true si el texto define la enfermedad como crónica o de larga duración; false si la define como aguda; null si no se especifica.",
    "relevant_fragments": "\"es una infección aguda de la faringe\".",
    "final_value": "Como el fragmento relevante define el cuadro como agudo, el valor debe ser false."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# Migraña crónica

La migraña crónica es un trastorno neurológico persistente en el que la cefalea aparece durante muchos días al mes y limita la actividad cotidiana. Sus mecanismos se relacionan con sensibilización del sistema trigeminovascular, predisposición individual y cambios en circuitos de dolor, aunque no se atribuye a una causa única demostrada.

Los pacientes describen cefalea pulsátil intensa, náuseas, fotofobia y fonofobia. Algunas crisis se acompañan de aura visual o dificultad para concentrarse, y en los periodos de mayor carga el dolor se califica como incapacitante. El texto revisa medidas preventivas y hábitos de sueño, pero no enumera pruebas concretas.
```

`instruction`:

```text
Extrae el perfil de la enfermedad.
```

`output`:

```json
{
  "pathology_name": "Migraña crónica",
  "etiology_type": "UNKNOWN",
  "etiology_description": null,
  "symptoms": [
    {
      "name": "cefalea pulsátil intensa",
      "severity_level": "Severe",
      "is_primary": true
    },
    {
      "name": "náuseas",
      "severity_level": null,
      "is_primary": true
    },
    {
      "name": "fotofobia",
      "severity_level": null,
      "is_primary": true
    },
    {
      "name": "fonofobia",
      "severity_level": null,
      "is_primary": true
    },
    {
      "name": "aura visual",
      "severity_level": null,
      "is_primary": false
    },
    {
      "name": "dificultad para concentrarse",
      "severity_level": null,
      "is_primary": false
    }
  ],
  "diagnosis_methods": [],
  "is_chronic": true
}
```

`reasoning`:

```json
{
  "pathology_name": {
    "field_asks": "el nombre médico de la enfermedad o trastorno.",
    "relevant_fragments": "\"# Migraña crónica\".",
    "final_value": "Como el fragmento relevante es el encabezado del perfil, el nombre debe ser \"Migraña crónica\"."
  },
  "etiology_type": {
    "field_asks": "el origen principal de la enfermedad, mapeado a uno de estos valores: INFECTIOUS, GENETIC, AUTOIMMUNE, DEGENERATIVE, UNKNOWN u OTHER.",
    "relevant_fragments": "\"se relacionan con sensibilización del sistema trigeminovascular, predisposición individual y cambios en circuitos de dolor\" y \"no se atribuye a una causa única demostrada\".",
    "final_value": "Como los fragmentos relevantes mencionan mecanismos y predisposición sin causa única demostrada, el valor del enum debe ser \"UNKNOWN\"."
  },
  "etiology_description": {
    "field_asks": "resumen breve de cómo se causa la enfermedad, o null si no hay causa explicada.",
    "relevant_fragments": "\"no se atribuye a una causa única demostrada\".",
    "final_value": "Como el fragmento relevante niega una causa demostrada, no hay descripción etiológica cerrada; el valor debe ser null."
  },
  "symptoms": {
    "field_asks": "lista estructurada de síntomas, con severidad si se menciona y marca de si son definitorios o secundarios.",
    "relevant_fragments": "\"cefalea pulsátil intensa, náuseas, fotofobia y fonofobia\" y \"Algunas crisis se acompañan de aura visual o dificultad para concentrarse\".",
    "final_value": "Como el primer fragmento da síntomas centrales, esos son primarios; aura visual y dificultad para concentrarse se marcan como secundarios por aparecer solo en algunas crisis."
  },
  "diagnosis_methods": {
    "field_asks": "pruebas clínicas o métodos mencionados para identificar la patología.",
    "relevant_fragments": "\"El texto revisa medidas preventivas y hábitos de sueño\".",
    "final_value": "El fragmento relevante describe manejo preventivo y hábitos, pero no pruebas ni métodos diagnósticos concretos; la lista debe ser vacía."
  },
  "is_chronic": {
    "field_asks": "true si el texto define la enfermedad como crónica o de larga duración; false si la define como aguda; null si no se especifica.",
    "relevant_fragments": "\"La migraña crónica es un trastorno neurológico persistente\".",
    "final_value": "Como el fragmento relevante define el trastorno como crónico y persistente, el valor debe ser true."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son perfiles médicos en Markdown con encabezado, fuente, definición, etiopatogenia, síntomas, diagnóstico y tratamiento. Para FSP conviene sintetizar esa estructura en textos compactos que separen causa, manifestaciones principales, complicaciones o signos secundarios, y métodos diagnósticos concretos; las ausencias deben surgir del foco clínico del texto, no de frases fabricadas para el benchmark.
