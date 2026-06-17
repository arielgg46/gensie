---
type: source
source_type: paper
url: https://aclanthology.org/N04-1022.pdf
title: "Minimum Bayes-Risk Decoding for Statistical Machine Translation"
fetched_at: 2026-06-17T15:17:31-05:00
fetcher: markitdown
---
Minimum Bayes-Risk Decoding for Statistical Machine Translation
|     |     |     |     | ShankarKumarandWilliamByrne |     |     |     |     | (cid:0) |     |     |     |     |
| --- | --- | --- | --- | --------------------------- | --- | --- | --- | --- | ------- | --- | --- | --- | --- |
Center forLanguageandSpeechProcessing,JohnsHopkinsUniversity,
|     |     |     | 3400North | CharlesStreet,Baltimore,MD, |                      |     |          |     | 21218,USA |     |     |     |     |
| --- | --- | --- | --------- | --------------------------- | -------------------- | --- | -------- | --- | --------- | --- | --- | --- | --- |
|     |     |     |           |                             | (cid:1) skumar,byrne |     | @jhu.edu |     |           |     |     |     |     |
(cid:2)
Abstract
thougheffective,donottakeintoaccountexplicitsyntac-
ticinformationwhenmeasuringtranslationquality.
We present Minimum Bayes-Risk (MBR) de- Given that different Machine Translation (MT) eval-
| codingforstatisticalmachinetranslation. |     |     |     |     |     | This |                |     |        |               |     |           |         |
| --------------------------------------- | --- | --- | --- | --- | --- | ---- | -------------- | --- | ------ | ------------- | --- | --------- | ------- |
|                                         |     |     |     |     |     |      | uation metrics | are | useful | for capturing |     | different | aspects |
statisticalapproachaimstominimizeexpected oftranslation quality,itbecomesdesirabletocreateMT
loss of translation errors under loss functions systemstunedwithrespecttoeachindividualcriterion.In
| that | measure | translation | performance. |     | We  | de- |     |     |     |     |     |     |     |
| ---- | ------- | ----------- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
contrast,themaximumlikelihoodtechniquesthatunder-
scribe a hierarchy of loss functions that incor- liethedecisionprocessesofmostcurrentMTsystemsdo
poratedifferentlevelsoflinguisticinformation
nottakeintoaccounttheseapplicationspecificgoals.We
from word strings, word-to-word alignments applytheMinimumBayes-Risk(MBR)techniquesdevel-
from an MT system, and syntactic structure opedforautomaticspeechrecognition(GoelandByrne,
fromparse-treesofsourceandtargetlanguage
|     |     |     |     |     |     |     | 2000)andbitextwordalignmentforstatisticalMT |     |     |     |     |     | (Ku- |
| --- | --- | --- | --- | --- | --- | --- | ------------------------------------------- | --- | --- | --- | --- | --- | ---- |
sentences. We report the performance of the mar and Byrne, 2002), to the problem of building au-
| MBR | decoders | on a | Chinese-to-English |     |     | trans- |         |            |       |     |          |          |         |
| --- | -------- | ---- | ------------------ | --- | --- | ------ | ------- | ---------- | ----- | --- | -------- | -------- | ------- |
|     |          |      |                    |     |     |        | tomatic | MT systems | tuned | for | specific | metrics. | This is |
lationtask. OurresultsshowthatMBRdecod- a framework that can be used with statistical models of
ing can be used to tune statistical MT perfor- speechandlanguagetodevelopdecisionprocessesopti-
manceforspecificlossfunctions.
mizedforspecificlossfunctions.
|     |     |     |     |     |     |     | We will | show | that MBR | decoding | can | be applied | to  |
| --- | --- | --- | --- | --- | --- | --- | ------- | ---- | -------- | -------- | --- | ---------- | --- |
machinetranslationintwoscenarios.Givenanautomatic
1 Introduction
|     |     |     |     |     |     |     | MTmetric, | we designa |     | lossfunctionbasedonthe |     |     | met- |
| --- | --- | --- | --- | --- | --- | --- | --------- | ---------- | --- | ---------------------- | --- | --- | ---- |
ricanduseMBRdecodingtotuneMTperformanceun-
| Statistical  | Machine  | Translation |        | systems  | have | achieved   |         |            |      |      |         |          |     |
| ------------ | -------- | ----------- | ------ | -------- | ---- | ---------- | ------- | ---------- | ---- | ---- | ------- | -------- | --- |
|              |          |             |        |          |      |            | der the | metric. We | also | show | how MBR | decoding | can |
| considerable | progress | in          | recent | years as | seen | from their |         |            |      |      |         |          |     |
beusedtoincorporatesyntacticstructureintoastatistical
| performance | on    | international | competitions |            | in       | standard |                                             |     |     |     |     |     |       |
| ----------- | ----- | ------------- | ------------ | ---------- | -------- | -------- | ------------------------------------------- | --- | --- | --- | --- | --- | ----- |
|             |       |               |              |            |          |          | MTsystembybuildingspecializedlossfunctions. |     |     |     |     |     | These |
| evaluation  | tasks | (NIST,        | 2003).       | This rapid | progress | has      |                                             |     |     |     |     |     |       |
beengreatlyfacilitatedbythedevelopmentofautomatic loss functions can use information from word strings,
|             |             |         |       |              |     |            | word-to-word | alignments |              | and | parse-trees   | of the | source   |
| ----------- | ----------- | ------- | ----- | ------------ | --- | ---------- | ------------ | ---------- | ------------ | --- | ------------- | ------ | -------- |
| translation | evaluation  | metrics | such  | as BLEU      |     | score (Pa- |              |            |              |     |               |        |          |
|             |             |         |       |              |     |            | sentence     | and its    | translation. |     | In particular | we     | describe |
| pineni et   | al., 2001), | NIST    | score | (Doddington, |     | 2002)      |              |            |              |     |               |        |          |
thedesignofaBilingualTreeLossFunctionthatcanex-
| and Position    | IndependentWord |       |          | Error Rate | (PER) | (Och,     |          |               |           |     |               |             |     |
| --------------- | --------------- | ----- | -------- | ---------- | ----- | --------- | -------- | ------------- | --------- | --- | ------------- | ----------- | --- |
|                 |                 |       |          |            |       |           | plicitly | use syntactic | structure |     | for measuring | translation |     |
| 2002). However, |                 | given | the many | factors    | that  | influence |          |               |           |     |               |             |     |
translationquality,itisunlikelythatwewillfindasingle quality. MBR decoding under this loss function allows
|     |     |     |     |     |     |     | us to integratesyntacticknowledgeinto |     |     |     |     | a statisticalMT |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------------------------- | --- | --- | --- | --- | --------------- | --- |
translationmetricthatwillbeabletojudgeallthesefac-
systemwithoutbuildingdetailedmodelsoflinguisticfea-
tors.Forexample,theBLEU,NISTandthePERmetrics,
tures,andretrainingthesystemfromscratch.
(cid:3) ThisworkwassupportedbytheNationalScienceFoun- Wefirstpresentahierarchyoflossfunctionsfortrans-
dation under Grant No. 0121285 and an ONR MURI Grant lation based on different levels of lexical and syntactic
N00014-01-1-0685.Anyopinions,findings,andconclusionsor
|     |     |     |     |     |     |     | information | from | source | and | target language | sentences. |     |
| --- | --- | --- | --- | --- | --- | --- | ----------- | ---- | ------ | --- | --------------- | ---------- | --- |
recommendationsexpressedinthismaterialarethoseoftheau-
Thishierarchyincludesthelossfunctionsusefulinboth
| thors and | do not | necessarily | reflect | the views | of the | National |                                            |     |     |     |     |     |     |
| --------- | ------ | ----------- | ------- | --------- | ------ | -------- | ------------------------------------------ | --- | --- | --- | --- | --- | --- |
|           |        |             |         |           |        |          | situationswhereweintendtoapplyMBRdecoding. |     |     |     |     |     | We  |
ScienceFoundationortheOfficeofNavalResearch.

| thenpresenttheMBRframeworkforstatisticalmachine |       |             |     |             |      |            | ence. | Weuse |     | .    |      |                                                                      |                  |     |
| ----------------------------------------------- | ----- | ----------- | --- | ----------- | ---- | ---------- | ----- | ----- | --- | ---- | ---- | -------------------------------------------------------------------- | ---------------- | --- |
|                                                 |       |             |     |             |      |            |       |       | 2;  | := < |      |                                                                      |                  |     |
| translation                                     | under | the various |     | translation | loss | functions. |       |       |     |      |      |                                                                      |                  |     |
|                                                 |       |             |     |             |      |            |       |       |     |      | GI H |                                                                      |                  |     |
| WefinallyreporttheperformanceofMBRdecodersop-   |       |             |     |             |      |            |       |       |     |      | J    |                                                                      |                  |     |
|                                                 |       |             |     |             |      |            | >     |       |     |      |      | E K (cid:8)(cid:25) (cid:1)(cid:17) (cid:11)(cid:23) (cid:1)(cid:21) | (cid:2)%(cid:13) |     |
timizedforeachlossfunction. (cid:7)? (cid:1)(cid:3) @A (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12) (cid:1) (cid:2)(cid:13)’ :C B(cid:16) DF E 56 (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12) (cid:1) (cid:2)(cid:13)(cid:20) (cid:11)
|     |     |     |     |     |     |     |     |     |     |     | KM LO NQ P(cid:25) R# S | 2   | TV U |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----------------------- | --- | ---- | --- |
2 TranslationLossFunctions where is the precision of -grams in the hy-
|     |     |     |     |     |     |     |          | E K             | (cid:8)(cid:25) (cid:1)(cid:17) (cid:11)(cid:23) (cid:1)(cid:21) | (cid:2)%(cid:13) |     | )   |     |     |
| --- | --- | --- | --- | --- | --- | --- | -------- | --------------- | ---------------------------------------------------------------- | ---------------- | --- | --- | --- | --- |
|     |     |     |     |     |     |     | pothesis |                 | . TheBLEUscoreiszeroifanyofthen-gram                             |                  |     |     |     |     |
|     |     |     |     |     |     |     |          | (cid:1)(cid:21) | (cid:2)                                                          |                  |     |     |     |     |
We now introduce translation loss functions to measure precisions is zero for that sentence pair. We
|     |     |     |     |     |     |     |     |     | E K (cid:8)(cid:10) (cid:1)(cid:17) | (cid:11)(cid:12) (cid:1)(cid:6) (cid:2)(cid:14)(cid:13) |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ----------------------------------- | ------------------------------------------------------- | --- | --- | --- | --- |
thequalityofautomaticallygeneratedtranslations. Sup- note that > . We derive a loss
pose we have a sentence in a source language for functionfromBLEUscoreas WX 7 (cid:7)? (cid:1)(cid:3) @A (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12) (cid:1) (cid:2)(cid:13)4 7Y .
(cid:0)
| which we | have | generated | an  | automatic | translation |                |         |     |      |     |     |     |     |     |
| -------- | ---- | --------- | --- | --------- | ----------- | -------------- | ------- | --- | ---- | --- | --- | --- | --- | --- |
|          |      |           |     |           |             | (cid:1)(cid:3) | (cid:2) |     | BLEU |     |     | >   | .   |     |
withword-to-wordalignment relativeto . Theword- (cid:7) (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12) (cid:1)(cid:6) (cid:2)((cid:13)Z :X ." [ (cid:7)Z (cid:1)(cid:3) @(cid:17) (cid:8)(cid:25) (cid:1)(cid:17) (cid:11)(cid:23) (cid:1)(cid:21) (cid:2)%(cid:13)
(cid:4)(cid:5) (cid:2) (cid:0) WordErrorRate (WER) is the ratio of the string-edit
| to-word | alignment |     | specifies | the words | in  | the source |     |     |     |     |     |     |     |     |
| ------- | --------- | --- | --------- | --------- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |
(cid:4)(cid:5) (cid:2) distance between the reference and the hypothesis word
| sentence | that | are aligned | to  | each | word in | the transla- |     |     |     |     |     |     |     |     |
| -------- | ---- | ----------- | --- | ---- | ------- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- |
(cid:0)
tion . We wish to compare this automatic translation strings to the number of words in the reference. String-
(cid:1)(cid:6) (cid:2) editdistanceismeasuredastheminimumnumberofedit
| with a referencetranslation |            |         |              | with word-to-wordalign- |           |           |                                                  |     |     |     |     |     |       |      |
| --------------------------- | ---------- | ------- | ------------ | ----------------------- | --------- | --------- | ------------------------------------------------ | --- | --- | --- | --- | --- | ----- | ---- |
|                             |            |         | (cid:1)      |                         |           |           | operationsneededtotransformawordstringtotheother |     |     |     |     |     |       |      |
| ment                        | relativeto | .       |              |                         |           |           |                                                  |     |     |     |     |     |       |      |
| (cid:4)                     |            | (cid:0) |              |                         |           |           | wordstring.                                      |     |     |     |     |     |       |      |
| We will                     | now        | present | a three-tier |                         | hierarchy | of trans- |                                                  |     |     |     |     |     |       |      |
|                             |            |         |              |                         |           |           | Position-independentWordErrorRate                |     |     |     |     |     | (PER) | mea- |
| lation loss                 | functions  | of      | the form     |                         |           |           |                                                  |     |     |     |     |     |       |      |
that measure against (cid:7)(cid:5) (cid:8)(cid:9) (cid:8)(cid:10) (cid:1)(cid:6) . (cid:2)(cid:10) These (cid:11)(cid:12) (cid:4)(cid:5) (cid:2)(cid:14)(cid:13)(cid:15) (cid:11)(cid:16) (cid:8)(cid:10) loss (cid:1)(cid:17) (cid:11)(cid:12) (cid:4)(cid:18) func- (cid:13)(cid:20) (cid:19)(cid:12) (cid:0)(cid:21) (cid:13) sures the minimum number of edit operations needed
(cid:8)(cid:10) (cid:1)(cid:21) (cid:2)(cid:22) (cid:11)(cid:23) (cid:4)(cid:24) (cid:2)(cid:14)(cid:13) (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12) (cid:4)(cid:18) (cid:13) to transform a word string to any permutation of the
tionswillmakeuseofdifferentlevelsofinformationfrom
|     |     |     |     |     |     |     | other | word | string. | The | PER score | (Och, | 2002) | is then |
| --- | --- | --- | --- | --- | --- | --- | ----- | ---- | ------- | --- | --------- | ----- | ----- | ------- |
wordstrings,MTalignmentsandsyntacticstructurefrom
|                   |     |     |           |               |     |          | computed |     | as a | ratio of | this distance | to  | the number | of  |
| ----------------- | --- | --- | --------- | ------------- | --- | -------- | -------- | --- | ---- | -------- | ------------- | --- | ---------- | --- |
| parse-treesofboth |     | the | sourceand | targetstrings |     | asillus- |          |     |      |          |               |     |            |     |
wordsinthereferencewordstring.
tratedinthefollowingtable.
2.2 TargetLanguageParse-TreeLossFunctions
| LossFunction |     |     |     | FunctionalForm |     |     |     |     |     |     |     |     |     |     |
| ------------ | --- | --- | --- | -------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Thesecondclassoftranslationlossfunctionsusesinfor-
Lexical
|     |     |     |     |     | (cid:7)(cid:5) (cid:8)(cid:25) (cid:1)(cid:17) (cid:11)(cid:23) | (cid:1)(cid:21) (cid:2)(cid:14)(cid:13) | mationonlyfromtheparse-treesofthetwotranslations, |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- |
TargetLanguageParse-Tree
|     |     |     |     |     | (cid:7)(cid:24) (cid:8)(cid:25) (cid:26)(cid:28) (cid:27)(cid:29) (cid:11)(cid:9) | (cid:26)(cid:30) (cid:27)  (cid:31)(cid:25) (cid:13) | so  | that |     |     |     |     | . This | loss |
| --- | --- | --- | --- | --- | --------------------------------------------------------------------------------- | ---------------------------------------------------- | --- | ---- | --- | --- | --- | --- | ------ | ---- |
BilingualParse-Tree
|     |     |     |     |     |     |     |     | (cid:7)(cid:5) | (cid:8)(cid:9) (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12) (cid:4)(cid:18) | (cid:13)(cid:20) (cid:11)(cid:16) (cid:8)(cid:10) (cid:1)(cid:21) (cid:2)(cid:22) (cid:11)(cid:12) (cid:4)(cid:5) | (cid:2)%(cid:13)(cid:20) (cid:19)(cid:12) (cid:0)(cid:21) (cid:13)\ | :] (cid:7)(cid:24) (cid:8)(cid:25) (cid:26)(cid:30) (cid:27)(cid:29) (cid:11)(cid:9) | (cid:26)(cid:30) (cid:27)  (cid:31)(cid:25) (cid:13) |     |
| --- | --- | --- | --- | --- | --- | --- | --- | -------------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------- | --- |
(cid:7)(cid:5) (cid:8)(cid:9) (cid:8)! (cid:26)(cid:28) (cid:27)" (cid:11)(cid:12) (cid:4)(cid:18) (cid:13)(cid:20) (cid:11)# (cid:8)! (cid:26)(cid:30) (cid:27)  (cid:31)$ (cid:11)(cid:23) (cid:4)(cid:24) (cid:2)%(cid:13)(cid:20) (cid:19)(cid:12) (cid:26)(cid:30) &’ (cid:13) functionhasnoaccesstoanyinformationfromthesource
sentenceorthewordalignments.
We start with an example of two competing English Examplesofsuchlossfunctionsaretree-editdistances
| translations | for | a Chinese | sentence |     | (in Pinyin | without |         |     |              |             |     |           |         |       |
| ------------ | --- | --------- | -------- | --- | ---------- | ------- | ------- | --- | ------------ | ----------- | --- | --------- | ------- | ----- |
|              |     |           |          |     |            |         | between |     | parse-trees, | string-edit |     | distances | between | event |
tones), with their word-to-word alignments in Figure 1. representationofparse-trees(Tangetal.,2002),andtree-
The reference translation for the Chinese sentence with kernels (Collins and Duffy, 2002). The computation of
| itsword-to-wordalignmentisshowninFigure2. |     |     |     |     |     | Inthis |     |     |     |     |     |     |     |     |
| ----------------------------------------- | --- | --- | --- | --- | --- | ------ | --- | --- | --- | --- | --- | --- | --- | --- |
tree-editdistanceinvolvesanunconstrainedalignmentof
section, we will show the computation of different loss the two English parse-trees. We can simplify this prob-
functionsforthisexample.
lemoncewehaveathirdparsetree(fortheChinesesen-
2.1 LexicalLossFunctions tence) with node-to-node alignment relative to the two
|           |       |         |           |     |      |             | English | trees. | We  | will | introducesuch | a   | loss functionin |     |
| --------- | ----- | ------- | --------- | --- | ---- | ----------- | ------- | ------ | --- | ---- | ------------- | --- | --------------- | --- |
| The first | class | of loss | functions |     | uses | no informa- |         |        |     |      |               |     |                 |     |
thenextsection.Wedidnotperformexperimentsinvolv-
| tion about | word | alignments |     | or parse-trees, |     | so that |     |     |     |     |     |     |     |     |
| ---------- | ---- | ---------- | --- | --------------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
ingthisclassoflossfunctions,butmentionthemforcom-
|     |     |     | canbereducedto |     |     | . We |     |     |     |     |     |     |     |     |
| --- | --- | --- | -------------- | --- | --- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
(cid:7)(cid:24) (cid:8)(cid:12) (cid:8)(cid:25) (cid:1)(cid:21) (cid:2)(cid:10) (cid:11)(cid:12) (cid:4)(cid:5) (cid:2)%(cid:13)(cid:20) (cid:11)(cid:16) (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12) (cid:4)(cid:18) (cid:13)(cid:20) (cid:19)(cid:23) (cid:0)(cid:21) (cid:13) (cid:7)(cid:24) (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12) (cid:1)(cid:3) (cid:2)((cid:13) pletenessinthehierarchyoflossfunctions.
considerthreelossfunctionsinthiscategory:TheBLEU
| score (Papineni |     | et al., | 2001), | word-error | rate, | and the |     |     |     |     |     |     |     |     |
| --------------- | --- | ------- | ------ | ---------- | ----- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
2.3 BilingualParse-TreeLossFunctions
| position-independent |     | word-error         |     | rate | (Och, | 2002). An- |      |          |            |         |           |                  |         |      |
| -------------------- | --- | ------------------ | --- | ---- | ----- | ---------- | ---- | -------- | ---------- | ------- | --------- | ---------------- | ------- | ---- |
|                      |     |                    |     |      |       |            | The  | third    | class      | of loss | functions | uses information |         | from |
| other example        |     | ofa lossfunctionin |     | this | class | is theMT-  |      |          |            |         |           |                  |         |      |
|                      |     |                    |     |      |       |            | word | strings, | alignments |         | and       | parse-trees      | in both | lan- |
evalmetricintroducedin Melamedetal. (2003). Aloss guages,andcanbedescribedby
| function     | of this | type depends |     | only on | information | from |                |                                                                         |                                                                                   |                                                                                                   |                                                            |                                                                                                                 |                                                                                      |                                              |
| ------------ | ------- | ------------ | --- | ------- | ----------- | ---- | -------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------- |
| wordstrings. |         |              |     |         |             |      |                |                                                                         |                                                                                   |                                                                                                   |                                                            |                                                                                                                 |                                                                                      | .                                            |
|              |         |              |     |         |             |      | (cid:7)(cid:5) | (cid:8)(cid:9) (cid:8)(cid:25) (cid:1)^ (cid:11)(cid:12) (cid:4)(cid:5) | (cid:13)(cid:15) (cid:11)(cid:16) (cid:8)(cid:10) (cid:1)(cid:21) (cid:2)(cid:22) | (cid:11)(cid:12) (cid:4)(cid:24) (cid:2)(cid:14)(cid:13)(cid:20) (cid:19)(cid:23) (cid:0)(cid:21) | (cid:13)Z :_ (cid:7)(cid:5) (cid:8)(cid:9) (cid:8)(cid:25) | (cid:26)‘ (cid:27)a (cid:11)(cid:12) (cid:4)(cid:5) (cid:13)(cid:15) (cid:11)(cid:16) (cid:8)(cid:25) (cid:26)‘ | (cid:27)O (cid:31)b (cid:11)(cid:23) (cid:4)(cid:24) (cid:2)(cid:14)(cid:13)(cid:20) | (cid:19)(cid:9) (cid:26)(cid:30) &’ (cid:13) |
BLEUscore (Papineni et al., 2001) computes the We will now describe one such loss function using the
geometric mean of the precision of -grams of vari- example in Figures 1 and 2. Figure 3 shows a tree-
)
ous lengths ( ) between a hypothesis and to-treemappingbetweenthesource(Chinese)parse-tree
|     | )+  | *- ,/ .1 | 0(024 3 |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | -------- | ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
a reference translation, and includes a brevity penalty andparse-treesofitsreferencetranslationandtwocom-
( )ifthehypothesisisshorterthantherefer- petinghypothesis(English)translations.
| 56 (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12) (cid:1)(cid:21) | (cid:2)(cid:14)(cid:13)8 79 . |     |     |     |     |     |     |     |     |     |     |     |     |     |
| ------------------------------------------------------------------- | ----------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

the first two months of this year guangdong ’s high−tech products 3.76 billion US dollars
E 1
 A1
jin−nian qian liangyue guangdong gao xinjishu chanpin chukou sanqidianliuyi meiyuan
F
A
2
E the first two months of this year guangdong exported high−tech products 3.76 billion US dollars
2
Figure1: TwocompetingEnglishtranslationsforaChinesesentencewiththeirword-to-wordalignments.
export of high−tech products in guangdong in first two months this year reached 3.76 billion US dollars
E
A
jin−nian qian liangyue guangdong gao xinjishu chanpin chukou sanqidianliuyi meiyuan
F
Figure2:ThereferencetranslationfortheChinesesentencefromFigure1withitsword-to-wordalignments.Wordsin
theChinese(English)sentenceshownasunalignedarealignedtotheNULLwordintheEnglish(Chinese)sentence.
Wefirstassumethatanode inthesourcetree can The Bilingual Parse-Tree (BiTree) Loss Function can
|                 |           |         |                         | )              |                        | (cid:26)                 | &   |                  |     |     |     |     |     |     |
| --------------- | --------- | ------- | ----------------------- | -------------- | ---------------------- | ------------------------ | --- | ---------------- | --- | --- | --- | --- | --- | --- |
| bemappedtoanode |           |         | in                      | (andanode      |                        | in )using                |     | thenbecomputedas |     |     |     |     |     |     |
|                 |           |         | (cid:0)                 |                | (cid:0)                |                          |     |                  |     |     |     |     |     |     |
|                 |           |         | (cid:26)                |                | (cid:2)                | (cid:26)(cid:24) (cid:2) |     |                  |     |     |     |     |     |     |
| word            | alignment |         | (and                    | respectively). | We                     | denote                   | the |                  |     |     |     |     |     |     |
|                 |           | (cid:4) | (cid:4)(cid:18) (cid:2) |                | (cid:1)(cid:3) (cid:2) |                          |     | BiTreeLoss       |     |     |     |     |     |     |
subtreeof rooted at node by andthe subtree of (cid:18)(cid:19) (cid:18)(cid:21)(cid:20)(cid:23) (cid:22)(cid:25) (cid:24)(cid:4) (cid:26)(cid:28) (cid:27)(cid:3) (cid:24)(cid:29) (cid:18)(cid:21)(cid:20) (cid:22) (cid:31) (cid:24)(cid:4) (cid:26)(cid:31) (cid:30) (cid:27)(cid:3) !" (cid:20)(cid:23) #$ (cid:27)$ %’ & (cid:18)(cid:21)2(cid:19) 34 (cid:24)" 2" (cid:30)3 (cid:31) (cid:27)(cid:3) (cid:24)
|                          |             |      |            | (cid:0)          |          |          |     |     |     |     |     | (* ), | -/+ .1 0 |     |
| ------------------------ | ----------- | ---- | ---------- | ---------------- | -------- | -------- | --- | --- | --- | --- | --- | ----- | -------- | --- |
| rooted                   | at (cid:26) | node | by (cid:1) | (cid:2) . We     | will now | describe | a   |     |     |     |     |       |          |     |
|                          |             |      | (cid:0)    |                  |          |          |     |     |     |     |     |       |          | (1) |
| (cid:26)(cid:24) (cid:2) |             |      | (cid:2)    | (cid:2) (cid:31) |          |          |     |     |     |     |     |       |          |     |
simple procedure that makes use of the word alignment where (cid:1) (cid:1) is a distance measure between sub-trees
5
| toconstructnode-to-nodealignmentbetweennodesin |     |     |     |     |     |     |     | (cid:1) (cid:1) (cid:8) (cid:11) | (cid:2)%(cid:13) |         |                |     |                |     |
| ---------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | -------------------------------- | ---------------- | ------- | -------------- | --- | -------------- | --- |
|                                                |     |     |     |     |     |     |     | and . Specific                   |                  | Bi-tree | loss functions |     | are determined |     |
| (cid:4)                                        |     |     |     |     |     |     |     | (cid:2)                          |                  |         |                |     |                |     |
thesourcetree andthetargettree . through particular choices of . In our experiments, we
|     |     | (cid:26)(cid:28) & |     |     | (cid:26) |     |     |                                      |     |     | 5   |     |         |         |
| --- | --- | ------------------ | --- | --- | -------- | --- | --- | ------------------------------------ | --- | --- | --- | --- | ------- | ------- |
|     |     |                    |     |     |          |     |     |                                      |     |     |     |     | (cid:1) | (cid:1) |
|     |     |                    |     |     |          |     |     | useda0/1lossfunctionbetweensub-trees |     |     |     |     | and     | .       |
(cid:2)
|     |     |     |     |     |     |     |     |     |     |     | (cid:1) | (cid:1) |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ------- | ------- | --- | --- |
2.3.1 AlignmentofParse-Trees
|     |     |     |     |     |     |     |     |     | (cid:1) | (cid:1) |             | (cid:9)   |     | (2) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ------- | ------- | ----------- | --------- | --- | --- |
|     |     |     |     |     |     |     |     |     | 5       | 7 6     | . otherwise | : (cid:2) |     |     |
(cid:8) (cid:11) (cid:2)(cid:13)’ :
| Foreachnode |     |     | inthesourcetree |     | weconsiderthe |     |     |     |     |     | W   |     | 0   |     |
| ----------- | --- | --- | --------------- | --- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
(cid:1) ) (cid:26) & We note that other tree-to-tree distance measures can
| subtree | rootedat |     | . Wefirstreadoffthesourceword |     |         |     |     |     |     |     |     |     |     |     |
| ------- | -------- | --- | ----------------------------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|         | K        |     | )                             |     | (cid:1) |     |     |     |     |     |     |     |     |     |
sequencecorrespondingtotheleavesof . Wenextcon- also be used to compute 5 , e.g. the distance function
|     |     |     |     |     | K   |     |     |     |     |     | (cid:1) | (cid:1) |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ------- | ------- | --- | --- |
sider the subset of words in the target sentence that are could compare if the subtrees and have the same
|         |        |      |         |        |                |     |     | headword/non-terminaltag. |     |     |     | (cid:2) |     |     |
| ------- | ------ | ---- | ------- | ------ | -------------- | --- | --- | ------------------------- | --- | --- | --- | ------- | --- | --- |
| aligned | to any | word | in this | source | word sequence, |     | and |                           |     |     |     |         |     |     |
select the leftmost and rightmost words from this sub- The Bitree loss function measures the distance be-
|     |     |     |     |     |     |     |     | tween two trees | in  | termsof | distances | betweentheir |     | cor- |
| --- | --- | --- | --- | --- | --- | --- | --- | --------------- | --- | ------- | --------- | ------------ | --- | ---- |
set. Welocatetheleafnodescorrespondingtothesetwo
wordsinthetargetparsetree ,andobtaintheirclosest responding subtrees. In this way, we replace the string-
commonancestornode (cid:26) . Thisproceduregivesus to-string(Levenshtein)alignments(forWER)or -gram
|     |     |     | (cid:0) |     |     |     |     |     |     |     |     |     |     | )   |
| --- | --- | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
* (cid:26) matches (for BLEU/PER) with subtree-to-subtree align-
| amappingfromanode |            |     |             | toanode            | (cid:0) | andthis     |     |        |     |     |     |     |     |     |
| ----------------- | ---------- | --- | ----------- | ------------------ | ------- | ----------- | --- | ------ | --- | --- | --- | --- | --- | --- |
|                   |            |     | ) *         | (cid:26)(cid:28) & | ;       | * (cid:26)  |     |        |     |     |     |     |     |     |
| mapping           | associates |     | one subtree | (cid:1)            | to      | one subtree |     | ments. |     |     |     |     |     |     |
K
(cid:1)(cid:4) (cid:2) * (cid:26)(cid:30) & TheBitreeErrorRate(in%)iscomputedasaratioof
.
* (cid:26)
|     |     |     |     |     |     |     |     | the Bi-tree | Loss function |     | to the | number | of nodes | in the |
| --- | --- | --- | --- | --- | --- | --- | --- | ----------- | ------------- | --- | ------ | ------ | -------- | ------ |
(cid:5)
|     |     |     |     |     |     |     |     | set .      |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ---------- | --- | --- | --- | --- | --- | --- |
|     |     |     |     |     |     |     |     | 2(cid:6) & |     |     |     |     |     |     |
2.3.2 LossComputationbetweenAligned The complete node-to-node alignment between the
Parse-Trees
parse-treeofthesource(Chinese)sentenceandtheparse
|       |                                    |         |           |         |                    |          |       | trees of its | reference | translation |          | and the | two hypothesis |        |
| ----- | ---------------------------------- | ------- | --------- | ------- | ------------------ | -------- | ----- | ------------ | --------- | ----------- | -------- | ------- | -------------- | ------ |
| Given | the                                | subtree | alignment | between |                    | and      | , and |              |           |             |          |         |                |        |
|       |                                    |         |           |         | (cid:26)(cid:28) & | (cid:26) |       | translations | (English) | is          | given in | Table   | 1. Each        | row in |
| and   | ,wefirstidentifythesubsetofnodesin |         |           |         |                    |          | for   |              |           |             |          |         |                |        |
thistableshowsthealignmentbetweenanodeintheChi-
| which (cid:26)(cid:30) & | we (cid:26) (cid:2) can | identify | a corresponding |     | node | in both (cid:26)  | &   |     |     |     |     |     |     |     |
| ------------------------ | ----------------------- | -------- | --------------- | --- | ---- | ----------------- | --- | --- | --- | --- | --- | --- | --- | --- |
neseparse-treeandnodesinthereferenceandthetwohy-
(cid:26)
and .
(cid:26)(cid:24) (cid:2) pothesisparse-trees. ThecomputationoftheBitreeLoss
functionandtheBitreeErrorRateispresentedinthelast
(cid:5)
tworowsofthetable.
|     |          |        | (cid:7)                | (cid:6)(cid:8) (cid:0)(cid:10) (cid:9)(cid:12) (cid:11)(cid:14) | (cid:13)(cid:15) (cid:0) (cid:16) (cid:9)(cid:17) (cid:11) |      |     |     |     |     |     |     |     |     |
| --- | -------- | ------ | ---------------------- | --------------------------------------------------------------- | ---------------------------------------------------------- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
|     | 2(cid:6) | & : ,# | ) * (cid:26)(cid:30) & | :                                                               | (cid:2) :                                                  | 3/ 0 |     |     |     |     |     |     |     |     |

: ReferenceTranslation(English)
S
(cid:26)
|     |     |     |     |     |               |          | NP1     |           |        |         | VP1  |          |            |
| --- | --- | --- | --- | --- | ------------- | -------- | ------- | --------- | ------ | ------- | ---- | -------- | ---------- |
|     |     |     |     |     | NP2           | PP1      |         |           | PP2    | VBD1    |      | NP9      |            |
|     |     |     |     |     | NN1 IN1       | NP3      |         | IN3       | NP6    | reached | CD2  | CD3 NNP2 | NNS3       |
|     |     |     |     |     | export of NP4 |          | PP2     | in NP7    |        | NP8     | 3.76 | billion  | US dollars |
|     |     |     |     |     | JJ1           | NNS1     | IN2 NP5 | JJ2 CD1   | NNS2   | DT1     | NN2  |          |            |
|     |     |     |     |     | high-tech     | products | in NNP1 | first two | months | this    | year |          |            |
guangdong
: SourceSentence(Chinese)
VP1
(cid:26)‘ &
|             |      |                  |     |          | LCP1          |           |           |               | VP2     |        |                |      |                    |
| ----------- | ---- | ---------------- | --- | -------- | ------------- | --------- | --------- | ------------- | ------- | ------ | -------------- | ---- | ------------------ |
|             |      |                  |     | NP1      | LC1           | VV1       |           | NP2           |         |        |                | QP1  |                    |
|             |      |                  |     | NT1      | qian liangyue |           | NP3       | ADJP1         | NP3     |        |                | CD1  | CLP1               |
|             |      |                  |     | jin-nian |               |           | NR2       | JJ1 NN1       | NN2     | NN3    | sanqidianliuyi |      | M1                 |
|             |      |                  |     |          |               | guangdong |           | gao xinjishu  | chanpin | chukou |                |      | meiyuan            |
|             |      | S                |     |          |               |           |           |               |         | NP1    |                |      |                    |
|             | NP1  |                  |     | VP1      |               |           | NP2       |               | PP1     |        |                |      | NP4 NP5            |
| NP2         |      | PP1 VBD1         |     | NP4      | NP5           |           | DT1 JJ1   | CD1 NNS1 IN1  |         | NP3    |                |      | QP1 NNP2 NNS3      |
|             |      |                  |     |          |               |           | the first | two months of | DT2 NN1 | NP4    | JJ2            | NNS2 | CD2 CD3 US dollars |
| DT1 JJ1 CD1 | NNS1 | IN1 NP3 exported | JJ2 | NNS2     | CD1 CD2 NNP2  | NNS3      |           |               |         |        |                |      |                    |
the first two months of DT2 NN1 NNP1 high-tech products 3.76 billion US dollars this year NNP1 POS1 high-tech products 3.76 billion
Guangdong ’s
|     |     | this year Guangdong |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | ------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
: HypothesisTranslation2(English)
: HypothesisTranslation1(English)
|     | (cid:26) | N   |     |     |     |     |     | (cid:26)(cid:1) (cid:0) |     |     |     |     |     |
| --- | -------- | --- | --- | --- | --- | --- | --- | ----------------------- | --- | --- | --- | --- | --- |
Figure 3: An example showing a parse-tree for a Chinese sentence and parse-trees for its reference translation and
twocompetinghypothesistranslations. WeshowasamplealignmentforoneofthenodesintheChinesetreewithits
correspondingnodesinthethreeEnglishtrees. Thecompletenode-to-nodealignmentbetweentheparse-treesofthe
ChinesesentenceandthethreeEnglishsentencesisgiveninTable1.

Node (cid:20)(cid:23) # Node (cid:20) Node (cid:20) (cid:18)(cid:21)2(cid:19) 3 (cid:24)" 2(cid:19) 3 (cid:27) Node (cid:20) , (cid:18)(cid:21)2" 3 (cid:24)" 2 (cid:30)3 (cid:27)
(cid:0)(cid:2) (cid:1) (cid:3)(cid:4) (cid:1) (cid:3)(cid:6) (cid:5)(cid:7) (cid:1) (cid:8) (cid:5) (cid:9) (cid:7) (cid:10) (cid:3)(cid:12) (cid:11)(cid:13) (cid:1) (cid:14) (cid:11) (cid:9) (cid:16) (cid:15)
|     |                    | VP1        |     | S         |     | S                 |                           | 1          | NP1       |                                     | 1          |     |     |
| --- | ------------------ | ---------- | --- | --------- | --- | ----------------- | ------------------------- | ---------- | --------- | ----------------------------------- | ---------- | --- | --- |
|     |                    | LCP        |     | NP6       |     | NP1               |                           | 1          | NP1       |                                     | 1          |     |     |
|     |                    | NP1        |     | NP8       |     | NP3               |                           | 1          | NP3       |                                     | 1          |     |     |
|     |                    | NT1        |     | NP8       |     | NP3               |                           | 1          | NP3       |                                     | 1          |     |     |
|     |                    | jin-nian   |     | NP8       |     | NP3               |                           | 1          | NP3       |                                     | 1          |     |     |
|     |                    | LC1        |     | first     |     | NP1               |                           | 1          | NP2       |                                     | 1          |     |     |
|     |                    | qian       |     | first     |     | NP1               |                           | 1          | NP2       |                                     | 1          |     |     |
|     |                    | VP2        |     | S         |     | S                 |                           | 1          | NP1       |                                     | 1          |     |     |
|     |                    | VV         |     | NP7       |     | NP2               |                           | 1          | NP2       |                                     | 1          |     |     |
|     |                    | liangyue   |     | NP7       |     | NP2               |                           | 1          | NP2       |                                     | 1          |     |     |
|     |                    | NP2        |     | S         |     | S                 |                           | 1          | NP1       |                                     | 1          |     |     |
|     |                    | NP3        |     | Guangdong |     | Guangdong         |                           | 0          | NP4       |                                     | 1          |     |     |
|     |                    | NR2        |     | Guangdong |     | Guangdong         |                           | 0          | NP4       |                                     | 1          |     |     |
|     |                    | guangdong  |     | Guangdong |     | Guangdong         |                           | 0          | NP4       |                                     | 1          |     |     |
|     |                    | ADJP1      |     | reached   |     | high-tech         |                           | 1          | high-tech |                                     | 1          |     |     |
|     |                    | JJ1        |     | reached   |     | high-tech         |                           | 1          | high-tech |                                     | 1          |     |     |
|     |                    | gao        |     | reached   |     | high-tech         |                           | 1          | high-tech |                                     | 1          |     |     |
|     |                    | NP3        |     | NP1       |     | VP1               |                           | 1          | NP3       |                                     | 1          |     |     |
|     |                    | NN2        |     | products  |     | products          |                           | 0          | products  |                                     | 0          |     |     |
|     |                    | chanpin    |     | products  |     | products          |                           | 0          | products  |                                     | 0          |     |     |
|     |                    | NN3        |     | export    |     | exported          |                           | 1          | products  |                                     | 1          |     |     |
|     |                    | chukou     |     | export    |     | exported          |                           | 1          | products  |                                     | 1          |     |     |
|     |                    | QP1        |     | NP9       |     | NP5               |                           | 0          | NP1       |                                     | 1          |     |     |
|     |                    | CLP1       |     | NP9       |     | NP5               |                           | 0          | NP1       |                                     | 1          |     |     |
|     |                    | M1         |     | NP9       |     | NP5               |                           | 0          | NP1       |                                     | 1          |     |     |
|     |                    | meiyuan    |     | NP9       |     | NP5               |                           | 0          | NP1       |                                     | 1          |     |     |
|     |                    | BiTreeLoss |     |           |     | Loss              |                           | 17         | Loss      |                                     | 24         |     |     |
|     |                    |            |     |           |     | (cid:18)          | (cid:24) (cid:27)         |            | (cid:18)  | (cid:24) (cid:27)                   |            |     |     |
|     |                    |            |     |           |     | (cid:18) (cid:17) | (cid:19) (cid:17) (cid:5) |            | (cid:18)  | (cid:17) (cid:20) (cid:17) (cid:11) |            |     |     |
|     | BiTreeErrorRate(%) |            |     |           |     |                   |                           | 17/26=65.4 |           |                                     | 24/26=92.3 |     |     |
Table1: Bi-TreeLossComputationfortheparse-treesshowninFigure3.Eachrowshowsamappingbetweenanode
intheparse-treeoftheChinesesentenceandthenodesinparse-treesofitsreferencetranslation,hypothesistranslation
1andhypothesistranslation2.
| 2.4 | ComparisonofLossFunctions |     |     |     |     |     |     | LossFunctions |     |                                                 |                                                     |                                                                                   |     |
| --- | ------------------------- | --- | --- | --- | --- | --- | --- | ------------- | --- | ----------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------- | --- |
|     |                           |     |     |     |     |     |     |               |     | (cid:7)(cid:24) (cid:8)(cid:10) (cid:1)(cid:17) | (cid:11)(cid:12) (cid:1) N (cid:13) (cid:7)(cid:24) | (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12) (cid:1) (cid:16)(cid:0) (cid:13) |     |
|     |                           |     |     |     |     |     |     | BLEU(%)       |     | 26.4                                            |                                                     | 26.4                                                                              |     |
|     |                           |     |     |     |     |     |     | WER(%)        |     | 70.6                                            |                                                     | 70.6                                                                              |     |
InTable2wecomparevarioustranslationlossfunctions
|     |     |     |     |     |     |     |     | PER(%) |     | 23.5 |     | 23.5 |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------ | --- | ---- | --- | ---- | --- |
fortheexamplefromFigure1.Thetwohypothesistrans-
|     |     |     |     |     |     |     | BiTreeErrorRate(%) |     |     | 65.4 |     | 92.3 |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------ | --- | --- | ---- | --- | ---- | --- |
lationsareverysimilaratthewordlevelandthereforethe
| BLEU | score,PERandtheWERare |     |     | identical. |     | However |       |               |     |               |      |           |     |
| ---- | --------------------- | --- | --- | ---------- | --- | ------- | ----- | ------------- | --- | ------------- | ---- | --------- | --- |
|      |                       |     |     |            |     |         | Table | 2: Comparison | of  | the different | loss | functions | for |
weobservethatthesentencesdiffersubstantiallyintheir
hypothesisandreferencetranslationsfromFigures1,2.
syntacticstructure(asseenfromParse-TreesinFigure3),
| and to      | a lesser | extent        | in their  | word-to-word              | alignments                                  |          |     |         |                    |     |     |     |     |
| ----------- | -------- | ------------- | --------- | ------------------------- | ------------------------------------------- | -------- | --- | ------- | ------------------ | --- | --- | --- | --- |
| (Figure     | 1)       | to the source | sentence. | The                       | first hypothesis                            |          |     |         |                    |     |     |     |     |
|             |          |               |           |                           |                                             |          | 3   | Minimum | Bayes-RiskDecoding |     |     |     |     |
| translation |          | isparsedasa   | sentence  |                           |                                             | while    |     |         |                    |     |     |     |     |
|             |          |               |           | (cid:21)(cid:23) (cid:22) | (cid:25)2 (cid:24)(cid:27) (cid:26)(cid:28) | (cid:24) |     |         |                    |     |     |     |     |
thesecondtranslationisparsedasanounphrase.TheBi-
|     |     |     |     |     |     |     | StatisticalMachine |     | Translation(Brownetal., |     |     | 1990)can |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------ | --- | ----------------------- | --- | --- | -------- | --- |
treelossfunctionwhichdependsbothontheparse-trees be formulated as a mapping of a word sequence in a
(cid:0)
andtheword-to-wordalignments,isthereforeverydiffer- source language to word sequence in the target lan-
entforthetwotranslations(Table2). Whilestringbased (cid:1)(cid:3) (cid:2)
|     |     |     |     |     |     |     | guagethathasaword-to-wordalignment |     |     |     |                 | relativeto | .       |
| --- | --- | --- | --- | --- | --- | --- | ---------------------------------- | --- | --- | --- | --------------- | ---------- | ------- |
|     |     |     |     |     |     |     |                                    |     |     |     | (cid:4)(cid:18) | (cid:2)    | (cid:0) |
metricssuchasBLEU,WERandPERareinsensitiveto Giventhesourcesentence ,theMTdecoder pro-
thesyntacticstructureofthetranslations,BiTreeLossis duces a target word string (cid:0) with word-to-word (cid:29) (cid:8)(cid:25) (cid:0)(cid:21) align- (cid:13)
(cid:1)(cid:6) (cid:2)
abletomeasurethisaspectoftranslationquality,andas- ment . Relativetoareferencetranslation withword
|     |     |     |     |     |     |     |     | (cid:4)(cid:5) (cid:2) |     |     |     | (cid:1) |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ---------------------- | --- | --- | --- | ------- | --- |
signsdifferentscorestothetwotranslations. alignment , the decoder performance is measured as
(cid:4)
|     |     |     |     |     |     |     |                                 |                                                                                                                                                             | . Ourgoalistofindthedecoderthathas |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | --- | --- | --- | --- |
|     |     |     |     |     |     |     | (cid:7)(cid:24) (cid:8)(cid:12) | (cid:8)(cid:25) (cid:1)(cid:17) (cid:11)(cid:23) (cid:4)(cid:5) (cid:13)(cid:15) (cid:30)(cid:11) (cid:29) (cid:8)(cid:25) (cid:0)(cid:21) (cid:13)(cid:12) | (cid:13)                           |     |     |     |     |
We providethisexampletoshowhowa lossfunction the best performance over all translations. This is mea-
suredthroughBayes-Risk:
| which  | makes | use of     | syntactic | structure from | source          | and |     |     |     |     |     |     |     |
| ------ | ----- | ---------- | --------- | -------------- | --------------- | --- | --- | --- | --- | --- | --- | --- | --- |
| target | parse | trees, can | capture   | properties     | of translations |     |     |     |     |     |     |     |     |
thatstringbasedlossfunctionsareunabletomeasure.
(cid:31)
|     |     |     |     |     |     |     |     |  (cid:8) (cid:29) (cid:8)(cid:25) (cid:0)(cid:21) (cid:13)(cid:9) | (cid:13)? := "(cid:1) !$ #$(cid:27) | %&’ %)& (+ (cid:7)(cid:24)* | (cid:8)(cid:12) (cid:8)(cid:25) (cid:1)(cid:17) (cid:11)(cid:23) (cid:4)(cid:5) (cid:13)(cid:20) ,(cid:11) | (cid:29) (cid:8)(cid:25) (cid:0)(cid:21) (cid:13)(cid:12) (cid:19)(cid:13) - | 0   |
| --- | --- | --- | --- | --- | --- | --- | --- | ----------------------------------------------------------------- | ----------------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | --- |

The expectation is taken under the true distribution
(cid:24)(cid:17) (cid:8)(cid:25) (cid:1)^ (cid:11)(cid:12) (cid:4)(cid:21) (cid:11)(cid:23) (cid:0)(cid:21) (cid:13)
thatdescribestranslationsofhumanquality.
Given a loss function and a distribution, it is well
known that the decision rule that minimizes the Bayes-
Risk is given by (Bickel and Doksum, 1977; Goel and
Byrne,2000):
(cid:29) (cid:8)(cid:10) (cid:0)(cid:21) (cid:13)Z
(cid:1)
:
(cid:0)(cid:3) (cid:2)(cid:5)
(cid:27)
(cid:4)(cid:7) (cid:6)(cid:9)
%& (cid:31)
(cid:8)(cid:11)(cid:10)
(cid:31)
J
$(cid:27) %&
(cid:7)(cid:5) (cid:8)(cid:9) (cid:8)(cid:25) (cid:1)^ (cid:11)(cid:12) (cid:4)(cid:5) (cid:13)(cid:15) (cid:11)(cid:16) (cid:8)(cid:10) (cid:1) (cid:2) (cid:11)(cid:12) (cid:4) (cid:2)(cid:13)(cid:20) (cid:19)(cid:23) (cid:0)(cid:21) (cid:20)(cid:13) (cid:24)(cid:17) (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12)
(cid:13)
(cid:4)
(cid:12)
(cid:0)(cid:21) (cid:13)(cid:15) 0
(3)
We shall refer to the decoder given by this equation
astheMinimumBayes-Risk(MBR)decoder. TheMBR
decodercanbethoughtofasselectingaconsensustrans-
lation: Foreachsentence
(cid:0)
,Equation3selectsthetrans-
lationthatisclosestonanaveragetoallthelikelytrans-
lationsandalignments. Theclosenessismeasuredunder
thelossfunctionofinterest.
This optimal decoder has the difficulties of search
(minimization)andcomputingtheexpectationunderthe
truedistribution. Inpractice, we willconsiderthe space
oftranslationstobean
2
-bestlistoftranslationalterna-
tives generated under a baseline translation model. Of
course, we do not have access to the true distribution
over translations. We therefore use statistical transla-
tionmodels (Och, 2002)to approximatethe distribution
(cid:24)(cid:17) (cid:8)(cid:25) (cid:1)^ (cid:11)(cid:12)
(cid:14)
(cid:4)
(cid:12)
(cid:0)(cid:21) (cid:13)
.
DecoderImplementation: The MBR decoder (Equa-
tion3)onthe
2
-bestListisimplementedas
(cid:15)(cid:16)
% (cid:28) (cid:30) )
(cid:17)(cid:19)
(cid:29)
(cid:18)(cid:21)
(cid:5)
(cid:20)(cid:23) (cid:22)(cid:25) (cid:24)(cid:27)(cid:26)
$ (cid:31)! (cid:31)"""(cid:31)-
(cid:11)
# &%!
-
&
(cid:5)
(cid:9) (cid:18)(cid:19) (cid:18) (cid:18) (cid:17)
%
(cid:24) (cid:26)
%
(cid:27)(cid:3) (cid:24) (cid:18) (cid:18) (cid:17)
(cid:28)
(cid:24) (cid:26)
(cid:28)
(cid:27)(cid:19)
(
(cid:27)
’
(cid:18) (cid:18) (cid:17)
%
(cid:24)(cid:4) (cid:26)
%(cid:3) )*
(cid:27)
and + * (cid:18) * (cid:27) % (cid:18)
(cid:18)
-
(cid:17)
(cid:28), (cid:24)(cid:4) . (cid:26) (cid:28), (cid:27) . This is a rescoring procedure that
searchesfor consensusundera givenlossfunction. The
posteriorprobabilityofeachhypothesisinthe
2
-bestlist
isderivedfromthejointprobabilityassignedbythebase-
linetranslationmodel.
(cid:24)(cid:17) (cid:8)(cid:12) (cid:8)(cid:25)
0
(cid:1)
/
/ (cid:11)(cid:12)
.
(cid:4)
/
#
1
(cid:13)
(cid:12)
(cid:0)(cid:21) (cid:13)’ :
2 3(cid:24)(cid:17)
H
LO
(cid:8)(cid:25)
N
0 (cid:1)
(cid:24)(cid:17)
/ / . (cid:11)(cid:12) (cid:4)
(cid:8)(cid:25) (cid:1)
/ 3 1
(cid:11)(cid:12)
(cid:11)(cid:23)
(cid:4)
(cid:0)(cid:21) 3 (cid:13)
(cid:11)(cid:23) (cid:0)(cid:21) (cid:13)
0
(4)
The conventional Maximum A Posteriori (MAP) de-
coder can be derived as a special case of the MBR de-
coderbyconsideringalossfunctionthatassignsaequal
cost (say 1) to all misclassifications. Under the 0/1 loss
function,
(cid:7)(cid:24) (cid:8)(cid:9) (cid:8)(cid:10) (cid:1)(cid:17) (cid:11)(cid:12) (cid:4)(cid:18) (cid:13)(cid:20) (cid:11)# (cid:8)(cid:25) (cid:1) (cid:2) (cid:11)(cid:12) (cid:4) (cid:2)(cid:13)(cid:12) (cid:13)Z : 6 W
if
.
(cid:1)X :C (cid:1)(cid:21)
5
(cid:2)
4
(cid:4)C :_ (cid:4)(cid:24) (cid:2) otherwise,
(5)
thedecoderofEquation3reducestotheMAPdecoder
(cid:29)
MAP
(cid:8)(cid:10) (cid:0)(cid:21) (cid:13)Z
6
:
(cid:0)(cid:7) (cid:2)! (cid:4)5
#(cid:27)
(cid:6)7
(cid:31) %&
(cid:0)(cid:30) 8
(cid:31)(
(cid:24)(cid:17) (cid:8)(cid:10) (cid:1) (cid:2) (cid:11)(cid:12) (cid:4) (cid:2)
(cid:12)
(cid:0)(cid:21) (cid:13)(cid:20) 0
doesnotdistinguishbetweendifferenttypesoftranslation
errors and good translationsreceivethe same penalty as
poortranslations.
4 PerformanceofMBRDecoders
We performedourexperimentsontheLarge-DataTrack
of the NIST Chinese-to-English MT task (NIST, 2003).
The goal of this task is the translation of news stories
fromChinesetoEnglish. Thetestsethasatotalof1791
sentences, consisting of 993 sentences from the NIST
2001MT-evalsetand878sentencesfromtheNIST2002
MT-evalset. Each Chinese sentence in this set has four
referencetranslations.
4.1 EvaluationMetrics
Theperformanceofthebaselineandthe MBRdecoders
underthedifferentlossfunctionswasmeasuredwithre-
spect to the four reference translations provided for the
test set. Four evaluation metrics were used. These
were multi-reference Word Error Rate (mWER) (Och,
2002), multi-reference Position-independent word Error
Rate (mPER) (Och, 2002) , BLEU and multi-reference
BiTreeErrorRate.
Among these evaluation metrics, the BLEU score
directly takes into account multiple reference transla-
tions(Papinenietal.,2001). Incaseoftheothermetrics,
weconsidermultiplereferencesinthefollowingway.For
eachsentence,wecomputetheerrorrateofthehypothe-
sis translation with respectto the mostsimilar reference
translationunderthecorrespondinglossfunction.
4.2 DecoderPerformance
In our experiments, a baseline translation model (JHU,
2003), trained on a Chinese-English parallel cor-
pus(NIST,2003)(
(6)
ThisillustrateswhyweareinterestedinMBRdecoders
basedonotherlossfunctions: theMAPdecoderisopti-
mal with respectto a loss function that is veryharsh. It
:
.
9
M
5
W
; Englishwordsand (cid:23)
.
<5 9(cid:7) ; Chi-
nese words), was used to generate 1000-best translation
hypothesesforeachChinesesentenceinthetestset. The
1000-best lists were then rescored using the different
translationlossfunctionsdescribedinSection2.
TheEnglishsentencesinthe
2
-bestlistswereparsed
usingtheCollinsparser(Collins,1999),andtheChinese
sentenceswereparsedusingaChineseparserprovidedto
us by D. Bikel (Bikel and Chiang, 2000). The English
parserwastrainedonthePennTreebankandtheChinese
parseronthePennChinesetreebank.
Undereachlossfunction,theMBRdecodingwasper-
formed using Equation 3. We say we have a matched
conditionwhenthesamelossfunctionisusedinboththe
error rate and the decoder design. The performance of
theMBRdecodersontheNIST2001+2002testsetisre-
portedinTable3. Forallperformancemetrics,weshow
the 70% confidence interval with respect to the MAP
baseline computed using bootstrap resampling (Press et
al.,2002;Och,2003).Wenotethatthissignificancelevel

does meet the customary criteria for minimum signifi- We present results under the Bitree loss function as
canceintervalsof68.3%(Pressetal.,2002). an example of incorporating linguistic information into
WeobserveinmostcasesthattheMBRdecoderunder a loss function; we have not yet measured its correla-
a loss function performs the best under the correspond- tionwithhumanassessmentsoftranslationquality. This
ingerrormetrici.e.matchedconditionsperformthebest. lossfunctionallowsustointegratesyntacticstructureinto
ThegainsfromMBRdecodingundermatchedconditions the statistical MT framework without building detailed
arestatisticallysignificantinmostcases.Wenotethatthe modelsof syntactic featuresand retrainingmodels from
MAPdecoderisnotoptimalinanyofthecases.Inpartic- scratch. However, we emphasize that the MBR tech-
ular,thetranslationperformanceundertheBLEUmetric niquesdonotprecludetheconstructionofcomplexmod-
canbeimprovedbyusingMBRrelativetoMAPdecod- els of syntactic structure. Translation models that have
ing. Thisshowsthevalueoffindingdecodingprocedure beentrainedwithlinguisticfeaturescouldstillbenefitby
matchedtotheperformancecriterionofinterest. theapplicationofMBRdecodingprocedures.
Wealsonoticesomeaffinityamongthelossfunctions. That machine translation evaluation continues to be
The MBR decoding under the Bitree Loss function per- an active area of research is evident from recent work-
formsbetterundertheWERrelativetotheMAPdecoder,
|     |     |     |     | shops (AMTA, | 2003). |     | We expect | new | automatic | MT  |
| --- | --- | --- | --- | ------------ | ------ | --- | --------- | --- | --------- | --- |
but perform poorly under the BLEU metric. The MBR evaluation metrics to emerge frequently in the future.
decoder under WER and PER perform better than the Givenanytranslation metric, the MBRdecoding frame-
MAPdecoderunderallerrormetrics. TheMBRdecoder work will allowus to optimize existing MT systems for
under BLEU loss function obtains a similar (or worse) thenewcriterion.Thisisintendedtocompensateforany
performancerelativetoMAPdecoderonallmetricsother mismatchbetweendecodingstrategyofMTsystemsand
thanBLEU. their evaluation criteria. While we have focused on de-
|     |     |     |     | veloping | MBR procedures |     | for | loss functions | that | mea- |
| --- | --- | --- | --- | -------- | -------------- | --- | --- | -------------- | ---- | ---- |
5 Discussion
|     |     |     |     | sure various | aspects | of  | translation | quality, | this | frame- |
| --- | --- | --- | --- | ------------ | ------- | --- | ----------- | -------- | ---- | ------ |
workcanalsobeusedwithlossfunctionswhichmeasure
| We have described | the formulation | of Minimum | Bayes- |     |     |     |     |     |     |     |
| ----------------- | --------------- | ---------- | ------ | --- | --- | --- | --- | --- | --- | --- |
application-specificerrorcriteria.
| Riskdecodersfor | machinetranslation. | Thisisa | general |     |     |     |     |     |     |     |
| --------------- | ------------------- | ------- | ------- | --- | --- | --- | --- | --- | --- | --- |
framework that allows us to build special purpose de- We now describe related training and search proce-
duresforNLPthatexplicitlytakeintoconsiderationtask-
codersfromgeneralpurposemodels.Theprocedureaims
atdirectminimizationoftheexpectedriskoftranslation specific performance metrics. Och(2003) developed a
|                                |     |                   |     | training procedure |     | that incorporates |     | various | MT  | evalua- |
| ------------------------------ | --- | ----------------- | --- | ------------------ | --- | ----------------- | --- | ------- | --- | ------- |
| errorsunderagivenlossfunction. |     | Inthispaperwehave |     |                    |     |                   |     |         |     |         |
focusedontwosituationswherethisframeworkcouldbe tion criteria in the training procedure of log-linear MT
| applied. |     |     |     | models. | Fosteretal. | (2002)developedatext-prediction |     |     |     |     |
| -------- | --- | --- | --- | ------- | ----------- | ------------------------------- | --- | --- | --- | --- |
systemfortranslatorsthatmaximizesexpectedbenefitto
| Given an | MT evaluation metric | of interest | such as |     |     |     |     |     |     |     |
| -------- | -------------------- | ----------- | ------- | --- | --- | --- | --- | --- | --- | --- |
BLEU, PER or WER, we can use this metric as a loss the translator under a statistical user model. In parsing,
|                |                    |                |     | Goodman(1996) |     | developed | parsing | algorithms |     | that are |
| -------------- | ------------------ | -------------- | --- | ------------- | --- | --------- | ------- | ---------- | --- | -------- |
| functionwithin | theMBR frameworkto | designdecoders |     |               |     |           |         |            |     |          |
optimized for the evaluation criterion. In particular, the appropriate for specific parsing metrics. There has also
MBR decoding underthe BLEU loss function can yield been recent work that combines 1-best hypotheses from
multipletranslationsystems(Bangaloreetal.,2002);this
furtherimprovementsontopofMAPdecoding.
Supposeweareinterestedinimprovingsyntacticstruc- approachusesstring-editdistancetoalignthehypotheses
andrescorestheresultinglatticewithalanguagemodel.
| ture of automatic | translations | and would like | to use an |     |     |     |     |     |     |     |
| ----------------- | ------------ | -------------- | --------- | --- | --- | --- | --- | --- | --- | --- |
existingstatisticalMTsystemthatistrainedwithoutany In future work we plan to extend the search space of
linguistic features. We have shown in such a situation MBR decoders to translation lattices produced by the
how MBR decoding can be applied to the MT system. baselinesystem.Translationlattices(Ueffingetal.,2002;
This can be done by the design of translation loss func- KumarandByrne,2003)areacompactrepresentationof
alargesetofmostlikelytranslationsgeneratedbyanMT
| tionsfromvariedlinguisticanalyzes. |     | Wehaveshownthe |     |     |     |     |     |     |     |     |
| ---------------------------------- | --- | -------------- | --- | --- | --- | --- | --- | --- | --- | --- |
construction of a Bitree loss function to compare parse- system. Whilean -bestlistcontainsonlyalimitedre-
2
trees of any two translations using alignments with re- ordering of hypotheses, a translation lattice will contain
hypotheseswithavastlygreaternumberofre-orderings.
| spect to a parse-tree | for the source | sentence. | The loss |     |     |     |     |     |     |     |
| --------------------- | -------------- | --------- | -------- | --- | --- | --- | --- | --- | --- | --- |
function therefore avoids the problem of unconstrained We aredevelopingefficientlatticesearchproceduresfor
|     |     |     |     | MBRdecoders. | Byextendingthesearchspaceofthede- |     |     |     |     |     |
| --- | --- | --- | --- | ------------ | --------------------------------- | --- | --- | --- | --- | --- |
tree-to-treealignment.Usinganexample,wehaveshown
that this loss function can measure qualities of transla- codertoamuchlargerspacethanthe -bestlist,weex-
2
tion that string (and ngram) based metrics cannot cap- pectfurtherperformanceimprovements.
ture. The MBR decoder under this loss function gives MBR is a promisingmodelingframeworkfor statisti-
improvements under an evaluation metric based on the cal machine translation. It is a simple model rescoring
lossfunction. framework that improves well-trained statistical models

PerformanceMetrics
Decoder BLEU(%) mWER(%) mPER(%) mBiTreeErrorRate(%)
70%ConfidenceIntervals +/-0.3 +/-0.9 +/-0.6 +/-1.0
MAP(baseline) 31.2 64.9 41.3 69.0
MBR
BLEU 31.5 65.1 41.1 68.9
WER 31.3 64.3 40.8 68.5
PER 31.3 64.6 40.4 68.6
BiTreeLoss 30.7 64.1 41.1 68.0
Table3: TranslationperformanceoftheMBRdecoderundervariouslossfunctionsontheNIST2001+2002Testset.
Foreachmetric,theperformanceunderamatchedconditionisshowninbold. Notethatbetterresultscorrespondto
higherBLEUscoresandtolowererrorrates.
bytuningthemforparticularcriteria.Thesecriteriacould G. Foster, P. Langlais, and G. Lapalme. 2002. User-
come from evaluation metrics or from other desiderata friendly text prediction for translators. In Proc. of
EMNLP,Philadelphia,PA,USA.
(such as syntactic well-formedness) that we wish to see
inautomatictranslations. V.GoelandW.Byrne. 2000. MinimumBayes-riskauto-
maticspeechrecognition. ComputerSpeechandLan-
Acknowledgments
guage,14(2):115–135.
Thisworkwasperformedaspartofthe2003JohnsHop-
J. Goodman. 1996. Parsing algorithms and metrics. In
kins Summer Workshop research group on Syntax for
Proc. of ACL-1996, pages 177–183, Santa Cruz, CA,
StatisticalMachineTranslation. Wewouldliketothank
USA.
all the group members for providing various resources
JHU. 2003. Syntax for statistical machine
and tools and contributing to useful discussions during
translation, Final report, JHU summer workshop.
thecourseoftheworkshop.
http://www.clsp.jhu.edu/ws2003/groups/translate/.
References
S. Kumar and W. Byrne. 2002. Minimum Bayes-Risk
AMTA. 2003. Workshop on Machine alignment of bilingual texts. In Proc. of EMNLP,
Translation Evaluation, MT Summit IX. Philadelphia,PA,USA.
www.issco.unige.ch/projects/isle/MTE-at-MTS9.html.
S. Kumar and W. Byrne. 2003. A weighted finite state
transducer implementation of the alignment template
S.Bangalore,V.Murdock,andG.Riccardi. 2002. Boot-
modelfor statisticalmachinetranslation. InProceed-
strappingbilingualdatausingconsensustranslationfor
ingsofHLT-NAACL,Edmonton,Canada.
a multilingual instantmessagingsystem. InProceed-
ingsofCOLING,Taipei,Taiwan. I.D.Melamed,R.Green,andJ.P.Turian. 2003. Preci-
sionandrecallofmachinetranslation. InProceedings
P. J. Bickel and K. A. Doksum. 1977. Mathematical oftheHLT-NAACL,Edmonton,Canada.
Statistics: Basic Ideas and Selected topics. Holden-
DayInc.,Oakland,CA,USA. NIST. 2003. The NIST Machine Translation Evalua-
tions. http://www.nist.gov/speech/tests/mt/.
D. Bikel and D. Chiang. 2000. Two statistical pars-
F. Och. 2002. Statistical Machine Translation: From
ing models applied to the chinese treebank. In Pro-
Single Word Models to Alignment Templates. Ph.D.
ceedingsoftheSecondChineseLanguageProcessing
thesis,RWTHAachen,Germany.
Workshop,pages1–6,HongKong.
F. Och. 2003. Minimumerrorratetraininginstatistical
P. F. Brown, J. Cocke, S. A. Della Pietra, V. J. Della machinetranslation. InProc.ofACL,Sapporo,Japan.
Pietra, F. Jelinek, J. D. Lafferty, R. L. Mercer, and
K. Papineni, S. Roukos, T. Ward, and W. Zhu. 2001.
P.S.Roossin. 1990. Astatisticalapproachtomachine
Bleu: a method for automatic evaluation of machine
translation. ComputationalLinguistics,16(2):79–85.
translation. TechnicalReportRC22176(W0109-022),
IBMResearchDivision.
M.CollinsandN.Duffy. 2002. Newrankingalgorithms
for parsing and tagging: Kernels over discrete struc- W.H.Press,S.A.Teukolsky,W.T.Vetterling,andB.P.
tures,andtheweightedperceptron. InProceedingsof Flannery. 2002. Numerical Recipes in C++. Cam-
EMNLP,Philadelphia,PA,USA. bridgeUniversityPress,Cambridge,UK.
M.J.Collins. 1999. Head-drivenStatisticalModelsfor M.Tang,X.Luo,andS.Roukos. 2002. Activelearning
NaturalLanguageParsing. Ph.D.thesis,Universityof forstatisticalnaturallanguageparsing. InProceedings
Pennsylvania,Philadelphia. ofACL2002,Philadelphia,PA,USA.
N. Ueffing, F. Och, and H. Ney. 2002. Generation of
G.Doddington. 2002. Automaticevaluationofmachine
wordgraphsinstatisticalmachinetranslation. InProc.
translation quality using n-gram co-occurrence statis-
ofEMNLP,pages156–163,Philadelphia,PA,USA.
tics. InProc.ofHLT2002,SanDiego,CA.USA.