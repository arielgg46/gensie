# legal_extraction

Los tasks `legal_extraction` son extracciones L1 de un unico fragmento verbatim desde textos normativos en espanol. El modelo debe localizar la frase legal que responde la pregunta y devolverla completa, conservando la redaccion del articulo, sin resumir ni normalizar el contenido.

## Ejemplos revisados

- `data/dev_rev/legal_extraction_002.json`
- `data/dev/legal_extraction_002.json`

Solo existe una instancia del prefijo en `dev_rev` y `data/dev` contiene la misma instancia sin `golden_note`; por tanto no hay mas ejemplos disponibles del prefijo para llegar a cinco.

## Dualidad por campo

| Campo | Opinion sobre dualidad |
| --- | --- |
| `answer` | Campo requerido, `string`, no nullable. La dualidad util esta en el tipo de fragmento legal: una oracion completa y directa bajo un articulo breve frente a un apartado numerado dentro de un articulo con varios incisos. En ambos casos la respuesta debe ser verbatim y suficientemente contextual, no una palabra aislada ni una reformulacion. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `answer` | Fragmento legal verbatim que responde exactamente la pregunta. Copia la oración o apartado completo que contiene la regla jurídica, sin resumir, modernizar, normalizar tildes ni reducir la respuesta a una palabra o cifra aislada; ignora artículos vecinos con materias parecidas que no respondan la pregunta. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `answer` | Oracion normativa directa en un articulo corto, parecida a "Los españoles son mayores de edad...". | Apartado numerado dentro de un articulo con varias reglas, donde el fragmento incluye la condicion y la consecuencia juridica. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
## Artículo 7

La capitalidad administrativa de la Comunidad Autónoma corresponde a la ciudad de Valdoria.


## Artículo 8

1. La bandera de la Comunidad estará formada por tres franjas horizontales de igual anchura, de colores verde, blanco y azul.

2. El escudo y el himno serán regulados por ley de la Asamblea, respetando la tradición histórica de sus municipios.

3. Las instituciones públicas podrán utilizar sus símbolos propios en los actos oficiales, de acuerdo con lo que establezcan sus normas internas.


## Artículo 9

Los poderes públicos promoverán el conocimiento de la historia, la cultura y las modalidades lingüísticas propias, especialmente en el sistema educativo y en los medios de titularidad pública.
```

`instruction`:

```text
¿A qué ciudad corresponde la capitalidad administrativa de la Comunidad Autónoma?
```

`output`:

```json
{
  "answer": "La capitalidad administrativa de la Comunidad Autónoma corresponde a la ciudad de Valdoria."
}
```

`reasoning`:

```json
{
  "answer": {
    "field_asks": "un fragmento verbatim del texto que responda a qué ciudad corresponde la capitalidad administrativa de la Comunidad Autónoma.",
    "relevant_fragments": "\"La capitalidad administrativa de la Comunidad Autónoma corresponde a la ciudad de Valdoria.\"",
    "final_value": "Como el fragmento relevante responde directamente la pregunta y nombra la ciudad, el valor debe conservar la oración legal completa."
  }
}
```

### Ejemplo 2

`input_text`:

```text
## Artículo 21

1. Los vecinos tendrán derecho a participar en los asuntos municipales mediante los procedimientos establecidos en la ley.

2. La iniciativa popular deberá estar suscrita por, al menos, el diez por ciento de los vecinos inscritos en el censo municipal.

3. No podrán ser objeto de iniciativa popular las materias tributarias, presupuestarias ni las relativas a la organización interna del Ayuntamiento.



## Artículo 22

1. El Pleno celebrará sesión ordinaria una vez al mes y sesión extraordinaria cuando lo solicite la Alcaldía o una cuarta parte de sus miembros.

2. Las sesiones serán públicas, salvo en los supuestos en que el debate pueda afectar al derecho fundamental de los ciudadanos al honor, a la intimidad personal o familiar o a la propia imagen.

3. Los acuerdos se adoptarán por mayoría simple, salvo que una norma con rango de ley exija mayoría absoluta.
```

`instruction`:

```text
¿Qué porcentaje de vecinos debe suscribir la iniciativa popular?
```

`output`:

```json
{
  "answer": "La iniciativa popular deberá estar suscrita por, al menos, el diez por ciento de los vecinos inscritos en el censo municipal."
}
```

`reasoning`:

```json
{
  "answer": {
    "field_asks": "un fragmento verbatim del texto que responda qué porcentaje de vecinos debe suscribir la iniciativa popular.",
    "relevant_fragments": "\"La iniciativa popular deberá estar suscrita por, al menos, el diez por ciento de los vecinos inscritos en el censo municipal.\"",
    "final_value": "Como el fragmento relevante incluye la regla completa y el porcentaje requerido, el valor debe conservar ese apartado como oración verbatim."
  }
}
```

## Estructura de los input_text

El `input_text` revisado es un fragmento legal en Markdown, sin linea `Source:`, compuesto por encabezados `## Artículo N`, parrafos normativos y apartados numerados. El estilo es sobrio, formal y no narrativo; no hay comentario editorial ni explicaciones fuera de la norma. La respuesta curada conserva la oracion completa que responde la pregunta, por ejemplo "Los españoles son mayores de edad a los dieciocho años.", en vez de devolver solo "dieciocho años". Los nuevos ejemplos mantienen articulos cercanos, distractores normativos en articulos vecinos y preguntas que obligan a escoger la frase exacta sin parafrasear.
