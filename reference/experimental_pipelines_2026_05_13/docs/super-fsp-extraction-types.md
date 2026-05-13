# Tipos de extraccion para el super FSP

Este documento resume los tipos de subtareas de extraccion observados al revisar un ejemplo por prefijo en `data/dev_rev`, junto con `docs/description.md`, `docs/gensie (PDF to MD).md` y el FSP actual de `src/gensie/enriched_inline_reasoning.py`.

El objetivo no es clasificar por dominio, sino por forma de razonamiento y forma JSON que el modelo debe aprender a producir en un few-shot prompt dinamico.

## Principio general

GenSIE evalua extraccion estructurada y grounded. Un buen FSP debe mostrar, de forma compacta, que el modelo debe:

- respetar estrictamente el schema;
- citar evidencia textual en `reasoning`;
- separar evidencia extractiva, normalizacion e inferencia;
- devolver `null` cuando el dato no esta en el texto y el schema lo permite;
- devolver `[]` cuando el campo es un array no nullable y no hay elementos;
- devolver `false` solo cuando el booleano no nullable se define como ausencia o negacion grounded;
- no usar conocimiento externo para completar trampas de hallucination.

## Tipos observados

### 1. String verbatim de respuesta QA

Campos tipo `answer`, usualmente con una pregunta en la instruction. El valor debe ser una frase o fragmento exacto del texto, no una respuesta abreviada.

Aparece en `technical_extraction`, `legal_extraction`, `medical_extraction` y `cultural_extraction`.

Riesgo que debe cubrir el FSP: el modelo tiende a responder solo la entidad o una frase reformulada. El ejemplo debe ensenar a copiar el fragmento minimo completo que responde la pregunta.

### 2. String scalar directo

Campos como titulos, nombres oficiales, licencias, municipios, desarrolladores o jurisdicciones.

Ejemplos reales: `official_name`, `contract_title`, `license`, `primary_developer`, `municipality`.

Riesgo: copiar un alias secundario en lugar del nombre principal, o devolver un fragmento demasiado largo cuando el campo pide solo el valor.

### 3. String de resumen o sintesis grounded

Campos como `summary`, `key_verdict` o `etiology_description`.

No son copia literal pura. Requieren condensar hechos del texto sin introducir informacion externa.

Riesgo: hacer un resumen plausible pero no apoyado por el texto, o copiar una oracion demasiado larga sin sintetizar.

### 4. String verbatim largo de evidencia

Campos que piden explicitamente `verbatim`, `source text`, `evidence` o fragmento completo.

El FSP actual ya cubre este caso con `literary_impact_evidence`.

Riesgo: devolver solo la entidad final o una etiqueta normalizada cuando el campo pide el fragmento textual completo.

### 5. Enum por clasificacion o inferencia

Campos rigid strings con opciones cerradas.

Ejemplos reales: `sentiment`, `category`, `contract_type`, `law_range`, `body_type`, `app_category`, `etiology_type`, `probability`, `impact`.

Riesgo: inventar etiquetas, cambiar mayusculas/minusculas, traducir el enum o devolver una frase libre. El FSP debe mostrar que el valor debe coincidir exactamente con una opcion del schema.

### 6. Numeros normalizados

Incluye enteros y flotantes extraidos desde texto con unidades, separadores o expresiones verbales.

Ejemplos reales: `publication_year`, `total_clauses`, `casualties`, `injured`, `complexity_score`, `monetary_amount`, `orbital_period_days`.

Riesgo: dejar unidades en campos numericos, copiar `50.000 euros` como string cuando el schema pide number, o no contar secciones enumeradas.

### 7. Booleanos inferidos no nullable

Campos `boolean` que requieren interpretar presencia, ausencia o negacion textual.

Ejemplos reales: `has_nda_clause`, `has_liability_limitation`, `is_declared`, `is_repealed`, `is_pediatric`, `is_primary`.

Riesgo: confundir `false` con `null`. Si el schema es boolean no nullable y la description define una condicion explicita, `false` puede ser correcto cuando la evidencia niega o no cumple la condicion.

### 8. Booleanos nullable

Campos como `is_chronic`, donde el schema permite `boolean | null`.

Riesgo: devolver `false` por falta de evidencia. Si el campo pregunta si algo es cronico y el texto no lo define, el valor correcto es `null`, no `false`.

### 9. Nulls grounded y hallucination traps

Campos nullable que piden datos ausentes, a veces conocidos por conocimiento externo.

Ejemplos reales: `original_language`, `release_year`, `rating`, `exact_release_date`, `latest_stable_version_sha256`, `current_ceo_name`, `discoverer`.

Riesgo: completar con memoria del modelo. El FSP debe mostrar explicitamente que se usa `null` si el texto solo da informacion parcial o no menciona el dato.

### 10. Fechas y normalizacion temporal

Campos de fecha que pueden pedir formato `YYYY-MM-DD`, fecha verbatim o fecha exacta.

Ejemplos reales: `effective_date`, `sanction_date`, `date`, `exact_release_date`, `discovery_date`.

Riesgo: normalizar cuando el schema lo pide, pero devolver `null` si el campo exige fecha exacta y el texto solo da un ano.

### 11. Arrays simples

Listas de strings o valores simples.

Ejemplos reales: `genres`, `key_themes`, `parties`, `platforms`, `features`, `pros`, `cons`, `key_people`, `key_organizations`.

Riesgo: duplicar menciones, mezclar entidades con descripciones largas, o devolver una cadena separada por comas en lugar de array.

### 12. Arrays vacios

Arrays no nullable sin elementos presentes en el texto.

Ejemplos reales: `key_people: []`, `dietary_tags: []`, `technique_sequence: []`, `diagnosis_methods: []`.

Riesgo: devolver `null` en un array, omitir el campo o inventar elementos.

### 13. Arrays de entidades

Listas de objetos `{text, label}` con mencion verbatim y etiqueta enum.

Aparece en `cultural_entities`, `legal_entities`, `medical_entities` y `technical_entities`.

Riesgo: normalizar demasiado el texto de la entidad, no conservar la mencion exacta, o escoger una etiqueta fuera del enum.

### 14. Arrays de objetos complejos

Listas de objetos con varios subcampos heterogeneos.

Ejemplos reales: `ingredients`, `symptoms`, `side_effects`.

Pueden mezclar strings verbatim, numeros nullable, enums, booleans inferidos y strings nullable dentro de cada item.

Riesgo: perder campos internos, rellenar subcampos ausentes con valores inventados, o no razonar item por item dentro del reasoning del campo.

### 15. Arrays de enums

Listas cuyos items son enums.

Ejemplos reales: `dietary_tags`, `technique_sequence`.

Riesgo: devolver etiquetas textuales del documento en vez de mapearlas a los literales exactos del schema.

### 16. Constraints, patrones y sentinels

Campos con `pattern`, `minimum`, `maximum` o reglas especiales como devolver `"NONE"` si no hay codigo.

Ejemplos reales: `registration_code` con pattern, `complexity_score` con rango 1-10.

Riesgo: aplicar la regla general de `null` cuando el schema no permite null y la description define un sentinel, o ignorar min/max en campos numericos inferidos.

## Subtareas recomendadas para el super FSP

Un super FSP util deberia poder activar subconjuntos de estas subtareas:

- `verbatim_answer`: respuesta QA como fragmento exacto.
- `direct_string`: valor string corto y directo.
- `summary_string`: resumen grounded.
- `long_verbatim_evidence`: evidencia verbatim larga.
- `enum_classification`: enum inferido con literal exacto.
- `date_normalization`: fecha normalizada.
- `numeric_normalization`: enteros y numbers sin unidades.
- `boolean_inference`: booleanos no nullable por presencia/ausencia/negacion.
- `nullable_boolean`: boolean nullable con `null` por falta de evidencia.
- `grounded_null`: campos nullable ausentes o parcialmente mencionados.
- `simple_array`: arrays simples.
- `empty_array`: arrays vacios no nullable.
- `entity_array`: arrays de entidades `{text, label}`.
- `complex_object_array`: arrays de objetos heterogeneos.
- `nested_numeric_object_array`: objetos con numeros nullable y enums internos.
- `enum_array`: arrays de enums.
- `bounded_score`: entero inferido con min/max.
- `sentinel_pattern`: string con pattern y sentinel explicito.

La seleccion dinamica del FSP puede hacerse inspeccionando el schema real del task. Por ejemplo, si el schema contiene arrays de objetos, se activa `complex_object_array`; si contiene campos nullable con descripciones como `exact`, `current`, `SHA256` o `not explicitly in the text`, se activa `grounded_null`; si contiene booleans nullable, se activa `nullable_boolean`.
