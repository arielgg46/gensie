# medical_diseases

Los tasks `medical_diseases` son extracciones L5 de perfiles patológicos: el modelo debe identificar nombre de enfermedad, tipo etiológico, descripción causal, síntomas agrupados con severidad e importancia primaria, métodos diagnósticos y cronicidad, separando síntomas definitorios de complicaciones o manifestaciones secundarias.

## Ejemplos revisados

- `data/dev_rev/medical_diseases_01.json`
- `data/dev_rev/medical_diseases_02.json`
- `data/dev/medical_diseases_03.json`
- `data/dev/medical_diseases_05.json`
- `data/dev/medical_diseases_08.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `pathology_name` | Requerido, `string`, no nullable. Dualidad entre nombre directo en encabezado y sinónimo en primera frase. |
| `etiology_type` | Enum requerido. Debe mapear a `INFECTIOUS`, `GENETIC`, `AUTOIMMUNE`, `DEGENERATIVE`, `UNKNOWN` u `OTHER`. Conviene alternar infecciosa, degenerativa/desconocida y reacciones inmunológicas que caen en `OTHER` o `AUTOIMMUNE` según el texto. |
| `etiology_description` | `string` vs `null`. Debe resumir causa si el texto la explica; si solo describe hipótesis o factores asociados sin causa clara, `null`. |
| `symptoms` | Array de objetos. Dualidad entre lista amplia con síntomas primarios/secundarios y lista corta; `severity_level` puede ser `null` o una severidad textual si el texto la califica o la deja inferir con claridad (`Mild`, `Moderate`, `Severe`). |
| `symptoms[].is_primary` | `true` vs `false`. Síntomas de definición clínica van `true`; complicaciones, signos tardíos o manifestaciones por extensión pueden ir `false`. |
| `diagnosis_methods` | `[]` vs lista poblada. Debe contener pruebas o métodos clínicos nombrados, no secciones genéricas de diagnóstico sin método concreto. |
| `is_chronic` | `boolean` vs `null`. `true` cuando el texto define enfermedad crónica o persistente; `false` cuando define cuadro agudo/autolimitado; `null` si no caracteriza duración. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `pathology_name` | Nombre médico principal de la patología. Usa el encabezado o el sinónimo formal de la primera frase; no elijas categorías amplias, ejemplos secundarios ni complicaciones como si fueran la enfermedad principal. |
| `etiology_type` | Tipo etiológico principal; enum completo: `INFECTIOUS`, `GENETIC`, `AUTOIMMUNE`, `DEGENERATIVE`, `UNKNOWN` u `OTHER`. Usa `INFECTIOUS` para infecciones, `GENETIC` para origen hereditario dominante, `AUTOIMMUNE` para autoinmunidad explícita, `DEGENERATIVE` para deterioro progresivo, `UNKNOWN` cuando no haya causa demostrada y `OTHER` para reacciones, cánceres, tóxicos o mecanismos no cubiertos. |
| `etiology_description` | Resumen breve de la causa si el texto la explica. Devuelve `null` si solo hay hipótesis, factores asociados, mecanismos no concluyentes o epidemiología sin causa directa. |
| `symptoms` | Manifestaciones clínicas mencionadas. Separa síntomas definitorios de complicaciones o signos tardíos; no incluyas tratamientos, factores de riesgo, pruebas diagnósticas ni consecuencias epidemiológicas como síntomas. |
| `symptoms[].severity_level` | Severidad textual cuando esté explícita o sea muy clara; valores esperados: `Mild`, `Moderate` o `Severe`, y `null` si no se puede justificar. No conviertas cualquier síntoma molesto en severo salvo que el texto hable de alarma, gravedad, incapacidad o riesgo vital. |
| `symptoms[].is_primary` | `true` para síntomas centrales del cuadro; `false` para complicaciones, manifestaciones secundarias, signos de alarma, afectación por extensión o síntomas que solo aparecen en algunos casos. |
| `diagnosis_methods` | Pruebas, escalas o métodos clínicos concretos usados para diagnosticar. Incluye radiografía, TAC, broncoscopía, test rápido, cultivo, escala clínica, etc.; no incluyas secciones llamadas “Diagnóstico” si no nombran un método. |
| `is_chronic` | `true` si el texto define la enfermedad como crónica, persistente o de larga duración; `false` si la define como aguda, autolimitada o de pocos días; `null` si no caracteriza duración. |

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

Source: https://es.wikipedia.org/wiki/Faringitis_estreptocócica

La faringitis estreptocócica es una infección aguda de la faringe causada con mayor frecuencia por Streptococcus pyogenes del grupo A. Afecta sobre todo a niños en edad escolar y aparece con más frecuencia en los meses fríos.

Etiopatogenia
El microorganismo se transmite por secreciones respiratorias y coloniza la mucosa faríngea. La inflamación local explica el dolor al tragar, mientras que la respuesta sistémica se manifiesta con fiebre y malestar.

Síntomas
El inicio suele ser brusco, con dolor de garganta, fiebre, amígdalas con exudado y ganglios cervicales dolorosos. La tos y la rinorrea orientan más a cuadros virales, aunque pueden coexistir en niños pequeños.

Complicaciones
La dificultad para tragar saliva y la desviación de la úvula se describen como signos de alarma de formas graves por posible absceso periamigdalino.

Diagnóstico
El diagnóstico se apoya en la exploración clínica y se confirma con test rápido de antígeno o cultivo faríngeo cuando la sospecha es alta.
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
    "field_asks": "lista estructurada de síntomas, con severidad si se menciona o se infiere claramente como Mild, Moderate o Severe, y marca de si son definitorios o secundarios.",
    "relevant_fragments": "\"Síntomas\n[...] dolor de garganta, fiebre, amígdalas con exudado y ganglios cervicales dolorosos\" y \"La dificultad para tragar saliva y la desviación de la úvula se describen como signos de alarma de formas graves\".",
    "final_value": "Como el primer fragmento enumera manifestaciones habituales, esos síntomas son primarios y sin severidad explícita. Dificultad para tragar saliva y desviación de la úvula se tratan como secundarios y Severe porque el segundo fragmento los sitúa como signos de alarma de formas graves."
  },
  "diagnosis_methods": {
    "field_asks": "pruebas clínicas o métodos mencionados para identificar la patología.",
    "relevant_fragments": "\"El diagnóstico se apoya en la exploración clínica y se confirma con test rápido de antígeno o cultivo faríngeo\".",
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

Source: https://es.wikipedia.org/wiki/Migraña_crónica

La migraña crónica es un trastorno neurológico persistente en el que la cefalea ocupa muchos días del mes y limita la actividad cotidiana. Se usa el término cuando el patrón se mantiene durante meses, con crisis que alternan intensidad variable y periodos de mayor carga.

Etiopatogenia
Sus mecanismos se relacionan con sensibilización del sistema trigeminovascular, predisposición individual y cambios en circuitos de dolor. También se mencionan sueño irregular, estrés y abuso de analgésicos como factores que pueden favorecer la cronificación, aunque no se atribuye a una causa única demostrada.

Cuadro clínico
Los pacientes describen cefalea pulsátil intensa, náuseas, fotofobia y fonofobia. Algunas crisis se acompañan de aura visual o dificultad para concentrarse; en los periodos de mayor carga el dolor se califica como incapacitante.

Tratamiento y evolución
La reseña comenta medidas preventivas, higiene del sueño, reducción de desencadenantes y ajustes del tratamiento cuando las crisis se repiten con frecuencia.
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
    "relevant_fragments": "\"se relacionan con sensibilización del sistema trigeminovascular, predisposición individual y cambios en circuitos de dolor\" y \"no se atribuye a una causa única demostrada\".",
    "final_value": "Aunque los fragmentos relevantes mencionan mecanismos y factores asociados, también niegan una causa demostrada de la enfermedad; por eso no hay una descripción etiológica cerrada y el valor debe ser null."
  },
  "symptoms": {
    "field_asks": "lista estructurada de síntomas, con severidad si se menciona o se infiere claramente como Mild, Moderate o Severe, y marca de si son definitorios o secundarios.",
    "relevant_fragments": "\"cefalea pulsátil intensa, náuseas, fotofobia y fonofobia\", \"Algunas crisis se acompañan de aura visual o dificultad para concentrarse\" y \"el dolor se califica como incapacitante\".",
    "final_value": "Como el primer fragmento da síntomas centrales, esos son primarios; la cefalea queda con severidad Severe porque se describe como intensa e incapacitante. Aura visual y dificultad para concentrarse se marcan como secundarios por aparecer solo en algunas crisis."
  },
  "diagnosis_methods": {
    "field_asks": "pruebas clínicas o métodos mencionados para identificar la patología.",
    "relevant_fragments": "\"medidas preventivas, higiene del sueño, reducción de desencadenantes y ajustes del tratamiento\".",
    "final_value": "El fragmento relevante describe manejo, prevención y tratamiento, pero no pruebas clínicas ni métodos para identificar la patología; la lista debe ser vacía."
  },
  "is_chronic": {
    "field_asks": "true si el texto define la enfermedad como crónica o de larga duración; false si la define como aguda; null si no se especifica.",
    "relevant_fragments": "\"La migraña crónica es un trastorno neurológico persistente\".",
    "final_value": "Como el fragmento relevante define el trastorno como crónico y persistente, el valor debe ser true."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son perfiles médicos de estilo Wikipedia: normalmente empiezan con encabezado `# <patología>` y línea `Source:`, aunque algunos de `data/dev` vienen como fragmentos continuos con `[...]` y secciones incrustadas. Suelen alternar definición inicial, etiopatogenia o causa, síntomas, diagnóstico, tratamiento y referencias, con encabezados simples como `Etiopatogenia`, `Síntomas`, `Diagnóstico` o `Tratamiento`. Para FSP conviene sintetizar esa estructura en textos compactos, cercanos a 1200-1600 caracteres cuando el campo lo necesite, separando causa, manifestaciones principales, complicaciones o signos secundarios, y métodos diagnósticos concretos; las ausencias deben surgir del foco clínico del texto, no de frases fabricadas para el benchmark.
