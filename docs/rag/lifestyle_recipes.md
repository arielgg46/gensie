# lifestyle_recipes

Los tasks `lifestyle_recipes` son extracciones L10 de recetas o descripciones culinarias: el modelo debe estructurar ingredientes con cantidades y unidades cuando existan, inferir raciones, tiempo total, dificultad, compatibilidad dietética y secuencia de técnicas, incluso cuando el texto sea enciclopédico o procedimental y no una receta con lista formal.

## Ejemplos revisados

- `data/dev_rev/lifestyle_recipes_01.json`
- `data/dev/lifestyle_recipes_02.json`
- `data/dev/lifestyle_recipes_03.json`
- `data/dev/lifestyle_recipes_08.json`
- `data/dev/lifestyle_recipes_05.json`

## Dualidad por campo

| Campo | Opinión sobre dualidad |
| --- | --- |
| `dish_name` | Requerido, `string`, no nullable. Dualidad entre nombre directo del encabezado y nombre de receta dentro del cuerpo cuando el encabezado es una técnica o ingrediente. |
| `servings` | `integer` vs `null`. Dualidad entre raciones explícitas y textos enciclopédicos o tradicionales sin número de porciones. |
| `ingredients` | Array requerido. Dualidad entre ingredientes con cantidades/unidades explícitas y nombres sin cantidad. Debe preservar nombres verbatim y usar `amount: null` y `unit: null` cuando el texto no cuantifica. En los ejemplos revisados conviene quedarse con la base canónica de preparación y no añadir guarniciones, platos derivados o variantes locales opcionales. |
| `ingredients[].unit` | Enum o `null`. Debe mapear a uno de estos valores: `g`, `ml`, `kg`, `unidad`, `pizca`, `cucharada` u `otro`; si la unidad no aparece o no es interpretable, `null`. |
| `complexity_score` | Entero 1-10. No es textual: debe inferirse por número de pasos, técnicas, precisión y tiempo. Conviene contrastar receta muy simple frente a una con varias fases. |
| `dietary_tags` | `[]` vs lista poblada. Debe mapear a `VEGANO`, `VEGETARIANO`, `SIN GLUTEN`, `SIN LÁCTEOS` o `BAJO EN CARBOHIDRATOS`. Se infiere por ausencia/presencia de carne, pescado, lácteos, gluten y carga de carbohidratos. |
| `technique_sequence` | Array requerido con valores `SOFREÍR`, `HERVIR`, `HORNEAR`, `FREÍR`, `VAPOR` o `COCCIÓN LENTA`. Dualidad entre técnica única y varias técnicas cronológicas. Si el texto no describe cocción aplicable, puede quedar vacío, como en adobo. |
| `total_time_minutes` | `integer` vs `null`. Dualidad entre tiempo total explícito o sumable y tiempos vagos como "hasta que esté tierno", "toda la tarde" o ausencia de duración. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `dish_name` | Nombre del plato, técnica o preparación principal, normalmente el encabezado `#`. Si el encabezado es genérico, usa el nombre de receta que el cuerpo presenta como preparación central; no elijas variantes, guarniciones ni platos listados en “véase también”. |
| `servings` | Número de raciones o porciones si aparece explícito. Devuelve `null` en entradas enciclopédicas sin cantidad de servicio; no infieras raciones desde número de ingredientes, tamaño de cazuela o costumbre familiar. |
| `ingredients` | Ingredientes de la preparación básica, con `amount` y `unit` cuando existan. No incluyas variantes opcionales, acompañamientos, platos derivados, notas históricas ni ingredientes de otras acepciones regionales si el texto los separa de la receta principal. |
| `ingredients[].unit` | Unidad normalizada; enum completo: `g`, `ml`, `kg`, `unidad`, `pizca`, `cucharada` u `otro`, además de `null` cuando no haya unidad. Usa `otro` para unidades textuales no incluidas como vaso o taza; no inventes unidades cuando el texto solo nombra el ingrediente. |
| `complexity_score` | Dificultad inferida de 1 a 10 según número de fases, control de textura, técnicas, precisión y tiempo. Usa 1-2 para mezcla, montaje o cocción muy simple; 3-4 para una o dos técnicas básicas con poco control fino, como cortar, vapor y aliño; 5-6 para guisos, sofritos con hervor o varias fases moderadas; 7-8 para marinado, reducción, horno, reposos o control de textura; 9-10 para técnicas precisas o profesionales. |
| `dietary_tags` | Etiquetas dietéticas inferidas del enum completo: `VEGANO`, `VEGETARIANO`, `SIN GLUTEN`, `SIN LÁCTEOS` o `BAJO EN CARBOHIDRATOS`. Evalúa la preparación básica, no acompañamientos opcionales; carne/pescado bloquea vegano/vegetariano; harina, pan o cerveza bloquean sin gluten; leche, yogur, queso, mantequilla, nata/crema, suero o leche en polvo bloquean sin lácteos si forman parte de la preparación principal. |
| `technique_sequence` | Secuencia cronológica de técnicas del enum completo: `SOFREÍR`, `HERVIR`, `HORNEAR`, `FREÍR`, `VAPOR` o `COCCIÓN LENTA`. Extrae solo técnicas descritas como preparación del plato; adobo, macerado, reposo o servicio no se fuerzan a un enum si no corresponden. |
| `total_time_minutes` | Tiempo total en minutos cuando el texto da tiempos explícitos posiblemente sumables. Devuelve `null` con expresiones vagas como “hasta que esté tierno”, “a fuego bajo”, “calor residual” o ausencia de duración. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `dish_name` | Nombre directo de receta vegetal. | Nombre directo de receta cárnica tradicional. |
| `servings` | Valor no null, por ejemplo 2 o 4 raciones explícitas. | `null`, sin raciones indicadas. |
| `ingredients` | Ingredientes con cantidades y unidades variadas. | Ingredientes nombrados sin cantidades precisas. |
| `complexity_score` | Medio-bajo, 4, por corte, vapor, reposo separado y aliño. | Medio-alto, 7, por marinado, sofrito, cocción lenta y horneado final. |
| `dietary_tags` | Lista poblada: `VEGANO`, `VEGETARIANO`, `SIN GLUTEN`, `SIN LÁCTEOS`. | `[]`, por carne, cerveza con gluten y mantequilla. |
| `technique_sequence` | Técnica única `VAPOR`. | Secuencia con `SOFREÍR`, `COCCIÓN LENTA`, `HORNEAR`. |
| `total_time_minutes` | Valor no null, inferido como suma de dos fases sucesivas, por ejemplo 18 + 7 minutos. | `null`, tiempos vagos y dependientes de textura. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# Berenjenas al vapor con tahini

Source: https://es.wikipedia.org/wiki/Berenjenas_al_vapor_con_tahini

Las berenjenas al vapor con tahini son una preparación vegetal de servicio templado, habitual como entrante. Para 2 raciones se usan 2 berenjenas pequeñas, 2 cucharadas de tahini, 30 ml de zumo de limón, 1 cucharada de aceite de oliva, 1 pizca de sal y hojas de perejil picadas.

== Contexto ==
La receta se asocia a mesas mediterráneas donde las hortalizas cocidas se sirven con salsas de semillas o frutos secos. A diferencia de las berenjenas rebozadas, no emplea harina ni huevo; la grasa procede del tahini y del aceite de oliva.

== Preparación ==
Las berenjenas se cortan en tiras gruesas y se cocinan al vapor durante 18 minutos, hasta que la pulpa queda tierna pero conserva la forma. Después se colocan en una fuente y reposan 7 minutos antes de cubrirlas con la salsa de tahini, limón, aceite y sal.

En algunas versiones se espolvorea sésamo tostado o granos de granada; en bares se sirve a veces con pan de pita, aunque esos añadidos no forman parte de la preparación básica.
```

`instruction`:

```text
Extrae la receta.
```

`output`:

```json
{
  "dish_name": "Berenjenas al vapor con tahini",
  "servings": 2,
  "ingredients": [
    {
      "name": "berenjenas pequeñas",
      "amount": 2,
      "unit": "unidad"
    },
    {
      "name": "tahini",
      "amount": 2,
      "unit": "cucharada"
    },
    {
      "name": "zumo de limón",
      "amount": 30,
      "unit": "ml"
    },
    {
      "name": "aceite de oliva",
      "amount": 1,
      "unit": "cucharada"
    },
    {
      "name": "sal",
      "amount": 1,
      "unit": "pizca"
    },
    {
      "name": "perejil",
      "amount": null,
      "unit": null
    }
  ],
  "complexity_score": 4,
  "dietary_tags": [
    "VEGANO",
    "VEGETARIANO",
    "SIN GLUTEN",
    "SIN LÁCTEOS"
  ],
  "technique_sequence": [
    "VAPOR"
  ],
  "total_time_minutes": 25
}
```

`reasoning`:

```json
{
  "dish_name": {
    "field_asks": "el nombre de la receta.",
    "relevant_fragments": "\"# Berenjenas al vapor con tahini\".",
    "final_value": "Como el fragmento relevante es el encabezado de la receta, el nombre debe ser \"Berenjenas al vapor con tahini\"."
  },
  "servings": {
    "field_asks": "número de raciones o porciones, o null si no se indica.",
    "relevant_fragments": "\"Para 2 raciones\".",
    "final_value": "Como el fragmento relevante da el número de raciones, el valor debe ser 2."
  },
  "ingredients": {
    "field_asks": "lista estructurada de ingredientes; cada unidad debe mapearse a g, ml, kg, unidad, pizca, cucharada, otro o null.",
    "relevant_fragments": "\"Para 2 raciones se usan 2 berenjenas pequeñas, 2 cucharadas de tahini, 30 ml de zumo de limón, 1 cucharada de aceite de oliva, 1 pizca de sal y hojas de perejil picadas\" y \"En algunas versiones se espolvorea sésamo tostado o granos de granada [...] aunque esos añadidos no forman parte de la preparación básica\".",
    "final_value": "Como el primer fragmento relevante da los ingredientes de la preparación básica, se extraen las cantidades y unidades explícitas; el perejil queda con amount y unit null porque no tiene cantidad numérica. El segundo fragmento relevante presenta sésamo, granada y pan de pita como variantes o acompañamientos, por lo que no deben añadirse a la lista canónica."
  },
  "complexity_score": {
    "field_asks": "dificultad inferida de 1 a 10 según pasos, técnicas y tiempo.",
    "relevant_fragments": "\"se cortan en tiras gruesas\", \"se cocinan al vapor durante 18 minutos\", \"reposan 7 minutos\" y \"cubrirlas con la salsa de tahini, limón, aceite y sal\".",
    "final_value": "Como los fragmentos relevantes combinan corte, control de punto al vapor, reposo separado y aliño, la dificultad es medio-baja y no mínima; el valor debe ser 4."
  },
  "dietary_tags": {
    "field_asks": "etiquetas dietéticas inferidas, usando solo estos valores: VEGANO, VEGETARIANO, SIN GLUTEN, SIN LÁCTEOS o BAJO EN CARBOHIDRATOS.",
    "relevant_fragments": "\"berenjenas\", \"tahini\", \"zumo de limón\", \"aceite de oliva\", \"sal\", \"no emplea harina ni huevo\" y \"pan de pita [...] no forma parte de la preparación básica\".",
    "final_value": "Como los fragmentos relevantes de la preparación básica solo contienen ingredientes vegetales, sin lácteos ni harina, la lista debe incluir \"VEGANO\", \"VEGETARIANO\", \"SIN GLUTEN\" y \"SIN LÁCTEOS\". El pan de pita aparece como acompañamiento externo, no como parte canónica del plato, y por eso no bloquea \"SIN GLUTEN\" para la preparación básica."
  },
  "technique_sequence": {
    "field_asks": "secuencia cronológica de técnicas principales, usando solo estos valores: SOFREÍR, HERVIR, HORNEAR, FREÍR, VAPOR o COCCIÓN LENTA.",
    "relevant_fragments": "\"se cocinan al vapor durante 18 minutos\".",
    "final_value": "Como el fragmento relevante solo describe cocción al vapor, la secuencia debe ser [\"VAPOR\"]."
  },
  "total_time_minutes": {
    "field_asks": "duración total normalizada en minutos, o null si no hay tiempo suficiente.",
    "relevant_fragments": "\"se cocinan al vapor durante 18 minutos\" y \"reposan 7 minutos antes de cubrirlas con la salsa\".",
    "final_value": "Como los fragmentos relevantes dan dos fases sucesivas, 18 minutos de vapor y 7 minutos de reposo posterior, la duración total sumable debe ser 25."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# Costillas con cerveza negra

Source: https://es.wikipedia.org/wiki/Costillas_con_cerveza_negra

Las costillas con cerveza negra son una preparación de carne guisada y acabada al horno, habitual en recetarios domésticos de invierno.

== Historia ==
La receta se documenta en cuadernos familiares de cocina centroeuropea y se adaptó en bares españoles como plato de temporada. Suele relacionarse con comidas de domingo y con el aprovechamiento de cortes con hueso que necesitan una cocción prolongada.

== Preparación ==
Las costillas con cerveza negra se preparan frotando la carne con sal, pimienta y pimentón. En una cazuela amplia se sofríen cebolla y ajo con mantequilla hasta que toman color; después se añade la carne, un vaso de cerveza negra, miel y laurel. La cazuela queda a fuego muy bajo hasta que la salsa se vuelve espesa y la carne empieza a separarse del hueso.

Al final se pasan las costillas a una bandeja, se pintan con la salsa reducida y se terminan en el horno fuerte para que la superficie quede brillante. En algunas casas se sirve con pan tostado para recoger la salsa.
```

`instruction`:

```text
Extrae la receta.
```

`output`:

```json
{
  "dish_name": "Costillas con cerveza negra",
  "servings": null,
  "ingredients": [
    {
      "name": "costillas",
      "amount": null,
      "unit": null
    },
    {
      "name": "sal",
      "amount": null,
      "unit": null
    },
    {
      "name": "pimienta",
      "amount": null,
      "unit": null
    },
    {
      "name": "pimentón",
      "amount": null,
      "unit": null
    },
    {
      "name": "cebolla",
      "amount": null,
      "unit": null
    },
    {
      "name": "ajo",
      "amount": null,
      "unit": null
    },
    {
      "name": "mantequilla",
      "amount": null,
      "unit": null
    },
    {
      "name": "cerveza negra",
      "amount": 1,
      "unit": "otro"
    },
    {
      "name": "miel",
      "amount": null,
      "unit": null
    },
    {
      "name": "laurel",
      "amount": null,
      "unit": null
    }
  ],
  "complexity_score": 7,
  "dietary_tags": [],
  "technique_sequence": [
    "SOFREÍR",
    "COCCIÓN LENTA",
    "HORNEAR"
  ],
  "total_time_minutes": null
}
```

`reasoning`:

```json
{
  "dish_name": {
    "field_asks": "el nombre de la receta.",
    "relevant_fragments": "\"# Costillas con cerveza negra\".",
    "final_value": "Como el fragmento relevante es el encabezado de la receta, el nombre debe ser \"Costillas con cerveza negra\"."
  },
  "servings": {
    "field_asks": "número de raciones o porciones, o null si no se indica.",
    "relevant_fragments": "\"Las costillas con cerveza negra se preparan\" y \"En algunas casas se sirve con pan tostado\".",
    "final_value": "Los fragmentos relevantes describen preparación y servicio, pero no dan número de raciones; el valor debe ser null."
  },
  "ingredients": {
    "field_asks": "lista estructurada de ingredientes; cada unidad debe mapearse a g, ml, kg, unidad, pizca, cucharada, otro o null.",
    "relevant_fragments": "\"costillas\", \"sal, pimienta y pimentón\", \"cebolla y ajo con mantequilla\", \"un vaso de cerveza negra, miel y laurel\" y \"En algunas casas se sirve con pan tostado\".",
    "final_value": "Como los fragmentos relevantes listan ingredientes sin cantidades numéricas salvo \"un vaso\", la mayoría queda con amount y unit null; \"un vaso\" se normaliza como amount 1 y unit \"otro\". El último fragmento habla de cómo se sirve en algunos lugares, pero no se incluye pan tostado como parte principal de la receta o plato."
  },
  "complexity_score": {
    "field_asks": "dificultad inferida de 1 a 10 según pasos, técnicas y tiempo.",
    "relevant_fragments": "\"se sofríen cebolla y ajo\", \"queda a fuego muy bajo hasta que la salsa se vuelve espesa\", \"se pintan con la salsa reducida\" y \"se terminan en el horno fuerte\".",
    "final_value": "Como los fragmentos relevantes combinan varias fases y control de textura, la dificultad debe ser relativamente alta: 7."
  },
  "dietary_tags": {
    "field_asks": "etiquetas dietéticas inferidas, usando solo estos valores: VEGANO, VEGETARIANO, SIN GLUTEN, SIN LÁCTEOS o BAJO EN CARBOHIDRATOS.",
    "relevant_fragments": "\"costillas\", \"mantequilla\", \"cerveza negra\" y \"pan tostado\".",
    "final_value": "Como los fragmentos relevantes de la preparación principal contienen carne, mantequilla como lácteo y cerveza negra con gluten, no corresponde ninguna de las etiquetas dietéticas permitidas; la lista debe ser vacía. El pan tostado es acompañamiento opcional y no decide la etiqueta por sí solo."
  },
  "technique_sequence": {
    "field_asks": "secuencia cronológica de técnicas principales, usando solo estos valores: SOFREÍR, HERVIR, HORNEAR, FREÍR, VAPOR o COCCIÓN LENTA.",
    "relevant_fragments": "\"se sofríen cebolla y ajo\", \"queda a fuego muy bajo\" y \"se terminan en el horno fuerte\".",
    "final_value": "Como los fragmentos relevantes describen primero sofrito, luego cocción lenta y al final horno, la secuencia debe ser [\"SOFREÍR\", \"COCCIÓN LENTA\", \"HORNEAR\"]."
  },
  "total_time_minutes": {
    "field_asks": "duración total normalizada en minutos, o null si no hay tiempo suficientemente concreto.",
    "relevant_fragments": "\"hasta que la salsa se vuelve espesa\" y \"hasta que la superficie quede brillante\".",
    "final_value": "Los fragmentos relevantes expresan puntos de textura, pero no una duración total ni tiempos sumables; el valor debe ser null."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados pueden ser entradas enciclopédicas sobre platos, técnicas o ingredientes, no siempre recetas formales: encabezado `# <plato>`, línea de fuente, descripción de origen, ingredientes y preparación. Para los FSP conviene usar textos más compactos y procedimentales, con ingredientes y pasos suficientes para inferir dieta, dificultad, técnicas y tiempo sin escribir frases que anuncien mecánicamente la ausencia de un campo.
