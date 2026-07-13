---
type: source
source_type: paper
url: https://aclanthology.org/D19-1410.pdf
title: "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks"
fetched_at: 2026-06-17T15:17:31-05:00
fetcher: markitdown
---
Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks
NilsReimersandIrynaGurevych
UbiquitousKnowledgeProcessingLab(UKP-TUDA)
DepartmentofComputerScience,TechnischeUniversita¨tDarmstadt
www.ukp.tu-darmstadt.de
|     |     | Abstract |     |     |     | ticsimilaritycomparison,clustering,andinforma- |     |     |     |     |     |     |
| --- | --- | -------- | --- | --- | --- | ---------------------------------------------- | --- | --- | --- | --- | --- | --- |
tionretrievalviasemanticsearch.
BERT(Devlinetal.,2018)andRoBERTa(Liu BERT set new state-of-the-art performance on
| et al., | 2019) | has | set a new | state-of-the-art |     |         |          |                |     |     |                   |     |
| ------- | ----- | --- | --------- | ---------------- | --- | ------- | -------- | -------------- | --- | --- | ----------------- | --- |
|         |       |     |           |                  |     | various | sentence | classification |     |     | and sentence-pair |     |
performanceonsentence-pairregressiontasks
|       |             |         |            |           |         | regressiontasks. |        | BERTusesacross-encoder: |               |                 |          | Two     |
| ----- | ----------- | ------- | ---------- | --------- | ------- | ---------------- | ------ | ----------------------- | ------------- | --------------- | -------- | ------- |
| like  | semantic    | textual | similarity | (STS).    | How-    |                  |        |                         |               |                 |          |         |
|       |             |         |            |           |         | sentences        | are    | passed                  | to            | the transformer |          | network |
| ever, | it requires | that    | both       | sentences | are fed |                  |        |                         |               |                 |          |         |
|       |             |         |            |           |         | and the          | target | value                   | is predicted. |                 | However, | this    |
intothenetwork,whichcausesamassivecom-
putational overhead: Finding the most sim- setupisunsuitableforvariouspairregressiontasks
ilar pair in a collection of 10,000 sentences due to too many possible combinations. Finding
requires about 50 million inference computa- in a collection of n = 10000 sentences the pair
tions(~65hours)withBERT.Theconstruction with the highest similarity requires with BERT
ofBERTmakesitunsuitableforsemanticsim-
|     |     |     |     |     |     | n·(n−1)/2 | =   | 49995000inferencecomputations. |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --------- | --- | ------------------------------ | --- | --- | --- | --- |
ilaritysearchaswellasforunsupervisedtasks
|     |     |     |     |     |     | On a modern |     | V100 | GPU, | this | requires | about 65 |
| --- | --- | --- | --- | --- | --- | ----------- | --- | ---- | ---- | ---- | -------- | -------- |
likeclustering.
|     |     |     |     |     |     | hours. | Similar, | finding | which | of  | the | over 40 mil- |
| --- | --- | --- | --- | --- | --- | ------ | -------- | ------- | ----- | --- | --- | ------------ |
Inthispublication,wepresentSentence-BERT
lionexistentquestionsofQuoraisthemostsimilar
| (SBERT), |     | a modification |     | of the | pretrained |     |     |     |     |     |     |     |
| -------- | --- | -------------- | --- | ------ | ---------- | --- | --- | --- | --- | --- | --- | --- |
foranewquestioncouldbemodeledasapair-wise
BERTnetworkthatusesiameseandtripletnet-
comparisonwithBERT,however,answeringasin-
| work | structures | to  | derive | semantically | mean- |     |     |     |     |     |     |     |
| ---- | ---------- | --- | ------ | ------------ | ----- | --- | --- | --- | --- | --- | --- | --- |
glequerywouldrequireover50hours.
| ingful | sentence | embeddings |     | that can | be com- |     |     |     |     |     |     |     |
| ------ | -------- | ---------- | --- | -------- | ------- | --- | --- | --- | --- | --- | --- | --- |
paredusingcosine-similarity.Thisreducesthe Acommonmethodtoaddressclusteringandse-
effortforfindingthemostsimilarpairfrom65 mantic search is to map each sentence to a vec-
hours with BERT / RoBERTa to about 5 sec- tor space such that semantically similar sentences
| onds | with SBERT, |     | while | maintaining | the ac- |            |             |     |      |         |     |             |
| ---- | ----------- | --- | ----- | ----------- | ------- | ---------- | ----------- | --- | ---- | ------- | --- | ----------- |
|      |             |     |       |             |         | are close. | Researchers |     | have | started | to  | input indi- |
curacyfromBERT.
|     |     |     |     |     |     | vidual | sentences | into | BERT | and | to derive | fixed- |
| --- | --- | --- | --- | --- | --- | ------ | --------- | ---- | ---- | --- | --------- | ------ |
WeevaluateSBERTandSRoBERTaoncom- size sentence embeddings. The most commonly
mon STS tasks and transfer learning tasks, usedapproachistoaveragetheBERToutputlayer
| where | it outperforms |     | other | state-of-the-art |     |     |     |     |     |     |     |     |
| ----- | -------------- | --- | ----- | ---------------- | --- | --- | --- | --- | --- | --- | --- | --- |
(knownasBERTembeddings)orbyusingtheout-
sentenceembeddingsmethods.1
[CLS]
|     |     |     |     |     |     | put of    | the first                         | token | (the |     | token). | As we |
| --- | --- | --- | --- | --- | --- | --------- | --------------------------------- | ----- | ---- | --- | ------- | ----- |
|     |     |     |     |     |     | willshow, | thiscommonpracticeyieldsratherbad |       |      |     |         |       |
1 Introduction
|     |     |     |     |     |     | sentence | embeddings, |     | often | worse | than | averaging |
| --- | --- | --- | --- | --- | --- | -------- | ----------- | --- | ----- | ----- | ---- | --------- |
In this publication, we present Sentence-BERT GloVeembeddings(Penningtonetal.,2014).
|     |     |     |     |     |     | To alleviate |     | this | issue, | we developed |     | SBERT. |
| --- | --- | --- | --- | --- | --- | ------------ | --- | ---- | ------ | ------------ | --- | ------ |
(SBERT),amodificationoftheBERTnetworkus-
|             |     |         |          |     |                 | The siamese |     | network | architecture |     |     | enables that |
| ----------- | --- | ------- | -------- | --- | --------------- | ----------- | --- | ------- | ------------ | --- | --- | ------------ |
| ing siamese | and | triplet | networks |     | that is able to |             |     |         |              |     |     |              |
derive semantically meaningful sentence embed- fixed-sized vectors for input sentences can be de-
dings2. This enables BERT to be used for certain rived. Using a similarity measure like cosine-
|            |       |           |     |      |                | similarity | or  | Manhatten | /   | Euclidean |     | distance, se- |
| ---------- | ----- | --------- | --- | ---- | -------------- | ---------- | --- | --------- | --- | --------- | --- | ------------- |
| new tasks, | which | up-to-now |     | were | not applicable |            |     |           |     |           |     |               |
forBERT.Thesetasksincludelarge-scaleseman- mantically similar sentences can be found. These
|     |     |     |     |     |     | similarity | measures |     | can | be performed |     | extremely |
| --- | --- | --- | --- | --- | --- | ---------- | -------- | --- | --- | ------------ | --- | --------- |
1Code available: https://github.com/UKPLab/ efficient on modern hardware, allowing SBERT
sentence-transformers
|     |     |     |     |     |     | to be used | for | semantic | similarity |     | search | as well |
| --- | --- | --- | --- | --- | --- | ---------- | --- | -------- | ---------- | --- | ------ | ------- |
2Withsemanticallymeaningfulwemeanthatsemantically
similarsentencesarecloseinvectorspace. as for clustering. The complexity for finding the
3982
Proceedingsofthe2019ConferenceonEmpiricalMethodsinNaturalLanguageProcessing
andthe9thInternationalJointConferenceonNaturalLanguageProcessing,pages3982–3992,
HongKong,China,November3–7,2019.(cid:13)c2019AssociationforComputationalLinguistics

mostsimilarsentencepairinacollectionof10,000 new state-of-the-art performance on the Semantic
sentencesisreducedfrom65hourswithBERTto Textual Semilarity (STS) benchmark (Cer et al.,
the computation of 10,000 sentence embeddings 2017). RoBERTa (Liu et al., 2019) showed, that
(~5 seconds with SBERT) and computing cosine- theperformanceofBERTcanfurtherimprovedby
similarity (~0.01 seconds). By using optimized small adaptations to the pre-training process. We
index structures, finding the most similar Quora alsotestedXLNet(Yangetal.,2019),butitledin
question can be reduced from 50 hours to a few generaltoworseresultsthanBERT.
milliseconds(Johnsonetal.,2017). A large disadvantage of the BERT network
We fine-tune SBERT on NLI data, which cre- structure is that no independent sentence embed-
ates sentence embeddings that significantly out- dingsarecomputed,whichmakesitdifficulttode-
performotherstate-of-the-artsentenceembedding rive sentence embeddings from BERT. To bypass
methodslikeInferSent(Conneauetal.,2017)and this limitations, researchers passed single sen-
UniversalSentenceEncoder(Ceretal.,2018). On tencesthroughBERTandthenderiveafixedsized
| seven Semantic |     | Textual | Similarity |     | (STS) | tasks, |           |        |           |     |         |          |     |
| -------------- | --- | ------- | ---------- | --- | ----- | ------ | --------- | ------ | --------- | --- | ------- | -------- | --- |
|                |     |         |            |     |       |        | vector by | either | averaging | the | outputs | (similar | to  |
SBERT achieves an improvement of 11.7 points average word embeddings) or by using the output
comparedtoInferSentand5.5pointscomparedto ofthespecialCLStoken(forexample: Mayetal.
Universal Sentence Encoder. On SentEval (Con- (2019); Zhang et al. (2019); Qiao et al. (2019)).
neau and Kiela, 2018), an evaluation toolkit for These two options are also provided by the popu-
sentenceembeddings,weachieveanimprovement larbert-as-a-service-repository3. Uptoourknowl-
of2.1and2.6points,respectively. edge,thereissofarnoevaluationifthesemethods
SBERT can be adapted to a specific task. It leadtousefulsentenceembeddings.
| sets new | state-of-the-art |     | performance |     | on  | a chal- |          |            |     |     |        |         |      |
| -------- | ---------------- | --- | ----------- | --- | --- | ------- | -------- | ---------- | --- | --- | ------ | ------- | ---- |
|          |                  |     |             |     |     |         | Sentence | embeddings |     | are | a well | studied | area |
lenging argument similarity dataset (Misra et al., with dozens of proposed methods. Skip-Thought
2016) and on a triplet dataset to distinguish sen- (Kiros et al., 2015) trains an encoder-decoder ar-
tencesfromdifferentsectionsofaWikipediaarti-
|     |     |     |     |     |     |     | chitecture | to predict |     | the surrounding |     | sentences. |     |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ---------- | --- | --------------- | --- | ---------- | --- |
cle(Doretal.,2018). InferSent (Conneau et al., 2017) uses labeled
The paper is structured in the following way: data of the Stanford Natural Language Inference
Section 3 presents SBERT, section 4 evaluates dataset (Bowman et al., 2015) and the Multi-
SBERT on common STS tasks and on the chal- Genre NLI dataset (Williams et al., 2018) to train
lenging Argument Facet Similarity (AFS) corpus a siamese BiLSTM network with max-pooling
(Misra et al., 2016). Section 5 evaluates SBERT over the output. Conneau et al. showed, that
onSentEval. Insection6,weperformanablation InferSent consistently outperforms unsupervised
studytotestsomedesignaspectofSBERT.Insec- methods like SkipThought. Universal Sentence
tion7,wecomparethecomputationalefficiencyof Encoder (Cer et al., 2018) trains a transformer
SBERT sentence embeddings in contrast to other networkandaugmentsunsupervisedlearningwith
state-of-the-artsentenceembeddingmethods. training on SNLI. Hill et al. (2016) showed, that
thetaskonwhichsentenceembeddingsaretrained
2 RelatedWork
|     |     |     |     |     |     |     | significantly | impacts |     | their quality. |     | Previous | work |
| --- | --- | --- | --- | --- | --- | --- | ------------- | ------- | --- | -------------- | --- | -------- | ---- |
(Conneauetal.,2017;Ceretal.,2018)foundthat
| We first | introduce | BERT, | then, | we  | discuss | state- |          |          |     |          |     |          |      |
| -------- | --------- | ----- | ----- | --- | ------- | ------ | -------- | -------- | --- | -------- | --- | -------- | ---- |
|          |           |       |       |     |         |        | the SNLI | datasets | are | suitable | for | training | sen- |
of-the-artsentenceembeddingmethods.
|      |         |     |            |     |               |     | tence embeddings. |          | Yang | et            | al. (2018) |      | presented |
| ---- | ------- | --- | ---------- | --- | ------------- | --- | ----------------- | -------- | ---- | ------------- | ---------- | ---- | --------- |
| BERT | (Devlin | et  | al., 2018) | is  | a pre-trained |     |                   |          |      |               |            |      |           |
|      |         |     |            |     |               |     | a method          | to train | on   | conversations |            | from | Reddit    |
transformernetwork(Vaswanietal.,2017),which
|                 |     |           |     |                  |     |     | using siamese | DAN | and     | siamese |         | transformer | net-    |
| --------------- | --- | --------- | --- | ---------------- | --- | --- | ------------- | --- | ------- | ------- | ------- | ----------- | ------- |
| set for various |     | NLP tasks | new | state-of-the-art |     | re- |               |     |         |         |         |             |         |
|                 |     |           |     |                  |     |     | works, which  |     | yielded | good    | results | on          | the STS |
sults,includingquestionanswering,sentenceclas-
benchmarkdataset.
| sification,andsentence-pairregression. |                   |           |     |              | Theinput     |          |          |          |                 |           |         |      |          |
| -------------------------------------- | ----------------- | --------- | --- | ------------ | ------------ | -------- | -------- | -------- | --------------- | --------- | ------- | ---- | -------- |
|                                        |                   |           |     |              |              |          | Humeau   | et       | al. (2019)      | addresses |         | the  | run-time |
| for BERT                               | for sentence-pair |           |     | regression   | consists     | of       |          |          |                 |           |         |      |          |
|                                        |                   |           |     |              |              |          | overhead | of the   | cross-encoder   |           | from    | BERT | and      |
| the two                                | sentences,        | separated |     | by a special |              | [SEP]    |          |          |                 |           |         |      |          |
|                                        |                   |           |     |              |              |          | present  | a method | (poly-encoders) |           |         | to   | compute  |
| token. Multi-head                      |                   | attention |     | over 12      | (base-model) |          |          |          |                 |           |         |      |          |
|                                        |                   |           |     |              |              |          | a score  | between  | m               | context   | vectors |      | and pre- |
| or 24 layers                           | (large-model)     |           |     | is applied   | and          | the out- |          |          |                 |           |         |      |          |
putispassedtoasimpleregressionfunctiontode-
3https://github.com/hanxiao/
| rive the | final label. | Using |     | this setup, | BERT | set a | bert-as-service/ |     |     |     |     |     |     |
| -------- | ------------ | ----- | --- | ----------- | ---- | ----- | ---------------- | --- | --- | --- | --- | --- | --- |
3983

|     |             | Softmax classifier  |     |             |     |     |     |             |                   | -1 … 1  |             |     |     |
| --- | ----------- | ------------------- | --- | ----------- | --- | --- | --- | ----------- | ----------------- | ------- | ----------- | --- | --- |
|     |             | (u, v, |u-v|)       |     |             |     |     |     |             | cosine-sim(u, v)  |         |             |     |     |
|     |             | u                   |     | v           |     |     |     |             | u                 |         |             | v   |     |
|     | pooling     |                     |     | pooling     |     |     |     | pooling     |                   |         | pooling     |     |     |
|     | BERT        |                     |     | BERT        |     |     |     | BERT        |                   |         | BERT        |     |     |
|     | Sentence A  |                     |     | Sentence B  |     |     |     | Sentence A  |                   |         | Sentence B  |     |     |
Figure 1: SBERT architecture with classification ob- Figure 2: SBERT architecture at inference, for exam-
jective function, e.g., for fine-tuning on SNLI dataset. ple, to compute similarity scores. This architecture is
The two BERT networks have tied weights (siamese alsousedwiththeregressionobjectivefunction.
networkstructure).
|     |     |     |     |     |     | training |     | data. | We experiment |     | with | the | following |
| --- | --- | --- | --- | --- | --- | -------- | --- | ----- | ------------- | --- | ---- | --- | --------- |
computed candidate embeddings using attention. structuresandobjectivefunctions.
This idea works for finding the highest scoring Classification Objective Function. We con-
|          |             |     |             |          |       | catenate |     | the sentence |     | embeddings |     | u and | v with |
| -------- | ----------- | --- | ----------- | -------- | ----- | -------- | --- | ------------ | --- | ---------- | --- | ----- | ------ |
| sentence | in a larger |     | collection. | However, | poly- |          |     |              |     |            |     |       |        |
encodershavethedrawbackthatthescorefunction theelement-wisedifference|u−v|andmultiplyit
R3n×k:
is not symmetric and the computational overhead withthetrainableweightW ∈
t
| is too | large for | use-cases |     | like clustering, | which |     |     |     |     |     |     |     |     |
| ------ | --------- | --------- | --- | ---------------- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
wouldrequireO(n2)scorecomputations. o = softmax(W t (u,v,|u−v|))
| Previous | neural | sentence |     | embedding | methods |     |     |     |     |     |     |     |     |
| -------- | ------ | -------- | --- | --------- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
n
|             |              |         |     |                 |                 |                                | where | is  | the dimension |           | of the | sentence    | em- |
| ----------- | ------------ | ------- | --- | --------------- | --------------- | ------------------------------ | ----- | --- | ------------- | --------- | ------ | ----------- | --- |
| started     | the training | from    | a   | random          | initialization. |                                |       |     |               |           |        |             |     |
|             |              |         |     |                 |                 | beddingsandkthenumberoflabels. |       |     |               |           |        | Weoptimize  |     |
| In this     | publication, | we      | use | the pre-trained | BERT            |                                |       |     |               |           |        |             |     |
|             |              |         |     |                 |                 | cross-entropy                  |       |     | loss. This    | structure |        | is depicted | in  |
| and RoBERTa |              | network | and | only            | fine-tune it to |                                |       |     |               |           |        |             |     |
Figure1.
| yield                               | useful sentence |            | embeddings. |          | This reduces   |            |            |             |           |           |          |            |           |
| ----------------------------------- | --------------- | ---------- | ----------- | -------- | -------------- | ---------- | ---------- | ----------- | --------- | --------- | -------- | ---------- | --------- |
|                                     |                 |            |             |          |                |            | Regression |             | Objective | Function. |          | The        | cosine-   |
| significantlytheneededtrainingtime: |                 |            |             |          | SBERTcan       |            |            |             |           |           |          |            |           |
|                                     |                 |            |             |          |                | similarity |            | between     | the       | two       | sentence | embeddings |           |
| be tuned                            | in less         | than       | 20 minutes, |          | while yielding |            |            |             |           |           |          |            |           |
|                                     |                 |            |             |          |                | u          | and v      | is computed |           | (Figure   | 2).      | We         | use mean- |
| better                              | results than    | comparable |             | sentence | embed-         |            |            |             |           |           |          |            |           |
squared-errorlossastheobjectivefunction.
dingmethods.
|     |     |     |     |     |     |          | Triplet | Objective | Function. |          | Given |     | an anchor  |
| --- | --- | --- | --- | --- | --- | -------- | ------- | --------- | --------- | -------- | ----- | --- | ---------- |
|     |     |     |     |     |     | sentence |         | a, a      | positive  | sentence | p,    | and | a negative |
3 Model
sentencen,tripletlosstunesthenetworksuchthat
|         |           |         |           |         |               | the      | distance | between |       | a and | p is            | smaller | than the |
| ------- | --------- | ------- | --------- | ------- | ------------- | -------- | -------- | ------- | ----- | ----- | --------------- | ------- | -------- |
| SBERT   | adds a    | pooling | operation |         | to the output |          |          |         |       |       |                 |         |          |
|         |           |         |           |         |               | distance |          | between | a and | n.    | Mathematically, |         | we       |
| of BERT | / RoBERTa |         | to derive | a fixed | sized sen-    |          |          |         |       |       |                 |         |          |
minimizethefollowinglossfunction:
| tenceembedding. |                               | Weexperimentwiththreepool- |               |         |        |     |         |     |               |     |      |                  |     |
| --------------- | ----------------------------- | -------------------------- | ------------- | ------- | ------ | --- | ------- | --- | ------------- | --- | ---- | ---------------- | --- |
| ingstrategies:  | UsingtheoutputoftheCLS-token, |                            |               |         |        |     |         |     |               |     |      |                  |     |
|                 |                               |                            |               |         |        |     | max(||s |     | a −s p ||−||s |     | a −s | n ||+(cid:15),0) |     |
| computing       | the                           | mean                       | of all output | vectors | (MEAN- |     |         |     |               |     |      |                  |     |
strategy), and computing a max-over-time of the withs thesentenceembeddingfora/n/p,||·||
x
| outputvectors(MAX-strategy). |     |     |     | Thedefaultconfig- |     |     |          |        |     |        |                  |     |                  |
| ---------------------------- | --- | --- | --- | ----------------- | --- | --- | -------- | ------ | --- | ------ | ---------------- | --- | ---------------- |
|                              |     |     |     |                   |     | a   | distance | metric | and | margin | (cid:15). Margin |     | (cid:15) ensures |
urationisMEAN.
|     |     |     |     |     |     | thats | isatleast(cid:15)closertos |     |     |     | thans | .   | Asmetric |
| --- | --- | --- | --- | --- | --- | ----- | -------------------------- | --- | --- | --- | ----- | --- | -------- |
|     |     |     |     |     |     |       | p                          |     |     |     | a     | n   |          |
Inordertofine-tuneBERT/RoBERTa,wecre- weuseEuclideandistanceandweset(cid:15) = 1inour
| ate siamese | and | triplet | networks | (Schroff | et al., | experiments. |     |     |     |     |     |     |     |
| ----------- | --- | ------- | -------- | -------- | ------- | ------------ | --- | --- | --- | --- | --- | --- | --- |
2015)toupdatetheweightssuchthattheproduced
sentenceembeddingsaresemanticallymeaningful 3.1 TrainingDetails
andcanbecomparedwithcosine-similarity. We train SBERT on the combination of the SNLI
Thenetworkstructuredependsontheavailable (Bowman et al., 2015) and the Multi-Genre NLI
3984

Model STS12 STS13 STS14 STS15 STS16 STSb SICK-R Avg.
Avg.GloVeembeddings 55.14 70.66 59.73 68.25 63.66 58.02 53.76 61.32
Avg.BERTembeddings 38.78 57.98 57.98 63.15 61.06 46.35 58.40 54.81
BERTCLS-vector 20.16 30.01 20.09 36.88 38.08 16.50 42.63 29.19
InferSent-Glove 52.86 66.75 62.15 72.77 66.87 68.03 65.65 65.01
UniversalSentenceEncoder 64.49 67.80 64.61 76.83 73.18 74.92 76.69 71.22
SBERT-NLI-base 70.97 76.53 73.19 79.09 74.30 77.03 72.91 74.89
SBERT-NLI-large 72.27 78.46 74.90 80.99 76.25 79.23 73.75 76.55
SRoBERTa-NLI-base 71.54 72.49 70.80 78.74 73.69 77.77 74.46 74.21
SRoBERTa-NLI-large 74.53 77.00 73.18 81.85 76.82 79.10 74.29 76.68
Table1: Spearmanrankcorrelationρbetweenthecosinesimilarityofsentencerepresentationsandthegoldlabels
for various Textual Similarity (STS) tasks. Performance is reported by convention as ρ×100. STS12-STS16:
SemEval2012-2016,STSb: STSbenchmark,SICK-R:SICKrelatednessdataset.
(Williamsetal.,2018)dataset. TheSNLIisacol- STS. Instead, we compute the Spearman’s rank
lection of 570,000 sentence pairs annotated with correlation between the cosine-similarity of the
the labels contradiction, eintailment, and neu- sentence embeddings and the gold labels. The
tral. MultiNLI contains 430,000 sentence pairs setup for the other sentence embedding methods
andcoversarangeofgenresofspokenandwritten isequivalent,thesimilarityiscomputedbycosine-
text. We fine-tune SBERT with a 3-way softmax- similarity. TheresultsaredepictedinTable1.
classifier objective function for one epoch. We Theresultsshowsthatdirectlyusingtheoutput
used a batch-size of 16, Adam optimizer with of BERT leads to rather poor performances. Av-
learning rate 2e−5, and a linear learning rate eraging the BERT embeddings achieves an aver-
warm-up over 10% of the training data. Our de- age correlation of only 54.81, and using the CLS-
faultpoolingstrategyisMEAN. token output only achieves an average correlation
of 29.19. Both are worse than computing average
4 Evaluation-SemanticTextual
GloVeembeddings.
Similarity
Using the described siamese network structure
andfine-tuningmechanismsubstantiallyimproves
We evaluate the performance of SBERT for com-
the correlation, outperforming both InferSent and
mon Semantic Textual Similarity (STS) tasks.
Universal Sentence Encoder substantially. The
State-of-the-art methods often learn a (complex)
only dataset where SBERT performs worse than
regression function that maps sentence embed-
UniversalSentenceEncoderisSICK-R.Universal
dingstoasimilarityscore. However,theseregres-
SentenceEncoderwastrainedonvariousdatasets,
sionfunctionsworkpair-wiseandduetothecom-
including news, question-answer pages and dis-
binatorialexplosionthoseareoftennotscalableif
cussionforums,whichappearstobemoresuitable
the collection of sentences reaches a certain size.
to the data of SICK-R. In contrast, SBERT was
Instead, we always use cosine-similarity to com-
pre-trainedonlyonWikipedia(viaBERT)andon
pare the similarity between two sentence embed-
NLIdata.
dings. We ran our experiments also with nega-
While RoBERTa was able to improve the per-
tive Manhatten and negative Euclidean distances
formance for several supervised tasks, we only
as similarity measures, but the results for all ap-
observe minor difference between SBERT and
proachesremainedroughlythesame.
SRoBERTaforgeneratingsentenceembeddings.
4.1 UnsupervisedSTS
4.2 SupervisedSTS
We evaluate the performance of SBERT for STS
without using any STS specific training data. We TheSTSbenchmark(STSb)(Ceretal.,2017)pro-
usetheSTStasks2012-2016(Agirreetal.,2012, vides is a popular dataset to evaluate supervised
2013,2014,2015,2016),theSTSbenchmark(Cer STS systems. The data includes 8,628 sentence
et al., 2017), and the SICK-Relatedness dataset pairsfromthethreecategoriescaptions,news,and
(Marelli et al., 2014). These datasets provide la- forums. Itisdividedintotrain(5,749),dev(1,500)
bels between 0 and 5 on the semantic relatedness and test (1,379). BERT set a new state-of-the-art
of sentence pairs. We showed in (Reimers et al., performance on this dataset by passing both sen-
2016) that Pearson correlation is badly suited for tences to the network and using a simple regres-
3985

sionmethodfortheoutput. descriptive,whileAFSdataareargumentativeex-
cerpts from dialogs. To be considered similar, ar-
Model Spearman guments must not only make similar claims, but
NottrainedforSTS
also provide a similar reasoning. Further, the lex-
Avg.GloVeembeddings 58.02
Avg.BERTembeddings 46.35 ical gap between the sentences in AFS is much
InferSent-GloVe 68.03 larger. Hence, simple unsupervised methods as
UniversalSentenceEncoder 74.92
wellasstate-of-the-artSTSsystemsperformbadly
SBERT-NLI-base 77.03
SBERT-NLI-large 79.23 onthisdataset(Reimersetal.,2019).
TrainedonSTSbenchmarkdataset
We evaluate SBERT on this dataset in two sce-
BERT-STSb-base 84.30±0.76
SBERT-STSb-base 84.67±0.19 narios: 1)AsproposedbyMisraetal.,weevaluate
SRoBERTa-STSb-base 84.92±0.34 SBERT using 10-fold cross-validation. A draw-
BERT-STSb-large 85.64±0.81
back of this evaluation setup is that it is not clear
SBERT-STSb-large 84.45±0.43
SRoBERTa-STSb-large 85.02±0.76 how well approaches generalize to different top-
TrainedonNLIdata+STSbenchmarkdata ics. Hence,2)weevaluateSBERTinacross-topic
BERT-NLI-STSb-base 88.33±0.19
setup. Two topics serve for training and the ap-
SBERT-NLI-STSb-base 85.35±0.17
SRoBERTa-NLI-STSb-base 84.79±0.38 proachisevaluatedontheleft-outtopic. Werepeat
BERT-NLI-STSb-large 88.77±0.46 thisforallthreetopicsandaveragetheresults.
SBERT-NLI-STSb-large 86.10±0.13
SBERT is fine-tuned using the Regression Ob-
SRoBERTa-NLI-STSb-large 86.15±0.35
jectiveFunction. Thesimilarityscoreiscomputed
Table 2: Evaluation on the STS benchmark test set. usingcosine-similaritybasedonthesentenceem-
BERTsystemsweretrainedwith10randomseedsand
beddings. We also provide the Pearson correla-
4epochs. SBERTwasfine-tunedontheSTSbdataset,
tion r to make the results comparable to Misra et
SBERT-NLI was pretrained on the NLI datasets, then
al. However, we showed (Reimers et al., 2016)
fine-tunedontheSTSbdataset.
that Pearson correlation has some serious draw-
backs and should be avoided for comparing STS
We use the training set to fine-tune SBERT us-
systems. TheresultsaredepictedinTable3.
ing the regression objective function. At predic-
Unsupervised methods like tf-idf, average
tion time, we compute the cosine-similarity be-
GloVe embeddings or InferSent perform rather
tween the sentence embeddings. All systems are
badly on this dataset with low scores. Training
trainedwith10randomseedstocountervariances
SBERTinthe10-foldcross-validationsetupgives
(ReimersandGurevych,2018).
aperformancethatisnearlyon-parwithBERT.
The results are depicted in Table 2. We ex-
However, in the cross-topic evaluation, we ob-
perimented with two setups: Only training on
serve a performance drop of SBERT by about 7
STSb, and first training on NLI, then training on
points Spearman correlation. To be considered
STSb. Weobservethatthelaterstrategyleadstoa
similar,argumentsshouldaddressthesameclaims
slight improvement of 1-2 points. This two-step
and provide the same reasoning. BERT is able to
approach had an especially large impact for the
use attention to compare directly both sentences
BERT cross-encoder, which improved the perfor-
(e.g. word-by-word comparison), while SBERT
manceby3-4points. Wedonotobserveasignifi-
must map individual sentences from an unseen
cantdifferencebetweenBERTandRoBERTa.
topic to a vector space such that arguments with
4.3 ArgumentFacetSimilarity similar claims and reasons are close. This is a
muchmorechallengingtask,whichappearstore-
We evaluate SBERT on the Argument Facet Sim-
quiremorethanjusttwotopicsfortrainingtowork
ilarity (AFS) corpus by Misra et al. (2016). The
on-parwithBERT.
AFS corpus annotated 6,000 sentential argument
pairs from social media dialogs on three contro-
4.4 WikipediaSectionsDistinction
versial topics: gun control, gay marriage, and
death penalty. The data was annotated on a scale Dor et al. (2018) use Wikipedia to create a the-
from0(“differenttopic”)to5(“completelyequiv- matically fine-grained train, dev and test set for
alent”). The similarity notion in the AFS corpus sentence embeddings methods. Wikipedia arti-
is fairly different to the similarity notion in the cles are separated into distinct sections focusing
STS datasets from SemEval. STS data is usually on certain aspects. Dor et al. assume that sen-
3986

Model r ρ Model Accuracy
Unsupervisedmethods mean-vectors 0.65
tf-idf 46.77 42.95 skip-thoughts-CS 0.62
Avg.GloVeembeddings 32.40 34.00 Doretal. 0.74
InferSent-GloVe 27.08 26.63 SBERT-WikiSec-base 0.8042
10-foldCross-Validation SBERT-WikiSec-large 0.8078
SVR(Misraetal.,2016) 63.33 - SRoBERTa-WikiSec-base 0.7945
BERT-AFS-base 77.20 74.84 SRoBERTa-WikiSec-large 0.7973
SBERT-AFS-base 76.57 74.13
BERT-AFS-large 78.68 76.38 Table 4: Evaluation on the Wikipedia section triplets
SBERT-AFS-large 77.85 75.93 dataset (Dor et al., 2018). SBERT trained with triplet
Cross-TopicEvaluation
lossforoneepoch.
BERT-AFS-base 58.49 57.23
SBERT-AFS-base 52.34 50.65
BERT-AFS-large 62.02 60.34
The purpose of SBERT sentence embeddings
SBERT-AFS-large 53.82 53.10
are not to be used for transfer learning for other
Table 3: Average Pearson correlation r and average tasks. Here, we think fine-tuning BERT as de-
Spearman’s rank correlation ρ on the Argument Facet
scribed by Devlin et al. (2018) for new tasks is
Similarity(AFS)corpus(Misraetal.,2016). Misraet
the more suitable method, as it updates all layers
al. proposes 10-fold cross-validation. We additionally
oftheBERTnetwork. However,SentEvalcanstill
evaluateinacross-topicscenario: Methodsaretrained
ontwotopics,andareevaluatedonthethirdtopic. give an impression on the quality of our sentence
embeddingsforvarioustasks.
We compare the SBERT sentence embeddings
tences in the same section are thematically closer
toothersentenceembeddingsmethodsonthefol-
thansentencesindifferentsections. Theyusethis
lowingsevenSentEvaltransfertasks:
to create a large dataset of weakly labeled sen-
tence triplets: The anchor and the positive exam- • MR:Sentimentpredictionformoviereviews
ple come from the same section, while the neg- snippets on a five start scale (Pang and Lee,
ative example comes from a different section of 2005).
the same article. For example, from the Alice
• CR: Sentiment prediction of customer prod-
Arnold article: Anchor: Arnold joined the BBC
uctreviews(HuandLiu,2004).
RadioDramaCompanyin1988.,positive: Arnold
gained media attention in May 2012., negative: • SUBJ: Subjectivity prediction of sentences
BaldingandArnoldarekeenamateurgolfers. from movie reviews and plot summaries
We use the dataset from Dor et al. We use the (PangandLee,2004).
Triplet Objective, train SBERT for one epoch on
theabout1.8Milliontrainingtripletsandevaluate • MPQA: Phrase level opinion polarity classi-
itonthe222,957testtriplets. Testtripletsarefrom ficationfromnewswire(Wiebeetal.,2005).
a distinct set of Wikipedia articles. As evaluation
• SST: Stanford Sentiment Treebank with bi-
metric, we use accuracy: Is the positive example
narylabels(Socheretal.,2013).
closertotheanchorthanthenegativeexample?
ResultsarepresentedinTable4. Doretal.fine- • TREC: Fine grained question-type classifi-
tuned a BiLSTM architecture with triplet loss to cationfromTREC(LiandRoth,2002).
derive sentence embeddings for this dataset. As
• MRPC:MicrosoftResearchParaphraseCor-
the table shows, SBERT clearly outperforms the
pus from parallel news sources (Dolan et al.,
BiLSTMapproachbyDoretal.
2004).
5 Evaluation-SentEval
The results can be found in Table 5. SBERT
SentEval (Conneau and Kiela, 2018) is a popular is able to achieve the best performance in 5 out
toolkit to evaluate the quality of sentence embed- of 7 tasks. The average performance increases
dings. Sentence embeddings are used as features by about 2 percentage points compared to In-
foralogisticregressionclassifier. Thelogisticre- ferSentaswellastheUniversalSentenceEncoder.
gression classifier is trained on various tasks in a Eventhoughtransferlearningisnotthepurposeof
10-fold cross-validation setup and the prediction SBERT, it outperforms other state-of-the-art sen-
accuracyiscomputedforthetest-fold. tenceembeddingsmethodsonthistask.
3987

|     | Model |     |     |     | MR  | CR SUBJ | MPQA | SST | TREC | MRPC | Avg. |
| --- | ----- | --- | --- | --- | --- | ------- | ---- | --- | ---- | ---- | ---- |
Avg.GloVeembeddings 77.25 78.30 91.17 87.85 80.18 83.0 72.87 81.52
Avg.fast-textembeddings 77.96 79.23 91.68 87.81 82.15 83.6 74.49 82.42
Avg.BERTembeddings 78.66 86.25 94.37 88.66 84.40 92.8 69.45 84.94
BERTCLS-vector 78.68 84.85 94.21 88.23 84.13 91.4 71.13 84.66
InferSent-GloVe 81.57 86.54 92.50 90.38 84.18 88.2 75.77 85.59
UniversalSentenceEncoder 80.09 85.19 93.98 86.70 86.38 93.2 70.14 85.10
SBERT-NLI-base 83.64 89.43 94.39 89.86 88.96 89.6 76.00 87.41
SBERT-NLI-large 84.88 90.07 94.52 90.33 90.66 87.4 75.94 87.69
Table 5: Evaluation of SBERT sentence embeddings using the SentEval toolkit. SentEval evaluates sentence
embeddingsondifferentsentenceclassificationtasksbytrainingalogisticregressionclassifierusingthesentence
| embeddingsasfeatures. |     |     | Scoresarebasedona10-foldcross-validation. |     |     |     |     |     |     |     |     |
| --------------------- | --- | --- | ----------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
It appears that the sentence embeddings from this section, we perform an ablation study of dif-
SBERT capture well sentiment information: We ferent aspects of SBERT in order to get a better
observelargeimprovementsforallsentimenttasks understandingoftheirrelativeimportance.
(MR,CR,andSST)fromSentEvalincomparison We evaluated different pooling strategies
toInferSentandUniversalSentenceEncoder. (MEAN, MAX, and CLS). For the classification
The only dataset where SBERT is significantly objective function, we evaluate different concate-
worse than Universal Sentence Encoder is the nation methods. For each possible configuration,
TREC dataset. Universal Sentence Encoder was we train SBERT with 10 different random seeds
pre-trainedonquestion-answeringdata,whichap- andaveragetheperformances.
pearstobebeneficialforthequestion-typeclassi- Theobjectivefunction(classificationvs.regres-
ficationtaskoftheTRECdataset. sion) depends on the annotated dataset. For the
Average BERT embeddings or using the CLS- classificationobjectivefunction,wetrainSBERT-
token output from a BERT network achieved bad base on the SNLI and the Multi-NLI dataset. For
resultsforvariousSTStasks(Table1),worsethan the regression objective function, we train on the
average GloVe embeddings. However, for Sent- trainingsetoftheSTSbenchmarkdataset. Perfor-
Eval, average BERT embeddings and the BERT mances are measured on the development split of
CLS-token output achieves decent results (Ta- the STS benchmark dataset. Results are shown in
| ble5),outperformingaverageGloVeembeddings. |        |          |         |           |         |     | Table6. |     |     |     |     |
| ------------------------------------------ | ------ | -------- | ------- | --------- | ------- | --- | ------- | --- | --- | --- | --- |
| The                                        | reason | for this | are the | different | setups. | For |         |     |     |     |     |
NLI STSb
| the | STS tasks, | we  | used cosine-similarity |     |     | to es- |     |     |     |     |     |
| --- | ---------- | --- | ---------------------- | --- | --- | ------ | --- | --- | --- | --- | --- |
PoolingStrategy
timate the similarities between sentence embed- MEAN 80.78 87.44
dings. Cosine-similarity treats all dimensions MAX 79.07 69.92
|     |     |     |     |     |     |     |     | CLS |     | 79.80 86.62 |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ----------- | --- |
equally. Incontrast,SentEvalfitsalogisticregres-
Concatenation
sion classifier to the sentence embeddings. This (u,v) 66.04 -
allows that certain dimensions can have higher or (|u−v|) 69.78 -
|     |     |     |     |     |     |     |     | (u∗v) |     | 70.54 | -   |
| --- | --- | --- | --- | --- | --- | --- | --- | ----- | --- | ----- | --- |
lowerimpactontheclassificationresult.
|                                          |          |      |         |      |            |     |     | (|u−v|,u∗v)     |     | 78.37 | -   |
| ---------------------------------------- | -------- | ---- | ------- | ---- | ---------- | --- | --- | --------------- | --- | ----- | --- |
| We                                       | conclude | that | average | BERT | embeddings | /   |     | (u,v,u∗v)       |     | 77.44 | -   |
| CLS-tokenoutputfromBERTreturnsentenceem- |          |      |         |      |            |     |     | (u,v,|u−v|)     |     | 80.78 | -   |
|                                          |          |      |         |      |            |     |     | (u,v,|u−v|,u∗v) |     | 80.44 | -   |
beddingsthatareinfeasibletobeusedwithcosine-
similarityorwithManhatten/Euclideandistance. Table 6: SBERT trained on NLI data with the clas-
|     |          |           |      |       |          |       | sification | objective | function, | on the STS | benchmark |
| --- | -------- | --------- | ---- | ----- | -------- | ----- | ---------- | --------- | --------- | ---------- | --------- |
| For | transfer | learning, | they | yield | slightly | worse |            |           |           |            |           |
results than InferSent or Universal Sentence En- (STSb) with the regression objective function. Con-
figurationsareevaluatedonthedevelopmentsetofthe
| coder. | However, | using | the | described | fine-tuning |     |     |     |     |     |     |
| ------ | -------- | ----- | --- | --------- | ----------- | --- | --- | --- | --- | --- | --- |
STSbusingcosine-similarityandSpearman’srankcor-
| setup | with | a siamese | network | structure |     | on NLI |     |     |     |     |     |
| ----- | ---- | --------- | ------- | --------- | --- | ------ | --- | --- | --- | --- | --- |
relation.Fortheconcatenationmethods,weonlyreport
datasets yields sentence embeddings that achieve scoreswithMEANpoolingstrategy.
anewstate-of-the-artfortheSentEvaltoolkit.
|     |     |     |     |     |     |     | When | trained | with | the classification | objective |
| --- | --- | --- | --- | --- | --- | --- | ---- | ------- | ---- | ------------------ | --------- |
6 AblationStudy
|     |     |     |     |     |     |     | function | on NLI | data, | the pooling strategy | has a |
| --- | --- | --- | --- | --- | --- | --- | -------- | ------ | ----- | -------------------- | ----- |
Wehavedemonstratedstrongempiricalresultsfor rather minor impact. The impact of the concate-
the quality of SBERT sentence embeddings. In nation mode is much larger. InferSent (Conneau
3988

etal.,2017)andUniversalSentenceEncoder(Cer V100 GPU, CUDA 9.2 and cuDNN. The results
etal.,2018)bothuse(u,v,|u−v|,u∗v)asinput aredepictedinTable7.
| forasoftmaxclassifier. |     |     | However, | inourarchitec- |     |     |     |     |     |     |     |     |
| ---------------------- | --- | --- | -------- | -------------- | --- | --- | --- | --- | --- | --- | --- | --- |
ture, adding the element-wise u∗v decreased the Model CPU GPU
|     |     |     |     |     |     |     | Avg.GloVeembeddings |     |     | 6469 |     | -   |
| --- | --- | --- | --- | --- | --- | --- | ------------------- | --- | --- | ---- | --- | --- |
performance.
|     |     |     |     |     |     |     | InferSent |     |     | 137 | 1876 |     |
| --- | --- | --- | --- | --- | --- | --- | --------- | --- | --- | --- | ---- | --- |
The most important component is the element- UniversalSentenceEncoder 67 1318
wise difference |u − v|. Note, that the concate- SBERT-base 44 1378
|             |     |               |     |              |     |           | SBERT-base-smartbatching |     |     | 83  | 2042 |     |
| ----------- | --- | ------------- | --- | ------------ | --- | --------- | ------------------------ | --- | --- | --- | ---- | --- |
| nation mode | is  | only relevant |     | for training |     | the soft- |                          |     |     |     |      |     |
maxclassifier. Atinference,whenpredictingsim- Table7: Computationspeed(sentencespersecond)of
|           |            |               |       |            |     |          | sentenceembeddingmethods. |     |     | Higherisbetter. |     |     |
| --------- | ---------- | ------------- | ----- | ---------- | --- | -------- | ------------------------- | --- | --- | --------------- | --- | --- |
| ilarities | for the    | STS benchmark |       | dataset,   |     | only the |                           |     |     |                 |     |     |
| sentence  | embeddings |               | u and | v are used | in  | combi-   |                           |     |     |                 |     |     |
nation with cosine-similarity. The element-wise On CPU, InferSent is about 65% faster than
difference measures the distance between the di- SBERT. This is due to the much simpler net-
mensions of the two sentence embeddings, ensur- work architecture. InferSent uses a single Bi-
ingthatsimilarpairsarecloseranddissimilarpairs LSTM layer, while BERT uses 12 stacked trans-
arefurtherapart. former layers. However, an advantage of trans-
|      |         |      |     |            |           |     | former networks | is  | the computational |     | efficiency |     |
| ---- | ------- | ---- | --- | ---------- | --------- | --- | --------------- | --- | ----------------- | --- | ---------- | --- |
| When | trained | with | the | regression | objective |     |                 |     |                   |     |            |     |
function, weobservethatthepoolingstrategyhas on GPUs. There, SBERT with smart batching
a large impact. There, the MAX strategy perform is about 9% faster than InferSent and about 55%
significantlyworsethanMEANorCLS-tokenstrat- faster than Universal Sentence Encoder. Smart
batchingachievesaspeed-upof89%onCPUand
| egy. This | is in | contrast | to (Conneau |     | et al., | 2017), |     |     |     |     |     |     |
| --------- | ----- | -------- | ----------- | --- | ------- | ------ | --- | --- | --- | --- | --- | --- |
who found it beneficial for the BiLSTM-layer of 48%onGPU.AverageGloVeembeddingsisobvi-
InferSenttouseMAXinsteadofMEANpooling. ouslybyalargemarginthefastestmethodtocom-
putesentenceembeddings.
7 ComputationalEfficiency
|           |            |     |            |             |        |         | 8 Conclusion |           |                |     |      |      |
| --------- | ---------- | --- | ---------- | ----------- | ------ | ------- | ------------ | --------- | -------------- | --- | ---- | ---- |
| Sentence  | embeddings |     | need       | potentially |        | be com- |              |           |                |     |      |      |
|           |            |     |            |             |        |         | We showed    | that BERT | out-of-the-box |     | maps | sen- |
| puted for | Millions   | of  | sentences, |             | hence, | a high  |              |           |                |     |      |      |
computation speed is desired. In this section, we tences to a vector space that is rather unsuit-
compare SBERT to average GloVe embeddings, able to be used with common similarity measures
InferSent (Conneau et al., 2017), and Universal like cosine-similarity. The performance for seven
|     |     |     |     |     |     |     | STS tasks | was below | the | performance | of  | average |
| --- | --- | --- | --- | --- | --- | --- | --------- | --------- | --- | ----------- | --- | ------- |
SentenceEncoder(Ceretal.,2018).
| For our | comparison |     | we use | the sentences |     | from | GloVeembeddings. |     |     |     |     |     |
| ------- | ---------- | --- | ------ | ------------- | --- | ---- | ---------------- | --- | --- | --- | --- | --- |
the STS benchmark (Cer et al., 2017). We com- To overcome this shortcoming, we presented
pute average GloVe embeddings using a sim- Sentence-BERT (SBERT). SBERT fine-tunes
|              |      |        |            |     |         |     | BERT in | a siamese | / triplet | network |     | architec- |
| ------------ | ---- | ------ | ---------- | --- | ------- | --- | ------- | --------- | --------- | ------- | --- | --------- |
| ple for-loop | with | python | dictionary |     | lookups | and |         |           |           |         |     |           |
NumPy. InferSent4 is based on PyTorch. For ture. We evaluated the quality on various com-
Universal Sentence Encoder, we use the Tensor- mon benchmarks, where it could achieve a sig-
|          | version5, |     |       |          |     |         | nificant | improvement | over | state-of-the-art |     | sen- |
| -------- | --------- | --- | ----- | -------- | --- | ------- | -------- | ----------- | ---- | ---------------- | --- | ---- |
| Flow Hub |           |     | which | is based | on  | Tensor- |          |             |      |                  |     |      |
Flow. SBERTisbasedonPyTorch. Forimproved tenceembeddingsmethods. ReplacingBERTwith
computation of sentence embeddings, we imple- RoBERTadidnotyieldasignificantimprovement
| mented  | a smart | batching    | strategy: | Sentences |     | with     | inourexperiments.                |     |     |     |         |     |
| ------- | ------- | ----------- | --------- | --------- | --- | -------- | -------------------------------- | --- | --- | --- | ------- | --- |
|         |         |             |           |           |     |          | SBERTiscomputationallyefficient. |     |     |     | OnaGPU, |     |
| similar | lengths | are grouped | together  |           | and | are only |                                  |     |     |     |         |     |
padded to the longest element in a mini-batch. itisabout9%fasterthanInferSentandabout55%
This drastically reduces computational overhead faster than Universal Sentence Encoder. SBERT
frompaddingtokens. can be used for tasks which are computationally
notfeasibletobemodeledwithBERT.Forexam-
| Performances |     | were | measured | on  | a server | with |     |     |     |     |     |     |
| ------------ | --- | ---- | -------- | --- | -------- | ---- | --- | --- | --- | --- | --- | --- |
Intel i7-5820K CPU @ 3.30GHz, Nvidia Tesla ple,clusteringof10,000sentenceswithhierarchi-
calclusteringrequireswithBERTabout65hours,
4https://github.com/facebookresearch/ asaround50Millionsentencecombinationsmust
InferSent
|     |     |     |     |     |     |     | be computed. | With | SBERT, | we were | able | to re- |
| --- | --- | --- | --- | --- | --- | --- | ------------ | ---- | ------ | ------- | ---- | ------ |
5https://tfhub.dev/google/
universal-sentence-encoder-large/3 ducetheefforttoabout5seconds.
3989

| Acknowledgments |     |     |     |     |     |     | SamuelR.Bowman,GaborAngeli,ChristopherPotts, |     |     |          |       |         |       |
| --------------- | --- | --- | --- | --- | --- | --- | -------------------------------------------- | --- | --- | -------- | ----- | ------- | ----- |
|                 |     |     |     |     |     |     | and Christopher                              |     | D.  | Manning. | 2015. | A large | anno- |
This work has been supported by the German tatedcorpusforlearningnaturallanguageinference.
Research Foundation through the German-Israeli In Proceedings of the 2015 Conference on Empiri-
calMethodsinNaturalLanguageProcessing,pages
ProjectCooperation(DIP,grantDA1600/1-1and
632–642,Lisbon,Portugal.AssociationforCompu-
| grantGU798/17-1). |     | Ithasbeenco-fundedbythe |                 |           |            |         | tationalLinguistics. |      |       |         |         |              |        |
| ----------------- | --- | ----------------------- | --------------- | --------- | ---------- | ------- | -------------------- | ---- | ----- | ------- | ------- | ------------ | ------ |
| German Federal    |     | Ministry                | of              | Education |            | and Re- |                      |      |       |         |         |              |        |
|                   |     |                         |                 |           |            |         | Daniel Cer,          | Mona | Diab, | Eneko   | Agirre, | Iigo         | Lopez- |
| search (BMBF)     |     | under                   | the promotional |           | references |         |                      |      |       |         |         |              |        |
|                   |     |                         |                 |           |            |         | Gazpio,              | and  | Lucia | Specia. | 2017.   | SemEval-2017 |        |
03VP02540(ArgumenText).
|     |     |     |     |     |     |     | Task             | 1: Semantic |         | Textual | Similarity  | Multilingual |          |
| --- | --- | --- | --- | --- | --- | --- | ---------------- | ----------- | ------- | ------- | ----------- | ------------ | -------- |
|     |     |     |     |     |     |     | and Crosslingual |             | Focused |         | Evaluation. | In           | Proceed- |
ingsofthe11thInternationalWorkshoponSemantic
|     |     |     |     |     |     |     | Evaluation |     | (SemEval-2017), |     | pages | 1–14, | Vancou- |
| --- | --- | --- | --- | --- | --- | --- | ---------- | --- | --------------- | --- | ----- | ----- | ------- |
References
ver,Canada.
| Eneko Agirre, | Carmen |       | Banea,           | Claire | Cardie, | Daniel |             |           |        |          |           |       |           |
| ------------- | ------ | ----- | ---------------- | ------ | ------- | ------ | ----------- | --------- | ------ | -------- | --------- | ----- | --------- |
|               |        |       |                  |        |         |        | Daniel Cer, | Yinfei    | Yang,  | Sheng-yi |           | Kong, | Nan Hua,  |
| Cer, Mona     | Diab,  | Aitor | Gonzalez-Agirre, |        |         | Weiwei |             |           |        |          |           |       |           |
|               |        |       |                  |        |         |        | Nicole      | Limtiaco, | Rhomni |          | St. John, | Noah  | Constant, |
Guo,InigoLopez-Gazpio,MontseMaritxalar,Rada Mario Guajardo-Cespedes, Steve Yuan, Chris Tar,
Mihalcea,GermanRigau,LarraitzUria,andJanyce
|                 |                    |          |                         |     |              |     | Yun-Hsuan | Sung,     | Brian    | Strope, |          | and Ray | Kurzweil. |
| --------------- | ------------------ | -------- | ----------------------- | --- | ------------ | --- | --------- | --------- | -------- | ------- | -------- | ------- | --------- |
| Wiebe.2015.     | SemEval-2015Task2: |          |                         |     | SemanticTex- |     |           |           |          |         |          |         |           |
|                 |                    |          |                         |     |              |     | 2018.     | Universal | Sentence |         | Encoder. | arXiv   | preprint  |
| tualSimilarity, |                    | English, | SpanishandPilotonInter- |     |              |     |           |           |          |         |          |         |           |
arXiv:1803.11175.
| pretability. | In  | Proceedings |     | of the | 9th International |     |     |     |     |     |     |     |     |
| ------------ | --- | ----------- | --- | ------ | ----------------- | --- | --- | --- | --- | --- | --- | --- | --- |
WorkshoponSemanticEvaluation(SemEval2015),
|     |     |     |     |     |     |     | AlexisConneauandDouweKiela.2018. |     |     |     |     | SentEval:An |     |
| --- | --- | --- | --- | --- | --- | --- | -------------------------------- | --- | --- | --- | --- | ----------- | --- |
pages 252–263, Denver, Colorado. Association for EvaluationToolkitforUniversalSentenceRepresen-
ComputationalLinguistics. tations. arXivpreprintarXiv:1803.05449.
AlexisConneau,DouweKiela,HolgerSchwenk,Lo¨ıc
| Eneko Agirre, | Carmen    |       | Banea,           | Claire | Cardie, | Daniel |           |     |           |          |     |                  |     |
| ------------- | --------- | ----- | ---------------- | ------ | ------- | ------ | --------- | --- | --------- | -------- | --- | ---------------- | --- |
|               |           |       |                  |        |         |        | Barrault, | and | Antoine   | Bordes.  |     | 2017. Supervised |     |
| Cer, Mona     | Diab,     | Aitor | Gonzalez-Agirre, |        |         | Weiwei |           |     |           |          |     |                  |     |
|               |           |       |                  |        |         |        | Learning  | of  | Universal | Sentence |     | Representations  |     |
| Guo, Rada     | Mihalcea, |       | German           | Rigau, | and     | Janyce |           |     |           |          |     |                  |     |
Wiebe.2014. SemEval-2014Task10: Multilingual fromNaturalLanguageInferenceData. InProceed-
|          |         |             |     | Proceedings |     | of the | ings of    | the 2017 | Conference |             | on  | Empirical | Methods  |
| -------- | ------- | ----------- | --- | ----------- | --- | ------ | ---------- | -------- | ---------- | ----------- | --- | --------- | -------- |
| Semantic | Textual | Similarity. |     | In          |     |        |            |          |            |             |     |           |          |
|          |         |             |     |             |     |        | in Natural | Language |            | Processing, |     | pages     | 670–680, |
8thInternationalWorkshoponSemanticEvaluation
|                |     |             |     |         |             |     | Copenhagen, |     | Denmark. | Association |     | for | Computa- |
| -------------- | --- | ----------- | --- | ------- | ----------- | --- | ----------- | --- | -------- | ----------- | --- | --- | -------- |
| (SemEval2014), |     | pages81–91, |     | Dublin, | Ireland.As- |     |             |     |          |             |     |     |          |
tionalLinguistics.
sociationforComputationalLinguistics.
|     |     |     |     |     |     |     | Jacob Devlin, |     | Ming-Wei | Chang, |     | Kenton | Lee, and |
| --- | --- | --- | --- | --- | --- | --- | ------------- | --- | -------- | ------ | --- | ------ | -------- |
EnekoAgirre,CarmenBanea,DanielM.Cer,MonaT. Kristina Toutanova. 2018. BERT: Pre-training of
| Diab, Aitor | Gonzalez-Agirre, |     |     | Rada | Mihalcea, | Ger- |     |     |     |     |     |     |     |
| ----------- | ---------------- | --- | --- | ---- | --------- | ---- | --- | --- | --- | --- | --- | --- | --- |
DeepBidirectionalTransformersforLanguageUn-
| man Rigau, | and | Janyce   | Wiebe.  | 2016.       |     | SemEval- |              |     |                                |     |     |     |     |
| ---------- | --- | -------- | ------- | ----------- | --- | -------- | ------------ | --- | ------------------------------ | --- | --- | --- | --- |
|            |     |          |         |             |     |          | derstanding. |     | arXivpreprintarXiv:1810.04805. |     |     |     |     |
| 2016 Task  | 1:  | Semantic | Textual | Similarity, |     | Mono-    |              |     |                                |     |     |     |     |
lingual and Cross-Lingual Evaluation. In Proceed- BillDolan,ChrisQuirk,andChrisBrockett.2004. Un-
ings of the 10th International Workshop on Seman- supervised Construction of Large Paraphrase Cor-
tic Evaluation, SemEval@NAACL-HLT 2016, San pora: Exploiting Massively Parallel News Sources.
Diego,CA,USA,June16-17,2016,pages497–511. In Proceedings of the 20th International Confer-
|     |     |     |     |     |     |     | ence | on Computational |     | Linguistics, |     | COLING | ’04, |
| --- | --- | --- | --- | --- | --- | --- | ---- | ---------------- | --- | ------------ | --- | ------ | ---- |
EnekoAgirre,DanielCer,MonaDiab,AitorGonzalez- Stroudsburg, PA, USA. Association for Computa-
| Agirre,andWeiweiGuo.2013. |     |         |             | *SEM2013shared |        |       | tionalLinguistics. |     |     |     |     |     |     |
| ------------------------- | --- | ------- | ----------- | -------------- | ------ | ----- | ------------------ | --- | --- | --- | --- | --- | --- |
|                           |     |         |             |                | Second | Joint |                    |     |     |     |     |     |     |
| task: Semantic            |     | Textual | Similarity. |                | In     |       |                    |     |     |     |     |     |     |
LiatEinDor,YosiMass,AlonHalfon,EladVenezian,
| Conference   | on     | Lexical    | and            | Computational |          | Seman-   |              |              |                                  |       |           |           |      |
| ------------ | ------ | ---------- | -------------- | ------------- | -------- | -------- | ------------ | ------------ | -------------------------------- | ----- | --------- | --------- | ---- |
|              |        |            |                |               |          |          | Ilya         | Shnayderman, |                                  | Ranit | Aharonov, | and       | Noam |
| tics (*SEM), | Volume |            | 1: Proceedings |               | of       | the Main |              |              |                                  |       |           |           |      |
|              |        |            |                |               |          |          | Slonim.2018. |              | LearningThematicSimilarityMetric |       |           |           |      |
| Conference   | and    | the Shared |                | Task:         | Semantic | Textual  |              |              |                                  |       |           |           |      |
|              |        |            |                |               |          |          | from         | Article      | Sections                         | Using | Triplet   | Networks. | In   |
Similarity,pages32–43,Atlanta,Georgia,USA.As-
|     |     |     |     |     |     |     | Proceedings |     | of the | 56th Annual |     | Meeting | of the As- |
| --- | --- | --- | --- | --- | --- | --- | ----------- | --- | ------ | ----------- | --- | ------- | ---------- |
sociationforComputationalLinguistics.
sociationforComputationalLinguistics(Volume2:
|               |      |     |       |        |      |           | Short | Papers), | pages | 49–54, | Melbourne, |     | Australia. |
| ------------- | ---- | --- | ----- | ------ | ---- | --------- | ----- | -------- | ----- | ------ | ---------- | --- | ---------- |
| Eneko Agirre, | Mona |     | Diab, | Daniel | Cer, | and Aitor |       |          |       |        |            |     |            |
AssociationforComputationalLinguistics.
| Gonzalez-Agirre. |     | 2012. | SemEval-2012 |     |     | Task 6: A |     |     |     |     |     |     |     |
| ---------------- | --- | ----- | ------------ | --- | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
Pilot on Semantic Textual Similarity. In Proceed- Felix Hill, Kyunghyun Cho, and Anna Korhonen.
ings of the First Joint Conference on Lexical and 2016. LearningDistributedRepresentationsofSen-
Computational Semantics - Volume 1: Proceedings tences from Unlabelled Data. In Proceedings of
of the Main Conference and the Shared Task, and the 2016 Conference of the North American Chap-
Volume 2: Proceedings of the Sixth International ter of the Association for Computational Linguis-
Workshop on Semantic Evaluation, SemEval ’12, tics: Human Language Technologies, pages 1367–
pages385–393,Stroudsburg,PA,USA.Association 1377, San Diego, California. Association for Com-
| forComputationalLinguistics. |     |     |     |     |     |     | putationalLinguistics. |     |     |     |     |     |     |
| ---------------------------- | --- | --- | --- | --- | --- | --- | ---------------------- | --- | --- | --- | --- | --- | --- |
3990

Minqing Hu and Bing Liu. 2004. Mining and Sum- BoPangandLillianLee.2005. SeeingStars: Exploit-
marizingCustomerReviews. InProceedingsofthe ing Class Relationships for Sentiment Categoriza-
Tenth ACM SIGKDD International Conference on tionwithRespecttoRatingScales. InProceedings
Knowledge Discovery and Data Mining, KDD ’04, of the 43rd Annual Meeting of the Association for
pages168–177,NewYork,NY,USA.ACM. Computational Linguistics (ACL’05), pages 115–
124,AnnArbor,Michigan.AssociationforCompu-
| Samuel Humeau,                      |            | Kurt  | Shuster, | Marie-Anne        | Lachaux,     |       | tationalLinguistics. |         |            |                          |                  |       |          |
| ----------------------------------- | ---------- | ----- | -------- | ----------------- | ------------ | ----- | -------------------- | ------- | ---------- | ------------------------ | ---------------- | ----- | -------- |
| and Jason                           | Weston.    |       | 2019.    | Real-time         | Inference    |       |                      |         |            |                          |                  |       |          |
|                                     |            |       |          |                   |              |       | Jeffrey Pennington,  |         |            | Richard                  | Socher,          | and   | Christo- |
| in Multi-sentence                   |            | Tasks |          | with Deep         | Pretrained   |       |                      |         |            |                          |                  |       |          |
|                                     |            |       |          |                   |              |       | pherD.Manning.2014.  |         |            | GloVe:                   | GlobalVectorsfor |       |          |
| Transformers.                       |            | arXiv | preprint | arXiv:1905.01969, |              |       |                      |         |            |                          |                  |       |          |
| abs/1905.01969.                     |            |       |          |                   |              |       | WordRepresentation.  |         |            | InEmpiricalMethodsinNat- |                  |       |          |
|                                     |            |       |          |                   |              |       | ural Language        |         | Processing |                          | (EMNLP),         | pages | 1532–    |
| JeffJohnson,MatthijsDouze,andHerve´ |            |       |          |                   | Je´gou.2017. |       | 1543.                |         |            |                          |                  |       |          |
| Billion-scale                       | similarity |       | search   | with              | GPUs.        | arXiv |                      |         |            |                          |                  |       |          |
|                                     |            |       |          |                   |              |       | Yifan Qiao,          | Chenyan |            | Xiong,                   | Zheng-Hao        |       | Liu, and |
preprintarXiv:1702.08734.
|             |       |      |        |     |                |     | Zhiyuan | Liu.    | 2019. | Understanding |     |       | the Be-  |
| ----------- | ----- | ---- | ------ | --- | -------------- | --- | ------- | ------- | ----- | ------------- | --- | ----- | -------- |
|             |       |      |        |     |                |     | haviors | of BERT |       | in Ranking.   |     | arXiv | preprint |
| Ryan Kiros, | Yukun | Zhu, | Ruslan | R   | Salakhutdinov, |     |         |         |       |               |     |       |          |
arXiv:1904.07531.
| Richard | Zemel, | Raquel | Urtasun, | Antonio | Torralba, |     |     |     |     |     |     |     |     |
| ------- | ------ | ------ | -------- | ------- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
and Sanja Fidler. 2015. Skip-Thought Vectors. In NilsReimers,PhilipBeyer,andIrynaGurevych.2016.
C.Cortes,N.D.Lawrence,D.D.Lee,M.Sugiyama, Task-OrientedIntrinsicEvaluationofSemanticTex-
| and R. | Garnett,   | editors, | Advances |           | in Neural  | Infor- |                  |            |     |                  |     |             |        |
| ------ | ---------- | -------- | -------- | --------- | ---------- | ------ | ---------------- | ---------- | --- | ---------------- | --- | ----------- | ------ |
|        |            |          |          |           |            |        | tual Similarity. |            | In  | Proceedings      | of  | the 26th    | Inter- |
| mation | Processing | Systems  |          | 28, pages | 3294–3302. |        |                  |            |     |                  |     |             |        |
|        |            |          |          |           |            |        | national         | Conference |     | on Computational |     | Linguistics |        |
CurranAssociates,Inc.
(COLING),pages87–96.
XinLiandDanRoth.2002. LearningQuestionClassi- Nils Reimers and Iryna Gurevych. 2018. Why Com-
fiers. InProceedingsofthe19thInternationalCon- paring Single Performance Scores Does Not Al-
ference on Computational Linguistics - Volume 1, low to Draw Conclusions About Machine Learn-
COLING ’02, pages 1–7, Stroudsburg, PA, USA. arXiv preprint arXiv:1803.09578,
ing Approaches.
AssociationforComputationalLinguistics.
abs/1803.09578.
YinhanLiu,MyleOtt,NamanGoyal,JingfeiDu,Man- Nils Reimers, Benjamin Schiller, Tilman Beck, Jo-
dar Joshi, Danqi Chen, Omer Levy, Mike Lewis, hannes Daxenberger, Christian Stab, and Iryna
Luke Zettlemoyer, and Veselin Stoyanov. 2019. Gurevych. 2019. Classification and Clustering of
RoBERTa: A Robustly Optimized BERT Pretrain- ArgumentswithContextualizedWordEmbeddings.
InProceedingsofthe57thAnnualMeetingoftheAs-
| ingApproach. |     | arXivpreprintarXiv:1907.11692. |     |     |     |     |     |     |     |     |     |     |     |
| ------------ | --- | ------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
sociationforComputationalLinguistics,pages567–
Marco Marelli, Stefano Menini, Marco Baroni, Luisa 578,Florence,Italy.AssociationforComputational
| Bentivogli,   | Raffaella |                | Bernardi,     | and      | Roberto    | Zam- | Linguistics.     |       |          |               |         |           |          |
| ------------- | --------- | -------------- | ------------- | -------- | ---------- | ---- | ---------------- | ----- | -------- | ------------- | ------- | --------- | -------- |
| parelli.      | 2014.     | A SICK         | cure          | for the  | evaluation | of   |                  |       |          |               |         |           |          |
|               |           |                |               |          |            |      | Florian Schroff, |       | Dmitry   | Kalenichenko, |         | and       | James    |
| compositional |           | distributional |               | semantic | models.    | In   |                  |       |          |               |         |           |          |
|               |           |                |               |          |            |      | Philbin.         | 2015. | FaceNet: | A             | Unified | Embedding | for      |
| Proceedings   | of        | the Ninth      | International |          | Conference |      |                  |       |          |               |         |           |          |
|               |           |                |               |          |            |      | Face Recognition |       | and      | Clustering.   |         | arXiv     | preprint |
onLanguageResourcesandEvaluation(LREC’14),
arXiv:1503.03832,abs/1503.03832.
| pages 216–223, |     | Reykjavik, |     | Iceland. | European | Lan- |     |     |     |     |     |     |     |
| -------------- | --- | ---------- | --- | -------- | -------- | ---- | --- | --- | --- | --- | --- | --- | --- |
guageResourcesAssociation(ELRA).
|              |               |        |                       |           |     |       | Richard                | Socher,               | Alex | Perelygin,             |        | Jean Wu,   | Jason |
| ------------ | ------------- | ------ | --------------------- | --------- | --- | ----- | ---------------------- | --------------------- | ---- | ---------------------- | ------ | ---------- | ----- |
|              |               |        |                       |           |     |       | Chuang,                | ChristopherD.Manning, |      |                        |        | AndrewNg,  | and   |
| ChandlerMay, | AlexWang,     |        | ShikhaBordia,SamuelR. |           |     |       |                        |                       |      |                        |        |            |       |
|              |               |        |                       |           |     |       | ChristopherPotts.2013. |                       |      | RecursiveDeepModelsfor |        |            |       |
| Bowman,      | and           | Rachel | Rudinger.             | 2019.     | On  | Mea-  |                        |                       |      |                        |        |            |       |
|              |               |        |                       |           |     |       | Semantic               | Compositionality      |      |                        | Over a | Sentiment  | Tree- |
| suring       | Social Biases |        | in Sentence           | Encoders. |     | arXiv |                        |                       |      |                        |        |            |       |
|              |               |        |                       |           |     |       | bank.                  | In Proceedings        |      | of the                 | 2013   | Conference | on    |
preprintarXiv:1903.10561.
|              |       |        |     |         |     |         | Empirical  | Methods    |     | in Natural | Language    |     | Process- |
| ------------ | ----- | ------ | --- | ------- | --- | ------- | ---------- | ---------- | --- | ---------- | ----------- | --- | -------- |
|              |       |        |     |         |     |         | ing, pages | 1631–1642, |     | Seattle,   | Washington, |     | USA.     |
| Amita Misra, | Brian | Ecker, | and | Marilyn | A.  | Walker. |            |            |     |            |             |     |          |
AssociationforComputationalLinguistics.
| 2016. | Measuring | the | Similarity | of  | Sentential | Ar- |     |     |     |     |     |     |     |
| ----- | --------- | --- | ---------- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |
guments in Dialogue. In Proceedings of the SIG- Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob
| DIAL 2016 | Conference, |     | The | 17th | Annual | Meeting |            |       |        |       |     |        |        |
| --------- | ----------- | --- | --- | ---- | ------ | ------- | ---------- | ----- | ------ | ----- | --- | ------ | ------ |
|           |             |     |     |      |        |         | Uszkoreit, | Llion | Jones, | Aidan | N   | Gomez, | Łukasz |
oftheSpecialInterestGrouponDiscourseandDi-
|         |       |           |       |     |          |     | Kaiser,andIlliaPolosukhin.2017. |     |           |     |             | AttentionisAll |         |
| ------- | ----- | --------- | ----- | --- | -------- | --- | ------------------------------- | --- | --------- | --- | ----------- | -------------- | ------- |
| alogue, | 13-15 | September | 2016, | Los | Angeles, | CA, |                                 |     |           |     |             |                |         |
|         |       |           |       |     |          |     | you Need.                       | In  | I. Guyon, | U.  | V. Luxburg, | S.             | Bengio, |
USA,pages276–287. H.Wallach,R.Fergus,S.Vishwanathan,andR.Gar-
|                           |     |     |     |                    |     |     | nett, editors, |     | Advances | in Neural |     | Information | Pro- |
| ------------------------- | --- | --- | --- | ------------------ | --- | --- | -------------- | --- | -------- | --------- | --- | ----------- | ---- |
| BoPangandLillianLee.2004. |     |     |     | ASentimentalEduca- |     |     |                |     |          |           |     |             |      |
cessingSystems30,pages5998–6008.
| tion: Sentiment |     | Analysis | Using | Subjectivity |     | Sum- |     |     |     |     |     |     |     |
| --------------- | --- | -------- | ----- | ------------ | --- | ---- | --- | --- | --- | --- | --- | --- | --- |
marization Based on Minimum Cuts. In Proceed- Janyce Wiebe, Theresa Wilson, and Claire Cardie.
ings of the 42nd Meeting of the Association for 2005. Annotating Expressions of Opinions and
ComputationalLinguistics(ACL’04),MainVolume, Emotions in Language. Language Resources and
| pages271–278,Barcelona,Spain. |     |     |     |     |     |     | Evaluation,39(2):165–210. |     |     |     |     |     |     |
| ----------------------------- | --- | --- | --- | --- | --- | --- | ------------------------- | --- | --- | --- | --- | --- | --- |
3991

AdinaWilliams,NikitaNangia,andSamuelBowman.
2018. A Broad-Coverage Challenge Corpus for
SentenceUnderstandingthroughInference. InPro-
ceedingsofthe2018ConferenceoftheNorthAmer-
ican Chapter of the Association for Computational
Linguistics: Human Language Technologies, Vol-
ume1(LongPapers),pages1112–1122.Association
forComputationalLinguistics.
YinfeiYang, SteveYuan, DanielCer,Sheng-YiKong,
Noah Constant, Petr Pilar, Heming Ge, Yun-hsuan
Sung, Brian Strope, and Ray Kurzweil. 2018.
LearningSemanticTextualSimilarityfromConver-
sations. In Proceedings of The Third Workshop
on Representation Learning for NLP, pages 164–
174,Melbourne,Australia.AssociationforCompu-
tationalLinguistics.
Zhilin Yang, Zihang Dai, Yiming Yang, Jaime G.
Carbonell, Ruslan Salakhutdinov, and Quoc V. Le.
2019. XLNet: GeneralizedAutoregressivePretrain-
ing for Language Understanding. arXiv preprint
arXiv:1906.08237,abs/1906.08237.
Tianyi Zhang, Varsha Kishore, Felix Wu, Kilian Q.
Weinberger, and Yoav Artzi. 2019. BERTScore:
Evaluating Text Generation with BERT. arXiv
preprintarXiv:1904.09675.
3992