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

**Ver insights generalizables de prefijos relacionados.** `technical_software`,
`legal_legislation`, `medical_extraction`, `stem_astronomy_detailed`.

**Respuesta a la observación.** La preocupación sobre `CONFIDENCIALIDAD` y
`has_nda_clause=true` es válida: si siempre aparecen juntos, el RAG puede aprender
una correlación espuria entre tipo contractual y cláusula NDA. Conviene que al
menos un ejemplo tenga `contract_type` distinto de `CONFIDENCIALIDAD` con
`has_nda_clause=true` por una cláusula de reserva/no divulgación, o un contrato
de `CONFIDENCIALIDAD` donde otro campo booleano cambie, para que el criterio sea
la evidencia de la cláusula y no el enum del tipo. Por tanto vamos a cambiar el ejemplo
actual de tipo `CONFIDENCIALIDAD` por otro que aún conserve `has_nda_clause=true`

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

**Ver insights generalizables de prefijos relacionados.** `cultural_entities`,
`legal_entities`, `medical_entities`.

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

**Ver insights generalizables de prefijos relacionados.** `environmental_ecology`,
`legal_judicial`, `medical_health_news`.

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

**Ver insights generalizables de prefijos relacionados.** `cultural_media`,
`legal_legislation`, `stem_astronomy_detailed`, `medical_drug`.

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

**Ver insights generalizables de prefijos relacionados.** `medical_diseases`,
`cultural_media`, `medical_drug`.

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

**Ver insights generalizables de prefijos relacionados.** `legal_legislation`,
`medical_entities`, `medical_drug`.

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

**Ver insights generalizables de prefijos relacionados.** `cultural_media`,
`cultural_entities`, `cultural_extraction`.

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

**Ver insights generalizables de prefijos relacionados.** `general_disasters`,
`legal_judicial`, `medical_health_news`.

**Respuesta a la observación.** Sí: en `summary`, los fragmentos deberían ser
oraciones o fragmentos completos con contexto suficiente, no subfrases cortadas
que solo contienen el dato final. Para `location` y campos similares, la evidencia
debe incluir contexto cercano o una elipsis que muestre por qué ese lugar es
central o por qué NO lo es: por ejemplo, “muestras tomadas en humedales boreales
y tropicales” justifica `location=null` mejor que “humedales boreales y
tropicales”. Esta regla aplica también a `general_disasters`, `medical_health_news`
y cualquier schema de noticia con `summary`, `location`, `date` y cifras humanas.

### `cultural_entities`

**Cambios puntuales observados.** Se añadió un `.md` nuevo para extracciones L5
de entidades culturales, con dos ejemplos sintéticos en formato de recorte
periodístico: titular Markdown, marcador `[...]`, tono de crítica/noticia cultural
y una sola lista `entities`. La dualidad se centra en lista corta frente a lista
más densa, y en cubrir todas las etiquetas del enum: `PERSON`, `ORGANIZATION`,
`LOCATION`, `DATE`, `EVENT` y `MISCELLANEOUS`.

**Por qué se hizo.** El schema no separa entidades por campos, así que los
ejemplos necesitan enseñar dos cosas a la vez: conservar la mención verbatim y
asignar la etiqueta correcta sin conocimiento externo. Los textos elegidos
mantienen el estilo de los inputs revisados y permiten contrastar títulos
culturales, personas/personajes, estudios, lugares, fechas y festivales.

**Insight generalizable.** En schemas de entidades, no basta con listar menciones
aisladas en `relevant_fragments`; la evidencia debe incluir contexto cercano que
explique la clasificación. Para recortes culturales, conviene citar fragmentos
como “la directora Sofía Galán”, “rodada entre Getaria y Zumaia”, “se estrenará
en salas el 17 de abril de 2026” o “premio en el Festival de San Sebastián”, y no
solo `Sofía Galán`, `Getaria`, `17 de abril de 2026` o `Festival de San Sebastián`.

**Ver insights generalizables de prefijos relacionados.** `technical_entities`,
`legal_entities`, `medical_entities`.

**Respuesta a la observación.** La observación es correcta: los `relevant_fragments`
actuales vienen demasiado compactos y pierden la relación que justifica cada
label. Hay que reescribirlos con oraciones o sintagmas con contexto y, siguiendo
el patrón de `technical_entities`, añadir un análisis relacional breve entre
paréntesis cuando el fragmento sea complejo: `"La directora Sofía Galán filma..."`
(persona con rol de directora), `"rodada entre Getaria y Zumaia"` (obra rodada en
lugares), `"A24 moverá la cinta fuera de Europa"` (organización distribuye o
mueve obra cultural), `"premio en el Festival de San Sebastián"` (evento cultural).
Eso debería replicarse en todos los prefijos de entidades.

### `cultural_extraction`

**Cambios puntuales observados.** Se añadió un `.md` nuevo para extracción L1 de
un único fragmento verbatim desde reseñas o recomendaciones culturales. Los dos
ejemplos usan artículos Markdown con titular, subtítulos `##`, tono opinativo,
distractores de elenco/creadores/personajes y una oración concreta que responde
la pregunta. El output conserva una cláusula completa, no solo el nombre propio.

**Por qué se hizo.** El campo `answer` requiere responder con texto fuente
suficiente para establecer la relación pedida. En este prefijo, devolver solo
`Paula Medina` o una lista de nombres enseña mal la tarea, porque el valor debe
anclar quién dirigió o quién protagonizó dentro de una frase verificable.

**Insight generalizable.** En schemas L1 de respuesta verbatim, el fragmento debe
ser tan corto como sea posible pero tan completo como sea necesario para resolver
la pregunta. Si la pregunta pide una relación cultural, el fragmento debe incluir
el verbo o construcción relacional: “la directora de X es Y”, “está protagonizada
por A, B y C”, “fue escrita por...”; no basta la entidad aislada.

**Ver insights generalizables de prefijos relacionados.** `legal_extraction`,
`medical_extraction`, `technical_extraction`.

**Respuesta a la observación.** Sí, los textos se pueden reducir un poco. Mantendría
el titular largo, un subtítulo y dos o tres párrafos de reseña con distractores,
pero recortaría el exceso de valoración atmosférica que no afecta la extracción.
La meta no es hacerlos telegráficos, porque los `dev` reales son reseñas con voz
periodística, sino evitar que un L1 dependa de un artículo demasiado largo cuando
la evidencia decisiva está en una sola oración.

### `cultural_media`

**Cambios puntuales observados.** Se añadieron dos fuentes revisadas de `data/dev`
y una tabla de descriptions enriquecidas para todos los campos. Los `input_text`
de los ejemplos se compactaron: pasaron de reseñas con subtítulos y párrafos
separados a recortes más continuos con saltos `[...]`, manteniendo el titular
largo, el tono crítico, la obra principal y los distractores de comparaciones,
plataformas, reparto y fechas.

**Por qué se hizo.** Los ejemplos reales de este prefijo son reseñas culturales
compactas, no artículos largos con estructura editorial completa. La compactación
acerca los sintéticos al estilo revisado y evita que el modelo aprenda una forma
de input demasiado ordenada, mientras las descriptions enriquecidas refuerzan
trampas clave: obra reseñada vs obra comparada, creador vs director, reparto vs
personajes, año de estreno vs fecha contextual y rating explícito vs valoración
verbal.

**Insight generalizable.** En reseñas culturales multicitadas, casi todos los
campos dependen de identificar primero la obra foco. Las evidencias de `medium`,
`director`, `main_cast`, `release_year`, `rating`, `pros` y `cons` deben
referirse a esa obra, no a referentes, plataformas o comparaciones cercanas. Para
sentimiento y veredicto, conviene mirar el balance global y el cierre, no una
frase positiva o negativa aislada.

**Ver insights generalizables de prefijos relacionados.** `cultural_literature`,
`legal_legislation`, `stem_astronomy_detailed`, `technical_software`.

### `legal_entities`

**Cambios puntuales observados.** Se añadió un `.md` nuevo para entidades en
textos legales españoles, con un ejemplo de fórmula solemne/preámbulo y otro de
real decreto administrativo. Las descriptions enriquecidas enumeran el enum
completo y enfatizan menciones verbatim con mayúsculas, tratamientos, artículos,
numeración normativa y títulos oficiales.

**Por qué se hizo.** El ejemplo revisado disponible era escaso y muy BOE, así que
los sintéticos amplían cobertura sin salir del registro jurídico: persona
institucional, órganos, pueblos/nación como sujetos jurídicos, normas, boletines,
territorios y fechas. Esto ayuda a no normalizar fórmulas como `DON`, `LAS CORTES`
o nombres de normas.

**Insight generalizable.** En entidades legales, la etiqueta depende del rol
jurídico en el fragmento, no solo de la forma superficial. `Boletín Oficial del
Estado` funciona como `ORGANIZATION`, una ley o real decreto como
`MISCELLANEOUS`, una comunidad autónoma puede ser `ORGANIZATION` si actúa como
administración, y un territorio puede ser `LOCATION` si aparece como lugar. Los
`relevant_fragments` deberían incluir contexto institucional suficiente, no solo
la mención aislada.

**Ver insights generalizables de prefijos relacionados.** `technical_entities`,
`cultural_entities`, `medical_entities`, `legal_legislation`.

### `legal_extraction`

**Cambios puntuales observados.** Se añadió un `.md` nuevo para extracción L1 de
fragmentos legales verbatim. Los ejemplos usan Markdown normativo con encabezados
`## Artículo N`, apartados numerados, artículos vecinos como distractores y una
pregunta que debe resolverse copiando la oración o apartado completo.

**Por qué se hizo.** El ejemplo revisado enseña que una respuesta legal no debe
reducirse a una entidad, porcentaje o cifra aislada. Si la pregunta pide la edad,
la capitalidad o el porcentaje exigido, el valor útil para el schema es la regla
jurídica completa que contiene condición, sujeto y consecuencia.

**Insight generalizable.** En extracción legal L1, el fragmento debe conservar la
formulación normativa completa, incluyendo modalidad verbal y límites como
`deberá`, `podrán`, `salvo`, `al menos` o referencias al sujeto obligado. Las
descriptions y el reasoning deben desalentar paráfrasis modernas y respuestas
mínimas cuando el texto fuente ofrece una oración legal autosuficiente.

**Ver insights generalizables de prefijos relacionados.** `cultural_extraction`,
`medical_extraction`, `technical_extraction`, `legal_contracts`.

### `legal_judicial`

**Cambios puntuales observados.** Se añadieron dos fuentes de `data/dev` hasta
llegar a cinco revisadas y una tabla completa de descriptions enriquecidas. Los
ejemplos contrastan sentencia por estafa digital con operativo policial: fecha
absoluta frente a referencia relativa, personas nombradas frente a roles
genéricos, afectados económicos frente a muertos/heridos, y cifras penales o
logísticas que no deben poblar campos humanos.

**Por qué se hizo.** El schema es el de noticias generales, pero en el dominio
judicial abundan números que no son víctimas: años de prisión, sospechosos,
detenidos, armas, vehículos, líneas telefónicas, expedientes o dinero. La
curación enseña que `casualties`, `injured` y `affected_count` solo se llenan
cuando la cifra corresponde a personas en la relación pedida.

**Insight generalizable.** En noticias judiciales, el modelo debe separar el
hecho procesal central de las cifras accesorias. Para `summary`, conviene citar
fragmentos completos que cubran decisión/operativo, acusación y consecuencia; y
para `location` o `date`, el fragmento debe indicar que ese lugar o fecha
pertenece al proceso u operativo, no solo que aparece cerca de una institución.

**Ver insights generalizables de prefijos relacionados.** `general_disasters`,
`environmental_ecology`, `medical_health_news`.

### `legal_legislation`

**Cambios puntuales observados.** Se añadieron dos fuentes de `data/dev`, una
tabla de descriptions enriquecidas y `Source` con URL de referencia en los dos
ejemplos. Las descriptions listan todos los enums de `law_range` y `jurisdiction`.
Los ejemplos contrastan real decreto-ley estatal vigente con ley autonómica
derogada, fecha formal normalizable frente a publicación/estación aproximada, y
artículos/disposiciones concretos frente a contenido normativo sin artículos.

**Por qué se hizo.** Este schema está lleno de referencias jurídicas que no son
la norma principal: nombre popular, normas citadas, leyes posteriores, artículos
constitucionales, publicación oficial, entrada en vigor o derecho europeo como
contexto. Los cambios enseñan a escoger el título y rango de la norma foco, no de
sus antecedentes o sustitutas.

**Insight generalizable.** En legislación, primero se identifica la norma
principal y luego se extraen sus metadatos. La fecha de publicación no debe llenar
`sanction_date` si el texto no la equipara con sanción/aprobación; una reforma o
modificación parcial no vuelve `is_repealed=true`; y `affected_articles` solo
incluye unidades normativas nombradas, no temas o medidas resumidas sin número de
artículo/disposición.

**Ver insights generalizables de prefijos relacionados.** `legal_contracts`,
`cultural_media`, `technical_software`, `stem_astronomy_detailed`.

### `medical_diseases`

**Cambios puntuales observados.** Se añadieron descriptions enriquecidas para el
perfil patológico completo. Los ejemplos contrastan enfermedad infecciosa aguda
con trastorno crónico de etiología no demostrada, causa explícita frente a
`etiology_description=null`, métodos diagnósticos poblados frente a `[]`, y
síntomas primarios frente a signos secundarios o de alarma.

**Por qué se hizo.** El schema exige separar dimensiones clínicas que suelen
mezclarse: etiología, síntomas, complicaciones, diagnóstico y evolución. Los
ejemplos enseñan que una infección bacteriana aguda puede tener causa y métodos
diagnósticos claros, mientras que un trastorno crónico puede mencionar mecanismos
o factores asociados sin justificar una etiología cerrada.

**Insight generalizable.** En perfiles médicos, el reasoning debe distinguir
síntomas de la enfermedad, signos de alarma, complicaciones, factores de riesgo,
métodos diagnósticos y tratamiento. Cuando el texto menciona rasgos que orientan
a diagnóstico diferencial o que “pueden coexistir”, conviene citarlos para
explicar si se excluyen o si entran como secundarios; dejarlos sin comentar parece
omisión.

**Ver insights generalizables de prefijos relacionados.** `medical_drug`,
`medical_health_news`, `lifestyle_recipes`.

**Respuesta a la observación.** La frase “La tos y la rinorrea orientan más a
cuadros virales” no está en el output porque el ejemplo parece tratarlas como
señales diferenciales, no como síntomas definitorios de la faringitis
estreptocócica. Aun así, tienes razón en marcarlo: el `reasoning` debería decirlo
explícitamente. En `symptoms.relevant_fragments` o `final_value` habría que añadir
que tos y rinorrea se excluyen porque el texto las presenta como orientación hacia
cuadros virales, aunque puedan coexistir en niños pequeños; así el modelo no
aprende a ignorar silenciosamente evidencia clínica cercana.

### `medical_drug`

**Cambios puntuales observados.** Se añadieron descriptions enriquecidas para
todos los campos de ficha técnica y dos ejemplos que contrastan monofármaco
sólido con combinación líquida, una sola dosis frente a concentraciones por ml,
uso pediátrico permitido frente a restricción por codeína, y lista breve frente a
lista amplia de reacciones adversas.

**Por qué se hizo.** Las fichas técnicas tienen secciones muy parecidas pero con
funciones distintas: composición, forma farmacéutica, posología, indicaciones,
advertencias y reacciones adversas. Los ejemplos obligan a extraer cada campo de
su sección correcta y a no convertir pautas de administración, máximos diarios o
advertencias en dosis estándar o efectos adversos.

**Insight generalizable.** En medicamentos, `side_effects` debe construirse desde
la sección 4.8 y, si el recorte es pequeño, conviene extraer todas las reacciones,
no una muestra. Cada reacción necesita su propia clase de órgano, probabilidad e
impacto; las frecuencias se mapean por texto (`Frecuentes`, `Poco frecuentes`,
`Raras`, `Frecuencia no conocida`) y el impacto se infiere clínicamente sin
alterar el nombre verbatim de la reacción.

**Ver insights generalizables de prefijos relacionados.** `medical_diseases`,
`medical_entities`, `medical_extraction`, `technical_software`.

### `medical_entities`

**Cambios puntuales observados.** Se añadió un `.md` nuevo para entidades en
fichas técnicas farmacéuticas. Los ejemplos cubren una lista densa de medicamento,
principios activos y excipientes casi todos `MISCELLANEOUS`, y una lista
administrativa con titular, dirección, localidad, país, fechas de autorización o
revisión y agencia reguladora.

**Por qué se hizo.** Los ejemplos revisados tenían pocas instancias únicas y un
estilo CIMA muy marcado. Los sintéticos mantienen encabezados de ficha técnica,
secciones numeradas, `[...]`, dosis, códigos E, formas farmacéuticas y datos
administrativos, para que el modelo aprenda a conservar menciones completas sin
normalizarlas ni atomizarlas de más.

**Insight generalizable.** En entidades médicas de fichas técnicas, muchas
menciones son técnicas y no encajan en persona/lugar/evento; medicamentos,
sustancias, excipientes, formas y códigos suelen ir a `MISCELLANEOUS`. Para
fragmentos administrativos, el reasoning debería incluir contexto de sección:
`# 7. TITULAR...` para laboratorios, `# 9`/`# 10` para fechas, y la frase de AEMPS
para agencia reguladora. Eso evita clasificar una fecha o dirección sin saber su
función documental.

**Ver insights generalizables de prefijos relacionados.** `technical_entities`,
`cultural_entities`, `legal_entities`, `medical_drug`.

### `medical_extraction`

**Cambios puntuales observados.** Se corrigió la lista de fuentes revisadas para
usar `data/dev_rev/medical_extraction_003.json` y se añadió nota de que solo hay
tres instancias únicas disponibles. También se incorporó una description
enriquecida para `answer`, enfocada en copiar línea completa, unidades,
puntuación, dos puntos, punto final y coma decimal sin normalizar.

**Por qué se hizo.** El prefijo es L1 literal sobre composición CIMA, donde el
error típico es devolver solo `18 mg`, normalizar `0,45` a otro formato, escoger
la presentación vecina o cortar una frase que necesita el nombre de la sustancia.
Los ejemplos mantienen líneas muy parecidas para obligar a seleccionar la exacta.

**Insight generalizable.** En extracción médica literal, la unidad mínima correcta
suele ser la línea u oración completa que responde la pregunta, no el dato
numérico aislado. Los `relevant_fragments` deben copiar el mismo fragmento que
justifica el output y conservar la puntuación final, porque en este prefijo la
forma textual es parte del valor.

**Ver insights generalizables de prefijos relacionados.** `cultural_extraction`,
`legal_extraction`, `technical_extraction`, `medical_drug`.

### `medical_health_news`

**Cambios puntuales observados.** Se añadieron dos fuentes de `data/dev` hasta
cinco revisadas y una tabla de descriptions enriquecidas para el schema de
noticias de salud. Los ejemplos contrastan alerta sanitaria con ubicación, fecha,
muertes y hospitalizaciones frente a estudio médico con investigadora nombrada,
muestra de participantes, fecha relativa, sin lugar concreto y sin personas
afectadas.

**Por qué se hizo.** Las noticias de salud mezclan muchas cifras: fallecidos,
hospitalizados, participantes de estudio, frascos retirados, meses de seguimiento,
dosis, contratos o centros. La curación enseña que solo las cifras de personas
clínicamente afectadas llenan `casualties`, `injured` o `affected_count`; una
muestra de investigación no equivale a afectados.

**Insight generalizable.** En schemas de noticias sanitarias, `summary` debe
apoyarse en fragmentos completos que incluyan alerta/hallazgo, actor sanitario,
medida y consecuencia; no en subfrases sueltas. Para `location` y `date`, la
evidencia debe mostrar que el lugar o la fecha pertenecen al evento principal,
mientras que referencias como `este martes` o periodos de seguimiento no deben
normalizarse a una fecha inventada.

**Ver insights generalizables de prefijos relacionados.** `general_disasters`,
`environmental_ecology`, `legal_judicial`, `medical_diseases`.

### `stem_astronomy_detailed`

**Cambios puntuales observados.** Se añadieron descriptions enriquecidas para
todos los campos, incluyendo enums completos de `body_type`. Los ejemplos
contrastan planeta clásico con planeta enano, masa/diámetro/excentricidad/periodo
explícitos frente a valores `null`, distancia media en UA frente a ausencia de
semieje, y descubrimiento documentado frente a observación desde la antigüedad.

**Por qué se hizo.** Los ejemplos reales traen muchas cantidades astronómicas
cercanas pero no siempre corresponden al campo: masa relativa, masa de muestras,
periodo de rotación, años de misiones, comparaciones de tamaño o descripciones de
órbita excéntrica sin número. Los casos sintéticos cubren positivos necesarios
sin abandonar el estilo enciclopédico de los inputs revisados.

**Insight generalizable.** En astronomía, no se debe normalizar una magnitud por
conocimiento externo ni convertir comparaciones en números. `mass_kg`,
`diameter_km`, `eccentricity`, `orbital_period_days` y `semi_major_axis_au` solo
se llenan cuando el texto da la magnitud pedida o una conversión directa y segura;
observadores históricos, misiones o astrónomos que midieron órbitas no son
`discoverer` salvo que el texto los presente como descubridores.

**Ver insights generalizables de prefijos relacionados.** `technical_software`,
`legal_legislation`, `cultural_media`.

### `technical_extraction`

**Cambios puntuales observados.** Se añadió una description enriquecida para
`answer`, centrada en copiar un único fragmento verbatim y descartar frases
técnicas cercanas que mencionan tecnologías, licencias, versiones o motores no
preguntados. Los ejemplos contrastan subfrase mínima con oración completa.

**Por qué se hizo.** En textos técnicos L1, la tentación principal es responder
con el nombre aislado de la tecnología o elegir el término más llamativo cercano.
Los ejemplos fuerzan a distinguir el algoritmo usado para deduplicar de los
algoritmos de compresión, y el motor actual de consultas de un motor legado.

**Insight generalizable.** Para extracción técnica literal, el valor debe copiar
la unidad textual mínima que responda exactamente la pregunta. Si el fragmento
necesita versión, sujeto o función para no ser ambiguo, se copia la oración
completa; si basta una subfrase con verbo y objeto, se evita arrastrar detalles
posteriores que no fueron pedidos.

**Ver insights generalizables de prefijos relacionados.** `cultural_extraction`,
`legal_extraction`, `medical_extraction`.

## Observaciones originales

Listado original de observaciones usado como insumo; las respuestas quedaron
integradas en las subsecciones correspondientes de `## Revisión por prefijos`.

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
