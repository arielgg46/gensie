# Revisión de los `docs\rag\*.md`

## Revisión por prefijos

### `legal_contracts`

**Cambios puntuales observados.** Se afinó la description de `contract_type`
para que `OTRO` quede como fallback para operaciones fuera del enum, con
ejemplos como licencias o arrendamientos. En `parties` se simplificó la trampa
de alias secundarios. En el ejemplo de compraventa se cambió `125.000 euros` por
`125'000 euros`, y se sincronizaron los `relevant_fragments` de `has_nda_clause`
y `monetary_amount` con esa forma textual.

**Por qué se hizo.** El cambio fuerza a copiar y razonar sobre la superficie real
del texto, incluso cuando la notación numérica no es la más canónica. También
reduce el riesgo de que el modelo confunda denominaciones secundarias o tipos
contractuales no cubiertos con categorías del enum.

**Insight generalizable.** En contratos, los examples deben cubrir campos
booleanos por la cláusula específica que los activa, no por el tipo global del
contrato. Si se introduce una forma rara de cantidad o redacción, todo el
reasoning debe citar esa forma exacta para no enseñar normalización invisible.

**Respuesta a la observación.** La preocupación sobre `CONFIDENCIALIDAD` y
`has_nda_clause=true` es válida: si siempre aparecen juntos, el RAG puede aprender
una correlación espuria entre tipo contractual y cláusula NDA. Conviene que al
menos un ejemplo tenga `contract_type` distinto de `CONFIDENCIALIDAD` con
`has_nda_clause=true` por una cláusula de reserva/no divulgación, o un contrato
de `CONFIDENCIALIDAD` donde otro campo booleano cambie, para que el criterio sea
la evidencia de la cláusula y no el enum del tipo.

### `technical_entities`

**Cambios puntuales observados.** Se reemplazaron `relevant_fragments` muy
compactos con elipsis amplias por fragmentos más completos y segmentados:
definición de la tecnología con creadora y organización mantenedora, oración de
reemplazo técnico en 2024, evento/lugar/fecha, presentación de módulo, repositorio
y algoritmo o identificador técnico. En el segundo ejemplo también se separaron
empresa, ubicación de banco de pruebas, paquete instalado, protocolos y modelo
anterior.

**Por qué se hizo.** El cambio da más contexto local para justificar cada label.
En entidades, una mención aislada como `Madrid` o `GitLab` no enseña por sí sola
por qué es `LOCATION` u `ORGANIZATION`; la relación sintáctica cercana sí lo hace.

**Insight generalizable.** Para schemas de entidades, `relevant_fragments` debe
preferir oraciones completas o sintagmas con verbo relacional, no solo listas de
menciones. La evidencia útil es “X creada por persona y mantenida por
organización”, “evento celebrado en lugar en fecha” o “módulo compatible con
protocolos”, porque eso enseña clasificación y no solo detección de strings.

**Respuesta a la observación.** Sí: conviene añadir, dentro de
`relevant_fragments`, un análisis relacional breve entre paréntesis después de
cada fragmento complejo. Por ejemplo: `"Nube Clara 2.0 es una biblioteca [...]
creada por Inés Lobo y mantenida por la Fundación BitÁgora"` (tecnología creada
por persona y mantenida por organización). Este patrón debería replicarse en
`cultural_entities`, `medical_entities`, `legal_entities` y cualquier schema de
entidades, cuidando que el paréntesis no invente entidades nuevas sino que explique
la relación que ya está en el fragmento.

### `general_disasters`

**Cambios puntuales observados.** Se amplió la description de `category` para
incluir matanzas o accidentes terribles dentro de `DISASTER` cuando el foco sea
una emergencia. `date` ahora explicita mejor que expresiones relativas no bastan.
`key_organizations` evita tratar países como organizaciones salvo que el texto
hable de su gobierno. En el reasoning, `location`, `date`, `injured` y
`affected_count` ganan contexto cercano en los fragmentos. Para `casualties`,
`injured` y `affected_count` del segundo ejemplo, los fragmentos negativos se
sustituyeron por `No hay fragmentos relevantes.`

**Por qué se hizo.** Los campos de noticias necesitan contexto suficiente para
saber si una cifra pertenece al evento y si cuenta personas. Un fragmento como
`43 heridos` es menos instructivo que `El primer balance oficial reportó [...] 43
heridos`, porque enseña que se trata de personas heridas en el balance del
desastre.

**Insight generalizable.** En schemas de noticias, los campos de lugar, fecha y
cifras humanas deben citar contexto causal o noticioso, no solo el valor aislado.
Para ausencias reales, `No hay fragmentos relevantes` es preferible a citar
fragmentos de prevención o meteorología que no deciden el valor y pueden enseñar
evidencia negativa espuria.

**Respuesta a la observación.** Sí, conviene cambiar la dualidad del último campo
y, en general, de los campos de cifras humanas. Ahora el primer ejemplo enseña
`casualties`, `injured` y `affected_count` poblados, mientras el segundo enseña
los tres como `null`; eso puede volver demasiado fácil la decisión por tipo de
noticia. Mejor tener combinaciones cruzadas: por ejemplo, un caso con muertes y
heridos pero `affected_count=null`, y otro con evacuados/desplazados pero sin
muertes o sin heridos. Así el modelo aprende a decidir cada campo por su propia
evidencia, no por un paquete “hay balance humano completo” vs “no hay cifras
humanas”.

### `technical_software`

**Cambios puntuales observados.** Se suavizó `platforms` con `etc.` para no cerrar
la lista de plataformas posibles. `exact_release_date` enfatiza en mayúsculas que
solo año no basta. En `current_ceo_name` se cambió “no equivalen” por “no
necesariamente equivalen”, dejando abierta la posibilidad de que el texto sí
afirme una equivalencia. En reasoning, `features` pasa a citar la sección y la
enumeración juntas, no como dos fragmentos separados.

**Por qué se hizo.** El schema tiene varias trampas de sobregeneralización: año
como fecha exacta, fundador como CEO, instaladores como plataformas o sección de
características sin contenido. Los cambios hacen más explícito cuándo una señal
textual es insuficiente.

**Insight generalizable.** En schemas técnicos con campos adversariales, las
descriptions deben decir qué NO activa el campo con ejemplos concretos. Cuando el
campo pide una relación corporativa actual, no basta con roles históricos,
técnicos o comunitarios.

**Respuesta a la observación.** Sí, `CEO` debería explicarse en la description
en español: director ejecutivo o máxima persona ejecutiva de una empresa, si el
texto lo afirma con ese cargo o equivalente claro. Además conviene decir que
`CEO` aplica sobre todo a organizaciones empresariales; en comunidades,
fundaciones o proyectos abiertos, “mantenedor”, “presidente”, “coordinador” o
“fundador” no debe llenar `current_ceo_name` salvo afirmación explícita de que
esa persona es CEO/directora ejecutiva actual.

### `lifestyle_recipes`

**Cambios puntuales observados.** `total_time_minutes` pasó de “tiempos explícitos
sumables” a “posiblemente sumables”, más realista cuando el texto da varios
tramos. En el segundo ejemplo, `ingredients` cita también `pan tostado` pero el
final_value aclara que es acompañamiento y no ingrediente principal. El
`complexity_score` añade “se pintan con la salsa reducida” como fase adicional.
El `field_asks` de tiempo exige un dato “suficientemente concreto”.

**Por qué se hizo.** Los cambios distinguen receta principal de servicio opcional,
y separan tiempos concretos de puntos de cocción por textura. También hacen que
la dificultad se base en una secuencia técnica completa, no solo en presencia de
un horno o un sofrito.

**Insight generalizable.** En recetas, el reasoning debe citar tanto lo incluido
como lo excluido cuando haya acompañamientos o variantes cerca. Para dificultad,
conviene enseñar escala por cantidad de fases, control técnico y tiempo concreto,
no por “plato elaborado” de forma vaga.

**Respuesta a la observación.** Sí: `complexity_score` necesita más granularidad.
Una descripción útil sería: 1-2 para mezcla, montaje o cocción muy simple; 3-4
para recetas con una o dos técnicas básicas y poco control fino; 5-6 para guisos,
sofritos con hervor o varias fases moderadas; 7-8 para reducción, horno,
marinado, reposos o control de textura; 9-10 para técnicas precisas o
profesionales. En `dietary_tags`, “lácteos bloquean sin lácteos” debe enumerar
ejemplos: leche, yogur, queso, mantequilla, nata/crema, suero, leche en polvo,
etc. Si aparecen solo como acompañamiento opcional, no deberían bloquear la
preparación básica.

### `cultural_monuments`

**Cambios puntuales observados.** En `registration_code` se amplió la trampa de
campo desplazado: ya no solo puede aparecer en `Declaration Date`, sino en otro
campo mal alineado. El resto del diff mantiene el criterio de usar `true` para
ficha BIC sin indicio de incoación y `false` solo con señal explícita de no
declarado.

**Por qué se hizo.** Los registros BIC revisados tienen columnas desplazadas o
contenido en campos incorrectos. El modelo debe extraer por patrón semántico y
formal, no por el nombre literal de la columna.

**Insight generalizable.** En fichas tabulares o semiestructuradas con columnas
rotas, las descriptions deben enseñar “lee el valor aunque esté desplazado” y
“no uses el nombre de la columna si el contenido contradice el tipo esperado”.

**Respuesta a la observación.** Sí, `bic_category` debe listar todos los enum en
la description enriquecida, no solo ejemplos: `MONUMENTO`, `JARDÍN HISTÓRICO`,
`CONJUNTO HISTÓRICO`, `SITIO HISTÓRICO`, `ZONA ARQUEOLÓGICA` y `OTRO` si esos
son los valores del schema. `registration_code` debería llevar un patrón exacto,
por ejemplo `RI-\d{2}-\d{7}` si ese es el formato esperado, y aclarar que otros
patrones solo se aceptan si el schema/revisión los permite. Sobre `is_declared`:
me parece correcto `true` cuando el estado dice declarado o cuando solo hay una
ficha BIC/registro consolidado sin incoación; `false` debe reservarse para
`Incoado`, pendiente, expediente abierto o señal explícita de no declaración.
También hay que revisar el resto de `.md` para que todo campo enum incluya todos
sus valores.

### `cultural_literature`

**Cambios puntuales observados.** `publication_year` ahora enfatiza que si solo
hay siglo o fechas secundarias debe ir `null`. `genres` añade `etc.` para no
limitar la lista de géneros a los ejemplos dados. En el reasoning del primer
ejemplo se agregó la frase inicial `"La ciudad de los espejos es una novela
breve"` como evidencia directa del género, no solo la ficha editorial posterior.

**Por qué se hizo.** El campo `genres` necesita evidencia textual explícita y
mejor si aparece cerca de la presentación de la obra. Para `publication_year`, el
riesgo es convertir fechas de composición, reedición o recepción en primera
publicación.

**Insight generalizable.** En literatura, las evidencias de género y tema deben
distinguir clasificación literaria, estructura formal, tono y asunto. “Novela
breve” o “narrativa fantástica” son géneros; “tono urbano”, “prosa contenida” o
“cambios de narrador” no necesariamente son temas.

**Respuesta a la observación.** Estoy de acuerdo: en este prefijo es poco natural
forzar `genres=[]` o `key_themes=[]` como dualidad principal si los textos reales
suelen describir obras con algún género y algún tema. Mejor cubrir granularidad:
uno vs varios géneros, género explícito en primera frase vs en recepción crítica,
temas nombrados directamente vs rasgos estilísticos que NO son temas. Sobre la
longitud, los sintéticos deberían ser algo más largos que recortes mínimos, porque
las fichas literarias reales traen contexto de autoría, publicación, recepción y
temas; recortarlos demasiado empobrece las trampas.

### `environmental_ecology`

**Cambios puntuales observados.** `date` y `key_organizations` se alinearon con
las mismas cautelas de noticias generales: no fechas relativas, no países como
organizaciones salvo gobierno explícito. `affected_count` enfatiza que cifras
ambientales no se convierten a personas sin conversión segura. En reasoning, se
ampliaron fragmentos para casualties/injured/location: por ejemplo, `1 200
vecinos` ahora aparece dentro de la acción de reparto de bidones, y `humedales
boreales y tropicales` dentro del contexto de muestras de estudio. El summary del
segundo ejemplo se ajustó para identificar a Lara Méndez como investigadora.

**Por qué se hizo.** El prefijo mezcla noticias ambientales con artículos de
estudio científico; las cifras pueden ser personas, muestras, focos, hectáreas o
animales. Sin contexto, el modelo puede mapear cualquier número a campos humanos.

**Insight generalizable.** Para schemas de noticias, los `relevant_fragments` de
summary y de campos derivados deben contener contexto de evento, actor y
consecuencia. Una cifra aislada o un lugar aislado no basta si el campo requiere
saber qué ocurrió, dónde ocurrió y si la cifra corresponde a personas.

**Respuesta a la observación.** Sí: en `summary`, los fragmentos deberían ser
oraciones o fragmentos completos con contexto suficiente, no subfrases cortadas
que solo contienen el dato final. Para `location` y campos similares, la evidencia
debe incluir contexto cercano o una elipsis que muestre por qué ese lugar es
central o por qué NO lo es: por ejemplo, “muestras tomadas en humedales boreales
y tropicales” justifica `location=null` mejor que “humedales boreales y
tropicales”. Esta regla aplica también a `general_disasters`, `medical_health_news`
y cualquier schema de noticia con `summary`, `location`, `date` y cifras humanas.

## Observaciones

- en legal_contracts me preocupa que se marque el ejemplo de CONFIDENCIALIDAD como el que tiene has_nda_clause true, porque me parece q puede sesgar a una equivalencia o correlación fuerte entre esos valores de esos campos
- en technical_entities (y seguro en todas las de entidades) en el reasoning quizás es bueno hacer que en relevant_fragments trate cada oración con entidades poniendo explícitamente después del fragmento entre paréntesis un análisis relacional, ej: "\"Nube Clara 2.0 es una biblioteca de sincronización [...] creada por Inés Lobo y mantenida por la Fundación BitÁgora\" (cosa ... creada por persona y mantenida por organización), \"En 2024 reemplazó su cola interna por PostgreSQL y añadió un operador para Kubernetes\" (en fecha reemplazó... por cosa y ... para cosa), \"Durante la OpenInfra Summit celebrada en Madrid el 12 de junio de 2025\" (durante evento celebrado en lugar en fecha), \"presentó Río, un módulo compatible con S3 y WebDAV\" (presentó cosa, ... con cosa y cosa), \"GitLab como repositorio espejo\" (organización) \"Ed25519\" (cosa)."
- deberíamos cambiar la dualidad del último campo de general_disasters, para que no quede en el último ejemplo como que todo (en cifras de personas) es null, ni en el primero que nada es null
- technical_software poner qué es CEO en desc enriq
- lifestyle_recipes su desc enriq complexity_score 3-4 qué? lácteos bloquean sin lácteos xd (detalles bro, leche, yogurt, queso, mantequilla...)
- cultural_monuments poner todos los Enum en el desc enriq (revisar el resto de .md por si en alguno falta hacer esto explícitamente). registration_code poner el patrón exacto. is_declared `true` si el estado es declarado o si el registro solo muestra ficha BIC sin indicio de incoación?
- cultural_literature dificilmente va a ser [] genres, quizás sería mejor no poner esa dualidad. key_themes igual. Y usualmente los textos son un poquito más largos
- En environmental_ecology (y todos los de schema que pide summary de noticias) en el reasoning del summary los fragmentos deben ser extraidos completos, no un subfragmento sin contexto, porque se requiere todo el contexto para el valor final. Los fragment de location (o campos similares) deben tener contexto cercano (o lejano y elipsis) que brinde contexto de por qué se saca como posible lugar donde ocurre el hecho
- cultural entities los fragmentos relevantes no vienen con contexto suficiente alrededor de las entidades para asociarlas a su clasificación
- reducir un poco los textos de cultural_extraction
- medical_diseases el ejemplo 1 tiene "La tos y la rinorrea orientan más a cuadros virales" en el input pero no se dice nada de eso en el output, why?
