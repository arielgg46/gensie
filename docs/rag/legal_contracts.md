# legal_contracts

Los tasks `legal_contracts` son extracciones L5 de acuerdos jurídicos: el modelo debe identificar el título formal, clasificar el contrato en un enum cerrado, extraer fecha de vigencia, partes, número de cláusulas, jurisdicción aplicable, cláusulas de confidencialidad o limitación de responsabilidad, y cuantía económica cuando esté expresada, separando nombres comerciales, representantes, anexos, fechas de firma y cantidades accesorias que pueden funcionar como distractores.

## Ejemplos revisados

- `data/dev_rev/legal_contracts_001.json`
- `data/dev_rev/legal_contracts_002.json`
- `data/dev/legal_contracts_003.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `contract_title` | Requerido, `string`, no nullable. Dualidad entre título directo en encabezado y título formal rodeado de nombres abreviados o subtítulos internos. |
| `contract_type` | Enum requerido. Debe mapear a uno de estos valores: `PRESTACIÓN DE SERVICIOS`, `COMPRAVENTA`, `LABORAL`, `CONFIDENCIALIDAD`, `ACUERDO MARCO` u `OTRO`. Conviene alternar tipos frecuentes con tipos semánticos más específicos, como compraventa frente a confidencialidad. |
| `effective_date` | `string` vs `null`. Puede ser fecha normalizada `YYYY-MM-DD` si hay fecha completa de entrada en vigor, o verbatim si la vigencia se expresa de forma relativa. Debe contrastarse con fechas de firma, entrega o anexos que no sean vigencia. |
| `parties` | Array requerido. Dualidad entre dos partes limpias y partes con representantes, nombres comerciales, filiales o roles que no deben desplazar a las entidades firmantes. |
| `total_clauses` | Entero requerido. Debe contar cláusulas numeradas o nombradas, no párrafos introductorios, comparecencias, anexos ni apartados sin rango de cláusula. |
| `governing_law_jurisdiction` | `string` vs `null`. Valor cuando una cláusula asigna ley aplicable, fuero o jurisdicción; `null` si el contrato solo da domicilios, sedes o lugares de firma. |
| `has_nda_clause` | `true` vs `false`. `true` si hay confidencialidad, reserva de información o no divulgación; `false` si el texto solo habla de documentación, entrega o propiedad sin deber de secreto. |
| `has_liability_limitation` | `true` vs `false`. `true` si una cláusula limita, excluye o topa responsabilidad; `false` si solo regula garantías, penalizaciones o incumplimientos sin exención o límite explícito. |
| `monetary_amount` | `number` vs `null`. Valor si se indica una cuantía total del contrato; `null` si solo hay depósitos, gastos, penalizaciones, precios unitarios sin total o referencias no contractuales. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `contract_title` | Título directo: contrato de compraventa de maquinaria agrícola. | Título directo: acuerdo de confidencialidad para prototipo sanitario. |
| `contract_type` | `COMPRAVENTA`, por transmisión de un bien concreto a cambio de precio. | `CONFIDENCIALIDAD`, por deber principal de reserva sobre documentación técnica. |
| `effective_date` | Valor no null normalizado: entrada en vigor el 2 de mayo de 2026. | `null`: hay entrega de materiales y duración de obligaciones, pero no fecha de entrada en vigor. |
| `parties` | Dos sociedades firmantes, con representantes como ruido menor. | Dos entidades firmantes, una reveladora y otra receptora. |
| `total_clauses` | Cuatro cláusulas numeradas. | Tres cláusulas numeradas. |
| `governing_law_jurisdiction` | Valor no null: leyes españolas y tribunales de Barcelona. | `null`: no se pacta ley aplicable ni fuero. |
| `has_nda_clause` | `false`: el contrato regula entrega, precio, garantía y responsabilidad, sin reserva de información. | `true`: cláusula expresa de confidencialidad y no divulgación. |
| `has_liability_limitation` | `true`: cláusula con límite máximo de responsabilidad. | `false`: hay deberes y devolución de soportes, pero no límite o exención de responsabilidad. |
| `monetary_amount` | `125000`, precio total del contrato. | `null`: no se pacta precio total. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# CONTRATO DE COMPRAVENTA DE MAQUINARIA AGRÍCOLA

En Barcelona, a 2 de mayo de 2026, comparecen Talleres Montseny S.L., representada por Clara Vidal, como parte vendedora, y Cooperativa Vall del Segre, representada por Joan Riera, como parte compradora. Ambas partes manifiestan interés en formalizar la transmisión de una cosechadora modelo Aurum 420, con sus accesorios descritos en el inventario anexo.

CLÁUSULAS

PRIMERA. Objeto.
La vendedora transmite a la compradora la propiedad de la cosechadora Aurum 420 y de dos cabezales de corte revisados el mes anterior.

SEGUNDA. Precio y pago.
El precio total de la compraventa se fija en 125.000 euros, pagaderos en dos transferencias bancarias: una al firmar y otra contra entrega de la máquina.

TERCERA. Entrada en vigor y entrega.
El contrato entrará en vigor el 2 de mayo de 2026. La entrega se realizará antes del 20 de mayo en la finca de Bellpuig.

CUARTA. Responsabilidad, ley aplicable y fuero.
La responsabilidad de la vendedora por defectos ocultos quedará limitada al importe efectivamente pagado por la compradora. El contrato se regirá por las leyes de España y las partes se someten a los juzgados y tribunales de Barcelona.
```

`instruction`:

```text
Extrae el resumen del contrato o acto legislativo
```

`output`:

```json
{
  "contract_title": "CONTRATO DE COMPRAVENTA DE MAQUINARIA AGRÍCOLA",
  "contract_type": "COMPRAVENTA",
  "effective_date": "2026-05-02",
  "parties": [
    "Talleres Montseny S.L.",
    "Cooperativa Vall del Segre"
  ],
  "total_clauses": 4,
  "governing_law_jurisdiction": "España; juzgados y tribunales de Barcelona",
  "has_nda_clause": false,
  "has_liability_limitation": true,
  "monetary_amount": 125000
}
```

`reasoning`:

```json
{
  "contract_title": {
    "field_asks": "el título formal o encabezado del contrato.",
    "relevant_fragments": "\"# CONTRATO DE COMPRAVENTA DE MAQUINARIA AGRÍCOLA\".",
    "final_value": "Como el fragmento relevante es el encabezado formal, el título debe ser \"CONTRATO DE COMPRAVENTA DE MAQUINARIA AGRÍCOLA\"."
  },
  "contract_type": {
    "field_asks": "la categoría legal amplia del acuerdo, mapeada a uno de estos valores: PRESTACIÓN DE SERVICIOS, COMPRAVENTA, LABORAL, CONFIDENCIALIDAD, ACUERDO MARCO u OTRO.",
    "relevant_fragments": "\"CONTRATO DE COMPRAVENTA\" y \"formalizar la transmisión de una cosechadora modelo Aurum 420\".",
    "final_value": "Como los fragmentos relevantes describen transmisión de un bien a cambio de precio, el valor del enum debe ser \"COMPRAVENTA\"."
  },
  "effective_date": {
    "field_asks": "la fecha en que el contrato entra en vigor, en formato YYYY-MM-DD si es normalizable o verbatim si solo aparece de forma relativa.",
    "relevant_fragments": "\"El contrato entrará en vigor el 2 de mayo de 2026\".",
    "final_value": "Como el fragmento relevante da una fecha completa de entrada en vigor, debe normalizarse a \"2026-05-02\"."
  },
  "parties": {
    "field_asks": "los nombres de las personas u organizaciones que celebran el acuerdo.",
    "relevant_fragments": "\"comparecen Talleres Montseny S.L., representada por Clara Vidal, como parte vendedora, y Cooperativa Vall del Segre, representada por Joan Riera, como parte compradora\".",
    "final_value": "Como el fragmento relevante presenta a las dos sociedades como partes y a Clara Vidal y Joan Riera como representantes, la lista debe incluir \"Talleres Montseny S.L.\" y \"Cooperativa Vall del Segre\"."
  },
  "total_clauses": {
    "field_asks": "el número total de cláusulas numeradas o nombradas del contrato.",
    "relevant_fragments": "\"PRIMERA. Objeto.\", \"SEGUNDA. Precio y pago.\", \"TERCERA. Entrada en vigor y entrega.\" y \"CUARTA. Responsabilidad, ley aplicable y fuero.\".",
    "final_value": "Como los fragmentos relevantes muestran cuatro cláusulas numeradas, el total debe ser 4."
  },
  "governing_law_jurisdiction": {
    "field_asks": "el país, estado o jurisdicción cuya ley o tribunales gobiernan el contrato, o null si no hay pacto de ley aplicable o fuero.",
    "relevant_fragments": "\"El contrato se regirá por las leyes de España\" y \"las partes se someten a los juzgados y tribunales de Barcelona\".",
    "final_value": "Como los fragmentos relevantes fijan ley española y fuero en Barcelona, el valor debe ser \"España; juzgados y tribunales de Barcelona\"."
  },
  "has_nda_clause": {
    "field_asks": "true si el texto menciona confidencialidad, reserva de información o no divulgación; false si no lo hace.",
    "relevant_fragments": "\"La vendedora transmite a la compradora la propiedad\", \"El precio total de la compraventa se fija en 125.000 euros\" y \"Responsabilidad, ley aplicable y fuero\".",
    "final_value": "Los fragmentos relevantes cubren objeto, precio, responsabilidad y fuero, pero no establecen confidencialidad ni no divulgación; el valor debe ser false."
  },
  "has_liability_limitation": {
    "field_asks": "true si el texto limita, excluye o topa responsabilidad; false si no hay limitación explícita.",
    "relevant_fragments": "\"La responsabilidad de la vendedora por defectos ocultos quedará limitada al importe efectivamente pagado por la compradora\".",
    "final_value": "Como el fragmento relevante limita expresamente la responsabilidad de la vendedora, el valor debe ser true."
  },
  "monetary_amount": {
    "field_asks": "el importe total del contrato si se especifica numéricamente, o null si no hay cuantía total.",
    "relevant_fragments": "\"El precio total de la compraventa se fija en 125.000 euros\".",
    "final_value": "Como el fragmento relevante da el precio total, el importe debe ser 125000."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# ACUERDO DE CONFIDENCIALIDAD PARA PROTOTIPO AURORA

REUNIDOS

Atlas BioData S.L., titular de varios informes preliminares sobre el prototipo Aurora, actúa como parte reveladora. Clínica Norte S.A., interesada en evaluar la viabilidad de una prueba piloto con pacientes simulados, actúa como parte receptora. Las personas firmantes comparecen en nombre de sus entidades y dejan constancia de que el material será entregado en una sala segura del hospital.

CLÁUSULAS

PRIMERA. Objeto.
La parte reveladora facilitará memorias técnicas, esquemas de sensores y resultados agregados de laboratorio para que la receptora valore una colaboración futura.

SEGUNDA. Confidencialidad y no divulgación.
La receptora tratará toda la información recibida como confidencial, no la comunicará a terceros y limitará su acceso al equipo médico autorizado para la revisión del prototipo.

TERCERA. Conservación y devolución.
Las obligaciones de reserva se mantendrán durante dos años desde la entrega de cada lote documental. Los soportes físicos deberán devolverse o destruirse cuando finalice la evaluación interna.
```

`instruction`:

```text
Extrae el resumen del contrato o acto legislativo
```

`output`:

```json
{
  "contract_title": "ACUERDO DE CONFIDENCIALIDAD PARA PROTOTIPO AURORA",
  "contract_type": "CONFIDENCIALIDAD",
  "effective_date": null,
  "parties": [
    "Atlas BioData S.L.",
    "Clínica Norte S.A."
  ],
  "total_clauses": 3,
  "governing_law_jurisdiction": null,
  "has_nda_clause": true,
  "has_liability_limitation": false,
  "monetary_amount": null
}
```

`reasoning`:

```json
{
  "contract_title": {
    "field_asks": "el título formal o encabezado del contrato.",
    "relevant_fragments": "\"# ACUERDO DE CONFIDENCIALIDAD PARA PROTOTIPO AURORA\".",
    "final_value": "Como el fragmento relevante es el encabezado formal, el título debe ser \"ACUERDO DE CONFIDENCIALIDAD PARA PROTOTIPO AURORA\"."
  },
  "contract_type": {
    "field_asks": "la categoría legal amplia del acuerdo, mapeada a uno de estos valores: PRESTACIÓN DE SERVICIOS, COMPRAVENTA, LABORAL, CONFIDENCIALIDAD, ACUERDO MARCO u OTRO.",
    "relevant_fragments": "\"ACUERDO DE CONFIDENCIALIDAD\" y \"Confidencialidad y no divulgación\".",
    "final_value": "Como los fragmentos relevantes sitúan la reserva de información como objeto central del acuerdo, el valor del enum debe ser \"CONFIDENCIALIDAD\"."
  },
  "effective_date": {
    "field_asks": "la fecha en que el contrato entra en vigor, en formato YYYY-MM-DD si es normalizable o verbatim si solo aparece de forma relativa.",
    "relevant_fragments": "\"el material será entregado en una sala segura del hospital\" y \"Las obligaciones de reserva se mantendrán durante dos años desde la entrega de cada lote documental\".",
    "final_value": "Los fragmentos relevantes hablan de entrega de materiales y duración de las obligaciones, pero no fijan una fecha de entrada en vigor del acuerdo; el valor debe ser null."
  },
  "parties": {
    "field_asks": "los nombres de las personas u organizaciones que celebran el acuerdo.",
    "relevant_fragments": "\"Atlas BioData S.L. [...] actúa como parte reveladora\" y \"Clínica Norte S.A. [...] actúa como parte receptora\".",
    "final_value": "Como los fragmentos relevantes nombran a las dos entidades que celebran el acuerdo, la lista debe incluir \"Atlas BioData S.L.\" y \"Clínica Norte S.A.\"."
  },
  "total_clauses": {
    "field_asks": "el número total de cláusulas numeradas o nombradas del contrato.",
    "relevant_fragments": "\"PRIMERA. Objeto.\", \"SEGUNDA. Confidencialidad y no divulgación.\" y \"TERCERA. Conservación y devolución.\".",
    "final_value": "Como los fragmentos relevantes muestran tres cláusulas numeradas, el total debe ser 3."
  },
  "governing_law_jurisdiction": {
    "field_asks": "el país, estado o jurisdicción cuya ley o tribunales gobiernan el contrato, o null si no hay pacto de ley aplicable o fuero.",
    "relevant_fragments": "\"PRIMERA. Objeto.\", \"SEGUNDA. Confidencialidad y no divulgación.\" y \"TERCERA. Conservación y devolución.\".",
    "final_value": "Los fragmentos relevantes delimitan las tres cláusulas sustantivas del acuerdo y ninguna fija ley aplicable, fuero o jurisdicción; el valor debe ser null."
  },
  "has_nda_clause": {
    "field_asks": "true si el texto menciona confidencialidad, reserva de información o no divulgación; false si no lo hace.",
    "relevant_fragments": "\"La receptora tratará toda la información recibida como confidencial, no la comunicará a terceros\".",
    "final_value": "Como el fragmento relevante establece confidencialidad y no divulgación, el valor debe ser true."
  },
  "has_liability_limitation": {
    "field_asks": "true si el texto limita, excluye o topa responsabilidad; false si no hay limitación explícita.",
    "relevant_fragments": "\"La receptora tratará toda la información recibida como confidencial\" y \"Los soportes físicos deberán devolverse o destruirse\".",
    "final_value": "Los fragmentos relevantes imponen deberes de reserva y devolución, pero no limitan ni excluyen responsabilidad; el valor debe ser false."
  },
  "monetary_amount": {
    "field_asks": "el importe total del contrato si se especifica numéricamente, o null si no hay cuantía total.",
    "relevant_fragments": "\"valore una colaboración futura\" y \"Las obligaciones de reserva se mantendrán durante dos años\".",
    "final_value": "Los fragmentos relevantes describen una evaluación futura y duración de obligaciones, pero no fijan un precio total del contrato; el valor debe ser null."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados tienen forma de contrato en Markdown: encabezado `# <título>`, lugar o fecha inicial, sección de comparecencia o partes, exposición breve y cláusulas numeradas con nombres como objeto, entrada en vigor, honorarios, confidencialidad, responsabilidad o ley aplicable. Para los nuevos ejemplos conviene mantener textos compactos de menos de 1600 caracteres, con cláusulas claras y contables, fechas y cuantías solo cuando sean jurídicamente relevantes para el campo, y distractores naturales como representantes, anexos, entregas o sedes que no sustituyan a partes, vigencia ni jurisdicción.
