# cultural_extraction

Los tasks `cultural_extraction` son extracciones L1 de un unico fragmento verbatim desde articulos culturales en espanol, normalmente resenas o recomendaciones de cine y television. El modelo debe responder con una clausula textual suficiente para contestar la pregunta, no con una entidad aislada si el fragmento completo explica la relacion pedida.

## Ejemplos revisados

- `data/dev_rev/cultural_extraction_001.json`
- `data/dev_rev/cultural_extraction_002.json`
- `data/dev/cultural_extraction_001.json`
- `data/dev/cultural_extraction_002.json`

Solo existen dos ejemplos del prefijo en `dev_rev` y los dos archivos de `data/dev` son las mismas instancias sin `golden_note`; por tanto no hay cinco ejemplos disponibles sin salir del prefijo.

## Dualidad por campo

| Campo | Opinion sobre dualidad |
| --- | --- |
| `answer` | Campo requerido, `string`, no nullable. Como el schema pide un unico fragmento verbatim, la dualidad principal esta en la forma de la evidencia: un fragmento que responde con responsable individual dentro de una frase opinativa y otro fragmento que responde con elenco multiple en una frase descriptiva. En ambos casos conviene conservar una clausula completa que establezca la relacion pedida, no solo el nombre propio. |

## Descriptions enriquecidas para RAG

| Campo | Description enriquecida |
| --- | --- |
| `answer` | Fragmento verbatim que responde directamente la pregunta cultural. Copia la cláusula u oración suficiente para establecer la relación pedida, por ejemplo quién dirigió o quién protagoniza, sin reducirla a nombres aislados ni añadir paráfrasis; ignora actores, títulos, creadores o comparaciones cercanas que sean distractores. |

## Propuesta de los dos ejemplos

| Campo | Ejemplo 1 | Ejemplo 2 |
| --- | --- | --- |
| `answer` | Fragmento verbal que identifica a la directora de una pelicula, con distractores de actores y titulos comparados. | Fragmento verbal que enumera a los protagonistas de una miniserie, con distractores de creadora, plataforma y personajes. |

## Input, output y reasoning propuestos

### Ejemplo 1

`input_text`:

```text
# 'La última noche de Vega' convierte un apagón en una pequeña joya de ciencia ficción doméstica

Hay películas que anuncian el fin del mundo con meteoritos y ejércitos digitales, y otras que entienden que basta con apagar una calle para que todo empiece a crujir. 'La última noche de Vega' pertenece a este segundo grupo: una cinta modesta, algo irregular, pero con intuición visual para convertir un barrio corriente en territorio de sospecha.

## Luces fuera

La película sigue a Clara, una operadora de radio que vuelve a casa justo cuando una tormenta deja sin electricidad a media ciudad. El guion no siempre evita el lugar común, pero la puesta en escena compensa muchas torpezas con sombras, silencios y buen uso del sonido. Vera Luján sostiene casi todo el peso emocional, mientras Daniel Arce aparece como vecino ambiguo.

Lo más interesante es que, detrás de una premisa de serie B, la película habla de vigilancia, dependencia tecnológica y culpa colectiva sin convertir cada diálogo en una pancarta. En ese equilibrio se nota la mano de su responsable: la directora de 'La última noche de Vega' es Paula Medina, que ya había probado en cortos su gusto por los espacios cerrados y las amenazas apenas visibles. No todo está al mismo nivel, pero cuando confía en esa atmósfera respira con personalidad.

## Un apagón con memoria

El tramo final explica demasiado y pierde parte del misterio, aunque deja una imagen preciosa de la ciudad recuperando la luz sin que sus personajes recuperen la calma. No es una obra redonda, pero sí una pequeña sorpresa íntima.
```

`instruction`:

```text
¿Quién dirigió la película 'La última noche de Vega'?
```

`output`:

```json
{
  "answer": "la directora de 'La última noche de Vega' es Paula Medina"
}
```

`reasoning`:

```json
{
  "answer": {
    "field_asks": "un fragmento verbatim del texto que responda quién dirigió la película 'La última noche de Vega'.",
    "relevant_fragments": "\"la directora de 'La última noche de Vega' es Paula Medina\".",
    "final_value": "Como el fragmento relevante identifica explícitamente a Paula Medina como directora de la película, el valor debe conservar esa cláusula verbatim completa."
  }
}
```

### Ejemplo 2

`input_text`:

```text
# La serie danesa que acaba de llegar a Filmin y demuestra que aún quedan dramas familiares sin piloto automático

El drama familiar televisivo lleva años convertido en una fábrica de secretos heredados, cenas tensas y hermanos que no se llaman hasta que muere alguien. 'Los mapas del invierno' no esquiva esas reglas, pero las usa con paciencia, más interesada en escuchar a sus personajes que en empujarles hacia el giro de guion.

## Herencias heladas

La miniserie arranca con el regreso de una cartógrafa a la isla donde creció, después de que su padre desaparezca durante una expedición menor. Lo que podría ser un thriller nórdico convencional se transforma en una historia sobre memoria, orgullo y versiones familiares contradictorias. Su creadora, Maja Holm, filma los paisajes como álbumes de fotos deteriorados.

La fuerza de 'Los mapas del invierno' está en su reparto. La miniserie está protagonizada por Ingrid Madsen, Jonas Eide y Clara Nygaard, que interpretan a tres hermanos incapaces de ponerse de acuerdo incluso cuando comparten la misma pérdida. Madsen aporta una dureza contenida, Eide funciona como contrapunto seco y Nygaard se lleva las escenas más delicadas.

## Frío de verdad

No todo encaja: algunos flashbacks repiten información y el desenlace quiere cerrar demasiadas heridas. Aun así, la serie encuentra voz propia en las conversaciones pequeñas, donde nadie dice la verdad pero todos entienden que ya no pueden seguir fingiendo.
```

`instruction`:

```text
¿Quiénes protagonizan la miniserie 'Los mapas del invierno'?
```

`output`:

```json
{
  "answer": "La miniserie está protagonizada por Ingrid Madsen, Jonas Eide y Clara Nygaard"
}
```

`reasoning`:

```json
{
  "answer": {
    "field_asks": "un fragmento verbatim del texto que responda quiénes protagonizan la miniserie 'Los mapas del invierno'.",
    "relevant_fragments": "\"La miniserie está protagonizada por Ingrid Madsen, Jonas Eide y Clara Nygaard\".",
    "final_value": "Como el fragmento relevante enumera explícitamente a las tres personas protagonistas, el valor debe conservar la frase verbatim que establece esa relación."
  }
}
```

## Estructura de los input_text

Los `input_text` revisados son articulos culturales en Markdown, sin linea `Source:`, con un encabezado largo de tono periodistico y opinativo, varios parrafos de resena y al menos un subtitulo `##` con juego verbal. El texto mezcla valoracion, comparaciones con otras obras, nombres de actores, directores, creadores o personajes, y una frase concreta que responde la pregunta. Los outputs curados conservan una clausula verbal completa como evidencia directa, por ejemplo "tras las camaras de..." o "Esta notable serie australiana esta protagonizada por...", en vez de reducir la respuesta a nombres aislados. Los nuevos ejemplos mantienen ese estilo de critica cultural, con distractores naturales y una longitud compacta cercana a 1500 caracteres, pero sin frases benchmark-aware que anuncien artificialmente la respuesta.
