---
type: source
source_type: paper
url: https://aclanthology.org/2023.emnlp-main.674.pdf
title: "Grammar-Constrained Decoding for Structured NLP Tasks without Finetuning"
fetched_at: 2026-06-17T15:17:31-05:00
fetcher: markitdown
---
|     | Grammar-Constrained |             |     |                   | Decoding |            | for Structured |     | NLP         | Tasks |     |
| --- | ------------------- | ----------- | --- | ----------------- | -------- | ---------- | -------------- | --- | ----------- | ----- | --- |
|     |                     |             |     |                   | without  | Finetuning |                |     |             |       |     |
|     |                     | SaiboGeng,♢ |     | MartinJosifoski,♢ |          |            |                | ♣   | RobertWest♢ |       |     |
MaximePeyrard,
∗
♢EPFL♣UniversitéGrenobleAlpes,CNRS,GrenobleINP,LIG
{saibo.geng,martin.josifoski,robert.west}@epfl.ch,maxime.peyrard@univ-grenoble-alpes.fr
Abstract
Grammar for closed information extraction (cIE):
S → (𝜀 | [s] 𝛼 [r] 𝛽 [o] 𝛼 S)
Despitetheirimpressiveperformance,largelan- 𝛼 = (Entity-1 | … | Entity-N),  𝛽 = (Relation-1 | … | Relation-M)
guagemodels(LMs)stillstrugglewithreliably
generatingcomplexoutputstructureswhennot x = “Burundi  y = “[s] Burundi
|     |     |     |     |     |     |     | m o v e d  it s  ca p | i t a l     |     |                         |              |
| --- | --- | --- | --- | --- | --- | --- | --------------------- | ----------- | --- | ----------------------- | ------------ |
|     |     |     |     |     |     |     |                       |             | LM  |                 [ r ]   | c a p i ta l |
finetuned to follow the required output for- f ro m  B u ju m b u r a   t o                 [ o ]   G it e g a ”
|             |          |          |         |             |          |     | G i t e g a ”           |     |     |     |     |
| ----------- | -------- | -------- | ------- | ----------- | -------- | --- | ----------------------- | --- | --- | --- | --- |
| mat         | exactly. | To       | address | this issue, | grammar- |     |                         |     |     |     |     |
| constrained |          | decoding | (GCD)   | can be      | used to  |     | Grammar-constrained     |     |     |     |     |
decoding (GCD)
| control                              | the | generation | of  | LMs, guaranteeing |      |     |              |     |         |         |     |
| ------------------------------------ | --- | ---------- | --- | ----------------- | ---- | --- | ------------ | --- | ------- | ------- | --- |
|                                      |     |            |     |                   |      |     | t = 0 During |     | Burundi | This GM | …   |
| thattheoutputfollowsagivenstructure. |     |            |     |                   | Most |     |              |     |         |         |     |
existingGCDmethodsare,however,limitedto
|     |     |     |     |     |     |     | t = 1   |     |        |          | …   |
| --- | --- | --- | --- | --- | --- | --- | ------- | --- | ------ | -------- | --- |
|     |     |     |     |     |     |     | capital |     | member | has also |     |
specifictasks,suchasparsingorcodegenera-
tion. Inthiswork,wedemonstratethatformal
…
|     |     |     |     |     |     |     | t = 2 a | Gitega | is  | Bujumbura |     |
| --- | --- | --- | --- | --- | --- | --- | ------- | ------ | --- | --------- | --- |
grammarscandescribetheoutputspacefora
muchwiderrangeoftasksandarguethatGCD
…
canserveasaunifiedframeworkforstructured t = 3 Airport is $ now
| NLP | tasks | in general. | For | increased | flexibil- |     |         |                      |     |     |     |
| --- | ----- | ----------- | --- | --------- | --------- | --- | ------- | -------------------- | --- | --- | --- |
|     |       |             |     |           |           |     | LEGEND: | S: root non-terminal |     |     |     |
ity, we introduce input-dependent grammars, x:  input 𝜀: empty string     : allowed tokens
|     |     |     |     |     |     |     | y:  output | 𝛼: entities from KB |     |     : forbidden tokens |     |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ------------------- | --- | ---------------------- | --- |
whichallowthegrammartodependonthein- $: end of sequence 𝛽: relations from KB →: decoding path
putandthusenablethegenerationofdifferent
outputstructuresfordifferentinputs. Wethen Figure1: Grammar-constraineddecoding(GCD),ap-
pliedtothetaskofclosedinformationextraction,where
| empirically |     | demonstrate |     | the power | and flexi- |     |     |     |     |     |     |
| ----------- | --- | ----------- | --- | --------- | ---------- | --- | --- | --- | --- | --- | --- |
thegoalistoextractalistyofsubject–relation–object
bilityofGCD-enhancedLMson(1)informa-
|     |     |     |     |     |     | tripletsfromtheinputtextx. |     |     | Subjectsandobjectsare |     |     |
| --- | --- | --- | --- | --- | --- | -------------------------- | --- | --- | --------------------- | --- | --- |
tionextraction,(2)entitydisambiguation,and
constrainedtobeWikidataentities,relationstobeaWi-
| (3)constituencyparsing. |     |     |     | Ourresultsindicate |     |     |     |     |     |     |     |
| ----------------------- | --- | --- | --- | ------------------ | --- | --- | --- | --- | --- | --- | --- |
that grammar-constrained LMs substantially kidatarelation. Duringdecoding,onlyvalidtokencon-
tinuationscompliantwiththegrammarareconsidered.
| outperform |     | unconstrained |     | LMs or | even beat |     |     |     |     |     |     |
| ---------- | --- | ------------- | --- | ------ | --------- | --- | --- | --- | --- | --- | --- |
Forsimplicity,weomitthespecialmarkersymbols[s],
| task-specificfinetunedmodels. |     |     |     | Grammarcon- |     |     |     |     |     |     |     |
| ----------------------------- | --- | --- | --- | ----------- | --- | --- | --- | --- | --- | --- | --- |
straintsthusholdgreatpromiseforharnessing [r],and[o]intheschemaofthegenerationprocess.
| off-the-shelf |     | LMs | for a | wide range | of struc- |     |     |     |     |     |     |
| ------------- | --- | --- | ----- | ---------- | --------- | --- | --- | --- | --- | --- | --- |
turedNLPtasks,especiallywheretrainingdata can be finetuned for specific tasks with minimal
modificationstothetrainingprocesswhilestillben-
| isscarceorfinetuningisexpensive. |     |     |     |     | Codeand |     |     |     |     |     |     |
| -------------------------------- | --- | --- | --- | --- | ------- | --- | --- | --- | --- | --- | --- |
data: https://github.com/epfl-dlab/GCD. efiting from the advantages of pretraining. More
recently,thescalingoflanguagemodelstolarger
1 Introduction
|     |     |     |     |     |     | sizes | has introduced |     | notable | in-context | learning |
| --- | --- | --- | --- | --- | --- | ----- | -------------- | --- | ------- | ---------- | -------- |
Pretrainedlanguagemodels(LMs)haveachieved capabilities (Brown et al., 2020; Radford et al.,
impressiveresultsacrossarangeoftasks,suchas 2019;SchickandSchütze,2021), suchthatlarge
machinetranslation,summarization,anddialogue language models (LLMs) can quickly and effec-
tivelyadapttonewtasksevenwithoutfinetuning,
| generation |     | (Brown | et al., | 2020; Touvron | et al., |     |     |     |     |     |     |
| ---------- | --- | ------ | ------- | ------------- | ------- | --- | --- | --- | --- | --- | --- |
2023). Allofthesemodelsarepretrainedonnext- when shown only few demonstrations as part of
| tokenpredictiontask,encouragingresearchersto |     |       |        |                     |     | theircontext. |     |     |     |     |     |
| -------------------------------------------- | --- | ----- | ------ | ------------------- | --- | ------------- | --- | --- | --- | --- | --- |
| cast other                                   | NLP | tasks | in the | same autoregressive |     |               |     |     |     |     |     |
Certainimportanttasks,however,suchasclosed
| generationframework. |     |     | Byframingtasksasautore- |     |     |     |     |     |     |     |     |
| -------------------- | --- | --- | ----------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
informationextraction(cIE),entitydisambiguation
| gressive | generation, |     | pretrained | language | models |     |     |     |     |     |     |
| -------- | ----------- | --- | ---------- | -------- | ------ | --- | --- | --- | --- | --- | --- |
(ED),orconstituencyparsing(CP),requiretheout-
∗WorkdonewhileatEPFL. put to follow a predefined format and adhere to
10932
Proceedingsofthe2023ConferenceonEmpiricalMethodsinNaturalLanguageProcessing,pages10932–10952
December6-10,2023©2023AssociationforComputationalLinguistics

arestrictedvocabulary(entities,relations,senses, perspective, the grammar-constrained decoding
dependency labels, etc.). Whereas LMs excel at (GCD)frameworkallowsresearcherstofocuson
generatingfree-formtext,theyarenotspecifically writingthegrammarwhileignoringtheimplemen-
designedforstructuredpredictiontaskswhereonly tationdetailsoftheconstraineddecodingprocess.
asmallsubsetoftheoutputspaceisvalid. Conse- Thisisincontrasttopreviouswork,wherethecon-
quently,structuredpredictiontaskspresentunique straintswereexpressedintheformoffinite-state
challengesbecauseconstrainedoutputspacesde- automata or trie-based data structures, which re-
mand both structural coherence and compliance quireasignificantengineeringefforttoimplement.
with a predefined vocabulary. For instance, Josi- WeenvisionGCDtobeassimpletouseasregular
foskietal.(2023)havedemonstratedthatfew-shot- expressions,inthesensethattheusercanspecifya
promptedlargelanguagemodelssuchasGPT-3.5 desiredoutputstructureinadeclarativeway,and
struggle with tasks such as cIE. This difficulty is theLM-generatedsequenceswillbeguaranteedto
primarily due to the extensive output vocabulary, bevalid. Withtheintroductionofinput-dependent
whichincludes2.7millionWikidataentitynames grammars, the scope of tasks that can be tackled
andapproximately1,000Wikidatarelationnames, withGCDcanbefurtherextendedtotaskssuchas
which is too vast to be conveyed with just a few entitydisambiguationandentitylinking,wherethe
demonstrationexamples. outputspaceisnotfixedbutdependsontheinput.
Weshowthat,bycombiningGCDwithpowerful
| One | way forward | is  | to finetune |     | LMs for | spe- |     |     |     |     |     |
| --- | ----------- | --- | ----------- | --- | ------- | ---- | --- | --- | --- | --- | --- |
LLMs,weachieveremarkableimprovementswith
cifictasks,whichinvolveslinearizingthedesired
few-shotlearning,evenrivalingtheperformanceof
| output format |         | into a string | format,    |     | thus enabling |     |                               |     |     |                    |     |
| ------------- | ------- | ------------- | ---------- | --- | ------------- | --- | ----------------------------- | --- | --- | ------------------ | --- |
|               |         |               |            |     |               |     | finetunedtask-specificmodels. |     |     | Thisisparticularly |     |
| training      | through | standard      | next-token |     | prediction.   |     |                               |     |     |                    |     |
excitingbecauseitshowsthatLMscanbeusedto
| For instance, | De  | Cao | et al. (2021) |     | and Josifoski |     |     |     |     |     |     |
| ------------- | --- | --- | ------------- | --- | ------------- | --- | --- | --- | --- | --- | --- |
solveamuchwiderrangeofstructuredtasksthan
| et al. (2022) | successfully |     | applied | this | technique |     |     |     |     |     |     |
| ------------- | ------------ | --- | ------- | ---- | --------- | --- | --- | --- | --- | --- | --- |
before,withouttheneedforfinetuning.
| to ED and | cIE, | respectively. |     | However, | this | ap- |     |     |     |     |     |
| --------- | ---- | ------------- | --- | -------- | ---- | --- | --- | --- | --- | --- | --- |
Ourcontributionscanbesummarizedasfollows:
| proach | has limitations: |     | it necessitates |     | an  | expen- |     |     |     |     |     |
| ------ | ---------------- | --- | --------------- | --- | --- | ------ | --- | --- | --- | --- | --- |
sivefinetuningpipelineforeachnewtask,which
|     |     |     |     |     |     |     | 1. We demonstrate |     | that the | output spaces | of  |
| --- | --- | --- | --- | --- | --- | --- | ----------------- | --- | -------- | ------------- | --- |
lacksflexibilityandrequiresbespoketrainingdata.
manystructuredNLPtaskscanbeformulated
Orthogonally,constraineddecoding(Trombleand
asformallanguages,thusconvertingthetasks
| Eisner, | 2006) | is a technique |     | that | can be | used |     |     |     |     |     |
| ------- | ----- | -------------- | --- | ---- | ------ | ---- | --- | --- | --- | --- | --- |
intogrammar-constraineddecodingproblems.
to enforce constraints on the output space of This formulation provides a unified frame-
| an autoregressive |     | language |     | model | during | infer- |     |     |     |     |     |
| ----------------- | --- | -------- | --- | ----- | ------ | ------ | --- | --- | --- | --- | --- |
worktotacklestructuredNLPtasks.
| ence. Constrained |               | decoding |     | has been | used   | in se- |                 |     |                 |           |     |
| ----------------- | ------------- | -------- | --- | -------- | ------ | ------ | --------------- | --- | --------------- | --------- | --- |
|                   |               |          |     |          |        |        | 2. We introduce |     | input-dependent | grammars, |     |
| mantic            | role labeling | (Deutsch |     | et al.,  | 2019), | con-   |                 |     |                 |           |     |
whichextendthesetoftasksthatcanbetack-
stituencyparsing(Deutschetal.,2019),codegen-
ledwithGCD.Weshowthatthiscanbeuseful,
| eration | (Scholak | et al., | 2021), | and | entity | disam- |     |     |     |     |     |
| ------- | -------- | ------- | ------ | --- | ------ | ------ | --- | --- | --- | --- | --- |
amongothers,fortaskssuchasEDandCP.
| biguation | (De | Cao et al., | 2021). | The | constraints |     |            |           |              |           |     |
| --------- | --- | ----------- | ------ | --- | ----------- | --- | ---------- | --------- | ------------ | --------- | --- |
|           |     |             |        |     |             |     | 3. Through | empirical | experiments, | we demon- |     |
havebeenexpressedintheformoffinite-stateau- stratetheeffectivenessofGCDonthreestruc-
| tomata | (Deutsch | et al., | 2019) | or trie-based |     | data |                |     |                     |     |     |
| ------ | -------- | ------- | ----- | ------------- | --- | ---- | -------------- | --- | ------------------- | --- | --- |
|        |          |         |       |               |     |      | turedNLPtasks: |     | cIE,ED,andCP.Weshow |     |     |
structuresforfastlookup(DeCaoetal.,2021).
|     |     |     |     |     |     |     | that our | method | can achieve | competitive | re- |
| --- | --- | --- | --- | --- | --- | --- | -------- | ------ | ----------- | ----------- | --- |
In this work, we show that, for a much wider sultsoncIEandEDwithoutanyfinetuning.
rangeofNLPtasks,therespectiveoutputspacecan
| be described | with      | a formal | grammar,       |     | giving | rise   |          |     |     |     |     |
| ------------ | --------- | -------- | -------------- | --- | ------ | ------ | -------- | --- | --- | --- | --- |
|              |           |          |                |     |        |        | 2 Method |     |     |     |     |
| to a unified | framework |          | for structured |     | NLP    | tasks. |          |     |     |     |     |
Given an appropriately defined grammar, we use WenowdescribeGCDandhowitcanconstrainthe
an incremental parser to play the role of a com- outputofLMsatdecodingtimebasedonaformal
pletion engine, which determines the set of valid grammar. Wefirstexplainhowtospecifytheoutput
nexttokensgiventhecurrentprefix. Weintegrate spacesofvariousNLPtasksviaformalgrammars.
thiscompletionenginewithapretrainedlanguage Then we show how an incremental parser can be
model to iteratively generate sequences that are usedasacompletionenginetoconstraintheLM’s
valid accordingtothegrammarandplausibleac- generationprocesstoproducegrammaticallyvalid
| cording | to the | LM (cf. | Fig. 1). | From | a practical |     | outputsonly. |     |     |     |     |
| ------- | ------ | ------- | -------- | ---- | ----------- | --- | ------------ | --- | --- | --- | --- |
10933

|     |     |     |     |     |     | Token-level | formal | grammars. |     | A   | formal gram- |
| --- | --- | --- | --- | --- | --- | ----------- | ------ | --------- | --- | --- | ------------ |
(1) Closed information extraction: see Fig. 1
marGisdefinedasatuple(V,Σ,P,S)where
(2)* Entity disambiguation: S → ℓ m[𝛼]r, where ℓ is left
context of mention m, r is right context, and 𝛼 is disjunction
of candidate entities for mention m • V isafinitesetofnon-terminalsymbols,
| (3)* Constituency parsing: S → B |     |     | ; B →[𝛼 (B |  | C   |     |     |     |     |     |     |     |
| -------------------------------- | --- | --- | ---------- | ------ | --- | --- | --- | --- | --- | --- | --- |
|                                  |     |     | 0, 0 i, j  | i, j+1 | i,  |     |     |     |     |     |     |
 → ](E
); C  → x (C  | E ); C  → E ; E  | B );  • Σisafinitesetofterminalsymbols,
| j+1 i, j        | i i+1, j i+1, j                 | n,j | n, j i, j+1 | i, j    | i, j |                                   |     |     |     |     |     |
| --------------- | ------------------------------- | --- | ----------- | ------- | ---- | --------------------------------- | --- | --- | --- | --- | --- |
| E  → ]E         | ; E  → 𝜀, where 𝛼 = (S|NP|VP|…) |     |             |         |      |                                   |     |     |     |     |     |
| n ,  j+ 1       | n ,  j n ,  0                   |     |             |         |      | • Pisafinitesetofproductionrules, |     |     |     |     |     |
| (4 ) *  C orefe | r e nc e   resolution: S → x    |     | [(x | … | x | | ⊥)] S | ;    |                                   |     |     |     |     |     |
|                 |                                 | i   | i   1       | n       | i+1  |                                   |     |     |     |     |     |
S → 𝜀, where ⊥ means “no referent”
| n                                                         |     |     |     |     |     | • S | V isthestartsymbol. |     |     |     |     |
| --------------------------------------------------------- | --- | --- | --- | --- | --- | --- | ------------------- | --- | --- | --- | --- |
| (5)* Part-of-speech tagging: S → x [(NOUN | VERB | ADJ |  |     |     |     |     |     |     | ∈                   |     |     |     |     |
i i
…)] S ; S → 𝜀
| i+1 | n   |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
(6)* Dependency parsing: S → x [(ROOT | NSUBJ | DOBJ |  Weillustratethesuitabilityofformalgrammars
| …) (x | … | x | ⊥)]S | ; S → 𝜀, where ⊥ means “no head” | i   | i   |     |     |     |     |     |     |     |     |
| -------------------- | -------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
forspecifyingtheoutputspacesofstructuredNLP
| (7)* Word sense disambiguation: S → x[𝛼] S 1 | n i+1 | n   |      | ; S → 𝜀,  |     |     |     |     |     |     |     |
| -------------------------------------------- | ----- | --- | ---- | --------- | --- | --- | --- | --- | --- | --- | --- |
|                                              |       |     | i i  | i i+ 1    | n   |     |     |     |     |     |     |
where 𝛼 is the disjunction of all Word Net g los ses  o f w ord x  tasksinFig.2using14commontasksasexamples.
| i                           |                                         |     |           |              | i   |         |           |             |            |          |             |
| --------------------------- | --------------------------------------- | --- | --------- | ------------ | --- | ------- | --------- | ----------- | ---------- | -------- | ----------- |
| (8)* Phrase chunking: S → B |                                         | ; B |  → [C ; B |  → 𝜀; C  → x |     |         |           |             |            |          |             |
|                             |                                         | 0   | i i       | n i          | i   | In our  | approach, | the         | user first | writes   | a formal    |
| (C  | 𝛼] B                  | ); C → 𝛼], where 𝛼 = (NP | VP | PP | …) |     |           |              |     |         |           |             |            |          |             |
| i+1                         | i+1 n                                   |     |           |              |     | grammar | G over    | characters. |            | In order | to obtain a |
(9)* Semantic role labeling: Same as phrase chunking,
but with 𝛼 = (TARGET | ARG0 | ARG1 | …) token-levelgrammarG thatcanbeusedtocon-
tok
(10)* Entity linking: Same as phrase chunking, but with 𝛼
strainthedirectoutputofLMs—tokensequences—
the disjunction of all KB entity names (or ⊥ for “no entity”)
(11)* CCG parsing: Same as constituency parsing, but  weusethetokensetΣ tok asterminalsymbolsand
with syntactic types (e.g., (S\NP)/NP)) instead of constituent  apply the tokenizer to the sequences of terminal
labels. Extra constraints ensure that nodes have at most
two children and that syntactic types combine correctly. symbols appearing in the rules P, obtaining the
(12)* Question answering: S → [q][A]; A → (𝜀 | 𝛼 A),
|                                                       |     |     |     |     |     | token-levelrulesP |       | .   | Thisyieldsthetoken-level |     |     |
| ----------------------------------------------------- | --- | --- | --- | --- | --- | ----------------- | ----- | --- | ------------------------ | --- | --- |
| where q is the question and 𝛼 the disjunction of all  |     |     |     |     |     |                   |       | tok |                          |     |     |
|                                                       |     |     |     |     |     | grammarG          | =(V,Σ |     | ,P ,S),whichdescribes    |     |     |
| vocabulary words                                      |     |     |     |     |     |                   | tok   | tok | tok                      |     |     |
(13)* Extractive summarization: S → (𝜀 |[𝛼]S), where 𝛼 is  thesamelanguageasthecharacter-levelgrammar
the disjunction of all sentences from input x
G. Wethenuseanincrementalparser(seebelow)
(14)* Semantic parsing with λ-calculus:  A logical form is
a rooted tree, generated by a context-free grammar todecidewhetheratokensequenceyisinthelan-
|     |     |     |     |     |     | guagegeneratedbyG |     |     | .   |     |     |
| --- | --- | --- | --- | --- | --- | ----------------- | --- | --- | --- | --- | --- |
tok
| Figure2: | Formalgrammarsfor14structuredNLP |     |     |     |     |         |                 |     |      |          |          |
| -------- | -------------------------------- | --- | --- | --- | --- | ------- | --------------- | --- | ---- | -------- | -------- |
|          |                                  |     |     |     |     | Despite | its simplicity, |     | this | approach | has some |
tasks,highlightingthegeneralapplicabilityofgrammar-
constraineddecoding. All14grammarsarecontext-free limitations. Widely used tokenization methods
(mostlyregular). *marksinput-dependentgrammars. suchasBPE(Sennrichetal.,2016)allowthesame
Inputsx= x ,...,x aresequencesoflexicalunits string to be tokenized in different ways. For ex-
⟨ 0 n 1 ⟩
| (e.g., words); | 0 i − | n 1; | single capital | letters | are |        |            |       |        |           |        |
| -------------- | ----- | ---- | -------------- | ------- | --- | ------ | ---------- | ----- | ------ | --------- | ------ |
|                |       |      |                |         |     | ample, | the string | “[[[” | can be | tokenized | as “[[ |
|                | ≤ ≤   | −    |                |         |     |        |            |       |        |           |        |
non-terminalsymbols;SorS isthestartsymbol;εis [”, “[[[” “[ [ [”,
|     |     |     | 0   |     |     |     | or  |     | all | of which | would be |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | -------- |
theemptystring;[and]arespecialterminalsymbols.
|     |     |     |     |     |     | detokenizedtotheoriginalstring“[[[”. |     |        |           |        | Toavoid |
| --- | --- | --- | --- | --- | --- | ------------------------------------ | --- | ------ | --------- | ------ | ------- |
|     |     |     |     |     |     | this ambiguity,                      |     | we can | add extra | spaces | between |
2.1 NLPtasksasformallanguages
|                                             |                                 |      |             |     |       | the brackets                                  | in the  | grammar |                   | and force  | the single |
| ------------------------------------------- | ------------------------------- | ---- | ----------- | --- | ----- | --------------------------------------------- | ------- | ------- | ----------------- | ---------- | ---------- |
|                                             |                                 |      |             |     |       | brackettobeatoken.                            |         |         | Thisapproachis,   |            | however,   |
|                                             |                                 |      |             |     |       | not principled                                | and     | relies  | on                | a specific | tokenizer. |
| The input                                   | x and output                    | y of | NLP tasks   | are | typi- |                                               |         |         |                   |            |            |
|                                             |                                 |      |             |     |       | We therefore                                  | believe |         | that a principled |            | approach   |
| cally sequences                             | of tokens,                      |      | x= x ,...,x |     | and   |                                               |         |         |                   |            |            |
|                                             |                                 |      | ⟨ 0         | n 1 | ⟩     |                                               |         |         |                   |            |            |
|                                             |                                 |      |             | −   |       | fordefiningtoken-levelgrammarsisaninteresting |         |         |                   |            |            |
| y= y 0 ,...,y                               | m 1 . Whereastheinputxisusually |      |             |     |       |                                               |         |         |                   |            |            |
| ⟨                                           | ⟩                               |      |             |     |       | directionforfuturework.                       |         |         |                   |            |            |
| arbitrary,formanytaskstheoutputyneedstofol- | −                               |      |             |     |       |                                               |         |         |                   |            |            |
lowaspecificstructure. Forinstance,ininforma- GrammaticalFramework. Sincethetoken-level
tionextraction,yisrequiredtoconsistofsubject– grammarG istokenizer-dependent,therearein
tok
relation–object triplets (cf. Fig. 1). Since formal generalmultipletoken-levelgrammarsforthesame
languagesprovidearigorousandcompleteframe- grammar G. This one-to-many mapping from a
workfordescribingthestructureofanycomputable character-levelgrammartoatoken-levelgrammar
setofobject(accordingtotheChurch–Turingthe- isanalogoustotheone-to-manymappingfromab-
sis),theyofferapromisingwaytodefinetheoutput stract syntax trees to different programming lan-
spacesofstructuredNLPtasks. Inordertodefine guages. For this reason, we adopt Grammatical
theformallanguagescorrespondingtotheoutput Framework(GF)(Ranta,2019)todefineboththe
grammarGandthetoken-levelgrammarG
| spacesofstructuredNLPtasks,ourframeworkre- |     |     |     |     |     |     |     |     |     |     | tok . GF |
| ------------------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- |
liesonformalgrammars,auniversalformalismthat isameta-languageformultilingualgrammarappli-
candescribeanyformallanguage. Fortractability, cations,whichallowsustodefineanabstractgram-
wefocusontheclassofcontext-freegrammars. maraswellasconcretegrammarsforlinearizing
10934

abstract syntax trees into different tokenizer-spe- 2.3 Few-shotlearningwithGCD
| cific“languages”. |     | Inourcase,theabstractgrammar |     |     |     |     |          |              |     |       |             |     |     |
| ----------------- | --- | ---------------------------- | --- | --- | --- | --- | -------- | ------------ | --- | ----- | ----------- | --- | --- |
|                   |     |                              |     |     |     |     | To adapt | a pretrained |     | LM to | a new task, | one | can |
isthecharacter-levelgrammarGandtheconcrete
|     |     |     |     |     |     |     | either finetune |     | the LM | on  | task-specific | training |     |
| --- | --- | --- | --- | --- | --- | --- | --------------- | --- | ------ | --- | ------------- | -------- | --- |
grammarsarethetoken-levelgrammarsfordiffer-
dataorusefew-shotlearningiftheLMispowerful
enttokenizers.
|                 |      |          |       |        |           |      | enough.                 | In this  | work,    | we use | GCD              | in conjunc-  |     |
| --------------- | ---- | -------- | ----- | ------ | --------- | ---- | ----------------------- | -------- | -------- | ------ | ---------------- | ------------ | --- |
|                 |      |          |       |        |           |      | tion with               | few-shot | learning |        | to adapt         | a pretrained |     |
| Input-dependent |      | grammars |       | (IDG). | While     | the  |                         |          |          |        |                  |              |     |
|                 |      |          |       |        |           |      | largeLM(LLM)tonewtasks. |          |          |        | Insteadofprompt- |              |     |
| output of       | many | NLP      | tasks | can be | described | by a |                         |          |          |        |                  |              |     |
formalgrammar,sometasksrequireagrammarthat ing the LLM to generate free-form text, we use
GCDtoconstraintheoutputtobegrammatically
| isdependentontheinputsequence. |     |     |     |     | Forexample, |     |          |                                    |     |     |     |     |     |
| ------------------------------ | --- | --- | --- | --- | ----------- | --- | -------- | ---------------------------------- | --- | --- | --- | --- | --- |
|                                |     |     |     |     |             |     | correct. | ThisallowsustoleveragetheLLM’sfew- |     |     |     |     |     |
inentitydismbiguation,theoutputneedstobecon-
shotlearningcapabilitytogetherwiththegrammar-
strainedtothesetofentitycandidates,whichusu-
allycontainsdozensofentitynamessemantically inducedknowledgeofthetask’soutputstructure.
Forthesametask,wecanusedifferentgrammars
relatedtothetargetmentionintheinputsequence.
toconstraintheoutputoftheLLM.Forexample,
| In constituency |     | parsing, | outputs |     | are parse | trees |     |     |     |     |     |     |     |
| --------------- | --- | -------- | ------- | --- | --------- | ----- | --- | --- | --- | --- | --- | --- | --- |
whoseterminalnodesaretheinputtokens. These in entity disambiguation, we can use a grammar
twotasksbothrequireagrammarthatisdependent G 1 thatdependsontheinputsequencetoconstrain
|             |                                |     |     |     |     |     | the output | to the | input-specific |     | candidate |     | set, or |
| ----------- | ------------------------------ | --- | --- | --- | --- | --- | ---------- | ------ | -------------- | --- | --------- | --- | ------- |
| ontheinput. | Existingworkhasfocusedonusinga |     |     |     |     |     |            |        |                |     |           |     |         |
singlegrammartoconstrainthedecodingregard- wecoulduseagrammarG thatisindependentof
2
lessoftheinputsequence. Whereasthisissuitable the input to constrain the output to be any valid
|                                              |     |     |     |     |     |     | entityname. | WhilebothG |     | andG     | canbeusedto |         |     |
| -------------------------------------------- | --- | --- | --- | --- | --- | --- | ----------- | ---------- | --- | -------- | ----------- | ------- | --- |
| fortaskswheretheoutputspaceisindependentof   |     |     |     |     |     |     |             |            |     | 1        | 2           |         |     |
|                                              |     |     |     |     |     |     | constrain   | the output | of  | the LLM, | G           | reduces | the |
| theinputsequence,suchascodegeneration(Poesia |     |     |     |     |     |     |             |            |     |          | 1           |         |     |
et al., 2022) or information extraction (Josifoski searchspacemoreandthusismoreeffective.
| et al., 2022) | (cf. | Fig. | 1), 13 | of the | 14 tasks | listed |                     |     |     |     |     |     |     |
| ------------- | ---- | ---- | ------ | ------ | -------- | ------ | ------------------- | --- | --- | --- | --- | --- | --- |
|               |      |      |        |        |          |        | 3 Experimentalsetup |     |     |     |     |     |     |
inFig.2(thosewithanasterisk)requireaninput-
dependentgrammar.
AlthoughGCDcanbeappliedtomanytasks,we
concentrateonthreetasksinordertoshowcaseits
2.2 Grammar-constraineddecoding(GCD) effectiveness: closedinformationextraction(cIE),
entitydisambiguation(ED),andconstituencypars-
TheLMdecodingprocessproducestokensoneby ing (CP). The first two tasks are examples where
one. Toenforcetheformalgrammar,weintervene the output is restricted to a predefined set of en-
duringdecodingbypruningtheprobabilitydistri-
|     |     |     |     |     |     |     | tities and | relations, | while | the | third is | an example |     |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ---------- | ----- | --- | -------- | ---------- | --- |
butiontoincludeonlythesubsetoftokensthatare ofataskwheretheoutputisacomplextreestruc-
allowedbytheformalgrammar. Thesubsetofal- ture. AllthreetasksarechallengingforLLMsin
lowedtokensisreturnedbyanincrementalparser, the few-shot setting, and we show that GCD can
whichtakesthepartiallygeneratedsequenceand
significantlyimproveLLMperformance.
| the formal           | grammar |     | as inputs             | and | returns | the set |                                      |     |     |     |     |     |     |
| -------------------- | ------- | --- | --------------------- | --- | ------- | ------- | ------------------------------------ | --- | --- | --- | --- | --- | --- |
|                      |         |     |                       |     |         |         | 3.1 Closedinformationextraction(cIE) |     |     |     |     |     |     |
| ofnextallowedtokens. |         |     | Theroleoftheparsercan |     |         |         |                                      |     |     |     |     |     |     |
beabstractedasacompletionengine(Poesiaetal.,
|     |     |     |     |     |     |     | Taskdescription. |     | Thegoalofclosedinformation |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ---------------- | --- | -------------------------- | --- | --- | --- | --- |
2022),whichderivescompletioncandidatesfrom
extraction(cIE)istoextractacomprehensivesetof
| thepartialsequenceandtheformalgrammarG. |     |     |     |     |     | In  |                                |     |     |     |                |     |     |
| --------------------------------------- | --- | --- | --- | --- | --- | --- | ------------------------------ | --- | --- | --- | -------------- | --- | --- |
|                                         |     |     |     |     |     |     | factsfromnatural-languagetext. |     |     |     | Formally,given |     |     |
thiswork,weusetheincrementalparserofGram-
aknowledgebase(KB)containingacollectionof
maticalFramework(Angelov,2009)asthecomple-
|              |            |         |           |            |           |          | entitiesE                  | andacollectionofrelationsR,thegoal |     |     |       |     |      |
| ------------ | ---------- | ------- | --------- | ---------- | --------- | -------- | -------------------------- | ---------------------------------- | --- | --- | ----- | --- | ---- |
| tion engine. | This       | process | is        | compatible |           | with any |                            |                                    |     |     |       |     |      |
|              |            |         |           |            |           |          | istoextractthecompletesety |                                    |     |     | set E | R   | E of |
| decoding     | algorithm, |         | including | greedy     | decoding, |          |                            |                                    |     |     | ⊂     | × × |      |
facttripletsfromagiveninputtextx.
| beam search, | top-k | sampling, |     | etc. | GCD | can also |     |     |     |     |     |     |     |
| ------------ | ----- | --------- | --- | ---- | --- | -------- | --- | --- | --- | --- | --- | --- | --- |
beappliedtoanyautoregressivelanguagemodel, Grammar. Weimplementthegrammarshownin
provided that we have access to the distribution Fig.1. Outputsaresetsy oftripletsrepresented
set
y
overthevocabularyateachdecodingstep. Since as structured sequences of tokens. Each triplet
API-basedservicessuchasOpenAIdonotprovide consistsofasubjectentityname,arelationname,
accesstothedistributionoverthevocabulary,they and an object entity name, each preceded by the
specialmarker[s],[r],or[o],respectively.
| cannotbeusedwithGCD. |     |     |     |     |     |     |     |     |     |     |     |     | For |
| -------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
10935

instance,thetwo-tripletsety = (Witchita,cast inthedataofLeandTitov(2018)). Theconstraints
|     |     |     | set | {   |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
member,JohnSmith);(Witchita,instanceof,film) imposedbyIIGarethusweakerthanthoseofIDG.
}
ismappedtoy=“[s]Witchita[r]castmember Moreover,forcingthemodelviatheIDGtorepeat
[o]JohnSmith[s]Witchita[r]instanceof[o] theleftcontext(e.g.,“Therearetwotypesofelec-
film”. Entityandrelationnamesarerestrictedtoa tricity:”) may guide the model (via conditioning)
predefinedsetofentities(2.7M)andrelations(888) ingeneratingthecorrectentityname.
| from the | Wikidata        | KB  | (Vrandecˇic´, | 2012). | The       |                                     |                |     |         |     |        |
| -------- | --------------- | --- | ------------- | ------ | --------- | ----------------------------------- | -------------- | --- | ------- | --- | ------ |
|          |                 |     |               |        |           | Dataset                             | and evaluation |     | metric. | For | the ED |
| grammar  | is context-free |     | and allows    | an     | arbitrary |                                     |                |     |         |     |        |
|          |                 |     |               |        |           | task,weemploysixwidelyuseddatasets: |                |     |         |     | AIDA-  |
numberoftripletstobegenerated,includingzero.
CoNLL(Hoffartetal.,2011),MSNBC,ACE2004,
|         |                |     |         | We  | use the | AQUAINT,CLUEWEB,andWIKI(Gabrilovich |     |     |     |     |     |
| ------- | -------------- | --- | ------- | --- | ------- | ----------------------------------- | --- | --- | --- | --- | --- |
| Dataset | and evaluation |     | metric. |     |         |                                     |     |     |     |     |     |
SynthIE-textdataset(Josifoskietal.,2023),asyn- etal.,2013;GuoandBarbosa,2017). Weuseonly
thetic dataset generated by prompting GPT-3.5. the test data to evaluate the effectiveness of our
Thisdataset, incomparisontopreviousoneslike method in a few-shot learning setting. To mea-
REBEL(HuguetCabotandNavigli,2021),ischar- suretheperformanceofourapproach,weemploy
acterizedbyitslargersize,increaseddiversity,and micro-accuracy as the evaluation metric. Further
higher quality according to human ratings (Josi- detailsaboutthedatasetsandevaluationmetricare
foskietal.,2023). TheSynthIE-textdatasetcom- providedinAppendixD.
| prises 10K | validation | samples | and | 50K | test sam- |     |     |     |     |     |     |
| ---------- | ---------- | ------- | --- | --- | --------- | --- | --- | --- | --- | --- | --- |
ples. For the purpose of evaluating our method 3.3 Constituencyparsing(CP)
| in the few-shot |     | scenario, | we exclusively |     | employ |     |     |     |     |     |     |
| --------------- | --- | --------- | -------------- | --- | ------ | --- | --- | --- | --- | --- | --- |
thetestdata. Wemeasureperformanceviatriplet- Task description. Constituency parsing (CP) is
thetaskofparsingasentenceintoaconstituency
basedmicro-precision,recall,andF1-score,follow-
|     |     |     |     |     |     | parse tree | capturing | the | syntactic | structure | of the |
| --- | --- | --- | --- | --- | --- | ---------- | --------- | --- | --------- | --------- | ------ |
ingJosifoskietal.(2022).
sentence.
3.2 Entitydisambiguation(ED)
|     |     |     |     |     |     | Grammar. | TheoutputinCPmustbeavalid—but |     |     |     |     |
| --- | --- | --- | --- | --- | --- | -------- | ----------------------------- | --- | --- | --- | --- |
notnecessarilycorrect—constituencyparsetreein
| Taskdescription. |     | Entitydisambiguation(ED)is |     |     |     |     |     |     |     |     |     |
| ---------------- | --- | -------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
PennTreebankformat(SekineandCollins,2008).
thetaskofidentifyingtheexactentityfromapre-
Avalidparsetreeisdefinedasatreethatsatisfies
| defined | knowledge | base | (e.g., Wikidata) |     | referred |     |     |     |     |     |     |
| ------- | --------- | ---- | ---------------- | --- | -------- | --- | --- | --- | --- | --- | --- |
theconstraintsofcompleteness(everywordinthe
| to by a | mention | demarcated | by special | tokens | in  |     |     |     |     |     |     |
| ------- | ------- | ---------- | ---------- | ------ | --- | --- | --- | --- | --- | --- | --- |
sentenceisincludedsomewhereintheparsetree),
| aninputtext. | Incertaincases,theinputmayalso |     |     |     |     |     |     |     |     |     |     |
| ------------ | ------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
balancedbrackets(everyrightbracketclosesapre-
| contain | a set of | candidate | entities | to narrow | the |     |     |     |     |     |     |
| ------- | -------- | --------- | -------- | --------- | --- | --- | --- | --- | --- | --- | --- |
viouslyunclosedleftbracket,andeveryleftbracket
| searchscope. |     |     |     |     |     | iseventuallyclosedbyarightbracket),andlabel |     |     |     |     |     |
| ------------ | --- | --- | --- | --- | --- | ------------------------------------------- | --- | --- | --- | --- | --- |
consistency(thelabelofterminalandnon-terminal
| Grammar. | We  | use grammar | 2   | of Fig. | 2. Fol- |     |     |     |     |     |     |
| -------- | --- | ----------- | --- | ------- | ------- | --- | --- | --- | --- | --- | --- |
lowing De Cao et al. (2021), the output structure nodesisconsistentwiththePennTreebankformat).
consists of the mention followed by the inferred Tocapturetheseconstraints,weusegrammar3
|                             |     |     |                   |     |     | ofFig.2. | Thegrammarreproducestheinput,rep- |     |     |     |     |
| --------------------------- | --- | --- | ----------------- | --- | --- | -------- | --------------------------------- | --- | --- | --- | --- |
| entitynameinsquarebrackets. |     |     | Forinstance,given |     |     |          |                                   |     |     |     |     |
theinput“Therearetwotypesofelectricity: <ent> resentedasasequencex= x ,...,x ofwords,
|     |     |     |     |     |     |     |     |     | 0   | n   | 1   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|     |     |     |     |     |     |     |     |     | ⟨   | −   | ⟩   |
DC </ent> and AC”, the output is represented inleft-to-rightorder,interspersingitwithnodela-
as“Therearetwotypesofelectricity: <ent>DC belsandbalancedbrackets. Inordertoguarantee
[Directcurrent]</ent>andAC”.Thegrammaris balancedbrackets,thenon-terminalsB countthe
i,j
regularandinput-dependent. Itforcesthemodelto number of opened left brackets [ using the sec-
generatethementionfirst,followedbyanopening ondsubscriptindex j,andtherulesensurethatthe
|     |     |     |     |     |     | number | of closed | brackets | can | never | exceed the |
| --- | --- | --- | --- | --- | --- | ------ | --------- | -------- | --- | ----- | ---------- |
squarebracket,anentitynamefromthecandidate
set,andfinallyaclosingsquarebracket. Thecan- numberofpreviouslyopenedbrackets. Asanex-
didatesetismention-dependentandisprovidedin ample,fortheinputx=“NkurunzizaleadsBurundi
y=
the dataset. To demonstrate the benefits of using from Gitega”, one valid parse tree would be
“[S[NPNkurunziza][VPleads[NPBurundi][PP
aninput-dependentgrammar(IDG),wealsoexper-
iment with an input-independent grammar (IIG). from[NPGitega]]]]”.
Forsuchagrammar,thecandidatesetneedstobe Note that the grammar in this task needs to be
theentireentitycatalogofallentities(e.g.,470K input-dependent due to the aforementioned com-
10936

pleteness constraint. To demonstrate this, we Method Precision Recall F1
alsoexperimentwithaninput-independentgram-
Weaklysupervised
mar,acontext-freegrammarthatrecursivelygen-
|     |     |     |     |     |     | GenIET5-base |     | 49.6±0.3 |     | 26.8±0.2 | 34.8±0.2 |
| --- | --- | --- | --- | --- | --- | ------------ | --- | -------- | --- | -------- | -------- |
eratesaparsetreeofarbitrarysizewhoseterminal
Few-shotunconstrained
XX.
nodes are anonymized as This grammar sat- LLaMA-7B 10.2±0.5 14.3±0.7 11.9±0.5
isfiesthebalanced-bracketsandlabel-consistency LLaMA-13B 10.3±0.6 17.0±0.9 12.9±0.6
|                                              |     |     |     |     |     | LLaMA-33B |     | 14.1±1.0 |     | 23.1±1.4 | 17.5±1.0 |
| -------------------------------------------- | --- | --- | --- | --- | --- | --------- | --- | -------- | --- | -------- | -------- |
| constraints,butnotthecompletenessconstraint. |     |     |     |     | As  |           |     |          |     |          |          |
|                                              |     |     |     |     |     | Vicuna-7B |     | 12.5±0.2 |     | 16.7±0.1 | 14.3±0.2 |
thegrammariscontext-free,itcangenerateaparse
|           |              |        |           |          |     | Vicuna-13B |     | 13.4±0.2 |     | 15.2±0.2 | 14.4±0.2 |
| --------- | ------------ | ------ | --------- | -------- | --- | ---------- | --- | -------- | --- | -------- | -------- |
| tree with | an arbitrary | number | of nodes, | possibly |     |            |     |          |     |          |          |
Few-shotconstrained
largerorsmallerthanthenumberofwordsinthe
|     |     |     |     |     |     | LLaMA-7B |     | 27.9±0.6 |     | 20.2±0.5 | 23.5±0.5 |
| --- | --- | --- | --- | --- | --- | -------- | --- | -------- | --- | -------- | -------- |
input,whichwouldresultinaninvalidparsetree. LLaMA-13B 36.2±0.7 26.5±0.5 30.6±0.5
|     |     |     |     |     |     | LLaMA-33B |     | 39.3±0.9 |     | 33.2±0.8 | 36.0±0.7 |
| --- | --- | --- | --- | --- | --- | --------- | --- | -------- | --- | -------- | -------- |
Dataset and evaluation metric. We use the test Vicuna-7B 25.4±0.5 15.8±0.3 19.5±0.3
split of Penn Treebank to evaluate the effective- Vicuna-13B 38.7±1.0 19.8±0.8 26.1±0.8
nessofourmethodinafew-shotlearningsetting.
|     |     |     |     |     |     | Table1: | Mainresultsforclosedinformationextrac- |     |     |     |     |
| --- | --- | --- | --- | --- | --- | ------- | -------------------------------------- | --- | --- | --- | --- |
SinceweobservedthattheLLaMAmodelsusedin
tion(4shots),intermsofprecision,recall,andF1-score
ourexperimentsstruggletogeneratefullycorrect (micro-averaged,with90%confidenceintervals)onthe
|     |     |     |     |     |     | SynthIE-text-smalldataset(Josifoskietal.,2023). |     |     |     |     | Best |
| --- | --- | --- | --- | --- | --- | ----------------------------------------------- | --- | --- | --- | --- | ---- |
parsetreesforlonginputsentences,bothwithand
without constraints, we use only sentences with resultsinbold. WereporttheGenIEmodel(Josifoski
etal.,2022)forthesupervisedsetting.
| goldparsetreesshorterthan64tokens. |     |     |     | Wereport |     |     |     |     |     |     |     |
| ---------------------------------- | --- | --- | --- | -------- | --- | --- | --- | --- | --- | --- | --- |
thebracketingF1-scorereturnedbythePYEVALB
|                                |         |             |              |           |     | 4.1 Closedinformationextraction(cIE) |             |          |     |       |           |
| ------------------------------ | ------- | ----------- | ------------ | --------- | --- | ------------------------------------ | ----------- | -------- | --- | ----- | --------- |
| toolasourmainevaluationmetric. |         |             | Asweobserved |           |     |                                      |             |          |     |       |           |
| that LLaMA                     | without | constraints | often        | generates |     |                                      |             |          |     |       |           |
|                                |         |             |              |           |     | Results                              | for cIE are | reported | in  | Table | 1. Uncon- |
invalidparsetrees,wealsoreportvalidity(theper- strained LLaMA, even with few-shot demonstra-
centageofvalidparsetrees)asanadditionalmetric. tions,performspoorlyoncIE.Thisisnotsurpris-
|     |     |     |     |     |     | ing, since | the cIE task | requires |     | generating | valid |
| --- | --- | --- | --- | --- | --- | ---------- | ------------ | -------- | --- | ---------- | ----- |
entityandrelationnamesfromaknowledgebase
3.4 LLMsandprompting
|     |     |     |     |     |     | (Wikidatainourcase). |     | AlthoughLLMshavebeen |     |     |     |
| --- | --- | --- | --- | --- | --- | -------------------- | --- | -------------------- | --- | --- | --- |
WeutilizeLLaMA(Touvronetal.,2023)andVi-
exposedtoWikidatatoacertainextentduringpre-
cuna(Chiangetal.,2023)asbackboneLMs,with- training,theystillstrugglewithgeneratingaccurate
outperforminganyfinetuningondownstreamtasks. entityandrelationnamescontainedintheKB.This
| Concretely,                   | we evaluate | the | LLaMA-{7B, |             | 13B, |             |              |       |           |                   |              |
| ----------------------------- | ----------- | --- | ---------- | ----------- | ---- | ----------- | ------------ | ----- | --------- | ----------------- | ------------ |
|                               |             |     |            |             |      | can be seen | as a special | case  | of        | the hallucination |              |
| 33B}andVicuna-{7B,13B}models. |             |     |            | Toconstruct |      |             |              |       |           |                   |              |
|                               |             |     |            |             |      | problem,    | where the    | model | generates |                   | entities and |
the prompt, we begin by randomly selecting sev- relationsnotpresentintheKB.
eraldatapointsfromthetrainingsetandusethem
|             |                |         |     |          |       | We see | a significant | improvement |     |     | when con- |
| ----------- | -------------- | ------- | --- | -------- | ----- | ------ | ------------- | ----------- | --- | --- | --------- |
| to manually | craft multiple | prompts |     | for each | task. |        |               |             |     |     |           |
strainingthegenerationtoonlyproducevalidenti-
| For more | details about | the used | prompts |     | and the |                   |                            |     |     |     |     |
| -------- | ------------- | -------- | ------- | --- | ------- | ----------------- | -------------------------- | --- | --- | --- | --- |
|          |               |          |         |     |         | tiesandrelations. | Notably,LLaMA-33BbeatsGen- |     |     |     |     |
decodingsettings,seeAppendicesEandF.
|     |     |     |     |     |     | IET5-base(Josifoskietal.,2022), |     |     |     | astate-of-the- |     |
| --- | --- | --- | --- | --- | --- | ------------------------------- | --- | --- | --- | -------------- | --- |
artautoregressivemodelspecificallytrainedforthe
4 Experimentalresults cIEtaskonsuperviseddatafromtheREBELdata-
|     |     |     |     |     |     | set(HuguetCabotandNavigli,2021). |     |     |     |     | Inthetable, |
| --- | --- | --- | --- | --- | --- | -------------------------------- | --- | --- | --- | --- | ----------- |
Next, we present the results for each task, show- werefertoGenIEasweaklysupervisedbecauseit
ing that, whereas the unconstrained LLaMA and was not trained on the train split of SynthIE-text,
Vicuna models perform poorly, the grammar- butonREBEL.Weobservethatthegrammar-con-
constrained versions perform significantly better. strainedLLaMAmodelsbalanceprecisionvs.re-
Wealsoshowinput-dependentgrammarstobecru- callbetterthanGenIE,achievingahigherF1-score.
cialforperformance,astheyallowthemodelsto WhileGenIEexhibitshigherprecision,itsrecallis
adapttotheinputandgeneratemoreaccurateout- lower,implyingthatitmissesmanyentitiesandre-
puts. Out of the tested few-shot-prompted mod- lations. ThismaybebecauseGenIEwasoptimized
els,LLaMA-33Bwithinput-dependentgrammars fortheREBELdatasetandmayhavememorized
achieves the best performance on all tasks, even theentitiesandrelationsinthedataset. Asdomain-
rivalingfinetunedmodelsoncIEandED. specific training data is often scarce (Dunn et al.,
10937

|     | Method |     |     |     | AIDA | MSNBC | AQUAINT | ACE2004 |     | CWeb | WIKI | Avg. |
| --- | ------ | --- | --- | --- | ---- | ----- | ------- | ------- | --- | ---- | ---- | ---- |
Supervised
|     | LeandTitov(2018)     |     |     |     | 89.6 | 92.2 | 90.7 | 88.1 |     | 78.2 | 81.7 | 86.8 |
| --- | -------------------- | --- | --- | --- | ---- | ---- | ---- | ---- | --- | ---- | ---- | ---- |
|     | BLINKw/ocandidateset |     |     |     | 79.6 | 80.0 | 80.3 | 82.5 |     | 64.2 | 75.5 | 77.0 |
|     | BLINK(Wuetal.,2020)  |     |     |     | 86.7 | 90.3 | 88.9 | 88.7 |     |      | 86.1 | 87.2 |
82.6
|     | GENREonlyAIDAdata         |     |     |     | 88.6 | 88.1 | 77.1 | 82.3 |     | 71.9 | 71.7 | 80.0 |
| --- | ------------------------- | --- | --- | --- | ---- | ---- | ---- | ---- | --- | ---- | ---- | ---- |
|     | GENRE(DeCaoetal.,2021)    |     |     |     | 93.3 | 94.3 | 89.9 | 90.1 |     | 77.3 | 87.4 | 88.8 |
|     | ReFinEDw/opretraining     |     |     |     | 88.2 | 92.3 | 86.8 | 90.6 |     | 75.1 | 74.5 | 84.6 |
|     | ReFinED(Ayoolaetal.,2022) |     |     |     | 93.9 | 94.1 | 90.8 | 90.8 |     | 79.4 | 87.4 | 89.4 |
Few-shotunconstrained
|     | LLaMA-7B  |     |     |     | 42.0 | 44.6 | 30.2 | 43.8 |     | 35.8 | 27.7 | 37.4 |
| --- | --------- | --- | --- | --- | ---- | ---- | ---- | ---- | --- | ---- | ---- | ---- |
|     | LLaMA-13B |     |     |     | 48.1 | 50.2 | 36.2 | 47.5 |     | 40.7 | 37.2 | 43.3 |
|     | LLaMA-33B |     |     |     | 62.6 | 63.0 | 42.9 | 56.3 |     | 48.1 | 51.4 | 54.1 |
Few-shotconstrained(IIG)
|     | LLaMA-7B  |     |     |     | 56.3 | 57.3 | 61.6 | 54.6 |     | 50.5 | 47.0 | 54.5 |
| --- | --------- | --- | --- | --- | ---- | ---- | ---- | ---- | --- | ---- | ---- | ---- |
|     | LLaMA-13B |     |     |     | 51.8 | 57.3 | 53.3 | 50.8 |     | 48.2 | 39.7 | 50.6 |
|     | LLaMA-33B |     |     |     | 69.8 | 73.3 | 74.9 | 71.7 |     | 61.6 | 57.6 | 68.2 |
Few-shotconstrained(IDG)
|     | LLaMA-7B  |     |     |     | 73.4 | 87.6 | 83.2 | 82.9 |     | 69.4 | 67.1 | 77.2 |
| --- | --------- | --- | --- | --- | ---- | ---- | ---- | ---- | --- | ---- | ---- | ---- |
|     | LLaMA-13B |     |     |     | 75.8 | 86.6 | 82.4 | 84.2 |     | 68.1 | 68.1 | 77.5 |
|     | LLaMA-33B |     |     |     | 81.0 | 88.2 | 86.2 | 85.4 |     | 70.7 | 70.5 | 80.3 |
Table2: Mainresultsforentitydisambiguation(4shots),intermsofmicro-accuracy. Widthof90%confidence
intervalsisbetween0.1and0.3forallresults. Bestresultsinbold. IIGstandsfor“input-independentgrammar”,
IDGfor“input-dependentgrammar”.
2022),thisresulthighlightsthepotentialforLLMs 4.3 Constituencyparsing(CP)
toexceloncIEwithoutfinetuning.
|     |     |     |     |     |     |     | Results | for CP | are reported |     | in Table | 3. In con- |
| --- | --- | --- | --- | --- | --- | --- | ------- | ------ | ------------ | --- | -------- | ---------- |
trasttotheprevioustwotasks,theperformanceof
|     |     |     |     |     |     |     | LLMs—with | or  | without | GCD—on |     | constituency |
| --- | --- | --- | --- | --- | --- | --- | --------- | --- | ------- | ------ | --- | ------------ |
4.2 Entitydisambiguation(ED)
parsingismuchworsewhencomparedtobespoke
|     |     |     |     |     |     |     | methods. | This | is not | surprising, | as  | constituency |
| --- | --- | --- | --- | --- | --- | --- | -------- | ---- | ------ | ----------- | --- | ------------ |
ResultsforEDarereportedinTable2. Whereasun- parsingrequiressyntacticunderstandingofthein-
constrainedLLaMAmodelsperformpoorly,GCD
put,asopposedtotheothertwotasks,whichonly
(eitherinput-dependent[IDG]orinput-independent
|     |     |     |     |     |     |     | required | semantic | understanding. |     | Through | error |
| --- | --- | --- | --- | --- | --- | --- | -------- | -------- | -------------- | --- | ------- | ----- |
[IIG]) significantly improves the performance of inspection,wefoundthat,althoughtheLLMsare
LLaMA.Althoughthereisstillagapwithrespect abletogenerateseeminglyreasonableoutput,their
| to the  | state-of-the-art |                     | model, | GENRE | (De       | Cao |         |           |               |     |            |          |
| ------- | ---------------- | ------------------- | ------ | ----- | --------- | --- | ------- | --------- | ------------- | --- | ---------- | -------- |
|         |                  |                     |        |       |           |     | outputs | are often | syntactically |     | incorrect. | (For ex- |
| et al., | 2021),           | grammar-constrained |        |       | LLaMA-33B |     |         |           |               |     |            |          |
amples,seeAppendixI.)
performsbetterthanaversionofGENREtrained
Whileoverall,LLaMAmodelsperformpoorly
| only | on the | AIDA | dataset | (without | pretraining |     |     |     |     |     |     |     |
| ---- | ------ | ---- | ------- | -------- | ----------- | --- | --- | --- | --- | --- | --- | --- |
onCP,theGCD-poweredLLaMAmodelsstillsig-
| on Wikipedia). |     | Considering |     | that | many domain- |     |            |            |     |                   |     |       |
| -------------- | --- | ----------- | --- | ---- | ------------ | --- | ---------- | ---------- | --- | ----------------- | --- | ----- |
|                |     |             |     |      |              |     | nificantly | outperform |     | the unconstrained |     | LLaMA |
specificinformationextractiontaskshavelimited
|     |     |     |     |     |     |     | models. | Importantly, |     | with | an input-dependent |     |
| --- | --- | --- | --- | --- | --- | --- | ------- | ------------ | --- | ---- | ------------------ | --- |
dataavailable(Dunnetal.,2022),theconstrained
grammar,GCDguaranteesthatthegeneratedout-
| LLaMA                 | models | can | thus                | be a | good choice | for |             |                                  |     |     |     |     |
| --------------------- | ------ | --- | ------------------- | ---- | ----------- | --- | ----------- | -------------------------------- | --- | --- | --- | --- |
|                       |        |     |                     |      |             |     | putisavalid | constituencyparsetree,whichisnot |     |     |     |     |
| low-resourcesettings. |        |     | AmongtheGCD-powered |      |             |     |             |                                  |     |     |     |     |
thecasewithaninput-independentgrammar.
| LLaMA | models, | we  | observe | that | IDG performs |     |     |     |     |     |     |     |
| ----- | ------- | --- | ------- | ---- | ------------ | --- | --- | --- | --- | --- | --- | --- |
betterthanIIG,highlightingthebenefitsofusing Inconclusion,GCDsubstantiallyimprovesthe
aninput-dependentgrammar. Thelatterallowsthe performance of LLMs on constituency parsing,
modeltoleverageaninput-specificcandidateset, but performance still falls short of the F1-scores
whereas an input-independent grammar can only achievedbysupervisedmethods(95%andabove).
usetheentireknowledgebaseasthecandidateset. We do not, however, rule out the possibility that
We believe this flexibility is crucial for GCD to GCDmightproducebetterresultsoncetheunder-
achievegoodperformanceonvarioustasks. lyingLLMsbecomemorepowerful.
10938

|     | Method |     |     |     | F1 Validity |     | Model/task |     |     |     |     | Latency |     |
| --- | ------ | --- | --- | --- | ----------- | --- | ---------- | --- | --- | --- | --- | ------- | --- |
Bespokemethods
|     |                      |     |     |      |       |      | UnconstrainedLLaMA-7B  |     |     |     |     |     | 54  |
| --- | -------------------- | --- | --- | ---- | ----- | ---- | ---------------------- | --- | --- | --- | --- | --- | --- |
|     | Vinyalsetal.(2015a)  |     |     | 92.1 |       | 98.5 |                        |     |     |     |     |     |     |
|     | Dyeretal.(2016)      |     |     | 93.3 | 100.0 |      | UnconstrainedLLaMA-33B |     |     |     |     |     | 87  |
|     | KitaevandKlein(2018) |     |     | 95.6 | 100.0 |      |                        |     |     |     |     |     |     |
|     |                      |     |     |      |       |      | UnconstrainedLLaMA-65B |     |     |     |     |     | 136 |
|     | Zhangetal.(2020)     |     |     | 95.7 | 100.0 |      |                        |     |     |     |     |     |     |
|     |                      |     |     |      |       |      | GCDoverhead:           |     |     | cIE |     |     | 69  |
Few-shotunconstrained
|     |           |     |     |      |     |      | GCDoverhead: |                                          |     | ED  |     |     | 1   |
| --- | --------- | --- | --- | ---- | --- | ---- | ------------ | ---------------------------------------- | --- | --- | --- | --- | --- |
|     | LLaMA-7B  |     |     | 28.1 |     | 54.3 |              |                                          |     |     |     |     |     |
|     | LLaMA-13B |     |     | 42.8 |     | 69.4 | GCDoverhead: |                                          |     | CP  |     |     | 4   |
|     | LLaMA-33B |     |     | 42.9 |     | 64.2 |              |                                          |     |     |     |     |     |
|     |           |     |     |      |     |      | Table4:      | Per-tokendecodinglatency(inmilliseconds) |     |     |     |     |     |
Few-shotconstrained(IIG) forunconstraineddecoding(top3rows,measuredon
|     | LLaMA-7B |     |     | 34.7 |     | 65.9 |     |     |     |     |     |     |     |
| --- | -------- | --- | --- | ---- | --- | ---- | --- | --- | --- | --- | --- | --- | --- |
LLaMA-13B 45.4 80.3 A100 GPU), compared to overhead due to grammar-
LLaMA-33B 47.1 72.3 constraineddecoding(bottom3rows,measuredoncon-
sumerCPU).
Few-shotconstrained(IDG)
|     | LLaMA-7B |     |     | 45.8 | 100.0 |     |     |     |     |     |     |     |     |
| --- | -------- | --- | --- | ---- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
putofneuralmachinetranslationmodelsisusually
|     | LLaMA-13B |     |     | 53.4 | 100.0 |     |                |     |     |     |     |     |     |
| --- | --------- | --- | --- | ---- | ----- | --- | -------------- | --- | --- | --- | --- | --- | --- |
|     | LLaMA-33B |     |     | 54.6 | 100.0 |     | anemptystring. |     |     |     |     |     |     |
Table 3: Main results for constituency parsing We hypothesize that the empty-string issue is
(8 shots), in terms of bracketing F1-score and parse- causedbyalikelihoodmisalignmentbetweenthe
| treevalidity. |     | Forfew-shot-promptedLLaMAmodels, |           |     |                   |     |                             |            |     |            |     |             |        |
| ------------- | --- | -------------------------------- | --------- | --- | ----------------- | --- | --------------------------- | ---------- | --- | ---------- | --- | ----------- | ------ |
|               |     |                                  |           |     |                   |     | grammarandthelanguagemodel. |            |     |            |     | WeusethecIE |        |
| test setwas   |     | restrictedto                     | goldparse |     | trees shorterthan |     |                             |            |     |            |     |             |        |
|               |     |                                  |           |     |                   |     | task as                     | an example | to  | illustrate | the | issue.      | In the |
64tokens,asLLaMAmodelsperformpoorlyonlonger
caseofcIE,thefirstgeneratedtokenmusteitherbe
| sentences. | Forbespokemethods,entirePennTreebank |     |     |     |     |     |     |     |     |     |     |     |     |
| ---------- | ------------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
theleft-brackettoken“[”ortheend-of-sequence
| testsetwasused.                  |     | Widthof90%confidenceintervalsis |     |     |               |     |             |        |              |          |               |          |        |
| -------------------------------- | --- | ------------------------------- | --- | --- | ------------- | --- | ----------- | ------ | ------------ | -------- | ------------- | -------- | ------ |
|                                  |     |                                 |     |     |               |     | token “$”.  | The    | latter       | denotes  | the situation |          | where  |
| between4.0and6.0forallF1-scores. |     |                                 |     |     | Bestresultsin |     |             |        |              |          |               |          |        |
| bold.                            |     |                                 |     |     |               |     | no triplets | can    | be extracted |          | from the      | input.   | With   |
|                                  |     |                                 |     |     |               |     | a beam      | size k | 2,           | both “[” | and           | “$” will | be in- |
≥
4.4 Latency cluded in the beam at the first step. Assume that
|                                 |     |         |         |     |            |       | thelikelihoodof“[”is |     |         | pandthelikelihoodof“$” |        |               |     |
| ------------------------------- | --- | ------- | ------- | --- | ---------- | ----- | -------------------- | --- | ------- | ---------------------- | ------ | ------------- | --- |
| Incremental                     |     | parsing | imposes | an  | additional | over- |                      |     |         |                        |        |               |     |
|                                 |     |         |         |     |            |       | is q. Since          | “$” | denotes | the                    | end of | the sequence, |     |
| headontopofpurevanilladecoding. |     |         |         |     | Toquantify |       |                      |     |         |                        |        |               |     |
thisgenerationisconsideredasacompletegenera-
| this | overhead, | we  | report | the latency | of  | pure de- |                              |     |     |     |                 |     |     |
| ---- | --------- | --- | ------ | ----------- | --- | -------- | ---------------------------- | --- | --- | --- | --------------- | --- | --- |
|      |           |     |        |             |     |          | tionwithatotallikelihoodofq. |     |     |     | Intheotherbeam, |     |     |
codingandcompareittotheaddedlatencydueto
thegenerationcontinueswith“[”astheprefix,but
| enforcing | grammar |     | constraints | in  | Table | 4. Note |                   |     |           |     |                |     |        |
| --------- | ------- | --- | ----------- | --- | ----- | ------- | ----------------- | --- | --------- | --- | -------------- | --- | ------ |
|           |         |     |             |     |       |         | as the generation |     | proceeds, |     | the likelihood |     | of the |
thatGCDoperatesentirelyontheCPU,notonthe
generationmaydecreasebelowq.
GPU,soGCDlatencyismeasuredonaconsumer
SinceLLMssuchasLLaMAaretrainedtomax-
CPU.AsshowninTable4,theaddedlatencyfrom
imizethelikelihoodofhumanlanguage,thestruc-
| GCD  | is negligible |               | for the | ED and     | CP tasks. | For  |               |     |            |         |     |              |        |
| ---- | ------------- | ------------- | ------- | ---------- | --------- | ---- | ------------- | --- | ---------- | ------- | --- | ------------ | ------ |
|      |               |               |         |            |           |      | ture imposed  |     | by the     | grammar | may | be unnatural |        |
| cIE, | GCD           | adds a modest |         | additional | latency   | com- |               |     |            |         |     |              |        |
|      |               |               |         |            |           |      | to the model, |     | especially | when    | the | model        | is not |
parableorinferiortothelatencyofpuredecoding,
|     |     |     |     |     |     |     | finetuned | on the | respective |     | task. | In the | extreme |
| --- | --- | --- | --- | --- | --- | --- | --------- | ------ | ---------- | --- | ----- | ------ | ------- |
dependingonthemodelused(cf.AppendixHfor
|     |     |     |     |     |     |     | case, the | correct | ground-truth |     | output | could | have |
| --- | --- | --- | --- | --- | --- | --- | --------- | ------- | ------------ | --- | ------ | ----- | ---- |
moredetails).
|     |     |     |     |     |     |     | a likelihood | lower | than | that | of the | empty | string |
| --- | --- | --- | --- | --- | --- | --- | ------------ | ----- | ---- | ---- | ------ | ----- | ------ |
“$”,resultinginthelatterbeingreturnedasthetop
5 LikelihoodmisalignmentinGCD generation. Thisintuitiongivesrisetoasimplefix:
penalizethemodelforgeneratingshortstrings,e.g.,
InthecIEandCPtasks,regardlessofmodelsize, byadjustingthelengthnormalizationparameterα
inthelength-adjustedsentencescoreS/mα,where
thetopgenerationisconsistentlyanemptystring
(technically,astring“$”consistingoftheend-of- Sistheunadjustedscoreforthesentenceandmis
sequence token only) and the second most likely thenumberoftokensinthesentence. Asshownin
Table5,thisfixindeedsolvestheproblem.
| generation |     | and subsequent |     | generations |     | are non- |     |     |     |     |     |     |     |
| ---------- | --- | -------------- | --- | ----------- | --- | -------- | --- | --- | --- | --- | --- | --- | --- |
empty output sequences. The issue is not unique Wealsoobservedthattheempty-stringissuecan
to a particular LLM, but emerges consistently. It be alleviated by using instruction-tuned models.
isalsosimilartoanobservationbyStahlbergand While,withoutapplyingtheaforementionedlength
Byrne(2019),whofoundthatthemostlikelyout- normalizationfix,LLaMA-13Balwaysoutputsthe
10939

Lengthnormalizationα 1.0 1.5 2.0 2.5 3.0 3.5 Neubig(2017)proposedagrammar-poweredneu-
Topgeneration=“$”? ✓ ✓ ✓ ral architecture for general-purpose code genera-
|     |     |     | ×   | × × |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
tion. Shinetal.(2021)proposedtousegrammar-
| Table 5: | Length normalization |     | mitigates | the empty- |             |          |          |         |            |
| -------- | -------------------- | --- | --------- | ---------- | ----------- | -------- | -------- | ------- | ---------- |
|          |                      |     |           |            | constraints | to solve | semantic | parsing | tasks with |
stringissue:largerαfavorslongersequencesandα=0
meansnoeffect(resultsforLLaMA-13B). GPT-3 and envisioned that a semantic parser can
bebuiltbycombiningalargelanguagemodelwith
empty string “$” as its top generation on the cIE acarefullydesignedgrammar. Royetal.(2022)re-
task, the instruction-tuned version (Vicuna-13B) leasedatoolkitforgrammar-constraineddecoding
|     |     |     |     |     | togeneratevalidmeaningrepresentations. |     |     |     | Finally, |
| --- | --- | --- | --- | --- | -------------------------------------- | --- | --- | --- | -------- |
outputsnon-emptyoutputasitstopgenerationonly
46%ofthetime. (ThesmallerVicuna-7B,however, Stengel-Eskin et al. (2023) tested the ability of
stillalwaysoutputs“$”asitstopgeneration.) LLMs to solve parsing task under ambiguity and
usedgrammarconstraintstoensurethegrammati-
| 6 Relatedwork                              |     |     |     |     | calityoftheoutput. |     |     |     |     |
| ------------------------------------------ | --- | --- | --- | --- | ------------------ | --- | --- | --- | --- |
| AutoregressivestructuredpredictioninNLP.It |     |     |     |     | 7 Conclusion       |     |     |     |     |
hasbecomepopulartouseautoregressivegenera-
Thisworkintroducesgrammar-constraineddecod-
tivemodelsforstructuredpredictiontasks,asthis
ing(GCD)forenhancingthefew-shotperformance
fitsthetrainingmodeandspecificstrengthsoflan-
|     |     |     |     |     | ofLLMsonchallengingstructuredNLPtasks. |     |     |     | We  |
| --- | --- | --- | --- | --- | -------------------------------------- | --- | --- | --- | --- |
guagemodels(Vinyalsetal.,2015b;Athiwaratkun
showedthatmanyNLPtaskscanbeformulatedas
| et al., 2020; | De Cao | et al., | 2021; Paolini | et al., |     |     |     |     |     |
| ------------- | ------ | ------- | ------------- | ------- | --- | --- | --- | --- | --- |
formalgrammars,andthatGCDcanenhancethe
| 2021). | For instance, | Vinyals | et al. (2015b) | mod- |                                |     |     |            |     |
| ------ | ------------- | ------- | -------------- | ---- | ------------------------------ | --- | --- | ---------- | --- |
|        |               |         |                |      | performanceofLLMsonthesetasks. |     |     | Withinput- |     |
eleddependencyparsingasasequencegeneration
dependentgrammars,wefurtherbroadenthescope
| problem | and leveraged | LSTMs | to tackle | it effec- |        |                |       |       |            |
| ------- | ------------- | ----- | --------- | --------- | ------ | -------------- | ----- | ----- | ---------- |
|         |               |       |           |           | of GCD | to accommodate | tasks | where | the set of |
tively. DeCaoetal.(2021)proposedautoregressive
validoutputstructuresisconstrainedbythegiven
| language | models to address |     | entity linking, | entity |     |     |     |     |     |
| -------- | ----------------- | --- | --------------- | ------ | --- | --- | --- | --- | --- |
input. Ourexperimentsindicatethat,whereasun-
disambiguation,anddocumentretrievaltasks.
|     |     |     |             |          | constrained | LLMs have | difficulty | tackling | tasks |
| --- | --- | --- | ----------- | -------- | ----------- | --------- | ---------- | -------- | ----- |
|     |     | For | tasks where | the out- |             |           |            |          |       |
Constrained decoding. requiringstructuredoutputs,GCDcansignificantly
putneedstosatisfycertainconstraints,constrained
|     |     |     |     |     | bolstertheperformanceofLLMsonsuchtasks. |     |     |     | We  |
| --- | --- | --- | --- | --- | --------------------------------------- | --- | --- | --- | --- |
decoding has been proposed to guide the genera- envisionGCDasaswiftandcost-efficientadapta-
tionprocesstoproducevalidoutputs. Forinstance, tionstrategy,allowingLLMstogeneratereliable
| Hokamp | and Liu (2017); | Hu  | et al. (2019); | Post |     |     |     |     |     |
| ------ | --------------- | --- | -------------- | ---- | --- | --- | --- | --- | --- |
structuredoutputswithoutthenecessityforcostly
andVilar(2018)proposedlexically-constrainedse- and cumbersome finetuning. Given the fast pace
quence decoding for generation tasks. Anderson of LLM evolution, we anticipate the usefulness
etal.(2017)extendedthebeamsearchalgorithm
|     |     |     |     |     | of GCD | for boosting | pretrained | LLMs | to further |
| --- | --- | --- | --- | --- | ------ | ------------ | ---------- | ---- | ---------- |
bypruningthesearchspacebasedonconstraints.
increaseovertime.
Scholaketal.(2021)leveragedanincrementalpars-
|     |     |     |     |     |                |          | We  | conclude | with con- |
| --- | --- | --- | --- | --- | -------------- | -------- | --- | -------- | --------- |
|     |     |     |     |     | Best practices | for GCD. |     |          |           |
ingtechniquetogenerateapproximatelyvalidSQL
siderationsregardingtheeffectiveuseofGCD.
queries. DeCaoetal.(2021)addressedentitydis-
ambiguationwithtrie-basedlexicalconstraintsat
|     |     |     |     |     | 1. GCD | is more effective |     | with larger | LLMs. |
| --- | --- | --- | --- | --- | ------ | ----------------- | --- | ----------- | ----- |
decodingtimetoforceoutputstobevalidentities.
Whenpossible,usethelargestavailableLLM.
| Josifoski | et al. (2022) | addressed | closed | informa- |     |     |     |     |     |
| --------- | ------------- | --------- | ------ | -------- | --- | --- | --- | --- | --- |
tionextractionbycombiningtrie-basedlexicalcon- 2. Grammarsshouldbeasrestrictiveaspossible.
Considerusinginput-dependentgrammars.
straintswithstate-basedconstraintstoforcetheout-
puttobevalidtripletsequences. Wangetal.(2023) 3. While GCD is broadly applicable to many
usedEarleyparser–basedconstraintstoforceout-
|     |     |     |     |     | tasks,itisnotasilverbullet. |     |     | Tasksthatrequire |     |
| --- | --- | --- | --- | --- | --------------------------- | --- | --- | ---------------- | --- |
putstolieinadomain-specificlanguage. syntacticunderstandingoftheinput(e.g.,con-
stituencyparsing)arelesssuitableforGCD.
| Grammar-constraineddecoding. |     |     | Deutschetal. |     |     |     |     |     |     |
| ---------------------------- | --- | --- | ------------ | --- | --- | --- | --- | --- | --- |
(2019) proposed a general framework for push- 4. Inthepresenceoftask-specifictrainingdata,
downautomata–basedconstraintsandapplieditto finetuningasmallmodelmaystillyieldbetter
parsing tasks, which is equivalent to CFG-based performance,atthecostofdecreasedconve-
constraints in terms of expressiveness. Yin and nience(cf.AppendixA).
10940

| Limitations   |           |      |           |          |         |       | BenAthiwaratkun,CiceroNogueiradosSantos,Jason |          |            |            |           |              |       |
| ------------- | --------- | ---- | --------- | -------- | ------- | ----- | --------------------------------------------- | -------- | ---------- | ---------- | --------- | ------------ | ----- |
|               |           |      |           |          |         |       | Krone,                                        | and Bing | Xiang.     | 2020.      | Augmented |              | natu- |
|               |           |      |           |          |         |       | ral language                                  | for      | generative |            | sequence  | labeling.    | In    |
| Compatibility |           | with | API-based |          | LLMs.   | GCD   |                                               |          |            |            |           |              |       |
|               |           |      |           |          |         |       | Proceedings                                   | of       | the 2020   | Conference |           | on Empirical |       |
| works by      | modifying |      | the       | decoding | process | of an |                                               |          |            |            |           |              |       |
MethodsinNaturalLanguageProcessing(EMNLP),
LLM.IftheLLMishostedinthecloud(asisthe pages 375–385, Online. Association for Computa-
| case for | OpenAI’s |     | GPT series) |     | and the | API does | tionalLinguistics. |     |     |     |     |     |     |
| -------- | -------- | --- | ----------- | --- | ------- | -------- | ------------------ | --- | --- | --- | --- | --- | --- |
notprovideusercontroloverthedecodingprocess,
|     |     |     |     |     |     |     | Tom Ayoola, | Shubhi | Tyagi, | Joseph | Fisher, | Christos |     |
| --- | --- | --- | --- | --- | --- | --- | ----------- | ------ | ------ | ------ | ------- | -------- | --- |
GCDcannotbeused. Christodoulopoulos,andAndreaPierleoni.2022. Re-
FinED:Anefficientzero-shot-capableapproachto
| Latency.   | Theintroductionofconstraintsintothe |     |           |          |     |           |                          |     |           |                        |     |         |        |
| ---------- | ----------------------------------- | --- | --------- | -------- | --- | --------- | ------------------------ | --- | --------- | ---------------------- | --- | ------- | ------ |
|            |                                     |     |           |          |     |           | end-to-endentitylinking. |     |           | InProceedingsofthe2022 |     |         |        |
| generation | process                             |     | increases | latency. |     | The extra |                          |     |           |                        |     |         |        |
|            |                                     |     |           |          |     |           | Conference               | of  | the North | American               |     | Chapter | of the |
overheadofGCDisintroducedbythecompletion AssociationforComputationalLinguistics: Human
|            |     |      |         |       |     |            | LanguageTechnologies: |     |     | IndustryTrack,pages209– |     |     |     |
| ---------- | --- | ---- | ------- | ----- | --- | ---------- | --------------------- | --- | --- | ----------------------- | --- | --- | --- |
| step where | the | next | allowed | token | is  | determined |                       |     |     |                         |     |     |     |
basedonthecurrentprefixandthegrammar. The 220,Hybrid: Seattle,Washington+Online.Associa-
tionforComputationalLinguistics.
speedofthecompletionstepdependsonthecom-
plexityofthegrammarandtheparsingalgorithm TomB.Brown,BenjaminMann,NickRyder,Melanie
|                   |     |            |     |         |     |             | Subbiah, | Jared | Kaplan, | Prafulla | Dhariwal, | Arvind |     |
| ----------------- | --- | ---------- | --- | ------- | --- | ----------- | -------- | ----- | ------- | -------- | --------- | ------ | --- |
| of the underlying |     | completion |     | engine. |     | In case the |          |       |         |          |           |        |     |
Neelakantan,PranavShyam,GirishSastry,Amanda
| grammar | is simple, |     | we do | not | observe | a signifi- |         |          |          |     |       |               |     |
| ------- | ---------- | --- | ----- | --- | ------- | ---------- | ------- | -------- | -------- | --- | ----- | ------------- | --- |
|         |            |     |       |     |         |            | Askell, | Sandhini | Agarwal, |     | Ariel | Herbert-Voss, |     |
cantincreaseinlatency(theoverheadisnegligible
|     |     |     |     |     |     |     | Gretchen | Krueger, | Tom | Henighan, |     | Rewon | Child, |
| --- | --- | --- | --- | --- | --- | --- | -------- | -------- | --- | --------- | --- | ----- | ------ |
comparedtothelatencyoftheLM).However,in Aditya Ramesh, Daniel M. Ziegler, Jeffrey Wu,
case the grammar contains a large number (e.g., ClemensWinter,ChristopherHesse,MarkChen,Eric
Sigler,MateuszLitwin,ScottGray,BenjaminChess,
millions)ofrules,suchasthegrammarforthecIE
|           |         |     |                 |     |         |      | Jack Clark,   | Christopher |                 | Berner, | Sam | McCandlish,   |     |
| --------- | ------- | --- | --------------- | --- | ------- | ---- | ------------- | ----------- | --------------- | ------- | --- | ------------- | --- |
| task, the | latency | of  | the incremental |     | parsing | step |               |             |                 |         |     |               |     |
|           |         |     |                 |     |         |      | Alec Radford, |             | Ilya Sutskever, |         | and | Dario Amodei. |     |
grows. (SeeresultsinTable4.)
2020. Languagemodelsarefew-shotlearners.
|     |     |     |     |     |     |     | Wei-Lin Chiang, |     | Zhuohan | Li, | Zi Lin, | Ying | Sheng, |
| --- | --- | --- | --- | --- | --- | --- | --------------- | --- | ------- | --- | ------- | ---- | ------ |
Acknowledgements
ZhanghaoWu,HaoZhang,LianminZheng,Siyuan
Zhuang,YonghaoZhuang,JosephE.Gonzalez,Ion
| We thank   | Viktor      | Kuncˇak |     | and Chris    | Wendler | for     |         |          |          |       |         |     |       |
| ---------- | ----------- | ------- | --- | ------------ | ------- | ------- | ------- | -------- | -------- | ----- | ------- | --- | ----- |
|            |             |         |     |              |         |         | Stoica, | and Eric | P. Xing. | 2023. | Vicuna: | An  | open- |
| insightful | discussions |         | and | suggestions, |         | as well |         |          |          |       |         |     |       |
sourcechatbotimpressinggpt-4with90%*chatgpt
astheGrammaticalFrameworkcommunity,espe-
quality.
ciallyInariListenmaa,foransweringourquestions.
NicolaDeCao,GautierIzacard,SebastianRiedel,and
| We also      | thank | Zheng | Zhou           | and | Yifei | Li for their |                    |     |                                |     |     |     |     |
| ------------ | ----- | ----- | -------------- | --- | ----- | ------------ | ------------------ | --- | ------------------------------ | --- | --- | --- | --- |
|              |       |       |                |     |       |              | FabioPetroni.2021. |     | Autoregressiveentityretrieval. |     |     |     |     |
| help setting | up    | the   | infrastructure |     | for   | the experi-  |                    |     |                                |     |     |     |     |
ments. West’s lab is partly supported by grants DanielDeutsch,ShyamUpadhyay,andDanRoth.2019.
Ageneral-purposealgorithmforconstrainedsequen-
fromSwissNationalScienceFoundation(200021_-
|          |       |      |         |     |        |           | tial inference. |     | In Proceedings |     | of the | 23rd Confer- |     |
| -------- | ----- | ---- | ------- | --- | ------ | --------- | --------------- | --- | -------------- | --- | ------ | ------------ | --- |
| 185043), | Swiss | Data | Science |     | Center | (P22_08), |                 |     |                |     |        |              |     |
enceonComputationalNaturalLanguageLearning
H2020(952215),MicrosoftSwissJointResearch
(CoNLL),pages482–492,HongKong,China.Asso-
Center, and Google, and by generous gifts from ciationforComputationalLinguistics.
Facebook,Google,andMicrosoft.
|     |     |     |     |     |     |     | Alexander | Dunn, | John | Dagdelen, | Nicholas | Walker, |     |
| --- | --- | --- | --- | --- | --- | --- | --------- | ----- | ---- | --------- | -------- | ------- | --- |
SanghoonLee,AndrewS.Rosen,GerbrandCeder,
|            |     |     |     |     |     |     | KristinPersson,andAnubhavJain.2022.            |     |     |     |     | Structured |     |
| ---------- | --- | --- | --- | --- | --- | --- | ---------------------------------------------- | --- | --- | --- | --- | ---------- | --- |
| References |     |     |     |     |     |     | informationextractionfromcomplexscientifictext |     |     |     |     |            |     |
withfine-tunedlargelanguagemodels.
PeterAnderson,BasuraFernando,MarkJohnson,and
StephenGould.2017. Guidedopenvocabularyim- Chris Dyer, Adhiguna Kuncoro, Miguel Ballesteros,
age captioning with constrained beam search. In andNoahA.Smith.2016. Recurrentneuralnetwork
| Proceedings |     | of the | 2017 | Conference | on  | Empirical |     |     |     |     |     |     |     |
| ----------- | --- | ------ | ---- | ---------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
grammars.
MethodsinNaturalLanguageProcessing,pages936–
945,Copenhagen,Denmark.AssociationforCompu-
EvgeniyGabrilovich,MichaelRinggaard,andAmarnag
tationalLinguistics. Subramanya.2013. Facc1: Freebaseannotationof
cluewebcorpora,version1(releasedate2013-06-26,
KrasimirAngelov.2009. Incrementalparsingwithpar- formatversion1,correctionlevel0).
| allelmultiplecontext-freegrammars. |     |     |     |     | InProceedings |     |     |     |     |     |     |     |     |
| ---------------------------------- | --- | --- | --- | --- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- |
ofthe12thConferenceoftheEuropeanChapterof Octavian-Eugen Ganea and Thomas Hofmann. 2017.
theACL(EACL2009),pages69–76,Athens,Greece. Deep joint entity disambiguation with local neural
| AssociationforComputationalLinguistics. |     |     |     |     |     |     | attention. |     |     |     |     |     |     |
| --------------------------------------- | --- | --- | --- | --- | --- | --- | ---------- | --- | --- | --- | --- | --- | --- |
10941

Zhaochen Guo and Denilson Barbosa. 2017. Robust NikitaKitaevandDanKlein.2018. Constituencypars-
namedentitydisambiguationwithrandomwalks. Se- ingwithaself-attentiveencoder.
manticWeb,9:1–21.
|     |     |     |     |     |     |     | PhongLeandIvanTitov.2018. |     |     | Improvingentitylink- |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------------- | --- | --- | -------------------- | --- | --- |
JohannesHoffart,MohamedAmirYosef,IlariaBordino, ingbymodelinglatentrelationsbetweenmentions.
| Hagen Fürstenau, |     | Manfred |     | Pinkal, | Marc | Spaniol, |                |     |        |             |         |        |
| ---------------- | --- | ------- | --- | ------- | ---- | -------- | -------------- | --- | ------ | ----------- | ------- | ------ |
|                  |     |         |     |         |      |          | In Proceedings |     | of the | 56th Annual | Meeting | of the |
BilyanaTaneva,StefanThater,andGerhardWeikum. AssociationforComputationalLinguistics(Volume
2011. Robust disambiguation of named entities in 1: LongPapers),pages1595–1604,Melbourne,Aus-
text. InProceedingsofthe2011ConferenceonEm- tralia.AssociationforComputationalLinguistics.
| pirical Methods |     | in Natural |     | Language | Processing, |     |     |     |     |     |     |     |
| --------------- | --- | ---------- | --- | -------- | ----------- | --- | --- | --- | --- | --- | --- | --- |
pages782–792,Edinburgh,Scotland,UK.Associa- Giovanni Paolini, Ben Athiwaratkun, Jason Krone,
tionforComputationalLinguistics.
|     |     |     |     |     |     |     | JIE MA, | Alessandro |     | Achille, Rishita | Anubhai, | Ci- |
| --- | --- | --- | --- | --- | --- | --- | ------- | ---------- | --- | ---------------- | -------- | --- |
ceroNogueiradosSantos,BingXiang,andStefano
| Chris Hokamp | and | Qun | Liu. | 2017. | Lexically | con- |              |     |                                      |     |     |     |
| ------------ | --- | --- | ---- | ----- | --------- | ---- | ------------ | --- | ------------------------------------ | --- | --- | --- |
|              |     |     |      |       |           |      | Soatto.2021. |     | Structuredpredictionastranslationbe- |     |     |     |
straineddecodingforsequencegenerationusinggrid
|              |     |                |     |        |      |        | tweenaugmentednaturallanguages. |     |     |     | InICLR2021. |     |
| ------------ | --- | -------------- | --- | ------ | ---- | ------ | ------------------------------- | --- | --- | --- | ----------- | --- |
| beam search. |     | In Proceedings |     | of the | 55th | Annual |                                 |     |     |     |             |     |
Meeting of the Association for Computational Lin- GabrielPoesia,OleksandrPolozov,VuLe,AshishTi-
guistics(Volume1: LongPapers),pages1535–1546, wari,GustavoSoares,ChristopherMeek,andSumit
Vancouver,Canada.AssociationforComputational
|     |     |     |     |     |     |     | Gulwani.2022. |     | Synchromesh: | Reliablecodegenera- |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------- | --- | ------------ | ------------------- | --- | --- |
Linguistics.
tionfrompre-trainedlanguagemodels.
| Edward J. | Hu, Yelong |     | Shen, Phillip |     | Wallis, | Zeyuan |           |           |        |       |                |      |
| --------- | ---------- | --- | ------------- | --- | ------- | ------ | --------- | --------- | ------ | ----- | -------------- | ---- |
|           |            |     |               |     |         |        | Matt Post | and David | Vilar. | 2018. | Fast lexically | con- |
Allen-Zhu,YuanzhiLi,SheanWang,LuWang,and
straineddecodingwithdynamicbeamallocationfor
WeizhuChen.2021. Lora: Low-rankadaptationof neural machine translation. In Proceedings of the
largelanguagemodels.
2018ConferenceoftheNorthAmericanChapterof
|     |     |     |     |     |     |     | theAssociationforComputationalLinguistics: |     |     |     |     | Hu- |
| --- | --- | --- | --- | --- | --- | --- | ------------------------------------------ | --- | --- | --- | --- | --- |
J.EdwardHu,HudaKhayrallah,RyanCulkin,Patrick
|              |       |          |      |           |              |     | man Language |       | Technologies, | Volume |          | 1 (Long Pa- |
| ------------ | ----- | -------- | ---- | --------- | ------------ | --- | ------------ | ----- | ------------- | ------ | -------- | ----------- |
| Xia, Tongfei |       | Chen,    | Matt | Post,     | and Benjamin |     |              |       |               |        |          |             |
|              |       |          |      |           |              |     | pers),       | pages | 1314–1324,    | New    | Orleans, | Louisiana.  |
| Van Durme.   | 2019. | Improved |      | lexically | constrained  |     |              |       |               |        |          |             |
AssociationforComputationalLinguistics.
decodingfortranslationandmonolingualrewriting.
InProceedingsofthe2019ConferenceoftheNorth
|     |     |     |     |     |     |     | Alec Radford, |     | Jeff Wu, | Rewon Child, |     | David Luan, |
| --- | --- | --- | --- | --- | --- | --- | ------------- | --- | -------- | ------------ | --- | ----------- |
AmericanChapteroftheAssociationforComputa-
|                    |     |                            |     |     |     |     | DarioAmodei,andIlyaSutskever.2019. |     |     |     |     | Language |
| ------------------ | --- | -------------------------- | --- | --- | --- | --- | ---------------------------------- | --- | --- | --- | --- | -------- |
| tionalLinguistics: |     | HumanLanguageTechnologies, |     |     |     |     |                                    |     |     |     |     |          |
modelsareunsupervisedmultitasklearners.
Volume1(LongandShortPapers),pages839–850,
Minneapolis,Minnesota.AssociationforComputa-
ColinRaffel,NoamShazeer,AdamRoberts,Katherine
tionalLinguistics.
Lee,SharanNarang,MichaelMatena,YanqiZhou,
|            |        |       |             |     |          |       | WeiLi,andPeterJ.Liu.2019. |     |     | Exploringthelimits |     |     |
| ---------- | ------ | ----- | ----------- | --- | -------- | ----- | ------------------------- | --- | --- | ------------------ | --- | --- |
| Pere-Lluís | Huguet | Cabot | and Roberto |     | Navigli. | 2021. |                           |     |     |                    |     |     |
REBEL:Relationextractionbyend-to-endlanguage oftransferlearningwithaunifiedtext-to-texttrans-
|     | InFindingsoftheAssociationforCom- |     |     |     |     |     | former. | CoRR,abs/1910.10683. |     |     |     |     |
| --- | --------------------------------- | --- | --- | --- | --- | --- | ------- | -------------------- | --- | --- | --- | --- |
generation.
| putationalLinguistics: |     |     | EMNLP2021,pages2370– |     |     |     |                  |     |                       |     |     |          |
| ---------------------- | --- | --- | -------------------- | --- | --- | --- | ---------------- | --- | --------------------- | --- | --- | -------- |
|                        |     |     |                      |     |     |     | AarneRanta.2019. |     | Grammaticalframework: |     |     | aninter- |
2381,PuntaCana,DominicanRepublic.Association
|     |     |     |     |     |     |     | lingualgrammarformalism. |     |     | InProceedingsofthe |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------------ | --- | --- | ------------------ | --- | --- |
forComputationalLinguistics.
14thInternationalConferenceonFinite-StateMeth-
|                |            |     |         |         |     |         | ods and | Natural | Language | Processing, |     | pages 1–2, |
| -------------- | ---------- | --- | ------- | ------- | --- | ------- | ------- | ------- | -------- | ----------- | --- | ---------- |
| Bernal Jimenez | Gutierrez, |     | Nikolas | McNeal, |     | Clayton |         |         |          |             |     |            |
Washington, You Chen, Lang Li, Huan Sun, and Dresden,Germany.AssociationforComputational
| YuSu.2022.                              | ThinkingaboutGPT-3in-contextlearn- |     |     |                 |     |       | Linguistics. |     |          |         |       |         |
| --------------------------------------- | ---------------------------------- | --- | --- | --------------- | --- | ----- | ------------ | --- | -------- | ------- | ----- | ------- |
| ingforbiomedicalIE?thinkagain.          |                                    |     |     | InFindingsofthe |     |       |              |     |          |         |       |         |
|                                         |                                    |     |     |                 |     |       | Subhro Roy,  | Sam | Thomson, | Tongfei | Chen, | Richard |
| AssociationforComputationalLinguistics: |                                    |     |     |                 |     | EMNLP |              |     |          |         |       |         |
Shin,AdamPauls,JasonEisner,andBenjaminVan
| 2022, pages | 4497–4512, |     | Abu | Dhabi, | United | Arab |             |     |             |                     |     |     |
| ----------- | ---------- | --- | --- | ------ | ------ | ---- | ----------- | --- | ----------- | ------------------- | --- | --- |
|             |            |     |     |        |        |      | Durme.2022. |     | Benchclamp: | Abenchmarkforevalu- |     |     |
Emirates.AssociationforComputationalLinguistics.
atinglanguagemodelsonsemanticparsing.
| Martin Josifoski, |     | Nicola | De Cao, | Maxime |     | Peyrard, |     |     |     |     |     |     |
| ----------------- | --- | ------ | ------- | ------ | --- | -------- | --- | --- | --- | --- | --- | --- |
FabioPetroni,andRobertWest.2022. GenIE:Gen- Timo Schick and Hinrich Schütze. 2021. Exploiting
erative information extraction. In Proceedings of cloze-questionsforfew-shottextclassificationand
the2022ConferenceoftheNorthAmericanChap- natural language inference. In Proceedings of the
16thConferenceoftheEuropeanChapteroftheAsso-
teroftheAssociationforComputationalLinguistics:
|     |     |     |     |     |     |     | ciationforComputationalLinguistics: |     |     |     | MainVolume, |     |
| --- | --- | --- | --- | --- | --- | --- | ----------------------------------- | --- | --- | --- | ----------- | --- |
HumanLanguageTechnologies,pages4626–4643,
Seattle,UnitedStates.AssociationforComputational pages 255–269, Online. Association for Computa-
| Linguistics. |     |     |     |     |     |     | tionalLinguistics. |     |     |     |     |     |
| ------------ | --- | --- | --- | --- | --- | --- | ------------------ | --- | --- | --- | --- | --- |
MartinJosifoski,MarijaSakota,MaximePeyrard,and TorstenScholak,NathanSchucher,andDzmitryBah-
RobertWest.2023. Exploitingasymmetryforsyn- danau. 2021. PICARD: Parsing incrementally for
thetic training data generation: SynthIE and the constrainedauto-regressivedecodingfromlanguage
case of information extraction. arXiv preprint models. InProceedingsofthe2021Conferenceon
arXiv:2303.04132. EmpiricalMethodsinNaturalLanguageProcessing,
10942

pages9895–9901,OnlineandPuntaCana,Domini- DennyVrandecˇic´.2012. Wikidata: Anewplatformfor
can Republic. Association for Computational Lin- collaborativedatacollection. InProceedingsofthe
guistics. 21stInternationalConferenceonWorldWideWeb,
WWW’12Companion,pages1063–1064,NewYork,
HiroyukiSeki,TakashiMatsumura,MamoruFujii,and NY,USA.AssociationforComputingMachinery.
TadaoKasami.1991. Onmultiplecontext-freegram-
mars. TheoreticalComputerScience,88(2):191–229. BailinWang,ZiWang,XuezhiWang,YuanCao,RifA.
Saurous,andYoonKim.2023. Grammarprompting
Satoshi Sekine and Michael Collins. 2008. Evalb: fordomain-specificlanguagegenerationwithlarge
Bracketscoringprogram. languagemodels.
Rico Sennrich, Barry Haddow, and Alexandra Birch. LedellWu,FabioPetroni,MartinJosifoski,Sebastian
2016. Neuralmachinetranslationofrarewordswith Riedel,andLukeZettlemoyer.2020. Scalablezero-
subword units. In Proceedings of the 54th Annual shot entity linking with dense entity retrieval. In
Meeting of the Association for Computational Lin- Proceedings of the 2020 Conference on Empirical
guistics(Volume1: LongPapers),pages1715–1725, MethodsinNaturalLanguageProcessing(EMNLP),
Berlin,Germany.AssociationforComputationalLin- pages6397–6407,Online.AssociationforComputa-
guistics. tionalLinguistics.
RichardShin,ChristopherLin,SamThomson,Charles PengchengYinandGrahamNeubig.2017. Asyntactic
Chen,SubhroRoy,EmmanouilAntoniosPlatanios, neural model for general-purpose code generation.
AdamPauls,DanKlein,JasonEisner,andBenjamin In Proceedings of the 55th Annual Meeting of the
Van Durme. 2021. Constrained language models AssociationforComputationalLinguistics(Volume
yieldfew-shotsemanticparsers. InProceedingsof 1: LongPapers),pages440–450,Vancouver,Canada.
the2021ConferenceonEmpiricalMethodsinNatu- AssociationforComputationalLinguistics.
ralLanguageProcessing,pages7699–7715,Online
YuZhang,HouquanZhou,andZhenghuaLi.2020. Fast
andPuntaCana,DominicanRepublic.Association
and accurate neural CRF constituency parsing. In
forComputationalLinguistics.
ProceedingsoftheTwenty-NinthInternationalJoint
FelixStahlbergandBillByrne.2019. OnNMTsearch Conference on Artificial Intelligence. International
errors and model errors: Cat got your tongue? In JointConferencesonArtificialIntelligenceOrgani-
Proceedings of the 2019 Conference on Empirical zation.
Methods in Natural Language Processing and the
9thInternationalJointConferenceonNaturalLan-
guageProcessing(EMNLP-IJCNLP),pages3356–
3362,HongKong,China.AssociationforComputa-
tionalLinguistics.
EliasStengel-Eskin,KyleRawlins,andBenjaminVan
Durme.2023. Zeroandfew-shotsemanticparsing
withambiguousinputs.
HugoTouvron,ThibautLavril,GautierIzacard,Xavier
Martinet,Marie-AnneLachaux,TimothéeLacroix,
BaptisteRozière,NamanGoyal,EricHambro,Faisal
Azhar,AurelienRodriguez,ArmandJoulin,Edouard
Grave,andGuillaumeLample.2023. Llama: Open
andefficientfoundationlanguagemodels.
RoyTrombleandJasonEisner.2006. Afastfinite-state
relaxation method for enforcing global constraints
on sequence decoding. In Proceedings of the Hu-
manLanguageTechnologyConferenceoftheNAACL,
Main Conference, pages 423–430, New York City,
USA.AssociationforComputationalLinguistics.
OriolVinyals,LukaszKaiser,TerryKoo,SlavPetrov,
IlyaSutskever,andGeoffreyHinton.2015a. Gram-
marasaforeignlanguage.
OriolVinyals,ŁukaszKaiser,TerryKoo,SlavPetrov,
IlyaSutskever,andGeoffreyHinton.2015b. Gram-
mar as a foreign language. In Advances in Neural
InformationProcessingSystems,volume28.Curran
Associates,Inc.
10943

A Fine-tuningvs. GCD Expensive, Delicious, Boring : Quality ;
|     |     |     |     |     |     |     | Listing1: | TheabstractsyntaxoftheFoodgrammar. |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --------- | ---------------------------------- | --- | --- | --- | --- | --- | --- |
Itisworthconsideringwhethertopreferfine-tuning
| or GCD | to adapt | LLMs |     | to structured | prediction |     |     |     |     |     |     |     |     |     |
| ------ | -------- | ---- | --- | ------------- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
tasks. Fine-tuningcanbeappliedtoeitherasmall B.1 AbstractSyntaxvs. ConcreteSyntax
model,suchasT5(Raffeletal.,2019),ordirectly
|     |     |     |     |     |     |     | Constrained |     | decoding | works | by  | pruning | the | set |
| --- | --- | --- | --- | --- | --- | --- | ----------- | --- | -------- | ----- | --- | ------- | --- | --- |
to a large model, like LLaMA (Touvron et al., of allowed tokens-id at each decoding step. This
2023). Therearethreecrucialfactorstotakeinto requires that both the grammar and the comple-
account:
|     |     |     |     |     |     |     | tion engine |     | work at | the token-id |     | level. | Since | the |
| --- | --- | --- | --- | --- | --- | --- | ----------- | --- | ------- | ------------ | --- | ------ | ----- | --- |
tokenizationschemeofLMsareusuallydifferent
1. availabilityoftrainingdata,
fromeachother,thegrammarbecomesdependent
2. computationalcostoffine-tuning,and
onthetokenizationschemeoftheLM.Thisbrings
3. performanceimprovement.
|     |     |     |     |     |     |     | two challenges: |     | (1)     | the grammar   |     | needs    | to be | re- |
| --- | --- | --- | --- | --- | --- | --- | --------------- | --- | ------- | ------------- | --- | -------- | ----- | --- |
|     |     |     |     |     |     |     | defined         | for | each LM | (tokenization |     | scheme), |       | and |
Constraineddecodingeliminatestheneedfortrain-
|     |     |     |     |     |     |     | (2) the | debugging |     | of the | grammar | is difficult |     | be- |
| --- | --- | --- | --- | --- | --- | --- | ------- | --------- | --- | ------ | ------- | ------------ | --- | --- |
ingdataandincursonlythecomputationalcostof
causethegrammarisdefinedatthetoken-idlevel.
runningtheLM,withsmalloverheadcomingfrom
Weproposetodecouplethegrammarfromthetok-
| theincrementalparser. |     |     | Fine-tuningasmallmodel |     |     |     |     |     |     |     |     |     |     |     |
| --------------------- | --- | --- | ---------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
enizationschemeoftheLMbydefininganabstract
isaffordableandcurrentlyrepresentsthestate-of-
|         |        |          |     |          |            |      | grammarandacoupleofconcretegrammars. |     |     |     |     |     |     | The |
| ------- | ------ | -------- | --- | -------- | ---------- | ---- | ------------------------------------ | --- | --- | --- | --- | --- | --- | --- |
| the-art | (SOTA) | approach |     | for most | structured | pre- |                                      |     |     |     |     |     |     |     |
abstractgrammarisdefinedatthetextlevel,which
| diction | tasks | when | training | data | is available | (De |     |     |     |     |     |     |     |     |
| ------- | ----- | ---- | -------- | ---- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ishuman-readableandindependentofthetokeniza-
| Cao et   | al., 2021; | Jimenez      |     | Gutierrez     | et     | al., 2022). |             |     |        |     |              |     |          |     |
| -------- | ---------- | ------------ | --- | ------------- | ------ | ----------- | ----------- | --- | ------ | --- | ------------ | --- | -------- | --- |
|          |            |              |     |               |        |             | tion scheme |     | of the | LM. | The concrete |     | grammars |     |
| However, | it         | necessitates |     | a substantial | amount | of          |             |     |        |     |              |     |          |     |
aredefinedatthetoken-idlevel,whicharedepen-
| data. Although |       | fine-tuning |                | a   | large model | is ex-  |                              |     |              |     |        |                |     |     |
| -------------- | ----- | ----------- | -------------- | --- | ----------- | ------- | ---------------------------- | --- | ------------ | --- | ------ | -------------- | --- | --- |
|                |       |             |                |     |             |         | dent on                      | the | tokenization |     | scheme | of the         | LM  | and |
| pensive,       | it is | highly      | data-efficient |     | (Brown      | et al., |                              |     |              |     |        |                |     |     |
|                |       |             |                |     |             |         | workwiththecompletionengine. |     |              |     |        | Onceanabstract |     |     |
2020). However,recentadvancementsinefficient
|     |     |     |     |     |     |     | grammar | is  | defined, | the | concrete | grammars |     | can |
| --- | --- | --- | --- | --- | --- | --- | ------- | --- | -------- | --- | -------- | -------- | --- | --- |
fine-tuningoflargemodels(Huetal.,2021)have
beautomaticallytranslatedfromtheabstractgram-
| significantly         |     | reduced | the               | computational |     | cost and |      |         |         |        |         |     |           |     |
| --------------------- | --- | ------- | ----------------- | ------------- | --- | -------- | ---- | ------- | ------- | ------ | ------- | --- | --------- | --- |
|                       |     |         |                   |               |     |          | mar. | This is | similar | to the | process | of  | compiling |     |
| hardwarerequirements. |     |         | WeviewGCDasarapid |               |     |          |      |         |         |        |         |     |           |     |
ahigh-levelprogramminglanguagetoalow-level
andcost-effectiveadaptationstrategythatenables
|     |     |     |     |     |     |     | assemblylanguage. |     |     | Theseparationoftheabstract |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ----------------- | --- | --- | -------------------------- | --- | --- | --- | --- |
LMstoproducereliablestructuredoutputswithout
grammarandtheconcretegrammarisimplemented
theneedforfine-tuning.
inGF.Forexample,thepredicationrule
|     |     |     |     |     |     |     | Pred. | Comment |     | ::= Item | "is" | Quality |     |     |
| --- | --- | --- | --- | --- | --- | --- | ----- | ------- | --- | -------- | ---- | ------- | --- | --- |
B GrammaticalFramework
|                          |     |     |     |     |                |     |     |     | Listing2: | BNFNotation |     |     |     |     |
| ------------------------ | --- | --- | --- | --- | -------------- | --- | --- | --- | --------- | ----------- | --- | --- | --- | --- |
| GrammaticalFramework(GF) |     |     |     |     | isaprogramming |     |     |     |           |             |     |     |     |     |
languageformultilingualgrammarapplications. It nowbecomestworules:
| is a special-purpose |     |     | language | for | grammars, | like |     |      |        |     |         |     |         |     |
| -------------------- | --- | --- | -------- | --- | --------- | ---- | --- | ---- | ------ | --- | ------- | --- | ------- | --- |
|                      |     |     |          |     |           |      | fun | Pred | : Item | ->  | Quality | ->  | Comment | ;   |
YACC, Bison, Happy, BNFC, but not restricted lin Pred item quality = item ++
|                         |           |     |      |                     |       |        |           |     | "is"                         | ++ quality |     | ;   |     |     |
| ----------------------- | --------- | --- | ---- | ------------------- | ----- | ------ | --------- | --- | ---------------------------- | ---------- | --- | --- | --- | --- |
| toprogramminglanguages. |           |     |      | Itisafunctionalpro- |       |        |           |     |                              |            |     |     |     |     |
| gramming                | language, |     | like | Haskell,            | Lisp, | OCaml, |           |     |                              |            |     |     |     |     |
|                         |           |     |      |                     |       |        | Listing3: |     | GrammaticalFrameworkNotation |            |     |     |     |     |
SML,Scheme,butspecializedtogrammarwriting.
|              |     |               |     |     |              |     | All        | that matters |        | in a linearization |     |        | rule is   | that |
| ------------ | --- | ------------- | --- | --- | ------------ | --- | ---------- | ------------ | ------ | ------------------ | --- | ------ | --------- | ---- |
| For example, |     | the following |     | is  | a GF grammar | to  |            |              |        |                    |     |        |           |      |
|              |     |               |     |     |              |     | it defines | a            | string | as a function      |     | of the | variables |      |
generatesimpleEnglishsentencesaboutfood:
|          |      |     |     |     |     |     | thatitdependson. |     |     | AGFgrammarconsistsoftwo |     |     |     |     |
| -------- | ---- | --- | --- | --- | --- | --- | ---------------- | --- | --- | ----------------------- | --- | --- | --- | --- |
| abstract | Food | =   | {   |     |     |     |                  |     |     |                         |     |     |     |     |
parts: abstractsyntaxandconcretesyntax.Below
| flags   | startcat |        | = Comment |      | ;         |     |                                            |     |     |     |     |     |     |     |
| ------- | -------- | ------ | --------- | ---- | --------- | --- | ------------------------------------------ | --- | --- | --- | --- | --- | --- | --- |
| cat     |          |        |           |      |           |     | istheconcretesyntaxoftheaforementionedFood |     |     |     |     |     |     |     |
| Comment |          | ; Item | ;         | Kind | ; Quality | ;   |                                            |     |     |     |     |     |     |     |
grammar:
fun
Pred : Item -> Quality -> Comment ; concrete FoodEng of Food = {
| This, | That | :   | Kind | -> Item | ;   |     | lincat |     |     |     |     |     |     |     |
| ----- | ---- | --- | ---- | ------- | --- | --- | ------ | --- | --- | --- | --- | --- | --- | --- |
Mod : Quality -> Kind -> Kind ; Comment, Item, Kind, Quality = Str ;
| Wine,  | Cheese, |         | Fish     | : Kind  | ;   |     | lin  |      |         |        |        |        |      |     |
| ------ | ------- | ------- | -------- | ------- | --- | --- | ---- | ---- | ------- | ------ | ------ | ------ | ---- | --- |
| Very   | :       | Quality | ->       | Quality | ;   |     | Pred | item | quality |        | = item | ++     | "is" |     |
| Fresh, |         | Warm,   | Italian, |         |     |     |      | ++   | quality | ;      |        |        |      |     |
| }      |         |         |          |         |     |     | This | kind | =       | "this" | ++     | kind ; |      |     |
10944

|     | That   | kind     | = "that" |     | ++ kind | ;   |        | C IETaskSettings                         |      |          |     |               |
| --- | ------ | -------- | -------- | --- | ------- | --- | ------ | ---------------------------------------- | ---- | -------- | --- | ------------- |
|     | Mod    | quality  | kind     | =   | quality | ++  | kind ; |                                          |      |          |     |               |
|     | Wine   | = "wine" |          | ;   |         |     |        | WeusethesameKBasin(Josifoskietal.,2023), |      |          |     |               |
|     | Cheese | =        | "cheese" | ;   |         |     |        |                                          |      |          |     |               |
|     |        |          |          |     |         |     |        | which contains                           | 2.7M | entities | and | 888 relations |
|     | Fish   | = "fish" |          | ;   |         |     |        |                                          |      |          |     |               |
(Vrandecˇic´,
Very quality = "very" ++ quality ; from the WikiData KG 2012). We
Fresh = "fresh" ; useSynthIE-textdataset(Josifoskietal.,2023),a
|     | Warm    | = "warm" |           | ;   |     |     |     |           |             |        |                |      |
| --- | ------- | -------- | --------- | --- | --- | --- | --- | --------- | ----------- | ------ | -------------- | ---- |
|     |         |          |           |     |     |     |     | synthetic | dataset for | the IE | task generated | from |
|     | Italian | =        | "Italian" |     | ;   |     |     |           |             |        |                |      |
Expensive = "expensive" ; prompting GPT3.5 model. This dataset consists
Delicious = "delicious" ; of 10K validation and 50K test samples. It was
|     | Boring | =   | "boring" | ;   |     |     |     |     |     |     |     |     |
| --- | ------ | --- | -------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
showntohaveabetterqualitythanthewidelyused
}
REBELdataset(HuguetCabotandNavigli,2021).
| Listing4: |     | TheconcretesyntaxoftheFoodgrammar. |     |     |     |     |     |     |     |     |     |     |
| --------- | --- | ---------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
D EDTaskSettings
AndalsotheconcretesyntaxoftheFoodgram-
marinItalian:
|          |     |         |     |      |     |     |     | DatasetPreprocessing. |            | Typically,solvingtheED |     |          |
| -------- | --- | ------- | --- | ---- | --- | --- | --- | --------------------- | ---------- | ---------------------- | --- | -------- |
| concrete |     | FoodIta | of  | Food | = { |     |     |                       |            |                        |     |          |
|          |     |         |     |      |     |     |     | task requires         | contextual | information.           |     | However, |
lincat
throughourobservations,wehavenoticedthatthe
|     | Comment, |            | Item,      | Kind, | Quality |        | = Str | ;                                       |                |         |           |                |
| --- | -------- | ---------- | ---------- | ----- | ------- | ------ | ----- | --------------------------------------- | -------------- | ------- | --------- | -------------- |
|     | lin      |            |            |       |         |        |       | performanceofLanguageModels(LMs)tendsto |                |         |           |                |
|     | Pred     | item       | quality    | =     | item    | ++ "e" |       |                                         |                |         |           |                |
|     |          |            |            |       |         |        |       | degrade                                 | when exposed   | to long | contexts. | To miti-       |
|     |          | ++ quality |            | ;     |         |        |       |                                         |                |         |           |                |
|     |          |            |            |       |         |        |       | gate this                               | issue, we have | limited | the       | left and right |
|     | This     | kind       | = "questo" |       | ++      | kind   | ;     |                                         |                |         |           |                |
That kind = "quel" ++ kind ; contextsurroundingthementiontoonly10tokens
|     | Mod | quality | kind | =   | kind | ++ quality | ;   |     |     |     |     |     |
| --- | --- | ------- | ---- | --- | ---- | ---------- | --- | --- | --- | --- | --- | --- |
each.
|     | Wine   | = "vino"  |             | ;       |     |         |     |                            |         |                |     |               |
| --- | ------ | --------- | ----------- | ------- | --- | ------- | --- | -------------------------- | ------- | -------------- | --- | ------------- |
|     | Cheese | =         | "formaggio" |         | ;   |         |     |                            |         |                |     |               |
|     |        |           |             |         |     |         |     | OutofKnowledgeBaseMention. |         |                |     | It’simportant |
|     | Fish   | = "pesce" |             | ;       |     |         |     |                            |         |                |     |               |
|     |        |           |             |         |     |         |     | to note that               | some of | these datasets |     | contain men-  |
|     | Very   | quality   | =           | "molto" | ++  | quality | ;   |                            |         |                |     |               |
Fresh = "fresco" ; tions that are not present in the knowledge base
|     | Warm | = "caldo" |     | ;   |     |     |     |     |     |     |     |     |
| --- | ---- | --------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
(YAGO_KB)Toensureconsistencyandaccuracy,
|     | Italian | =   | "italiano" |     | ;   |     |     |     |     |     |     |     |
| --- | ------- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
wefilteroutthesementions,exclusivelyutilizing
|     | Expensive |     | = "caro" |     | ;   |     |     |     |     |     |     |     |
| --- | --------- | --- | -------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Delicious = "delizioso" ; theonesthatareavailable. Wereportthenumberof
|     | Boring | =   | "noioso" | ;   |     |     |     |     |     |     |     |     |
| --- | ------ | --- | -------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
datapointswhosetargetentityisnotintheknowl-
}
|           |     |                                     |     |     |     |     |     | edgebase. | Thesedatapointsarefilteredoutinthe |     |     |     |
| --------- | --- | ----------------------------------- | --- | --- | --- | --- | --- | --------- | ---------------------------------- | --- | --- | --- |
| Listing5: |     | TheconcretesyntaxoftheFoodgrammarin |     |     |     |     |     |           |                                    |     |     |     |
experimentswithinput-independentgrammar.
Italian.
• AIDA-CoNLL:0outof4485
B.2 MultilingualGrammars
|     |     |     |     |     |     |     |     | • ACE2004: | 0outof257 |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ---------- | --------- | --- | --- | --- |
Amultilingualgrammarisasystemwithoneab-
stractsyntaxandanynumberofconcretesyntaxes.
• AQUAINT:4outof727
| While                   | GF  | was        | originally | designed               |      | for    | machine |            |              |     |     |     |
| ----------------------- | --- | ---------- | ---------- | ---------------------- | ---- | ------ | ------- | ---------- | ------------ | --- | --- | --- |
|                         |     |            |            |                        |      |        |         | • ClueWeb: | 12outof11154 |     |     |     |
| translation,            |     | it happens |            | to be                  | well | suited | to han- |            |              |     |     |     |
| dlemulti-tokenizations. |     |            |            | Differentlargelanguage |      |        |         |            |              |     |     |     |
• MSNBC:0outof656
| models        | have | different                     |                 | tokenizers. |     | For   | the same |              |             |     |     |     |
| ------------- | ---- | ----------------------------- | --------------- | ----------- | --- | ----- | -------- | ------------ | ----------- | --- | --- | --- |
| sentence,     |      | their                         | representations |             | in  | token | id space |              |             |     |     |     |
|               |      |                               |                 |             |     |       |          | • Wikipedia: | 23outof6821 |     |     |     |
| aredifferent. |      | Thisphenomenonisverysimilarto |                 |             |     |       |          |              |             |     |     |     |
themultilingualgrammarscenario,wherethesame Intheexperimentswithinput-dependentgram-
abstractsyntaxtreecanbelinearizedintodifferent mar,wealsofilteroutthedatapointswhosecandi-
| languagesasshowninintheFoodgrammar. |     |     |     |     |     |     |     | datesetisempty. |     |     |     |     |
| ----------------------------------- | --- | --- | --- | --- | --- | --- | --- | --------------- | --- | --- | --- | --- |
B.3 Expressivity
• AIDA-CoNLL:0outof4485
| Grammatical  |          |            | Framework |     | (GF)’s    | incremental |          |            |            |     |     |     |
| ------------ | -------- | ---------- | --------- | --- | --------- | ----------- | -------- | ---------- | ---------- | --- | --- | --- |
|              |          |            |           |     |           |             |          | • ACE2004: | 17outof257 |     |     |     |
| parser,      | supports |            | PMCFG     |     | (Parallel |             | Multiple |            |            |     |     |     |
| Context-Free |          | Grammars). |           |     | PMCFG     | lies        | between  |            |            |     |     |     |
• AQUAINT:24outof727
mildlycontext-sensitiveandfullycontext-sensitive
| grammars(Sekietal.,1991). |     |     |     |     |     |     |     | • ClueWeb: | 44outof11154 |     |     |     |
| ------------------------- | --- | --- | --- | --- | --- | --- | --- | ---------- | ------------ | --- | --- | --- |
10945

• MSNBC:5outof656 isatextandtheoutputisasetoftriplesinsubject-
collapsedformat. Aconcreteexamplewouldbe:
• Wikipedia: 7outof6821
Vettaikaaran (2009 film) was originally
written in the Tamil language, with
• UnseenMention(wikilinksNED): 114 out of
B. Babusivan as the screenwriter. ->
10000
[s] Vettaikaaran_(2009_film) [r] original
language of film or TV show [o]
Metrics. Many previous works (De Cao et al.,
Tamil_language [r] screenwriter [o] B._-
2021; Ganea and Hofmann, 2017; Ayoola et al.,
Babusivan [e]
2022)reportthemicro-averagedF1scorefromGer-
bilevaluationtool. Inourapproach,wealwaystake
E.2 EntityDisambiguation
thetop-1predictionasthefinalprediction. Since
Weshowtwopromptconstructionmethodsforen-
each mention is only associated with one target
titydisambiguation.
entity,themicro-averagedF1scoreisequivalentto
the accuracy in this case (accuracy = precision = Prompt construction A. The instruction is
recall=F1)Wereporttheaccuracyastheevalua- Disambiguate the entity surrounded by
tion metric for the ED task and didn’t use Gerbil [START_ENT] and [END_ENT] by giving the
evaluationtool. correct entity name in the knowledge base.
Werandomlyselectsomedemonstrationexamples
E PromptConstruction
from the training set. We use the following for-
mat to represent the demonstration examples as
In this section, we provide more details on the
a string: [input] -> [mention] [ [target
promptconstructionprocess. Thepromptusedin
entity] ],wheretheinputisatext,themention
ourexperimentsiscomposedoftwoparts:
istheentitymentionsurroundedby[START_ENT]
1. instruction: ashortsentencethatdescribesthe and[END_ENT],andthetargetentityistheentity
task. name in the knowledge base. A concrete exam-
pleofdemoexamplerepresentationwouldbe: Eu
2. demonstration examples: a set of examples
rejects [START_ENT] German [END_ENT] call
thatdemonstratetheexpectedbehaviorofthe
to boycott British lamb Peter Blackburn
model.
Brussels 1996 08¨-> German [ Germany ]The
final prompt is a concatenation of the instruction
We observe that the performance of the model is
and the demonstration examples. A full prompt
sensitivetothewordingoftheinstructionandthe
with2demoexampleswouldbe:
format of the demonstration examples. To find
Disambiguate the entity surrounded by
a good instruction and demonstration examples,
[START_ENT] and [END_ENT] by giving the
we first manually construct a set of instructions
correct entity name in the knowledge base:
and demonstration formats. Then, we randomly
"Eu rejects [START_ENT] German [END_-
sample a few demonstration examples from the
ENT] call to boycott British lamb Peter
trainingsetandmanuallycheckwhetherthemodel
Blackburn Brussels 1996 08" -> German [
can solve the task with the given instruction and
Germany ]; 16 other items that were put up
demonstration examples. This process helps us
for auction by [START_ENT] Hendrix [END_-
findagoodinstructionanddemonstrationformat,
ENT] s former girlfriend Kathy Etchingham
thought probably not the best. Since our goal is
-> Hendrix [ Jimi Hendrix ]; lead with a
nottofindthebestinstructionanddemonstration
well struck header in the seventh minute
format, we didn’t spend too much time on this
[START_ENT] Japan [END_ENT] then laid
process. Below, we provide more details on the
siege to the Syrian penalty area for most
promptconstructionprocessforeachtask.
-> "
E.1 InformationExtraction
Prompt construction B. The instruction is:
TheinstructionusedisExtract the triples in Disambiguate the entity surrounded by
subject-collapsed format from texts below. [START_ENT] and [END_ENT] by giving the
Thedemonstrationexamplesareinthefollowing canonical entity name in the knowledge
format: [input] -> [output], where the input base:. The demonstration examples are in the
10946

following format: [input] -> [mention] [ The dollar weakened against most other
| [target | entity] | ],  |       |     |          |         | major | currencies |     | -> [ | ( S ( | NP-SBJ | ( DT |
| ------- | ------- | --- | ----- | --- | -------- | ------- | ----- | ---------- | --- | ---- | ----- | ------ | ---- |
|         |         |     | where | the | input is | a text, |       |            |     |      |       |        |      |
the mention is the entity mention surrounded by The ) ( NN dollar ) ) ( VP ( VBD weakened
[START_ENT] and [END_ENT], and the target ) ( PP ( IN against ) ( NP ( RBS most ) (
|           |               |     |        |      |        |        | JJ other | )   | ( JJ major |     | ) ( NNS | currencies |     |
| --------- | ------------- | --- | ------ | ---- | ------ | ------ | -------- | --- | ---------- | --- | ------- | ---------- | --- |
| entity is | the canonical |     | entity | name | in the | knowl- |          |     |            |     |         |            |     |
edge base. A concrete example of demo ex- ) ) ) ) ) ],wherethecorrespondingparsetree
| ample would  |           | be: "Eu   | rejects |            | [START_ENT] |       | isshowninListing6. |        |                                      |     |     |     |     |
| ------------ | --------- | --------- | ------- | ---------- | ----------- | ----- | ------------------ | ------ | ------------------------------------ | --- | --- | --- | --- |
| German       | [END_ENT] | call      | to      | boycott    | British     |       |                    |        |                                      |     |     |     |     |
| lamb Peter   |           | Blackburn |         | Brussels   | 1996        | 08    |                    |        |                                      |     |     |     |     |
|              |           |           |         |            |             |       | Listing6:          |        | parsetreewithhierarchicalindentation |     |     |     |     |
| -> German    | :         | Canonical |         | form       | [ Germany   |       |                    |        |                                      |     |     |     |     |
|              |           |           |         |            |             |       | ( S                |        |                                      |     |     |     |     |
| ] A full     | prompt    | with      | 2 demo  | examples   |             | would | (                  | NP−SBJ |                                      |     |     |     |     |
| Disambiguate |           | the       | entity  | surrounded |             | by    |                    | (      | DT The                               | )   |     |     |     |
be:
|             |     |               |     |     |        |     |     | (   | NN dollar | )   |     |     |     |
| ----------- | --- | ------------- | --- | --- | ------ | --- | --- | --- | --------- | --- | --- | --- | --- |
| [START_ENT] |     | and [END_ENT] |     | by  | giving | the |     |     |           |     |     |     |     |
)
| canonical | entity | name    |             | in the | knowledge |        | (   | VP  |              |     |     |     |     |
| --------- | ------ | ------- | ----------- | ------ | --------- | ------ | --- | --- | ------------ | --- | --- | --- | --- |
|           |        |         |             |        |           |        |     | (   | VBD weakened |     | )   |     |     |
| base:     | "Eu    | rejects | [START_ENT] |        |           | German |     |     |              |     |     |     |     |
( PP
| [END_ENT]       | call | to       | boycott   | British |         | lamb   |     |     |      |          |            |     |     |
| --------------- | ---- | -------- | --------- | ------- | ------- | ------ | --- | --- | ---- | -------- | ---------- | --- | --- |
|                 |      |          |           |         |         |        |     |     | ( IN | against  | )          |     |     |
| Peter Blackburn |      | Brussels |           | 1996    | 08 ->   | German |     |     | ( NP |          |            |     |     |
|                 |      |          |           |         |         |        |     |     | (    | RBS      | most )     |     |     |
| : Canonical     |      | form     | [ Germany |         | ] 16    | other  |     |     |      |          |            |     |     |
|                 |      |          |           |         |         |        |     |     | (    | JJ other | )          |     |     |
| items that      |      | were put | up        | for     | auction | by     |     |     |      |          |            |     |     |
|                 |      |          |           |         |         |        |     |     | (    | JJ major | )          |     |     |
| [START_ENT]     |      | Hendrix  | [END_ENT] |         | s       | former |     |     | (    | NNS      | currencies |     | )   |
)
| girlfriend | Kathy | Etchingham |     |     | -> Hendrix |     |     |     |     |     |     |     |     |
| ---------- | ----- | ---------- | --- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |
)
| : Canonical |             | form [     | Jimi   | Hendrix   |             | ] lead | )                                        |         |        |        |       |         |        |
| ----------- | ----------- | ---------- | ------ | --------- | ----------- | ------ | ---------------------------------------- | ------- | ------ | ------ | ----- | ------- | ------ |
| with a      | well        | struck     | header | in        | the seventh |        | )                                        |         |        |        |       |         |        |
| minute      | [START_ENT] |            | Japan  | [END_ENT] |             | then   |                                          |         |        |        |       |         |        |
|             |             |            |        |           |             |        | One                                      | variant | of the | prompt | is to | provide | a rea- |
| laid siege  | to          | the Syrian |        | penalty   | area        | for    |                                          |         |        |        |       |         |        |
| most ->     | "           |            |        |           |             |        | soningchainwiththedemonstrationexamples. |         |        |        |       |         | A      |
concreteexamplewouldbe:
Prompt used in each dataset We compare the "The constituency parse tree is: ( S (
performance of the two prompts in each dataset NP-SBJ ( NN Bond ) ( NNS prices ) ) ( VP
| overthevalidationset.         |     |     | Weselectthepromptthat |               |     |     |            |      |              |     |      |        |     |
| ----------------------------- | --- | --- | --------------------- | ------------- | --- | --- | ---------- | ---- | ------------ | --- | ---- | ------ | --- |
|                               |     |     |                       |               |     |     | ( VBD      | were | ) ( ADJP-PRD |     | ( RB | barely | ) ( |
| performsthebestineachdataset. |     |     |                       | Thepromptused |     |     |            |      |              |     |      |        |     |
|                               |     |     |                       |               |     |     | JJR higher |      | ) ) )        | )   |      |        |     |
ineachdatasetisshowninTable6. " "S: This stands for Sentence, the
|     | Dataset |     | Prompt  |     |     |     | top-level |           | structure  | in          | the parse |           | tree." |
| --- | ------- | --- | ------- | --- | --- | --- | --------- | --------- | ---------- | ----------- | --------- | --------- | ------ |
|     |         |     |         |     |     |     | "NP-SBJ:  | This      | is         | the subject |           | noun      | phrase |
|     | AIDA    |     | Prompt1 |     |     |     |           |           |            |             |           |           |        |
|     |         |     |         |     |     |     | of the    | sentence, |            | which       | is ’Bond  | prices’." |        |
|     | MSNBC   |     | Prompt2 |     |     |     |           |           |            |             |           |           |        |
|     |         |     |         |     |     |     | "NN:      | This      | stands     | for         | Noun,     | Singular  | or     |
|     | AQUAINT |     | Prompt2 |     |     |     |           |           |            |             |           |           |        |
|     |         |     |         |     |     |     | Mass.     | In this   | case,      | the         | word      | ’Bond’    | falls  |
|     | ACE2004 |     | Prompt2 |     |     |     |           |           |            |             |           |           |        |
|     |         |     |         |     |     |     | into      | this      | category." |             |           |           |        |
|     | CWEB    |     | Prompt2 |     |     |     |           |           |            |             |           |           |        |
|     |         |     |         |     |     |     | "NNS:     | This      | stands     | for         | Noun,     | Plural.   | The    |
|     | WIKI    |     | Prompt1 |     |     |     |           |           |            |             |           |           |        |
|     |         |     |         |     |     |     | word      | ’prices’  | is         | an example  |           | of this." |        |
Table6: Promptusedineachdataset "VP: This stands for Verb Phrase, which
|     |     |     |     |     |     |     | in this | case | is ’were |     | barely | higher’." |        |
| --- | --- | --- | --- | --- | --- | --- | ------- | ---- | -------- | --- | ------ | --------- | ------ |
|     |     |     |     |     |     |     | "VBD:   | This | stands   | for | Verb,  | Past      | Tense. |
E.3 ConstiutencyParsing
|                 |     |     |         |     |              |     | The word   | ’were’ | falls | into   | this | category." |     |
| --------------- | --- | --- | ------- | --- | ------------ | --- | ---------- | ------ | ----- | ------ | ---- | ---------- | --- |
|                 |     |     | Perform |     | constituency |     | "ADJP-PRD: |        | This  | stands | for  | Adjective  |     |
| The instruction |     | is: |         |     |              |     |            |        |       |        |      |            |     |
parsing on the provided sentences Phrase, used as a predicate. The phrase
in accordance with the Penn TreeBank ’barely higher’ is an example of this."
annotation guidelines.. The demonstration "RB: This stands for Adverb. The word
|     |     |     |     |     | [input] | ->  | ’barely’ | falls | into | this | category." |     |     |
| --- | --- | --- | --- | --- | ------- | --- | -------- | ----- | ---- | ---- | ---------- | --- | --- |
examplesareinthefollowingformat:
[output],wheretheinputisatextandtheoutput "JJR: This stands for Adjective,
istheflattenedconstituencyparsetree. Aconcrete Comparative. The word ’higher’ falls into
|     |     |     |     |     |     |     | this | category.’" |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ---- | ----------- | --- | --- | --- | --- | --- |
examplewouldbe:
10947

|     |     |     | SynthIE-text |     | improvementovertheunconstraineddecodingap- |     |     |     |     |     |     |
| --- | --- | --- | ------------ | --- | ------------------------------------------ | --- | --- | --- | --- | --- | --- |
Method Precision Recall F1 proach for LMs of all sizes. Compared with the
resultsinTable7,theperformanceofthesubject-
Few-shotUnconstrained
|                     |     |     |     |         | collapsed | linearization |     | is  | indeed lower | than | the |
| ------------------- | --- | --- | --- | ------- | --------- | ------------- | --- | --- | ------------ | ---- | --- |
| LLaMA-7B-sc(4shots) |     |     | 9.7 | 8.6 9.2 |           |               |     |     |              |      |     |
LLaMA-13B-sc(4shots) 6.7 12.5 8.7 fully-expandedlinearization.
| LLaMA-33B-sc(4shots) |     |     | 10.6 | 20.6 14.0 |     |     |     |     |     |     |     |
| -------------------- | --- | --- | ---- | --------- | --- | --- | --- | --- | --- | --- | --- |
With a
|     |     |     |     |     | Adding | all relations |     | to  | the prompt. |     |     |
| --- | --- | --- | --- | --- | ------ | ------------- | --- | --- | ----------- | --- | --- |
Few-shotConstrained maximum context length of 2048 tokens, it’s not
| LLaMA-7B-sc(4shots)  |     |     | 24.1 | 19.3 21.5 |          |        |         |          |             |     |        |
| -------------------- | --- | --- | ---- | --------- | -------- | ------ | ------- | -------- | ----------- | --- | ------ |
|                      |     |     |      |           | possible | to add | all the | millions | of entities |     | to the |
| LLaMA-13B-sc(4shots) |     |     | 26.4 | 30.5 28.3 |          |        |         |          |             |     |        |
prompt. However,wecanaddalltherelationsto
| LLaMA-33B-sc(4shots) |     |     | 31.3 | 36.2 33.6 |     |     |     |     |     |     |     |
| -------------------- | --- | --- | ---- | --------- | --- | --- | --- | --- | --- | --- | --- |
theprompt,whichisamuchsmallerset(888rela-
Table7: ResultsforcIEwithsubject-collapsedlin- tions). Onemaywonderifaddingalltherelations
earization.
|        |     |     |              |           | to the prompt                             |     | would | help                     | the model       | to learn | the |
| ------ | --- | --- | ------------ | --------- | ----------------------------------------- | --- | ----- | ------------------------ | --------------- | -------- | --- |
|        |     |     |              |           | relationextractiontaskbetter.             |     |       |                          | Becausethemodel |          |     |
|        |     |     | SynthIE-text |           | cancopytherelationfromthepromptandthismay |     |       |                          |                 |          |     |
| Method |     |     | Precision    | Recall F1 |                                           |     |       |                          |                 |          |     |
|        |     |     |              |           | makethetaskeasier.                        |     |       | However,wefindthatadding |                 |          |     |
Supervised
|                                      |     |     |      |           | all the relations |       | to           | the prompt | does       | not help | the     |
| ------------------------------------ | --- | --- | ---- | --------- | ----------------- | ----- | ------------ | ---------- | ---------- | -------- | ------- |
| GenIET5-base-fe(Josifoskietal.,2022) |     |     | 49.1 | 26.7 34.6 |                   |       |              |            |            |          |         |
|                                      |     |     |      |           | model to          | learn | the relation |            | extraction | task     | better. |
Few-shotUnconstrained
Table8showsthataddingalltherelationstothe
| LLaMA-7B-feR(4shots)  |     |     | 9.9  | 13.5 11.4 |     |     |     |     |     |     |     |
| --------------------- | --- | --- | ---- | --------- | --- | --- | --- | --- | --- | --- | --- |
| LLaMA-13B-feR(4shots) |     |     | 10.8 | 17.5 13.4 |     |     |     |     |     |     |     |
promptonlybringsasmallimprovementoverthe
| LLaMA-33B-feR(4shots) |     |     | 14.0 | 22.5 17.3 |     |     |     |     |     |     |     |
| --------------------- | --- | --- | ---- | --------- | --- | --- | --- | --- | --- | --- | --- |
baseline.
| Vicuna-13B-feR(4shots) |     |     | 12.5 | 16.7 14.3 |     |     |     |     |     |     |     |
| ---------------------- | --- | --- | ---- | --------- | --- | --- | --- | --- | --- | --- | --- |
Few-shotConstrained ConstituencyParsingwithVicuna. Wealsoeval-
| LLaMA-7B-feR(4shots)   |     |     | 28.1 | 23.6 25.7 |               |     |           |        |             |     |          |
| ---------------------- | --- | --- | ---- | --------- | ------------- | --- | --------- | ------ | ----------- | --- | -------- |
| LLaMA-13B-feR(4shots)  |     |     | 31.8 | 31.2 31.5 |               |     |           |        |             |     |          |
|                        |     |     |      |           | Method        |     | Precision | Recall | TagAccuracy |     | Validity |
| LLaMA-33B-feR(4shots)  |     |     | 36.4 | 34.8 35.6 |               |     |           |        |             |     |          |
| Vicuna-13B-feR(4shots) |     |     | 40.3 | 23.8 29.9 | Unconstrained |     |           |        |             |     |          |
|                        |     |     |      |           | Vicuna-7B     |     | 13.5      | 12.7   | 27.8        |     | 42.2     |
Table8: ResultsforcIEwithallrelationsaddedto
|     |     |     |     |     | Vicuna-13B |     | 31.6 | 28.1 | 29.6 |     | 51.4 |
| --- | --- | --- | --- | --- | ---------- | --- | ---- | ---- | ---- | --- | ---- |
theprompt.feRstandsforfully-expandedlinearization
ConstrainedIIG
withrelationsaddedtotheprompt.
|     |     |     |     |     | Vicuna-7B  |     | 17.4 | 16.3 | 30.5 |     | 54.3 |
| --- | --- | --- | --- | --- | ---------- | --- | ---- | ---- | ---- | --- | ---- |
|     |     |     |     |     | Vicuna-13B |     | 30.8 | 27.7 | 33.4 |     | 56.1 |
F DecodingSettings
ConstrainedIDG
|     |     |     |     |     | Vicuna-7B |     | 35.6 | 31.9 | 41.4 |     | 100.0 |
| --- | --- | --- | --- | --- | --------- | --- | ---- | ---- | ---- | --- | ----- |
Weemployconstrainedbeamsearchduringourex-
|     |     |     |     |     | Vicuna-13B |     | 51.6 | 44.4 | 42.4 |     | 100.0 |
| --- | --- | --- | --- | --- | ---------- | --- | ---- | ---- | ---- | --- | ----- |
periments,withabeamsizeof2andlengthpenalty
|     |     |     |     |     | Table9: | ConstituencyparsingresultswithVicuna. |     |     |     |     | The |
| --- | --- | --- | --- | --- | ------- | ------------------------------------- | --- | --- | --- | --- | --- |
of1.0. Ourchoiceofasmallbeamsizeisbasedon
experimentssettingisthesameasinTable3.
ourobservationthatlargerbeamsizesdonotyield
significantimprovementandmayevenresultinde-
uatetheconstraineddecodingapproachonthecon-
creasedperformance. Incontrast,abeamsizeof2 stituency parsing task with the instruction-tuned
| proves to                               | be sufficient | for achieving | good | results |       |         |       |         |          |     |         |
| --------------------------------------- | ------------- | ------------- | ---- | ------- | ----- | ------- | ----- | ------- | -------- | --- | ------- |
|                                         |               |               |      |         | model | Vicuna. | Table | 9 shows | Vicuna’s |     | perfor- |
| whilealsobeingcomputationallyefficient. |               |               |      | When    |       |         |       |         |          |     |         |
manceisevenworsethantheLLaMAmodel.
evaluatingthegeneratedoutputs,weselectthemost
| probablenon-emptygenerationastheoutput. |     |     |     |     | H Latency |           |       |           |     |         |     |
| --------------------------------------- | --- | --- | --- | --- | --------- | --------- | ----- | --------- | --- | ------- | --- |
|                                         |     |     |     |     | Here’s    | a concise | table | comparing | the | latency | of  |
G AdditionalExperimentalResults
|     |     |     |     |     | pure decoding |     | to the | additional | delay | introduced |     |
| --- | --- | --- | --- | --- | ------------- | --- | ------ | ---------- | ----- | ---------- | --- |
G.1 InformationExtraction
bygrammarconstraints.
Subject-Collapsed Linearization. Subject- LatencyforIE.Weprovideameasurementofla-
collapsedlinearizationisavariantoflinearization tencyforIEtaskinFigure3andFigure4. Wecon-
where the subject is collapsed into the object. It sidertwolargegrammars,theWikiNERgrammar
has the advantage of being more compact (token and the REBEL grammar. The WikiNER gram-
efficient)thanthefully-expandedlinearization,but marcontains279Kentitiesand158relations. The
ityieldsslightlylowerperformance,intuitivelybe- REBELgrammarcontains5.9Mentitiesand857
cause it’s less explicit. Table 7 shows that the relations. Given the grammar, we randomly pick
constraineddecodingapproachbringsasignificant thenexttokenfromthesetofnextallowedtokens
10948

withtheend-of-sentencetokenexcludedtoavoid theinstruction. Thegenerationontheleftisfrom
earlytermination. Theincrementalparsingstepis Vicuna-13Bandthegenerationontherightisfrom
doneonCPUandwedonotuseanyoptimization LLaMA-13B.Themajorityoftheerroneousoutput
techniquessuchasmulti-threading. sequencescontainunbalancedbracketsandlength
mismatch(missingwordsorextrawordsfromthe
inputsentence).
| Figure3: | latencyofWikiNERgrammar |     |     |     |
| -------- | ----------------------- | --- | --- | --- |
| Figure4: | latencyofREBELgrammar   |     |     |     |
AsshowninFigure3s,thelatencyforWikiNER
grammar(0.05s)iscomparabletothelatencyofthe
LMonGPU.However,thelatencyfortheREBEL
grammar(0.5s)issignificantlyhigherthanthela-
| tency of | the LM. We | believe | this can | be largely |
| -------- | ---------- | ------- | -------- | ---------- |
improvedbyusingmoreappropriateincremental
parserandleaveitasfuturework.
I ErrorExamplesofConstituency
Parsing
HerewegiveexamplesofusingLMstoperformCP
| inafree-formgenerationsetting. |                          |     | Weshowsome |     |
| ------------------------------ | ------------------------ | --- | ---------- | --- |
| outputexamples1                | ofLLaMA-13BandVicuna-13B |     |            |     |
onCPonPennTreebank(PTB).Weseethatwhile
instruction-tunedLMs(Vicuna-13B)cangenerate
| seemingly        | reasonable | parse      | trees, most | of them   |
| ---------------- | ---------- | ---------- | ----------- | --------- |
| are not correct. | On         | the        | other hand, | base LMs  |
| (LLaMA-13B)      | almost     | completely | fail        | to follow |
1Thevisualisationaremadefromhttps://chat.lmsys.
org/
10949

Figure5: Exampleof1shotCPonPTBinstanceNo.12Thegoldenparsetreeis"(S(ADVP-TMP(RBNow))
(NP-SBJ(PRPwe))(VP(VBP’re)(PP-LOC-PRD(INat)(NP(NP(DTthe)(NNbottom))(PP(IN
of)(NP(DTthe)(NNheap)))))))"ThegenerationfromVicuna-13Bisnotcorrect,butitstilllookslikea
reasonableparsetree. ThegenerationfromLLaMA-13Bfailstofollowtheinstruction.
Figure6: Exampleof1shotCPonPTBinstanceNo.12Thegoldenparsetreeis"(S(ADVP-TMP(RBNow))(
NP-SBJ(PRPwe))(VP(VBP’re)(PP-LOC-PRD(INat)(NP(NP(DTthe)(NNbottom))(PP(INof)(
NP(DTthe)(NNheap)))))))"ThegenerationfromVicuna-13Blooksreasonable,butitsbracketingisactually
unbalanced. ThegenerationfromLLaMA-13Bfailstofollowtheinstruction.
10950

Figure7: Exampleof1shotCPonPTBinstanceNo.12Thegoldenparsetreeis"(S(ADVP-TMP(RBNow))(
NP-SBJ(PRPwe))(VP(VBP’re)(PP-LOC-PRD(INat)(NP(NP(DTthe)(NNbottom))(PP(INof)(
NP(DTthe)(NNheap)))))))"ThegenerationfromVicuna-13Bisavalidtreestructure,butitisnotthesame
asthegoldenparsetree. ThegenerationfromLLaMA-13Bfailstofollowtheinstruction.
Figure8: Exampleof1shotCPonPTBinstanceNo.29Thegoldenparsetreeis"(S(ADVP-TMP(RBNow))(
NP-SBJ(NNSproducers))(VP(VBPhope)(SBAR(S(NP-SBJ(NNSprices))(VP(VBPhave)(VP(VBN
hit)(NP(NNbottom))))))))"ThegenerationfromVicuna-13Bhaswrongwords(somemissing,someextra)
andwrongbracketing. ThegenerationfromLLaMA-13Bfailstofollowtheinstruction.
10951

Figure9: Exampleof1shotCPonPTBinstanceNo.29fromanothersamplingThegoldenparsetreeis"(S(
ADVP-TMP(RBNow))(NP-SBJ(NNSproducers))(VP(VBPhope)(SBAR(S(NP-SBJ(NNSprices))
(VP(VBPhave)(VP(VBNhit)(NP(NNbottom))))))))"ThegenerationfromVicuna-13Bhaswrong
words(somemissing, someextra)andwrongbracketing. ThegenerationfromLLaMA-13Bfailstofollowthe
instruction.
Figure10: Exampleof1shotCPonPTBinstanceNo.86(longsentence)Thisisalongsentence. Thegolden
parsetreeis"(SINV(S-TPC-2(S(NP-SBJ(DTThe)(JJoverall)(ADJP(CD0.9)(NN%))(NNincrease))
(VP(VBZis)(ADJP-PRD(JJserious))(PP(INin)(NP(PRPitself)))))(CCbut)(S(SBAR-NOM-SBJ(
WHNP-1(WPwhat))(S(VP(VBZis)(ADJP-PRD(RBeven)(JJRworse)))))(VP(VBZis)(SBAR-PRD
(INthat)(S(PP(VBGexcluding)(NP(NNfood)(CCand)(NNenergy)))(NP-SBJ(DTthe)(NN
producer)(NNprice)(NNindex))(ADVP-TMP(RBstill))(VP(VBDincreased)(PP-EXT(INby)(NP(
CD0.7)(NN%)))))))))(VP(VBDsaid))(NP-SBJ(NP(NNPGordon)(NNPRichards))(NP(NP(DT
an)(NNeconomist))(PP-LOC(INat)(NP(NP(DTthe)(NNPNational)(NNPAssociation))(PP(INof
)(NP(NNPManufacturers))))))))"ThegenerationfromVicuna-13Bhaswrongwords(somemissing,some
extra)andwrongbracketing. ThegenerationfromLLaMA-13Bisnotavalidparsetree,e.g. thelastconstituent
NNPdoesn’thaveacorrespondingword.
10952