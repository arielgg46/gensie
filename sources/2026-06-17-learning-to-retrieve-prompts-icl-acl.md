---
type: source
source_type: paper
url: https://aclanthology.org/2022.naacl-main.191.pdf
title: "Learning To Retrieve Prompts for In-Context Learning"
fetched_at: 2026-06-17T15:17:31-05:00
fetcher: markitdown
---
|     | Learning |           | To  | Retrieve | Prompts        | for | In-Context     |     | Learning |     |     |
| --- | -------- | --------- | --- | -------- | -------------- | --- | -------------- | --- | -------- | --- | --- |
|     |          | OhadRubin |     |          | JonathanHerzig |     | JonathanBerant |     |          |     |     |
TheBlavatnikSchoolofComputerScience,TelAvivUniversity
{ohad.rubin,jonathan.herzig,joberant}@cs.tau.ac.il
Abstract
|     |     |     |     |     |     |     |     |     | Retriever | What is the length of the  |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --------- | -------------------------- | --- |
longest river in the usa?
| In-contextlearningisarecentparadigminnat- |     |     |     |     |     |     |     |     |     |     | Question |
| ----------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- |
Retriever Index
| urallanguageunderstanding,wherealargepre- |     |     |     |     |     |                               |     | Similar examples         |     |                         |     |
| ----------------------------------------- | --- | --- | --- | --- | --- | ----------------------------- | --- | ------------------------ | --- | ----------------------- | --- |
|                                           |     |     |     |     |     | What is the longest river in  |     | Which states border the  |     | Which states border the |     |
trainedlanguagemodel(LM)observesatestin- the smallest state in the usa? shortest river in the usa?  longest river in the usa?
| stanceandafewtrainingexamplesasitsinput, |     |     |     |     |     | 1) states |     |            |     |            |     |
| ---------------------------------------- | --- | --- | --- | --- | --- | --------- | --- | ---------- | --- | ---------- | --- |
|                                          |     |     |     |     |     |           |     | 1) the usa |     | 1) the usa |     |
anddirectlydecodestheoutputwithoutanyup- 2) size of #1 2) rivers of #1 2) rivers of #1
3) #1 where #2 is the lowest
|     |     |     |     |     |     | 4) rivers of #3 |     | 3) how long are #2 |     | 3) how long are #2 |     |
| --- | --- | --- | --- | --- | --- | --------------- | --- | ------------------ | --- | ------------------ | --- |
datetoitsparameters. However,performance 4) #2 where #3 is the lowest 4) #2 where #3 is the highest
|                                        |     |     |     |     |     | 5) how long are #4            |     | 5) border states of #4 |     | 5) border states of #4 |     |
| -------------------------------------- | --- | --- | --- | --- | --- | ----------------------------- | --- | ---------------------- | --- | ---------------------- | --- |
| hasbeenshowntostronglydependonthese-   |     |     |     |     |     | 6) #4 where #5 is the highest |     |                        |     |                        |     |
| lectedtrainingexamples(termedprompts). |     |     |     |     | In  |                               |     |                        |     |                        |     |
Inference LM
thiswork,weproposeanefficientmethodfor
retrievingpromptsforin-contextlearningus-
1) rivers
2) #1 in the usa
ingannotateddataandanLM.Givenaninput-
3) lengths of #2
outputpair,weestimatetheprobabilityofthe 4) #2 where #3 is longest
5) length of #4
| output | given | the input | and | a candidate | train- |     |     |     |     |     |     |
| ------ | ----- | --------- | --- | ----------- | ------ | --- | --- | --- | --- | --- | --- |
ingexampleastheprompt,andlabeltraining Figure 1: An overview of prompt retrieval: Given a
examplesaspositiveornegativebasedonthis
|     |     |     |     |     |     | question | from | BREAK, | one retrieves | similar | training |
| --- | --- | --- | --- | --- | --- | -------- | ---- | ------ | ------------- | ------- | -------- |
probability. We then train an efficient dense examplesfromanindexofthetrainingset.Thequestion
| retriever | from | this data, | which | is  | used to re- |              |          |     |              |     |              |
| --------- | ---- | ---------- | ----- | --- | ----------- | ------------ | -------- | --- | ------------ | --- | ------------ |
|           |      |            |       |     |             | and training | examples |     | (the prompt) | are | passed to an |
trievetrainingexamplesaspromptsattesttime.
inferenceLMthatdecodestheoutput.
Weevaluateourapproachonthreesequence-to-
sequencetaskswherelanguageutterancesare
mappedtomeaningrepresentations, andfind (2021a)showedthatdownstreamperformancecan
thatitsubstantiallyoutperformspriorworkand varywidelydependingonthechoiceofin-context
multiplebaselinesacrosstheboard.
|     |     |     |     |     |     | examples. | Thishassparkedinterestinpromptre- |     |             |     |                |
| --- | --- | --- | --- | --- | --- | --------- | --------------------------------- | --- | ----------- | --- | -------------- |
|     |     |     |     |     |     | trieval   | (see Fig.                         | 1), | where given | a   | test instance, |
1 Introduction
trainingexamplesarechosenforthepromptbased
Thestrikinglanguageskillsandworldknowledge onsomesimilaritymetric. Recentworkhaseither
embedded in large pre-trained language models usedoff-the-shelfunsupervisedsimilaritymetrics,
(LMs)(Devlinetal.,2019;Petronietal.,2019;Raf- or trained a prompt retriever to select examples
feletal.,2020;Brownetal.,2020)haverecently basedonsurfacesimilarity(Dasetal.,2021).
ledtoin-contextlearning,anewparadigminnatu- In this work, we suggest to use language mod-
rallanguageunderstanding. Underthisparadigm, elsthemselvestolabelexamplesthatcanserveas
a language model is given a prompt, which typi- good prompts, and train a prompt retriever from
callycontainsafewtrainingexamples,aswellasa this signal. To train the retriever (see Fig. 2), we
testinstanceasinput,andgeneratestheoutputfor assumeaccesstoatrainingsetofinput-outputpairs
thetestinstancedirectly,withoutanyupdatetoits and to a scoring LM, i.e., a language model that
parameters. Thisapproachwasfirstintroducedin will be used to score prompts. For each training
GPT-3(Brownetal.,2020),buthasquicklyspread example (x,y), we go over other candidate train-
tootherLMs(Lieberetal.,2021;Duetal.,2021; ingexamples,andestimatetheprobability,accord-
| Raeetal.,2021). |     |     |     |     |     | ingtothescoringLM,ofy |     |     | conditionedonxand |     |     |
| --------------- | --- | --- | --- | --- | --- | --------------------- | --- | --- | ----------------- | --- | --- |
Anattractivepropertyofin-contextlearningis thecandidateprompt. Welabeltrainingexamples
that it provides a single model for multiple lan- that lead to high probability as positive and low
guage understanding tasks. However, Liu et al. probabilityasnegativeandtrainapromptretriever
2655
Proceedingsofthe2022ConferenceoftheNorthAmericanChapteroftheAssociationforComputationalLinguistics:
HumanLanguageTechnologies,pages2655-2671
July10-15,2022©2022AssociationforComputationalLinguistics

D
Figure2: AnoverviewofourapproachfortrainingEPR.Givenatrainingexample,weuseanunsupervisedretriever
R u toobtainasetofcandidates. WethenpassthecandidatestoascoringLMandlabelthetop-kandthebottom-k
aspositiveandnegativeexamples,respectively. Last,weusethistrainingdatatotrainadenseretriever.
from this data using contrastive learning. We ar- 2020), a benchmark for mapping questions to a
gue that using an LM for labeling examples is a language-based meaning representation. We ob-
better proxy for training a retriever compared to servethatEPRsubstantiallyimprovesperformance
previously-proposedsurfacesimilarityheuristics. comparedtopriorworkonpromptretrieval. When
Importantly, when creating the training data, we the scoring LM and inference LM are identical
haveaccesstothegoldlabely,whichcanbeused (using GPT-NEO (Black et al., 2021)), perfor-
toobtainahigh-qualitysetofcandidateprompts. mance compared to the best baseline improves
Thisleadstogoodpositiveexamplesandhardneg- from 26% to 31.9% on BREAK, from 57% to
ative examples, which are beneficial for training 64.2% on MTOP, and from 51.4% to 54.3% on
withacontrastiveobjective. SMCALFLOW. WhenusingGPT-NEOasaproxy
|     |     |     |     |     |     |     | for larger | LMs (GPT-J, | GPT-3, and | CODEX), | we  |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ----------- | ---------- | ------- | --- |
UsingascoringLMtotrainanefficientretriever
observesimilargains,whereperformanceimproves
| forapotentiallydifferenttesttimeinferenceLM |     |     |     |     |     | is  |     |     |     |     |     |
| ------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
substantiallyinallcases.
| beneficialintwoscenarios. |     |     | First,whenthescoring |     |     |     |     |     |     |     |     |
| ------------------------- | --- | --- | -------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
Toconclude,weproposeanapproachforretriev-
LMissmallerthantheinferenceLMandservesas
|                         |         |              |            |            |               |      | ing training             | examples | for in-context      | learning      | in  |
| ----------------------- | ------- | ------------ | ---------- | ---------- | ------------- | ---- | ------------------------ | -------- | ------------------- | ------------- | --- |
| a proxy                 | for it. | This results | in         | cheap      | and efficient |      |                          |          |                     |               |     |
|                         |         |              |            |            |               |      | large language           | models,  | and show it         | substantially |     |
| data generation         |         | for the      | retriever, | accessible |               | to a |                          |          |                     |               |     |
|                         |         |              |            |            |               |      | outperformspriormethods. |          | Givenrecentdevelop- |               |     |
| widerangeofresearchers. |         |              | Second,    |            | ourapproach   |      |                          |          |                     |               |     |
mentsinscalingLMs,designingefficientmethods
canbeusedevenwhenthescoringandinference
forinteractingwithLMsisanimportantdirection
| LMs are | identical | (e.g., | both | are GPT-3). | This | is  |     |     |     |     |     |
| ------- | --------- | ------ | ---- | ----------- | ---- | --- | --- | --- | --- | --- | --- |
forfutureresearch.
| beneficial                   | when | we do    | not have | access           | to model   |     |               |                 |     |     |     |
| ---------------------------- | ---- | -------- | -------- | ---------------- | ---------- | --- | ------------- | --------------- | --- | --- | --- |
| parameters                   | and  | can only | use      | it as            | a service, | an  |               |                 |     |     |     |
|                              |      |          |          |                  |            |     | 2 Background: | PromptRetrieval |     |     |     |
| increasinglypopularparadigm. |      |          |          | Inthiscase,weuse |            |     |               |                 |     |     |     |
theLMtotrainalight-weightretrieverthatisonly Given a training set =
|     |     |     |     |     |     |     | Problem | setup |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------- | ----- | --- | --- | --- |
D
tasked with learning a similarity function. More (x ,y ) n of input-output sequences, and a
i i }i=1
| generally,giventhatthescaleofLMsislikelyto |     |     |     |     |     |     | {            |         |                  |              |     |
| ------------------------------------------ | --- | --- | --- | --- | --- | --- | ------------ | ------- | ---------------- | ------------ | --- |
|                                            |     |     |     |     |     |     | test example | x , our | goal is to train | a retriever, |     |
test
| keepincreasingintheforeseeablefuture,onecan |     |     |     |     |     |     | R(x , | ),                 |          |             |     |
| ------------------------------------------- | --- | --- | --- | --- | --- | --- | ----- | ------------------ | -------- | ----------- | --- |
|                                             |     |     |     |     |     |     | test  | that will retrieve | a subset | of training |     |
D
viewourapproachforEfficientPromptRetrieval, examples = (x ,y ) m ,wherem n.
|                                            |     |     |     |     |     |     |                     | j j | }j=1          |     |     |
| ------------------------------------------ | --- | --- | --- | --- | --- | --- | ------------------- | --- | ------------- | --- | --- |
| orEPR,asamethodforinterfacingandlearningto |     |     |     |     |     |     |                     | P { | ⊂ D           |     | ≪   |
|                                            |     |     |     |     |     |     | Wesuccinctlyreferto |     | astheprompt.1 |     |     |
| interactwithlargeLMs.                      |     |     |     |     |     |     |                     | P   |               |     |     |
GivenaninferenceLM,g,agoodpromptshould
We empirically test EPR on three structured lead to the target output sequence when the test
examplex
sequence-to-sequence tasks, where input natural test isconcatenatedtotheprompt and
P
|     |     |     |     |     |     |     | passedasaprefixtog. |     | Specifically,decodingfrom |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------- | --- | ------------------------- | --- | --- |
languageutterancesaremappedtoameaningrep-
| resentation: | MTOP |     | (Li et | al., 2021) | and | SM- |     |     |     |     |     |
| ------------ | ---- | --- | ------ | ---------- | --- | --- | --- | --- | --- | --- | --- |
1Promptoftenreferstoanaturallanguagetemplatefilled
CALFLOW(Andreasetal.,2020),whichfocuson
byaninputexample(Liuetal.,2021b),buthereitdenotesthe
task-orienteddialogue,andBREAK(Wolfsonetal., sequenceoftrainingexamplesprovidedasinputtotheLM.
2656

theLMg([ ;x ])shouldyieldy . Inthiswork, To obtain a high-quality candidate set of train-
|     |     | P test |     |     | test |     |     |     |     |     |     |     |     |
| --- | --- | ------ | --- | --- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
wefocusonstructuredtasks,suchassemanticpars- ing examples, we take advantage of an unsuper-
ing,wherexisanaturallanguageutteranceandy visedretriever, ¯= R ((x,y), ). Forthechoice
u
|     |     |     |     |     |     |     |     |     |     | E   |     | D   |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
isameaningrepresentationforthatutterance. oftheunsupervisedretriever,weexperimentwith
|       |      |     |        |         |              |     |     | BM25 (Robertson |     | and | Zaragoza, | 2009), a | sparse |
| ----- | ---- | --- | ------ | ------- | ------------ | --- | --- | --------------- | --- | --- | --------- | -------- | ------ |
| Prior | work | Liu | et al. | (2021a) | investigated |     | the |                 |     |     |           |          |        |
retrieverthatreliesonsurfacetextsimilarity,and
| effect | of  | different | prompts | on  | the | performance |     |     |     |     |     |     |     |
| ------ | --- | --------- | ------- | --- | --- | ----------- | --- | --- | --- | --- | --- | --- | --- |
SBERT(ReimersandGurevych,2019),whichis
| of GPT-3 |     | and demonstrated |     | that | the | choice | of in- |          |       |          |           |           |     |
| -------- | --- | ---------------- | --- | ---- | --- | ------ | ------ | -------- | ----- | -------- | --------- | --------- | --- |
|          |     |                  |     |      |     |        |        | based on | dense | sentence | encoding. | For both, | we  |
contextexamplesstronglyaffectsdownstreamper-
experimentedwithpassingtheretrieverthetraining
| formance. |     | They | used | an unsupervised |     | sentence |     |                               |     |     |     |               |     |
| --------- | --- | ---- | ---- | --------------- | --- | -------- | --- | ----------------------------- | --- | --- | --- | ------------- | --- |
|           |     |      |      |                 |     |          |     | pair(x,y)orthetargetsequencey |     |     |     | only,andfound |     |
encodertoencodetrainingexamples,andretrieved
|     |     |     |     |     |     |     |     | thatusingy | leadstoslightlyhigherperformance. |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ---------- | --------------------------------- | --- | --- | --- | --- |
foreverytestinstanceitsnearestneighbors.
Das et al. (2021) trained a supervised prompt Scoringthecandidateset Onceweretrievethe
¯=
retrieverforknowledge-basequestionanswering. setofcandidates e¯ , ,e¯ foratraining
|     |     |     |     |     |     |     |     |     |         | E   | { 1 ··· | L } |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ------- | --- | ------- | --- | --- |
|     |     |     |     |     |     |     |     |     | (x,y),2 |     |         |     | ¯   |
Theretrieverwastrainedwithsupervisionthatis example we score each candidate e¯ l
∈ E
tailoredforknowledge-basequeries,andrelieson independentlywithascoringLM,gˆ,whichserves
surface similarity between formal queries. Con- as a proxy for the inference LM, g. Specifically,
versely,ourapproachtakesadvantageofthegener- thescoreforacandidatepromptis
ativeLMitselfandisthusmoregeneral.
Shinetal.(2021)usedGPT-3toselectexamples s(e¯ ) = Prob (y e¯ ,x),
|                                         |     |     |     |     |     |     |      |     |     | l   | gˆ  | | l |     |
| --------------------------------------- | --- | --- | --- | --- | --- | --- | ---- | --- | --- | --- | --- | --- | --- |
| forthepromptforfew-shotsemanticparsing. |     |     |     |     |     |     | How- |     |     |     |     |     |     |
whichistheprobabilityundertheLM,gˆ,oftheout-
ever,ratherthantrainingaretriever,theyrandomly
samplealargesetofutterance-programpairsfrom putsequenceconditionedonthecandidateprompt
|     |     |     |     |     |     |     |     | andinputsequence. |     | Thisindicateshowhelpfulthis |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ----------------- | --- | --------------------------- | --- | --- | --- |
thetrainingset,andchoosethosethataresimilar
candidateisfordecodingthetarget(independent
tothetargetinstancequestionaccordingtoGPT-3.
This results in an expensive inference procedure, of all other candidates). We argue this score is a
betterproxyfortheutilityofatrainingexampleat
whereGPT-3isrunhundredsoftimesforeachtest
inferencetimecomparedtopriorapproaches.
instance,unlikeourapproach,whichisbasedona
Weapplythisscoringfunctiontoalltrainingex-
light-weightsub-linearretriever.
amples,anddefineforeachtrainingexampleaset
3 EfficientPromptRetriever ofpositiveexamples ,whichincludesthetop-k
pos
¯ E
|     |     |     |     |     |     |     |     | candidatesin |     | accordingtos(e¯),andasetofneg- |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------ | --- | ------------------------------ | --- | --- | --- |
l
| We  | now       | describe | our       | method | for training   |     | EPR,   |               | E   |                               |     |                |     |
| --- | --------- | -------- | --------- | ------ | -------------- | --- | ------ | ------------- | --- | ----------------------------- | --- | -------------- | --- |
|     |           |          |           |        |                |     |        | ativeexamples |     | neg ,whichincludesthebottom-k |     |                |     |
| an  | efficient | prompt   | retriever |        | for in-context |     | learn- |               |     | E                             |     |                |     |
|     |           |          |           |        |                |     |        | candidatesin  | ¯   | a ccordingtos(e¯).            |     | Thisshouldlead |     |
l
| ing. | Wefirstdescribehowtogeneratelabeleddata |     |     |     |     |     |     |     | E   |     |     |     |     |
| ---- | --------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
torelevantpositiveexamples,assumingthattheset
| (§3.1),  | and | then      | how to  | use | the training | data     | for |               |     | ¯                            |     |     |     |
| -------- | --- | --------- | ------- | --- | ------------ | -------- | --- | ------------- | --- | ---------------------------- | --- | --- | --- |
|          |     |           |         |     |              |          |     | ofcandidates, |     | includesgoodpromptcandidates |     |     |     |
| training | and | inference | (§3.2). |     | Fig. 2       | provides | an  |               | E   |                              |     |     |     |
andhardnegatives,sinceallcandidateshavehigh
overviewofthetrainingprocedure.
|     |     |     |     |     |     |     |     | similaritywith(x,y)accordingtoR |     |     |     | (y, | ). With |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------------------------- | --- | --- | --- | --- | ------- |
u
D
positiveandnegativeexamplesatourdisposal,we
3.1 GeneratingtheTrainingData
cannowapplycontrastivelearning,whichwede-
Ourapproachreliesonfindingwhichtrainingex-
scribenext.
amplescanserveasgoodpromptsforothertraining
examples. Scoringallpairsoftrainingexamplesis 3.2 TrainingandInference
| quadraticin |     |     | ,andthusprohibitive. |     |     | Hence,we |     |          |     |          |           |          |     |
| ----------- | --- | --- | -------------------- | --- | --- | -------- | --- | -------- | --- | -------- | --------- | -------- | --- |
|             |     | |D| |                      |     |     |          |     | Training | Our | training | procedure | proceeds | ex- |
presentamethodforchoosingasetofcandidateex-
actlylikethecontrastivelearningprocedurefrom
¯
| amples                                      |          | D,fromwhichwewillchoosepositive |     |               |     |              |     |                           |     |     |     |                    |     |
| ------------------------------------------- | -------- | ------------------------------- | --- | ------------- | --- | ------------ | --- | ------------------------- | --- | --- | --- | ------------------ | --- |
|                                             | E        | ⊂                               |     |               |     |              |     | DPR(Karpukhinetal.,2020). |     |     |     | Thisprocedurere-   |     |
| and                                         | negative | examples                        |     | for training. |     | Importantly, |     |                           |     |     |     |                    |     |
|                                             |          |                                 |     |               |     |              |     | sultsinaninputencoderE    |     |     | X ( | ),whichreceivesthe |     |
| sincewearenotattesttimeandareonlygenerating |          |                                 |     |               |     |              |     |                           |     |     | ·   |                    |     |
sequenceofinputtokens,x,andapromptencoder
| data                            | for training, |     | we can | use | the target | sequence  |     |                                             |     |        |        |                    |     |
| ------------------------------- | ------------- | --- | ------ | --- | ---------- | --------- | --- | ------------------------------------------- | --- | ------ | ------ | ------------------ | --- |
|                                 |               |     |        |     |            |           |     | E ( ),whichreceivesacandidateprompt,namely, |     |        |        |                    |     |
| y                               |               |     |        |     |            |           |     | P                                           |     |        |        |                    |     |
| toretrieveagoodsetofcandidates. |               |     |        |     |            | Thiscanbe |     | ·                                           |     |        |        |                    |     |
|                                 |               |     |        |     |            |           |     | a concatenation                             |     | of the | tokens | in an input-output |     |
approachedusingasimpleretrievalmethod,given
|     |     |     |     |     |     |     |     | pair. BothencodersareinitializedwithBERT-base |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --------------------------------------------- | --- | --- | --- | --- | --- |
thatourgoalistoretrieveexamplesthataresimilar
¯on(x,y)forsimplicity.
totheinputintermsoftheiroutputsequence,y. 2Weomitthedependenceof
E
2657

(Devlin etal.,2019), and theoutputvector repre- scoringLM,gˆ,issmallerthantheinferenceLM,g,
sentationisgivenbytheCLStoken,asusual. The andwhentheyareidentical.
goaloftrainingistolearnasimilaritymetricsuch
thatgivenatestexamplex ,itwillbesimilarto 4.1 Datasets
test
trainingexamplesthatleadtodecodingofy .
test Wefocusontasksthatmaputterancestomeaning
Our training instances are of the form
representations,wherein-contextexamplescanbe
⟨ x i ,e+ i ,e −i,1 ,...e −i,2B 1⟩ . Where the positive ex- usedtolearnthemappingfrominputstooutputs.
ample e+ is sampled − from the set (i) , and our Examples from each dataset and the number of
i E pos
negativeexamplesconsistofonehardnegativeex- examplesareinTable1.
amplesampledfrom (i) ,B 1positiveexamples • BREAK (Wolfson et al., 2020): A dataset map-
neg
E −
from the other instances in the same mini-batch, pingcomplexnaturallanguagequestionsintoa
andtheB 1hardnegativesfromthoseinstances. language-basedmeaningrepresentation, where
−
We define the similarity score between an input a question is decomposed into an ordered list
and an input-output pair to be the inner product of atomic steps. We use the low-level BREAK
sim(x,e) = E (x) E (e). We can now define subset, containing 44K/7K/8K examples in its
X ⊤ P
thetypicalcontrastivelearningobjectiveandmini- training/development/testsets.
mizeforeachexamplethenegativeloglikelihood
• MTOP (Li et al., 2021): A semantic parsing
ofthepositiveexample:
dataset,focusedontask-orienteddialogue,where
L(x i ,e+ i ,e −i,1 ,...e −i,2B 1 ) (1) commandsaremappedtocomplexnestedqueries
− across11domains. Similartopastwork(Pasu-
= log
esim(xi,e+
i
)
. pat et al., 2021), we use the English subset of
− esim(xi,e+ i )+ 2 j= B 1− 1esim(xi,e−i,j ) MTOP, containing 16K/2K/4K examples in its
training/development/testsets.
AnadvantageofthisapproacPhisthatforbatchsize
B theeffectivebatchsizeisoforderB2,withthe • SMCALFLOW (Andreas et al., 2020): A large
in-batchnegativestrick(Hendersonetal.,2017). English-languagetask-orienteddatasetthatcov-
erstaskssuchascalendar,weather,places,and
Inference After training the input encoder and
people. Themeaningrepresentationisadataflow
promptencoder,weencodetheentiresetoftrain-
program,whichincludesAPIcalls,functioncom-
ingexampleswithE ( )inapre-processingstep
P · positionandcomplexconstraints. SMCALFLOW
using FAISS (Johnson et al., 2017). At test time,
includes 15K development set examples and
givenaninputsequence,x ,wecomputeitsen-
test 134Ktrainingexamples,fromwhichwesample
coding E (x ), and then use maximum inner-
X test arandomsetof44Kexamplesfortraining.
productsearchoverthetrainingdatatofindtheL
mostsimilartrainingexamples,sortedbytheirin-
4.2 BaselinesandOracles
nerproduct(fromhightolow): = (e ,...,e ).
1 L
P Weconsiderthefollowingunsupervisedbaselines,
Thefinalprompt isdeterminedbyC,themax-
′
P whichareappliedattesttimeonly.
imalcontextsizesupportedbytheinferenceLM,
g. Specifically, L L is the largest L such
• RANDOM: werandomlysampleexamplesfrom
′ ′
L′ e + x + ≤ y C, where y is the thetrainingset .
i=1| i | | test | | ′ | ≤ | ′ | D
desiredmaximallengthofthegeneratedoutput. Fi- • SBERT:WeuseSentenceTransformers,
P
nally,wereturntheoutputofgreedydecodingon a library providing BERT-based sen-
g([e L ;e L 1 ;...;e 1 ;x test ]). tence embeddings.3 Specifically, we use
′ ′−
Wenotethatwhileattrainingtimewescoreeach paraphrase-mpnet-base-v2, a 110M
training example independently, at test time the parameter model to encode the test utterance
languagemodelobservesaprompt,i.e.,asequence x and retrieve the examples with the most
test
ofexamples. Weleavemodelingthedependence similarutterancesasin-contextexamples.
betweendifferenttrainingexamplestofuturework.
• BM25: We use the classical sparse retrieval
4 ExperimentalResults methodBM25(RobertsonandZaragoza,2009),
whichisanextensionofTF-IDF,toretrievefor
We now compare EPR to a wide range of unsu-
pervisedandsupervisedbaselines,bothwhenthe 3https://www.sbert.net/index.html.
2658

|     | Dataset | Size | Utterance                        |     |     |     | MeaningRepresentation |     |             |           |      |     |     |
| --- | ------- | ---- | -------------------------------- | --- | --- | --- | --------------------- | --- | ----------- | --------- | ---- | --- | --- |
|     | BREAK   | 60K  | Therearemorebirdsintheimageon    |     |     |     | 1) return             |     | right       | image;    |      |     |     |
|     |         |      | therightthanintheimageontheleft. |     |     |     | 2) return             |     | birds       | in #1;    |      |     |     |
|     |         |      |                                  |     |     |     | 3) return             |     | number      | of #2;    |      |     |     |
|     |         |      |                                  |     |     |     | 4) return             |     | left image; |           |      |     |     |
|     |         |      |                                  |     |     |     | 5) return             |     | birds       | in #4     |      |     |     |
|     |         |      |                                  |     |     |     | 6) return             |     | number      | of #5;    |      |     |     |
|     |         |      |                                  |     |     |     | 7) return             |     | if #3       | is higher | than | #6; |     |
|     | MTOP    |      | callZoey’swife.                  |     |     |     | [IN:CREATE_CALL       |     |             | =         |      |     |     |
22K
|     |     |     |     |     |     |     | [SL:CONTACT         |                   | =   | [IN:GET_CONTACT |            | =   |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------- | ----------------- | --- | --------------- | ---------- | --- | --- |
|     |     |     |     |     |     |     | [SL:CONTACT_RELATED |                   |     |                 | = Zoey]    |     |     |
|     |     |     |     |     |     |     |                     | [SL:TYPE_RELATION |     |                 | = wife]]]] |     |     |
SMCALFLOW Canyoucreatemeanewmeeting (Yield (CreateCommitEventWrapper
148K
|     |     |     | onthursdaymorning? |     |     |     | (CreatePreflightEventWrapper |     |     |     |     |     |     |
| --- | --- | --- | ------------------ | --- | --- | --- | ---------------------------- | --- | --- | --- | --- | --- | --- |
(Event.start_?
|     |     |         |     |                                            |     |     |     | (DateTimeConstraint |     |                  | (Morning) |     |     |
| --- | --- | ------- | --- | ------------------------------------------ | --- | --- | --- | ------------------- | --- | ---------------- | --------- | --- | --- |
|     |     |         |     |                                            |     |     |     | (NextDOW            |     | (Thursday))))))) |           |     |     |
|     |     | Table1: |     | Examplesfromeachofthedatasetsweevaluateon. |     |     |     |                     |     |                  |           |     |     |
each test utterance x the training examples wedefinethescorebetweentwooutputsequence
test
withthemostsimilarutterance. y i and y j to be the F 1 between the two sets of
|               |     |          |     |        |           |     | tokensiny | andy |     | ,omittingstopwords. |     |     |     |
| ------------- | --- | -------- | --- | ------ | --------- | --- | --------- | ---- | --- | ------------------- | --- | --- | --- |
| • BRUTEFORCE: |     | We apply | the | prompt | selection |     |           | i    | j   |                     |     |     |     |
methodforfew-shotsemanticparsingfromShin • EFFICIENT PROMPT RETRIEVAL (EPR): Our
Givenatestexamplex
| etal.(2021). |          |           |     | test | ,wesam-  |     | fullapproachfrom§3. |     |     |     |     |     |     |
| ------------ | -------- | --------- | --- | ---- | -------- | --- | ------------------- | --- | --- | --- | --- | --- | --- |
| ple 200      | training | examples. | For | each | training |     |                     |     |     |     |     |     |     |
Last,wealsoconsidertwooraclemodels.
| example(x |     | ,y ),computeProb |     | (x     | x ),and |     |              |     |     |     |       |               |     |
| --------- | --- | ---------------- | --- | ------ | ------- | --- | ------------ | --- | --- | --- | ----- | ------------- | --- |
|           | i   | i                |     | g test | | i     | •   | BM25-ORACLE: |     |     | We  | score | test examples |     |
usethehighestscoringexamplesfortheprompt.
|         |        |               |          |     |            |     | with BM25                    |      | using   | the      | gold | output sequence |     |
| ------- | ------ | ------------- | -------- | --- | ---------- | --- | ---------------------------- | ---- | ------- | -------- | ---- | --------------- | --- |
| Similar | to us, | this approach | uses     | the | inference  |     |                              |      |         |          |      |                 |     |
|         |        |               |          |     |            |     | R                            | (y , | ). This | provides |      | an upper-bound  |     |
| LM to   | choose | prompts.      | However, | it  | does so at |     | BM25                         | test | D       |          |      |                 |     |
|         |        |               |          |     |            |     | onwhatcanbelearnedbyDR-BM25. |      |         |          |      | EPRcan          |     |
testtime,whichresultsinslowinference.
potentiallyoutperformthisoracle,sinceitstrain-
| Next, | we describe | baselines | that | use | the train- |     |     |     |     |     |     |     |     |
| ----- | ----------- | --------- | ---- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |
ingsignalgoesbeyondsurfacetextsimilarity.
| ing set, | , to | train a prompt | retriever. |     | All super- |     |     |     |     |     |     |     |     |
| -------- | ---- | -------------- | ---------- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |
D
visedmethodssharethefollowingtemplate. First, • LM-ORACLE: Weusetheprocedureforlabeling
¯
acandidateset ofL = 50examplesisretrieved training data at test time. Given a test example
E
withtheunsupervisedretrieverR (y, ). Weuse (x ,y ),wefirstretrieveLcandidatetraining
|     |     |     |     | u   |     |     | test | test |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ---- | ---- | --- | --- | --- | --- | --- |
D
BM25asanunsupervisedretriever,sinceitoutper- exampleswithR (y , ),wethensortthe
|     |     |     |     |     |     |     |     |     | BM25 | test |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---- | ---- | --- | --- | --- |
D
formedSBERT(see§4.4). Wethenscoreeachcan- candidateswiththescoringLMgˆ,estimatingthe
didateprompte¯ ¯ withsomescoringfunction, probabilityofy givenx
|     |     | l   |     |     |     |     |     |     | test |     | test andthecandidate |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---- | --- | -------------------- | --- | --- |
∈ E
andlabelthetop-k promptsaspositiveexamples prompt. ThisprovidesanupperboundforEPR,
and the bottom-k as negative examples (k = 5). sinceEPRistrainedtoemulatethisbehaviour.
| Different               | supervised   | methods  | only    | differ   | in the |          |                     |            |     |         |         |               |       |
| ----------------------- | ------------ | -------- | ------- | -------- | ------ | -------- | ------------------- | ---------- | --- | ------- | ------- | ------------- | ----- |
| scoringfunctionitself.4 |              |          |         |          |        | 4.3      | ExperimentalDetails |            |     |         |         |               |       |
| • DR-BM25:              |              | Here, we | use the | original | BM25   |          |                     |            |     |         |         |               |       |
|                         |              |          |         |          |        | Language |                     | models     |     | In this | work,   | we only       | train |
| scores                  | for labeling | positive | and     | negative | exam-  |          |                     |            |     |         |         |               |       |
|                         |              |          |         |          |        | a        | dense               | retriever, | but | use     | scoring | and inference |       |
plesandtrainingadenseretriever. LMs. For our scoring LM, gˆ, we use GPT-NEO
• CASE-BASED REASONING (CBR): We adapt (Blacketal.,2021),a2.7B-parameterLMtrained
the scoring function from Das et al. (2021), onThePile(Gaoetal.,2021),an825GBEnglish
whichfocusedonknowledge-basequestionan- textcorpus,constructedfromawiderangeofhigh-
| swering. | Theydefinetheweightforapairoflog- |     |     |     |     | qualityresources. |     |     |     |     |     |     |     |
| -------- | --------------------------------- | --- | --- | --- | --- | ----------------- | --- | --- | --- | --- | --- | --- | --- |
icalformstobetheF scorebetweenthetwosets In addition, we consider the following infer-
1
ofrelationsappearinginthoselogicalforms,and ence LMs: (a) GPT-J (Wang and Komatsuzaki,
| use this | weight | to softly | label | their data. | Since |        |     |              |     |     |      |         |        |
| -------- | ------ | --------- | ----- | ----------- | ----- | ------ | --- | ------------ | --- | --- | ---- | ------- | ------ |
|          |        |           |       |             |       | 2021): | a   | 6B-parameter |     | LM, | also | trained | on The |
in our setting we do not assume logical forms, Pile. The advantage in this setup, is that GPT-J
|            |     |          |       |        |        | wastrainedonthesamecorpusas |        |     |         |        |     | GPT-NEO.       | (b) |
| ---------- | --- | -------- | ----- | ------ | ------ | --------------------------- | ------ | --- | ------- | ------ | --- | -------------- | --- |
| 4Results   | for | k 1,5,10 | and L | 50,100 | are in |                             |        |     |         |        |     |                |     |
|            |     | ∈ {      | }     | ∈ {    | }      |                             |        |     |         |        |     |                |     |
| AppendixA. |     |          |       |        |        | GPT-3                       | (Brown |     | et al., | 2020): | A   | 175B-parameter |     |
2659

|     | Model  |     | BREAK | MTOP | SMCALFLOW |     | Model  |     |     | One-shot |     | Full-context |
| --- | ------ | --- | ----- | ---- | --------- | --- | ------ | --- | --- | -------- | --- | ------------ |
|     | RANDOM |     | 1.7   | 7.3  | 8.9       |     | RANDOM |     |     | 1.1      |     | 1.7          |
Unsuper.
| Unsuper. | SBERT       |     | 21.6 | 48.7 | 43.6 |        | BM25              |     |     | 15.2 |     | 26.0 |
| -------- | ----------- | --- | ---- | ---- | ---- | ------ | ----------------- | --- | --- | ---- | --- | ---- |
|          | BM25        |     | 26.0 | 52.9 | 46.1 |        | DR-BM25           |     |     | 14.1 |     | 23.6 |
|          | BRUTEFORCE  |     | 7.7  | 18.1 | 11.1 |        |                   |     |     |      |     |      |
|          |             |     |      |      |      | Super. | CBR               |     |     | 14.5 |     | 25.7 |
|          | DR-BM25     |     | 23.6 | 50.2 | 43.1 |        | EPR               |     |     | 23.0 |     | 31.9 |
| Super.   | CBR         |     | 25.7 | 57.0 | 51.4 |        | BM25-ORACLE       |     |     | 18.0 |     | 32.3 |
|          | EPR(ours)   |     | 31.9 | 64.2 | 54.3 | Oracle | LM-ORACLE         |     |     | 33.3 |     | 43.1 |
|          |             |     |      |      |      |        | ANYCORRECT-ORACLE |     |     | 53.6 |     | -    |
|          | BM25-ORACLE |     | 32.3 | 58.9 | 47.3 |        |                   |     |     |      |     |      |
Oracle
|     | LM-ORACLE |     | 43.1 | 71.6 | 73.7 |         |                      |     |     |       |      |      |
| --- | --------- | --- | ---- | ---- | ---- | ------- | -------------------- | --- | --- | ----- | ---- | ---- |
|     |           |     |      |      |      | Table4: | Developmentresultson |     |     | BREAK | with | GPT- |
Table 2: Development results when GPT-NEO is the NEOintheone-shotsetting.NumbersareLF-EM.Full-
scoring and inference LM. Numbers for BREAK are contextisthecorrespondingnumbersfromTable2.
LF-EM,andforMTOPandSMCALFLOWareEM.
4.4 Results
|     |          | Model |     | BREAK | MTOP |                 |     |           |     |         |         |            |
| --- | -------- | ----- | --- | ----- | ---- | --------------- | --- | --------- | --- | ------- | ------- | ---------- |
|     |          |       |     |       |      | LM-as-a-service |     | Table     | 2   | reports | results | where      |
|     | Unsuper. | BM25  |     | 17.6  | 49.0 |                 |     |           |     |         |         |            |
|     |          |       |     |       |      | the scoring     | and | inference |     | LMs     | are     | identical. |
|     |          | CBR   |     | 18.4  | 57.5 |                 |     |           |     |         |         |            |
Super.
EPR(ours) 23.9 64.4 EPRsubstantiallyoutperformsallotherbaselines.
Specifically,whencomparingtothebestbaseline,
| Table 3: | Test | results | where GPT-NEO |     | is the scoring |             |             |     |     |           |     |         |
| -------- | ---- | ------- | ------------- | --- | -------------- | ----------- | ----------- | --- | --- | --------- | --- | ------- |
|          |      |         |               |     |                | it improves | performance |     |     | from 26.0 | to  | 31.9 on |
andinferenceLM.NumbersforBREAKareNEM,the
|     |     |     |     |     |     | BREAK, | from | 57.0 to | 64.2 | on MTOP, |     | and from |
| --- | --- | --- | --- | --- | --- | ------ | ---- | ------- | ---- | -------- | --- | -------- |
officialmetric,andforMTOPareEM.
|     |     |     |     |     |     | 51.4 to | 54.3 on | SMCALFLOW. |     | This | shows | that |
| --- | --- | --- | --- | --- | --- | ------- | ------- | ---------- | --- | ---- | ----- | ---- |
usingtheLMitselftolabelexamplesisaneffective
|     |     |     |     |     |     | approach | for obtaining |     | a strong | prompt |     | retriever. |
| --- | --- | --- | --- | --- | --- | -------- | ------------- | --- | -------- | ------ | --- | ---------- |
model,trainedmostlyonafilteredsubsetofcom-
|            |     |           |       |     |               | Table | 3 shows | test results |     | on BREAK | and | MTOP |
| ---------- | --- | --------- | ----- | --- | ------------- | ----- | ------- | ------------ | --- | -------- | --- | ---- |
| mon crawl. |     | (c) CODEX | (Chen | et  | al., 2021): A |       |         |              |     |          |     |      |
GPT-3175B-parametermodelfinedtunedoncode corroboratingthatEPRsubstantiallyimprovesper-
formancecomparedtoBM25andCBR.
| from GitHub. |     | Since | our tasks | involve | mapping |     |                  |     |          |     |            |     |
| ------------ | --- | ----- | --------- | ------- | ------- | --- | ---------------- | --- | -------- | --- | ---------- | --- |
|              |     |       |           |         |         | For | the unsupervised |     | methods, |     | the RANDOM |     |
fromutterancestoprogramsormeaningrepresen-
|     |     |     |     |     |     | baseline | shows | that random |     | sampling | of  | training |
| --- | --- | --- | --- | --- | --- | -------- | ----- | ----------- | --- | -------- | --- | -------- |
tations,CODEXmightpotentiallyperformwellat
in-contextlearning. examplesleadstopoorperformance. BM25 out-
|     |     |     |     |     |     | performs | SBERT | for | prompt | retrieval, |     | and con- |
| --- | --- | --- | --- | --- | --- | -------- | ----- | --- | ------ | ---------- | --- | -------- |
ForallLMs,weuseamaximumcontextsizeof
|     |     |     |     |     |     | sequently | we use | BM25 | in  | all of | our supervised |     |
| --- | --- | --- | --- | --- | --- | --------- | ------ | ---- | --- | ------ | -------------- | --- |
C =2,048tokens.
¯
|     |     |     |     |     |     | approachestoretrievethesetofcandidates, |     |     |     |     |     | . Last, |
| --- | --- | --- | --- | --- | --- | --------------------------------------- | --- | --- | --- | --- | --- | ------- |
E
|     |     |     |     |     |     | BRUTEFORCEperformsworsethanBM25. |     |     |     |     |     | Weas- |
| --- | --- | --- | --- | --- | --- | -------------------------------- | --- | --- | --- | --- | --- | ----- |
Evaluation On BREAK, we evaluate perfor- sumethisissincethetrainingsetsarelarge( 14-
| manceonthedevelopmentsetwithLF-EM(Has- |     |     |     |     |     |     |     |     |     |     |     | ∼   |
| -------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
120Kexamples),andsampling200examplesdoes
| son and | Berant, | 2021), | which | is a | better metric |                                  |     |     |     |     |          |     |
| ------- | ------- | ------ | ----- | ---- | ------------- | -------------------------------- | --- | --- | --- | --- | -------- | --- |
|         |         |        |       |      |               | notcoverexamplesthatareusefulfor |     |     |     |     | GPT-NEO. |     |
comparedtoNormalizedExactMatch(NEM),the Interestingly,EPRoutperformsBM25-ORACLE
officialmetric,asitmeasureswhethertwomean-
onMTOPandSMCALFLOWandiscomparableon
| ingrepresentationsaresemanticallyequivalent. |     |     |     |     | On  |        |                                  |     |     |     |     |     |
| -------------------------------------------- | --- | --- | --- | --- | --- | ------ | -------------------------------- | --- | --- | --- | --- | --- |
|                                              |     |     |     |     |     | BREAK. | ThisissurprisingsinceBM25-ORACLE |     |     |     |     |     |
the test set, we use NEM. On MTOP and SM- hasaccesstotheoutputsequencey attesttime,
test
CALFLOW,weevaluatewithExactMatch(EM), illustratingthatthesignalprovidedbythescoring
i.e.,whetherthestringoutputbytheinferenceLM
LMfortraininggoesbeyondsurfacetextsimilarity.
isidenticaltothereferencestring.
TheperformanceofLM-ORACLEissubstantially
WeevaluateEPRintwosettings: (a)LM-as-a- higherthanEPR,showingthatthesupervisionpro-
service, and (b) LM-as-a-proxy. In the first set- videdbythescoringLMisstrong,andtraininga
ting, we use GPT-NEO as both the scoring LM better retriever from this signal can substantially
andinferenceLM.Inthissetting,weevaluateon enhanceperformance.
thefulldevelopmentsetsof BREAK, MTOP,and Wefurtherevaluateourmodelsintheone-shot
SMCALFLOW. Inthelattersetting,asweaccess setup,i.e.,whenthepromptgiventotheinference
GPT-3andCODEXthroughapaidAPI,wesample LMincludesthehighestscoringexampleonly. In
a random subset of 1,000 development examples thissetup,theinferenceLMisappliedinthesame
fromeachdatasetandevaluateeachmodelonceon setting as when we generate labeled data, where
| thissubset. |     |     |     |     |     | wegoovereachpromptcandidateindependently. |     |     |     |     |     |     |
| ----------- | --- | --- | --- | --- | --- | ----------------------------------------- | --- | --- | --- | --- | --- | --- |
2660

|     |     |     | BREAK |     |     | MTOP |     |     |     | SMCALFLOW |     |     |
| --- | --- | --- | ----- | --- | --- | ---- | --- | --- | --- | --------- | --- | --- |
Method RANDOM BM25 CBR EPR RANDOM BM25 CBR EPR RANDOM BM25 CBR EPR
GPT-3 4.2 20.1 21.3 25.3 7.6 52.5 54.8 62.6 5.8 35.3 41.6 46.5
CODEX 8.9 24.5 24.2 29.5 10.8 60.6 59.4 66.1 7.2 45.1 48.7 50.3
GPT-J 3.3 26.7 26.7 31.5 8.8 56.6 58.0 65.4 10.6 50.4 50.9 57.4
GPT-NEO 1.0 22.8 25.8 29.9 7.6 52.8 55.4 63.6 8.0 46.1 50.1 53.5
Table5: Resultsonarandomsampleof1,000examplesfromthedevelopmentsetwhenusingGPT-Neoasascoring
LMacrossdifferentinferenceLMsanddatasets.
|     |         |           |     |                                | EPR |     |     |     | CBR |     |     |     |
| --- | ------- | --------- | --- | ------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- |
|     | Test    | Utterance |     | Givethecodeoftheairportwiththe |     |     |     |     |     |     |     |     |
|     | Example |           |     | leastflights.                  |     |     |     |     |     |     |     |     |
Meaning
1) airports
Representation
|     |     |           |     | 2) flights                    | of #1       |        |                                   |     |     |     |     |     |
| --- | --- | --------- | --- | ----------------------------- | ----------- | ------ | --------------------------------- | --- | --- | --- | --- | --- |
|     |     |           |     | 3) number                     | of #2 for   | each   | #1                                |     |     |     |     |     |
|     |     |           |     | 4) #1                         | where #3 is | lowest |                                   |     |     |     |     |     |
|     |     |           |     | 5) code                       | of #4       |        |                                   |     |     |     |     |     |
|     |     | Utterance |     | Whatisthecodeofthecitywiththe |             |        | Whatdestinationhasthefewestnumber |     |     |     |     |     |
Top-1
|     |     |     |     | moststudents? |     |     | offlights? |     |     |     |     |     |
| --- | --- | --- | --- | ------------- | --- | --- | ---------- | --- | --- | --- | --- | --- |
Meaning
|     |     |                |     | 1) cities                        |             |         | 1)                               | destinations |       |           |         |     |
| --- | --- | -------------- | --- | -------------------------------- | ----------- | ------- | -------------------------------- | ------------ | ----- | --------- | ------- | --- |
|     |     | Representation |     | 2) students                      | in #1       |         | 2)                               | flights      | of    | #1        |         |     |
|     |     |                |     | 3) number                        | of #2 for   | each    | #1 3)                            | number       | of #2 | for       | each #1 |     |
|     |     |                |     | 4) #1                            | where #3 is | highest | 4)                               | #1 where     | #3    | is lowest |         |     |
|     |     |                |     | 5) code                          | of #4       |         |                                  |              |       |           |         |     |
|     |     | Utterance      |     | Returnthecodeofthecitythathasthe |             |         | Whichdestinationhasleastnumberof |              |       |           |         |     |
Top-2
|     |     |         |     | moststudents. |     |     | flights? |              |     |     |     |     |
| --- | --- | ------- | --- | ------------- | --- | --- | -------- | ------------ | --- | --- | --- | --- |
|     |     | Meaning |     | 1) cities     |     |     | 1)       | destinations |     |     |     |     |
Representation
|     |     |           |     | 2) students                    | in #1       |         | 2)                           | flights  | to    | #1        |         |     |
| --- | --- | --------- | --- | ------------------------------ | ----------- | ------- | ---------------------------- | -------- | ----- | --------- | ------- | --- |
|     |     |           |     | 3) number                      | of #2 for   | each    | #1 3)                        | number   | of #2 | for       | each #1 |     |
|     |     |           |     | 4) #1                          | where #3 is | highest | 4)                           | #1 where | #3    | is lowest |         |     |
|     |     |           |     | 5) code                        | of #4       |         |                              |          |       |           |         |     |
|     |     | Utterance |     | Findthecountandcodeofthejobhas |             |         | Whatisthenumberofairportsper |          |       |           |         |     |
Top-3
|     |     |     |     | mostemployees. |     |     | country,orderedfrommosttoleast? |     |     |     |     |     |
| --- | --- | --- | --- | -------------- | --- | --- | ------------------------------- | --- | --- | --- | --- | --- |
Meaning
|     |     |     |     | 1) jobs |     |     | 1)  | countries |     |     |     |     |
| --- | --- | --- | --- | ------- | --- | --- | --- | --------- | --- | --- | --- | --- |
Representation
|     |     |     |     | 2) employees | of #1       |         | 2)    | airports  | in    | #1   |          |     |
| --- | --- | --- | --- | ------------ | ----------- | ------- | ----- | --------- | ----- | ---- | -------- | --- |
|     |     |     |     | 3) number    | of #2 for   | each    | #1 3) | number    | of #2 | for  | each #1  |     |
|     |     |     |     | 4) #1        | where #3 is | highest | 4)    | #3 sorted | by    | most | to least |     |
|     |     |     |     | 5) employees | of #4       |         |       |           |       |      |          |     |
|     |     |     |     | 6) number    | of #5       |         |       |           |       |      |          |     |
|     |     |     |     | 7) code      | of #4       |         |       |           |       |      |          |     |
|     |     |     |     | 8) #6        | , #7        |         |       |           |       |      |          |     |
Table6: AnexamplefromBREAKdevelopmentsetwhereEPRiscorrectandCBRisincorrectalongwiththetop-3
trainingexamplesretrievedfromeachretriever.
Sincetrainandtesttimearenowcloser,wecanex- a-servicesetup,i.e.,EPRsubstantiallyoutperforms
pecttheadvantageofEPRtobemorepronounced. prior baselines, including our best unsupervised
Table 4 shows the results. Indeed, EPR out- baseline,BM25,andthebestsupervisedbaseline,
|          |          |          |     |       |           | CBR, | by  | 2-8 points | on  | all datasets | and | all pre- |
| -------- | -------- | -------- | --- | ----- | --------- | ---- | --- | ---------- | --- | ------------ | --- | -------- |
| performs | the best | baseline | by  | 8.5%, | and BM25- |      |     |            |     |              |     |          |
ORACLE by 5%. In addition, we examine trainedmodels. Thus, GPT-NEOservesasagood
ANYCORRECT-ORACLE,whichtestswhetherany proxyforchoosingtrainingexamples.
of the candidates returned by BM25 leads to the Tofurthervalidatethisfinding,weevaluatethe
correct output. ANYCORRECT-ORACLE reaches performanceof GPT-Jon BREAKwith GPT-NEO
53.6%,20pointsaboveLM-ORACLE. Thisshows as the scoring LM compared to using GPT-J it-
thehighqualityofcandidatesprovidedbyBM25 self as the scoring LM. We find performance im-
(appliedonthey),asonecanreachmorethan50% proves slightly from 31.5 to 33.6. Analogously,
LF-EM with just a single prompt. Moreover, it when using CODEX as the scoring LM and infer-
hintsthatabetterscoringfunctioncanpotentially enceLMperformanceremainsroughlythesame:
furtherimproveperformance. 29.5 29.3. Thus,usingasmallerLM(GPT-NEO)
→
isaneffectivestrategyfortrainingaretrieverthat
LM-as-a-proxy Table5showsresultswhenthe willbeappliedonotherLMs. Zoominginondif-
scoringLMisGPT-NEOandtheinferenceLMisa ferentinferenceLMs,GPT-Jperformsslightlybet-
largerLM.First,thetrendsaresimilartotheLM-as- ter than GPT-NEO across the board, since it was
2661

Exact
Abstract
8.0
2.0
%
0.5
0.125
|     |     |     |     |     |     |     |     | 0.0 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Distance
Figure3: At-SNEprojectionandclusteringoftherep- Figure4: Onthesubsetofcopiedpatternsweplotthe
resentationslearnedbyEPRforthetrainingexamples distributionofthedistancefromthetestinstancetothe
inBREAK. Aninteractiveversiondisplayingindividual examplecontainingthepattern. ShownontheBREAK
examplesisavailablehere.
validationsetusingEPRintheLM-as-a-servicesetup
|         |        |      |      |           |     |           | usingGPT-NEO. |     | Notethatthey-axisisinlog-scale. |     |     |     |     |
| ------- | ------ | ---- | ---- | --------- | --- | --------- | ------------- | --- | ------------------------------- | --- | --- | --- | --- |
| trained | on the | same | data | and using | the | same pro- |               |     |                                 |     |     |     |     |
cedure as GPT-NEO. CODEX outperforms GPT- showsthatEPRcapturesbothlexicalandstructure
3, which can be explained by the fact that it was similarity. Examplesforclustersarealsoavailable
| trained                                 | on code, | and | our | datasets | involve | map- | inApp.A. |     |     |     |     |     |     |
| --------------------------------------- | -------- | --- | --- | -------- | ------- | ---- | -------- | --- | --- | --- | --- | --- | --- |
| pingtoprogramsormeaningrepresentations. |          |     |     |          |         | Sur- |          |     |     |     |     |     |     |
prisingly,GPT-J outperformsCODEX(excepton Prompt copying We analyze how the LM uti-
|                                      |     |              |     |        |           |       | lizesin-contextprompts. |        |      |     | Specifically,isthetarget |         |            |
| ------------------------------------ | --- | ------------ | --- | ------ | --------- | ----- | ----------------------- | ------ | ---- | --- | ------------------------ | ------- | ---------- |
| MTOP)andGPT-3despitebeing30xsmaller. |     |              |     |        |           | This  |                         |        |      |     |                          |         |            |
|                                      |     |              |     |        |           |       | output                  | copied | from | one | of the                   | prompts | or is it a |
| can perhaps                          |     | be explained |     | by the | fact that | GPT-J |                         |        |      |     |                          |         |            |
compositionofdifferentpromptfragments,which
| was trained | on  | a different |     | dataset | (The | Pile (Gao |     |     |     |     |     |     |     |
| ----------- | --- | ----------- | --- | ------- | ---- | --------- | --- | --- | --- | --- | --- | --- | --- |
resultingeneralizationtonewstructures.
etal.,2021)).
|     |     |     |     |     |     |     |     | To achieve | this, | we  | define two | types | of copy- |
| --- | --- | --- | --- | --- | --- | --- | --- | ---------- | ----- | --- | ---------- | ----- | -------- |
Copied Novel Total ing. (a) Exact copying measures if the generated
Pattern
|     |     | Acc | Rate | Acc | Rate | Acc |     |     |     |     |     |     |     |
| --- | --- | --- | ---- | --- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
outputexactlymatchesoneoftheexamplesinthe
|     | Exact | 55.1% | 10.4% | 29.7% | 89.6% |     |     |     |     |     |     |     |     |
| --- | ----- | ----- | ----- | ----- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
BREAK 32.3% prompt, and (b) Abstract copying, that quantifies
|     | Abstract | 58.0% | 41.1% | 14.5% | 58.9% |     |     |     |     |     |     |     |     |
| --- | -------- | ----- | ----- | ----- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
ifthestructureofthedecodedoutputmatchesany
| MTOP | Exact    | 77.3% | 25.3% | 59.7% | 74.7% | 64.2% |                                 |     |     |     |     |               |     |
| ---- | -------- | ----- | ----- | ----- | ----- | ----- | ------------------------------- | --- | --- | --- | --- | ------------- | --- |
|      | Abstract | 71.6% | 84.5% | 23.4% | 15.5% |       |                                 |     |     |     |     |               |     |
|      |          |       |       |       |       |       | ofthestructuresseenintheprompt. |     |     |     |     | Specifically, |     |
Exact 62.5% 60.2% 42.4% 39.8% weeliminatetheeffectofnon-structuralelements
| SMCAL | Abstract | 62.4% | 81.2% | 20.6% | 18.8% | 54.5% |      |             |     |          |            |     |        |
| ----- | -------- | ----- | ----- | ----- | ----- | ----- | ---- | ----------- | --- | -------- | ---------- | --- | ------ |
|       |          |       |       |       |       |       | such | as entities | and | function | arguments. |     | We re- |
Table 7: Accuracy comparison between the decoded placeeverysequenceofwordsinthelogicalform
instancesthatcontainedpatternsfromthepromptand
thatappearsintheinpututterancewiththestring
novelinstancesthosethatdon’t. Resultsshownareon [MASKED] for both the target utterance and in-
theLM-as-a-servicesetupusingGPT-NEO.
|     |     |     |     |     |     |     | contextexamples. |     |     | Ifthemaskedlogicalformthat |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ---------------- | --- | --- | -------------------------- | --- | --- | --- |
theLMdecodedappearsinthesetofmaskedex-
Table6showsanexamplefromBREAK amplesdefinedbytheprompt,wesaythattheLM
Analysis
whereEPRdecodesthecorrectoutput,whileCBR copiedthatabstractpattern.
doesnot. AlltrainingexamplesretrievedbyEPR Table 7 presents the results on the validation
perform an argmax (argmin in the original utter- set for each of our three datasets, as well as the
ance),andreturninthefinalstep“acode”,while accuracy on each subset. We observe that the
thethirdexampleretrievedbyCBRdoesnotper- rateofcopyingismuchhigherin MTOPandSM-
formanargmaxorargmin,anddonotinvolve“a CALFLOWcomparedtoBREAK,whereinMTOP
code”. WeprovideadditionalexamplesinApp.A. and SMCALFLOW abstractcopyingreachesmore
Figure 3 shows a t-SNE (Hinton and Roweis, than80%. Moreover,accuracyonexampleswhere
2002)projectionoftheembeddingslearnedbyEPR copyingoccurredismuchhighercomparedtoac-
for the training examples of BREAK, with a link curacy where no copying happened. For exam-
to an interactive version, where we applied the ple, on MTOP, 84.5% of the examples were ab-
OPTICS(Ankerstetal.,1999;SchubertandGertz, stractly copied, and on that subset of examples,
2018) clustering algorithm. Examining clusters EPRachieves71.6%EM,comparedto64.2%on
2662

theentirevalidationset. Nevertheless,eventhough Prompts Developing methods for interacting
accuracyismuchlowerincaseswherenocopying with LMs and extracting desired behaviours has
occurred,accuracyisnotnegligible,whichshows attractedconsiderableattention,undertheumbrella
thatsomeformofgeneralizationtonewstructures termprompting. Inthiswork,promptsareasetof
istakingplace. in-contexttrainingexamples,butsubstantialeffort
hasalsobeendevotedtocastingnaturallanguage
Anotherfollow-upquestioniswhetherthemodel
|     |     |     |     |     |     |     | tasks as | language | modeling |     | by phrasing | the tar- |
| --- | --- | --- | --- | --- | --- | --- | -------- | -------- | -------- | --- | ----------- | -------- |
copiespatternsfrompromptsuniformlyordoesit
attendmostlytotheoneswithhighretrievalscore. get task in natural language (see survey in (Liu
|           |       |         |     |            |     |       | et al., 2021b)). |     | Such | approaches | include | prompt |
| --------- | ----- | ------- | --- | ---------- | --- | ----- | ---------------- | --- | ---- | ---------- | ------- | ------ |
| To answer | this, | we look | at  | the subset | of  | exam- |                  |     |      |            |         |        |
engineeringthroughmanualpatterns(Petronietal.,
| pleswherecopyingoccurred. |     |     |     | Wethenidentifyfor |     |     |     |     |     |     |     |     |
| ------------------------- | --- | --- | --- | ----------------- | --- | --- | --- | --- | --- | --- | --- | --- |
eachexamplethehighest-rankingpromptthatwas 2019;SchickandSchütze,2021),decodingmeth-
copiedfrom,anddefinethedistanceofthatprompt ods(Minetal.,2021;Zhaoetal.,2021;Holtzman
etal.,2021),andmethodsforextractingeitherhard
bydividingtherankbythenumberofpromptsthat
(Shinetal.,2020;Havivetal.,2021)orsoft(Liand
| fitinthatexample. |     | Figure4showsthedistribution |     |     |     |     |     |     |     |     |     |     |
| ----------------- | --- | --------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
overdistancesforthe BREAKdataset. Weobserve Liang, 2021; Zhong et al., 2021; Qin and Eisner,
2021)promptsautomatically.
| that copying | happens |     | mostly | from | highly-ranked |     |     |     |     |     |     |     |
| ------------ | ------- | --- | ------ | ---- | ------------- | --- | --- | --- | --- | --- | --- | --- |
prompts.
|     |     |     |     |     |     |     | Promptretrievalforsupervisedmodels |     |     |     |     | Inpar- |
| --- | --- | --- | --- | --- | --- | --- | ---------------------------------- | --- | --- | --- | --- | ------ |
alleltothiswork,addingtrainingexamplesasaddi-
| 5 RelatedWork |     |     |     |               |     |        | tionalinputhasbeenshowntobeusefulforsuper- |     |     |                      |     |     |
| ------------- | --- | --- | --- | ------------- | --- | ------ | ------------------------------------------ | --- | --- | -------------------- | --- | --- |
|               |     |     |     |               |     |        | visedmodelsaswell.                         |     |     | Wangetal.(2022)andXu |     |     |
|               |     |     | Our | understanding |     | of in- |                                            |     |     |                      |     |     |
In-context learning etal.(2021)usedBM25toretrieveandaugmentthe
contextlearninghasgrownsubstantiallyrecently.
inputwithsimilarexamplesfromthetrainingset.
Saunshietal.(2021)suggeststhatbyconditioning Fine-tuning the model with the additional inputs
onaprompt,thetaskofpredictingthenextword improvedperformanceontaskssuchassummariza-
| approaches | linear | separability. |     | Xie | et al. | (2021) |          |          |            |     |              |     |
| ---------- | ------ | ------------- | --- | --- | ------ | ------ | -------- | -------- | ---------- | --- | ------------ | --- |
|            |        |               |     |     |        |        | tion and | question | answering. |     | Such methods | can |
suggeststhatin-contextlearningoccurswhenthe alsopotentiallybenefitfromastrongerretriever.
| model infers   |              | a shared | latent        | concept | between   | ex-     |               |     |     |     |     |     |
| -------------- | ------------ | -------- | ------------- | ------- | --------- | ------- | ------------- | --- | --- | --- | --- | --- |
| amples         | in a prompt. | Levine   |               | et al.  | (2021)    | present |               |     |     |     |     |     |
|                |              |          |               |         |           |         | 6 Conclusions |     |     |     |     |     |
| a pre-training |              | scheme   | theoretically |         | motivated | by      |               |     |     |     |     |     |
Largepre-trainedLMsarebecominganinsepara-
| the bias | of in-context |     | learning, | that | gives | signif- |     |     |     |     |     |     |
| -------- | ------------- | --- | --------- | ---- | ----- | ------- | --- | --- | --- | --- | --- | --- |
blepartofthenaturallanguageunderstandingeco-
| icant improvements. |     |     | Recently, | Min | et al. | (2022) |     |     |     |     |     |     |
| ------------------- | --- | --- | --------- | --- | ------ | ------ | --- | --- | --- | --- | --- | --- |
showedthatthemodeldoesnotrelyontheground system. However,accessingtheirweightsorupdat-
ingthemcanbeprohibitiveformanyresearchers.
truthinput-labelmappingprovidedinthedemon-
Inthiswork,weproposeEPR,amethodforlearn-
strationsasmuchaspreviouslythought.
ingtoretrievegoodpromptsforin-contextlearning,
byusinglanguagemodelsthemselvesasthescor-
| Retrieval       | Researchontrainingdenseretrievers |           |           |     |             |     |              |                                  |     |     |     |     |
| --------------- | --------------------------------- | --------- | --------- | --- | ----------- | --- | ------------ | -------------------------------- | --- | --- | --- | --- |
|                 |                                   |           |           |     |             |     | ingfunction. | Thisallowsustotrainalight-weight |     |     |     |     |
| has skyrocketed |                                   | recently, | propelled |     | by interest |     |              |                                  |     |     |     |     |
retrieverandsubstantiallyimproveperformanceon
| in open-domain |     | question | answering |     | (Chen | et al., |     |     |     |     |     |     |
| -------------- | --- | -------- | --------- | --- | ----- | ------- | --- | --- | --- | --- | --- | --- |
threechallengingtasks.
2017;Leeetal.,2019;Karpukhinetal.,2020;Guu
Morebroadly,giventhatlargeLMsmodelsare
etal.,2020;KhattabandZaharia,2020;Quetal.,
|     |     |     |     |     |     |     | likely to | play | a prominent | role | in developing | lan- |
| --- | --- | --- | --- | --- | --- | --- | --------- | ---- | ----------- | ---- | ------------- | ---- |
2021). Workonretrieval-basedmethodshasalso
guageunderstandingmodels,itisimportanttode-
spreadmorewidelytootherknowledge-intensive
velopapproachesforinteractingwithsuchmodels
| tasks (Lewis |     | et al., 2020), |     | e.g., fact | verification |     |              |     |     |           |           |         |
| ------------ | --- | -------------- | --- | ---------- | ------------ | --- | ------------ | --- | --- | --------- | --------- | ------- |
|              |     |                |     |            |              |     | effectively. | EPR | can | be viewed | as a step | in this |
(Samarinasetal.,2021).
direction.
Similartous,Pasupatetal.(2021)proposedto
| useretrievalinsemanticparsing. |     |     |     | However,theyfo- |     |     |     |     |     |     |     |     |
| ------------------------------ | --- | --- | --- | --------------- | --- | --- | --- | --- | --- | --- | --- | --- |
Acknowledgement
cusoncontrollingtheoutputgeneratedbyamodel.
Retrievalmethodshavealsobeensuccessfullyused WethankOriRamandItayItzhakforhelpfulsug-
in language modeling (Khandelwal et al., 2020; gestionsandmeaningfuldiscussions. Thisresearch
Borgeaudetal.,2021;Alonetal.,2022)andma- wassupportedinpartbyTheYandexInitiativefor
chinetranslation(Khandelwaletal.,2021). Machine Learning, and The European Research
2663

Council (ERC) under the European Union Hori- Jack Clark, Christopher Berner, Sam McCandlish,
|                         |          |     |                 |           |     | Alec Radford,                            | Ilya Sutskever, | and Dario | Amodei. |
| ----------------------- | -------- | --- | --------------- | --------- | --- | ---------------------------------------- | --------------- | --------- | ------- |
| zons 2020               | research | and | innovation      | programme |     |                                          |                 |           |         |
|                         |          |     |                 |           |     | 2020. Languagemodelsarefew-shotlearners. |                 |           | InAd-   |
| (grantERCDELPHI802800). |          |     | Thisworkwascom- |           |     |                                          |                 |           |         |
vancesinNeuralInformationProcessingSystems33:
pletedinpartialfulfillmentforthePh.Ddegreeof
AnnualConferenceonNeuralInformationProcess-
| OhadRubin. |     |     |     |     |     | ing Systems | 2020, NeurIPS | 2020, December | 6-12, |
| ---------- | --- | --- | --- | --- | --- | ----------- | ------------- | -------------- | ----- |
2020,virtual.
DanqiChen,AdamFisch,JasonWeston,andAntoine
References
|           |       |        |             |         |      | Bordes.2017.     | ReadingWikipediatoansweropen- |     |     |
| --------- | ----- | ------ | ----------- | ------- | ---- | ---------------- | ----------------------------- | --- | --- |
|           |       |        |             |         |      | domainquestions. | InProceedingsofthe55thAnnual  |     |     |
| Uri Alon, | Frank | F. Xu, | Junxian He, | Sudipta | Sen- |                  |                               |     |     |
gupta, Dan Roth, and Graham Neubig. 2022. Meeting of the Association for Computational Lin-
Neuro-symboliclanguagemodelingwithautomaton- guistics(Volume1: LongPapers),pages1870–1879,
augmentedretrieval. ArXiv,abs/2201.12431. Vancouver,Canada.AssociationforComputational
Linguistics.
| Jacob Andreas, |     | John Bufe, | David | Burkett, | Charles |     |     |     |     |
| -------------- | --- | ---------- | ----- | -------- | ------- | --- | --- | --- | --- |
Chen, Josh Clausman, Jean Crawford, Kate Crim, Mark Chen, Jerry Tworek, Heewoo Jun, Qiming
Yuan,HenriquePonde,JaredKaplan,HarrisonEd-
| Jordan | DeLoach, | Leah | Dorner, Jason | Eisner, | Hao |     |     |     |     |
| ------ | -------- | ---- | ------------- | ------- | --- | --- | --- | --- | --- |
wards,YuraBurda,NicholasJoseph,GregBrockman,
Fang,AlanGuo,DavidHall,KristinHayes,Kellie
Hill, Diana Ho, Wendy Iwaszuk, Smriti Jha, Dan Alex Ray, Raul Puri, Gretchen Krueger, Michael
Klein,JayantKrishnamurthy,TheoLanman,Percy Petrov,HeidyKhlaaf,GirishSastry,PamelaMishkin,
Liang,ChristopherH.Lin,IlyaLintsbakh,AndyMc- Brooke Chan, Scott Gray, Nick Ryder, Mikhail
|     |     |     |     |     |     | Pavlov, | Alethea. Power, | Lukasz Kaiser, | Moham- |
| --- | --- | --- | --- | --- | --- | ------- | --------------- | -------------- | ------ |
Govern,AleksandrNisnevich,AdamPauls,Dmitrij
madBavarian,ClemensWinter,PhilippeTillet,Fe-
| Petters, | Brent | Read, Dan | Roth, Subhro | Roy, | Jesse |     |     |     |     |
| -------- | ----- | --------- | ------------ | ---- | ----- | --- | --- | --- | --- |
Rusak,BethShort,DivSlomin,BenSnyder,Stephon lipePetroskiSuch,DavidW.Cummings,Matthias
Striplin,YuSu,ZacharyTellman,SamThomson,An- Plappert, Fotios Chantzis, Elizabeth Barnes, Ariel
dreiVorobev,IzabelaWitoszko,JasonWolfe,Abby Herbert-Voss, William H. Guss, Alex Nichol, Igor
Babuschkin,S.ArunBalaji,ShantanuJain,Andrew
| Wray, | Yuchen | Zhang, | and Alexander | Zotov. | 2020. |     |     |     |     |
| ----- | ------ | ------ | ------------- | ------ | ----- | --- | --- | --- | --- |
Carr,JanLeike,JoshuaAchiam,VedantMisra,Evan
| Task-orienteddialogueasdataflowsynthesis. |     |     |     |     | Trans- |     |     |     |     |
| ----------------------------------------- | --- | --- | --- | --- | ------ | --- | --- | --- | --- |
actionsoftheAssociationforComputationalLinguis- Morikawa,AlecRadford,MatthewM.Knight,Miles
tics,8:556–571. Brundage,MiraMurati,KatieMayer,PeterWelinder,
BobMcGrew,DarioAmodei,SamMcCandlish,Ilya
Mihael Ankerst, Markus M. Breunig, Hans-Peter Sutskever, and Wojciech Zaremba. 2021. Evaluat-
Kriegel, and Jörg Sander. 1999. Optics: Ordering ing large language models trained on code. ArXiv
|     |     |     |     |     | SIGMOD | preprint,abs/2107.03374. |     |     |     |
| --- | --- | --- | --- | --- | ------ | ------------------------ | --- | --- | --- |
pointstoidentifytheclusteringstructure.
Rec.,28(2):49–60.
RajarshiDas,ManzilZaheer,DungThai,AmeyaGod-
EmilyM.Bender,TimnitGebru,AngelinaMcMillan- bole,EthanPerez,JayYoonLee,LizhenTan,Lazaros
Major, and Shmargaret Shmitchell. 2021. On the Polymenakos,andAndrewMcCallum.2021. Case-
dangers of stochastic parrots: Can language mod- based reasoning for natural language queries over
els be too big? In Proceedings of the 2021 ACM knowledgebases. InProceedingsofthe2021Confer-
ConferenceonFairness,Accountability,andTrans- enceonEmpiricalMethodsinNaturalLanguagePro-
parency,FAccT’21,page610–623,NewYork,NY, cessing,pages9594–9611,OnlineandPuntaCana,
USA.AssociationforComputingMachinery. DominicanRepublic.AssociationforComputational
Linguistics.
| Sid Black, | Leo | Gao, | Phil Wang, | Connor | Leahy, |     |     |     |     |
| ---------- | --- | ---- | ---------- | ------ | ------ | --- | --- | --- | --- |
and Stella Biderman. 2021. GPT-Neo: Large Jacob Devlin, Ming-Wei Chang, Kenton Lee, and
ScaleAutoregressiveLanguageModelingwithMesh- Kristina Toutanova. 2019. BERT: Pre-training of
| Tensorflow. |     |     |     |     |     | deepbidirectionaltransformersforlanguageunder- |                                    |     |     |
| ----------- | --- | --- | --- | --- | --- | ---------------------------------------------- | ---------------------------------- | --- | --- |
|             |     |     |     |     |     | standing.                                      | InProceedingsofthe2019Conferenceof |     |     |
SebastianBorgeaud,ArthurMensch,JordanHoffmann,
theNorthAmericanChapteroftheAssociationfor
TrevorCai,ElizaRutherford,KatieMillican,George ComputationalLinguistics: HumanLanguageTech-
vandenDriessche, Jean-BaptisteLespiau, Bogdan nologies,Volume1(LongandShortPapers),pages
Damoc, Aidan Clark, et al. 2021. Improving lan- 4171–4186,Minneapolis,Minnesota.Associationfor
guagemodelsbyretrievingfromtrillionsoftokens. ComputationalLinguistics.
arXivpreprintarXiv:2112.04426.
NanDu,YanpingHuang,AndrewM.Dai,DmitryLep-
TomB.Brown,BenjaminMann,NickRyder,Melanie ikhinSimonTong,YuanzhongXu,MaximKrikun,
Subbiah, Jared Kaplan, Prafulla Dhariwal, Arvind Yanqi Zhou, Adams Wei Yu, Orhan Firat, Bar-
Neelakantan,PranavShyam,GirishSastry,Amanda ret Zoph, Liam Fedus, Maarten Bosma, Zongwei
Askell, Sandhini Agarwal, Ariel Herbert-Voss, Zhou, Tao Wang, Yu Emma Wang, Kellie Web-
Gretchen Krueger, Tom Henighan, Rewon Child, ster, Marie Pellat, Kevin Robinson, Kathy Meier-
Aditya Ramesh, Daniel M. Ziegler, Jeffrey Wu, Hellstern, Toju Duke, Lucas Dixon, Kun Zhang,
ClemensWinter,ChristopherHesse,MarkChen,Eric QuocVLe,YonghuiWu,ZhifengChen,andClaire
Sigler,MateuszLitwin,ScottGray,BenjaminChess, Cui. 2021. GLaM: Efficient scaling of language
2664

models with mixture-of-experts. arXiv preprint OmarKhattabandMateiZaharia.2020. Colbert: Effi-
arXiv:2112.06905. cientandeffectivepassagesearchviacontextualized
|     |     |     |     |     | lateinteractionoverbert. |     |     | InProceedingsofthe43rd |     |     |
| --- | --- | --- | --- | --- | ------------------------ | --- | --- | ---------------------- | --- | --- |
LeoGao,StellaBiderman,SidBlack,LaurenceGold- International ACM SIGIR conference on research
ing,TravisHoppe,CharlesFoster,JasonPhang,Ho- anddevelopmentinInformationRetrieval,pages39–
| raceHe,   | AnishThite, |         | NoaNabeshima, | etal.2021.    | 48. |     |     |     |     |     |
| --------- | ----------- | ------- | ------------- | ------------- | --- | --- | --- | --- | --- | --- |
| The pile: | An 800gb    | dataset | of diverse    | text for lan- |     |     |     |     |     |     |
guagemodeling. ArXivpreprint,abs/2101.00027. Diederik P Kingma and Jimmy Ba. 2015. Adam: A
|     |     |     |     |     | methodforstochasticoptimization. |     |     |     | InProceedings |     |
| --- | --- | --- | --- | --- | -------------------------------- | --- | --- | --- | ------------- | --- |
ofICLR.
KelvinGuu,KentonLee,ZoraTung,PanupongPasupat,
| and Ming-Wei |     | Chang. | 2020. Retrieval | augmented |     |     |     |     |     |     |
| ------------ | --- | ------ | --------------- | --------- | --- | --- | --- | --- | --- | --- |
KentonLee,Ming-WeiChang,andKristinaToutanova.
| languagemodelpre-training. |     |          | InICML. |                |                          |        |           |                    |            |      |
| -------------------------- | --- | -------- | ------- | -------------- | ------------------------ | ------ | --------- | ------------------ | ---------- | ---- |
|                            |     |          |         |                | 2019.                    | Latent | retrieval | for weakly         | supervised | open |
|                            |     |          |         |                | domainquestionanswering. |        |           | InProceedingsofthe |            |      |
| Matan Hasson               | and | Jonathan | Berant. | 2021. Question |                          |        |           |                    |            |      |
57thAnnualMeetingoftheAssociationforComputa-
decomposition with dependency graphs. ArXiv, tionalLinguistics,pages6086–6096,Florence,Italy.
abs/2104.08647.
AssociationforComputationalLinguistics.
AdiHaviv,JonathanBerant,andAmirGloberson.2021. Yoav Levine, Noam Wies, Daniel Jannai, Daniel I.
| BERTese: | LearningtospeaktoBERT. |     |     | InProceed- |        |              |     |                       |     |     |
| -------- | ---------------------- | --- | --- | ---------- | ------ | ------------ | --- | --------------------- | --- | --- |
|          |                        |     |     |            | Navon, | YedidHoshen, |     | andAmnonShashua.2021. |     |     |
ingsofthe16thConferenceoftheEuropeanChap-
|     |     |     |     |     | Theinductivebiasofin-contextlearning: |     |     |     |     | Rethinking |
| --- | --- | --- | --- | --- | ------------------------------------- | --- | --- | --- | --- | ---------- |
teroftheAssociationforComputationalLinguistics: pretrainingexampledesign. ArXiv,abs/2110.04541.
MainVolume,pages3618–3623,Online.Association
forComputationalLinguistics. Patrick S. H. Lewis, Ethan Perez, Aleksandra Pik-
|     |     |     |     |     | tus, Fabio | Petroni, | Vladimir | Karpukhin, |     | Naman |
| --- | --- | --- | --- | --- | ---------- | -------- | -------- | ---------- | --- | ----- |
MatthewHenderson,RamiAl-Rfou,BrianStrope,Yun Goyal,HeinrichKüttler,MikeLewis,Wen-tauYih,
|     |     |     |     |     | Tim | Rocktäschel, | Sebastian | Riedel, |     | and Douwe |
| --- | --- | --- | --- | --- | --- | ------------ | --------- | ------- | --- | --------- |
hsuanSung,LaszloLukacs,RuiqiGuo,SanjivKu-
|                                       |     |     |     |       | Kiela. | 2020. | Retrieval-augmented |     | generation | for |
| ------------------------------------- | --- | --- | --- | ----- | ------ | ----- | ------------------- | --- | ---------- | --- |
| mar,BalintMiklos,andRayKurzweil.2017. |     |     |     | Effi- |        |       |                     |     |            |     |
cientnaturallanguageresponsesuggestionforsmart knowledge-intensiveNLPtasks. InProceedingsof
| reply.                               |     |     |         |          | NeurIPS. |             |        |            |         |        |
| ------------------------------------ | --- | --- | ------- | -------- | -------- | ----------- | ------ | ---------- | ------- | ------ |
|                                      |     |     |         |          | Haoran   | Li, Abhinav | Arora, | Shuohui    | Chen,   | Anchit |
| GeoffreyE.HintonandSamT.Roweis.2002. |     |     |         | Stochas- |          |             |        |            |         |        |
|                                      |     |     |         |          | Gupta,   | Sonal       | Gupta, | and Yashar | Mehdad. | 2021.  |
| ticneighborembedding.                |     |     | InNIPS. |          |          |             |        |            |         |        |
MTOP:Acomprehensivemultilingualtask-oriented
|     |     |     |     |     | semanticparsingbenchmark. |     |     | InProceedingsofthe |     |     |
| --- | --- | --- | --- | --- | ------------------------- | --- | --- | ------------------ | --- | --- |
AriHoltzman,PeterWest,VeredShwartz,YejinChoi,
16thConferenceoftheEuropeanChapteroftheAsso-
| and Luke  | Zettlemoyer. |             | 2021. Surface | form com-    |                                     |     |     |     |             |     |
| --------- | ------------ | ----------- | ------------- | ------------ | ----------------------------------- | --- | --- | --- | ----------- | --- |
|           |              |             |               |              | ciationforComputationalLinguistics: |     |     |     | MainVolume, |     |
| petition: | Why          | the highest | probability   | answer isn’t |                                     |     |     |     |             |     |
pages2950–2962,Online.AssociationforComputa-
| alwaysright. | InProceedingsofthe2021Conference |     |     |     |     |     |     |     |     |     |
| ------------ | -------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
tionalLinguistics.
onEmpiricalMethodsinNaturalLanguageProcess-
ing,pages7038–7051,OnlineandPuntaCana,Do-
|         |           |             |     |               | Xiang Lisa | Li and     | Percy | Liang. 2021. | Prefix-tuning:  |     |
| ------- | --------- | ----------- | --- | ------------- | ---------- | ---------- | ----- | ------------ | --------------- | --- |
| minican | Republic. | Association | for | Computational |            |            |       |              |                 |     |
|         |           |             |     |               | Optimizing | continuous |       | prompts      | for generation. | In  |
Linguistics.
Proceedingsofthe59thAnnualMeetingoftheAsso-
ciationforComputationalLinguisticsandthe11th
JeffJohnson,MatthijsDouze,andHervéJégou.2017. InternationalJointConferenceonNaturalLanguage
Billion-scale similarity search with gpus. ArXiv Processing (Volume 1: Long Papers), pages 4582–
preprint,abs/1702.08734.
|     |     |     |     |     | 4597, | Online. | Association | for Computational |     | Lin- |
| --- | --- | --- | --- | --- | ----- | ------- | ----------- | ----------------- | --- | ---- |
guistics.
VladimirKarpukhin,BarlasOguz,SewonMin,Patrick
Lewis,LedellWu,SergeyEdunov,DanqiChen,and OpherLieber,OrSharir,BarakLenz,andYoavShoham.
Wen-tauYih.2020. Densepassageretrievalforopen- 2021. Jurassic-1: Technicaldetailsandevaluation.
domainquestionanswering. InProceedingsofthe WhitePaper.AI21Labs.
2020ConferenceonEmpiricalMethodsinNatural
LanguageProcessing(EMNLP),pages6769–6781, JiachangLiu,DinghanShen,YizheZhang,BillDolan,
|     |     |     |     |     | Lawrence | Carin, | and | Weizhu Chen. | 2021a. | What |
| --- | --- | --- | --- | --- | -------- | ------ | --- | ------------ | ------ | ---- |
Online.AssociationforComputationalLinguistics.
|     |     |     |     |     | makesgoodin-contextexamplesforgpt-3? |     |     |     |     | ArXiv |
| --- | --- | --- | --- | --- | ------------------------------------ | --- | --- | --- | --- | ----- |
preprint,abs/2101.06804.
UrvashiKhandelwal,AngelaFan,DanJurafsky,Luke
| Zettlemoyer,andMikeLewis.2021. |     |     |     | NearestNeigh- |     |     |     |     |     |     |
| ------------------------------ | --- | --- | --- | ------------- | --- | --- | --- | --- | --- | --- |
PengfeiLiu,WeizheYuan,JinlanFu,ZhengbaoJiang,
| borMachineTranslation. |     |     | InProceedingsofICLR. |     |                                       |         |              |              |     |           |
| ---------------------- | --- | --- | -------------------- | --- | ------------------------------------- | ------- | ------------ | ------------ | --- | --------- |
|                        |     |     |                      |     | HiroakiHayashi,andGrahamNeubig.2021b. |         |              |              |     | Pre-      |
|                        |     |     |                      |     | train,                                | prompt, | and predict: | A systematic |     | survey of |
UrvashiKhandelwal,OmerLevy,DanJurafsky,Luke promptingmethodsinnaturallanguageprocessing.
| Zettlemoyer,andMikeLewis.2020. |     |     |     | Generalization |     |     |     |     |     |     |
| ------------------------------ | --- | --- | --- | -------------- | --- | --- | --- | --- | --- | --- |
throughmemorization: Nearestneighborlanguage Sewon Min, Mike Lewis, Hannaneh Hajishirzi, and
models. In8thInternationalConferenceonLearning Luke Zettlemoyer. 2021. Noisy channel language
Representations,ICLR2020,AddisAbaba,Ethiopia, model prompting for few-shot text classification.
| April26-30,2020.OpenReview.net. |     |     |     |     | arXivpreprint. |     |     |     |     |     |
| ------------------------------- | --- | --- | --- | --- | -------------- | --- | --- | --- | --- | --- |
2665

SewonMin,XinxiLyu,AriHoltzman,MikelArtetxe, Stephen Robertson and Hugo Zaragoza. 2009. The
MikeLewis,HannanehHajishirzi,andLukeZettle- probabilistic relevance framework: Bm25 and be-
moyer. 2022. Rethinking the role of demonstra- yond. Foundations and Trends in Information Re-
tions: Whatmakesin-contextlearningwork? ArXiv, trieval,3:333–389.
abs/2202.12837.
ChrisSamarinas,WynneHsu,andMongLiLee.2021.
PanupongPasupat,YuanZhang,andKelvinGuu.2021. Improvingevidenceretrievalforautomatedexplain-
Controllablesemanticparsingviaretrievalaugmen- ablefact-checking. InProceedingsofthe2021Con-
tation. In Proceedings of the 2021 Conference on ferenceoftheNorthAmericanChapteroftheAsso-
EmpiricalMethodsinNaturalLanguageProcessing, ciationforComputationalLinguistics: HumanLan-
pages7683–7698,OnlineandPuntaCana,Domini- guageTechnologies: Demonstrations,pages84–91,
can Republic. Association for Computational Lin- Online.AssociationforComputationalLinguistics.
guistics.
NikunjSaunshi,SadhikaMalladi,andSanjeevArora.
Fabio Petroni, Tim Rocktäschel, Sebastian Riedel, 2021. Amathematicalexplorationofwhylanguage
Patrick Lewis, Anton Bakhtin, Yuxiang Wu, and models help solve downstream tasks. In Interna-
AlexanderMiller.2019. Languagemodelsasknowl- tionalConferenceonLearningRepresentations.
edge bases? In Proceedings of the 2019 Confer-
enceonEmpiricalMethodsinNaturalLanguagePro- Timo Schick and Hinrich Schütze. 2021. Exploiting
cessingandthe9thInternationalJointConference cloze-questionsforfew-shottextclassificationand
onNaturalLanguageProcessing(EMNLP-IJCNLP), natural language inference. In Proceedings of the
pages2463–2473,HongKong,China.Association 16thConferenceoftheEuropeanChapteroftheAsso-
forComputationalLinguistics. ciationforComputationalLinguistics: MainVolume,
pages 255–269, Online. Association for Computa-
GuanghuiQinandJasonEisner.2021. Learninghow tionalLinguistics.
toask: QueryingLMswithmixturesofsoftprompts.
InProceedingsofthe2021ConferenceoftheNorth Erich Schubert and Michael Gertz. 2018. Improving
AmericanChapteroftheAssociationforComputa- theclusterstructureextractedfromopticsplots. In
tionalLinguistics: HumanLanguageTechnologies, LWDA.
pages5203–5212,Online.AssociationforComputa-
tionalLinguistics. RichardShin,ChristopherLin,SamThomson,Charles
Chen,SubhroRoy,EmmanouilAntoniosPlatanios,
YingqiQu,YuchenDing,JingLiu,KaiLiu,Ruiyang AdamPauls,DanKlein,JasonEisner,andBenjamin
Ren,WayneXinZhao,DaxiangDong,HuaWu,and Van Durme. 2021. Constrained language models
HaifengWang.2021. RocketQA:Anoptimizedtrain- yieldfew-shotsemanticparsers. InProceedingsof
ing approach to dense passage retrieval for open- the2021ConferenceonEmpiricalMethodsinNatu-
domainquestionanswering. InProceedingsofthe ralLanguageProcessing,pages7699–7715,Online
2021ConferenceoftheNorthAmericanChapterof andPuntaCana,DominicanRepublic.Association
theAssociationforComputationalLinguistics: Hu- forComputationalLinguistics.
manLanguageTechnologies,pages5835–5847,On-
line.AssociationforComputationalLinguistics. TaylorShin,YasamanRazeghi,RobertL.LoganIV,Eric
Wallace,andSameerSingh.2020. AutoPrompt:Elic-
Jack W Rae, Sebastian Borgeaud, Trevor Cai, Katie itingKnowledgefromLanguageModelswithAuto-
Millican, Jordan Hoffmann, Francis Song, John maticallyGeneratedPrompts. InProceedingsofthe
Aslanides, Sarah Henderson, Roman Ring, Susan- 2020ConferenceonEmpiricalMethodsinNatural
nah Young, et al. 2021. Scaling language models: LanguageProcessing(EMNLP),pages4222–4235,
Methods,analysis&insightsfromtraininggopher. Online.AssociationforComputationalLinguistics.
arXivpreprintarXiv:2112.11446.
Ben Wang and Aran Komatsuzaki. 2021. GPT-
Colin Raffel, Noam Shazeer, Adam Roberts, Kather- J-6B: A 6 Billion Parameter Autoregressive
ine Lee, Sharan Narang, Michael Matena, Yanqi Language Model. https://github.com/
Zhou,WeiLi,andPeterJ.Liu.2020. Exploringthe kingoflolz/mesh-transformer-jax.
limitsoftransferlearningwithaunifiedtext-to-text
transformer. JournalofMachineLearningResearch, ShuoWang,YichongXu,YuweiFang,YangLiu,S.Sun,
21(140):1–67. Ruochen Xu, Chenguang Zhu, and Michael Zeng.
2022. Trainingdataismorevaluablethanyouthink:
Nils Reimers and Iryna Gurevych. 2019. Sentence- A simple and effective method by retrieving from
BERT:SentenceembeddingsusingSiameseBERT- trainingdata. ArXiv,abs/2203.08773.
networks. InProceedingsofthe2019Conferenceon
EmpiricalMethodsinNaturalLanguageProcessing Tomer Wolfson, Mor Geva, Ankit Gupta, Matt Gard-
andthe9thInternationalJointConferenceonNatu- ner, Yoav Goldberg, Daniel Deutch, and Jonathan
ralLanguageProcessing(EMNLP-IJCNLP),pages Berant.2020. Breakitdown: Aquestionunderstand-
3982–3992,HongKong,China.AssociationforCom- ingbenchmark. TransactionsoftheAssociationfor
putationalLinguistics. ComputationalLinguistics,8:183–198.
2666

Sang Michael Xie, Aditi Raghunathan, Percy Liang, Risk assessment Large language models have
| andTengyuMa.2021. |     |     | Anexplanationofin-context |     |     |     |     |     |     |     |     |
| ----------------- | --- | --- | ------------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
beenshowntoexhibitvariouskindsofbias(Bender
| learning | as  | implicit | bayesian | inference. |     | ArXiv, |                |       |     |            |               |
| -------- | --- | -------- | -------- | ---------- | --- | ------ | -------------- | ----- | --- | ---------- | ------------- |
|          |     |          |          |            |     |        | et al., 2021), | since | EPR | is trained | on the signal |
abs/2111.02080.
obtainedfromsuchlargeLMs,itmightalsoexhibit
| Yichong | Xu, Chenguang |     | Zhu, | Shuohang | Wang, | Siqi |     |     |     |     |     |
| ------- | ------------- | --- | ---- | -------- | ----- | ---- | --- | --- | --- | --- | --- |
thesebiases.
| Sun, | Hao Cheng, |     | Xiaodong | Liu, | Jianfeng | Gao, |     |     |     |     |     |
| ---- | ---------- | --- | -------- | ---- | -------- | ---- | --- | --- | --- | --- | --- |
PengchengHe,MichaelZeng,andXuedongHuang.
|       |                             |     |     |     |     |          | Additionalexamples |          |     | Tables9,    | 10, and11pro- |
| ----- | --------------------------- | --- | --- | --- | --- | -------- | ------------------ | -------- | --- | ----------- | ------------- |
| 2021. | Humanparityoncommonsenseqa: |     |     |     |     | Augment- |                    |          |     |             |               |
|       |                             |     |     |     |     |          | vide more          | examples | for | cases where | EPR is cor-   |
ingself-attentionwithexternalattention.
|             |      |          |     |       |     |            | rect while | CBR is | incorrect | along | with the top-3 |
| ----------- | ---- | -------- | --- | ----- | --- | ---------- | ---------- | ------ | --------- | ----- | -------------- |
| Zihao Zhao, | Eric | Wallace, | Shi | Feng, | Dan | Klein, and |            |        |           |       |                |
promptsforeachmethod.
| SameerSingh.2021. |     |             | Calibratebeforeuse: |             |         | Improv- |     |     |     |     |     |
| ----------------- | --- | ----------- | ------------------- | ----------- | ------- | ------- | --- | --- | --- | --- | --- |
| ing few-shot      |     | performance |                     | of language | models. | In      |     |     |     |     |     |
ICML,pages12697–12706.
ZexuanZhong,DanFriedman,andDanqiChen.2021.
| Factual           | probing | is [MASK]:   |         | Learning | vs.                | learning |     |     |     |     |     |
| ----------------- | ------- | ------------ | ------- | -------- | ------------------ | -------- | --- | --- | --- | --- | --- |
| to recall.        | In      | Proceedings  |         | of the   | 2021 Conference    |          |     |     |     |     |     |
| of the            | North   | American     | Chapter |          | of the Association |          |     |     |     |     |     |
| for Computational |         | Linguistics: |         |          | Human              | Language |     |     |     |     |     |
Technologies,pages5017–5033,Online.Association
forComputationalLinguistics.
A Appendix
Distributionofthenumberofin-contextexam-
ples Sincetheselectionprocedureforin-context
examplesisdynamic,thenumberofin-contextex-
| amplesdiffersforeachtestinstance. |     |     |     |     | InFigure5, |     |     |     |     |     |     |
| --------------------------------- | --- | --- | --- | --- | ---------- | --- | --- | --- | --- | --- | --- |
weplotthehistogramofthenumberofexamples
| wefitinC  | =               | 2,048tokens. |     |     |      |            |     |     |     |     |     |
| --------- | --------------- | ------------ | --- | --- | ---- | ---------- | --- | --- | --- | --- | --- |
| Effect of | hyperparameters |              |     | We  | test | the effect |     |     |     |     |     |
ofk,thenumberofpromptslabeledaspositiveor
negative,andL,thenumberofpromptsretrieved
| bytheunsupervisedretriever. |     |     |     | Table8showsthat |     |     |     |     |     |     |     |
| --------------------------- | --- | --- | --- | --------------- | --- | --- | --- | --- | --- | --- | --- |
performanceisisgenerallyrobustw.r.tthesehyper-
parameters.
|       |     | BREAK | MTOP  |     | SMCALFLOW |     |     |     |     |     |     |
| ----- | --- | ----- | ----- | --- | --------- | --- | --- | --- | --- | --- | --- |
| k =1  |     | 31.5% | 63.0% |     | 54.5%     |     |     |     |     |     |     |
| k =5  |     | 31.9% | 64.2% |     | 54.3%     |     |     |     |     |     |     |
| k =10 |     | 31.0% | 64.1% |     | 52.2%     |     |     |     |     |     |     |
| L=50  |     | 31.9% | 64.2% |     | 54.3%     |     |     |     |     |     |     |
| L=100 |     | 32.3% | 63.7% |     | 51.0%     |     |     |     |     |     |     |
Table8: IntheLM-as-a-servicesetup,usingGPT-Neo,
wesearchforothervaluesforLandk,andnotethatthe
choiceofourhyperparametersisrobust.
| Trainingdetails |     | TotrainEPR,weusetheAdam |     |     |     |     |     |     |     |     |     |
| --------------- | --- | ----------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
optimizer(KingmaandBa,2015)withbatchsize
| 120andlearningrate1e-4oneightRTX3090. |     |            |     |         |           | We      |     |     |     |     |     |
| ------------------------------------- | --- | ---------- | --- | ------- | --------- | ------- | --- | --- | --- | --- | --- |
| run training                          | for | 30 epochs. |     | We      | used the  | default |     |     |     |     |     |
| DPRhyperparameterswithouttuning.      |     |            |     |         | Weusedthe |         |     |     |     |     |     |
| final epoch                           | of  | the model  | to  | perform | model     | selec-  |     |     |     |     |     |
tion,andappliedminimallearningratetuningon
| thevalidationsetof |     | BREAK. |     |     |     |     |     |     |     |     |     |
| ------------------ | --- | ------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
2667

|     |     | Break |     |     |     | MTop |     |     |     | SMCalFlow |     |     |
| --- | --- | ----- | --- | --- | --- | ---- | --- | --- | --- | --------- | --- | --- |
0.030
0.035
0.035
| 0.030 |     |     |     |     |     |     |     | 0.025 |     |     |     |     |
| ----- | --- | --- | --- | --- | --- | --- | --- | ----- | --- | --- | --- | --- |
0.030
0.025
|     |     |     |     | 0.025 |     |     |     | 0.020 |     |     |     |     |
| --- | --- | --- | --- | ----- | --- | --- | --- | ----- | --- | --- | --- | --- |
0.020
0.020
0.015
| 0.015 |     |     |     | 0.015 |     |     |     |     |     |     |     |     |
| ----- | --- | --- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
0.010
| 0.010 |     |     |     | 0.010 |     |     |     |     |     |     |     |     |
| ----- | --- | --- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
0.005
| 0.005 |     |          |       | 0.005 |     |     |     |       |     |     |     |        |
| ----- | --- | -------- | ----- | ----- | --- | --- | --- | ----- | --- | --- | --- | ------ |
| 0.000 |     |          |       | 0.000 |     |     |     | 0.000 |     |     |     |        |
| 10    | 20  | 30 40 50 | 60 70 | 20    | 40  | 60  | 80  | 100   | 20  | 40  | 60  | 80 100 |
Figure5: Distributionofthenumberofin-contextexamplespertestinstanceforeachofthedatasets. Wemarkthe
distributionmeanusingadashedline.
|         |           |                             |     |     | EPR |     |     |     |     |     | CBR |     |
| ------- | --------- | --------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Test    | Utterance | Remindmetoadd2dozeneggstomy |     |     |     |     |     |     |     |     |     |     |
| Example |           | grocerylist.                |     |     |     |     |     |     |     |     |     |     |
Meaning
|     |     | [IN:CREATE_REMINDER |     |     | [SL:PERSON_REMINDED |     |     |     |     |     |     |     |
| --- | --- | ------------------- | --- | --- | ------------------- | --- | --- | --- | --- | --- | --- | --- |
Representation
|     |     | me ]    | [SL:TODO | add | 2 dozen | eggs | to my |     |     |     |     |     |
| --- | --- | ------- | -------- | --- | ------- | ---- | ----- | --- | --- | --- | --- | --- |
|     |     | grocery | list     | ] ] |         |      |       |     |     |     |     |     |
Utterance Remindmetogettwobottlesofwater. Pleaseaddagrocerylisttomylistof
| Top-1 |     |     |     |     |     |     |     | thingstoberemindedaboutdoingtoday. |     |     |     |     |
| ----- | --- | --- | --- | --- | --- | --- | --- | ---------------------------------- | --- | --- | --- | --- |
Meaning
[IN:CREATE_REMINDER [SL:PERSON_REMINDED [IN:CREATE_REMINDER [SL:TODO a grocery
Representation
me ] [SL:TODO get two bottles of water ] list ] [SL:PERSON_REMINDED my ]
|     |     | ]   |     |     |     |     |     | [SL:DATE_TIME |     |     | today ] | ]   |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------- | --- | --- | ------- | --- |
Utterance Remindmetobringanextrapairof Remindmetomakeagrocerylist
| Top-2 |     | shoestotheriver. |     |     |     |     |     |     |     |     |     |     |
| ----- | --- | ---------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Meaning
[IN:CREATE_REMINDER [SL:PERSON_REMINDED [IN:CREATE_REMINDER [SL:PERSON_REMINDED
Representation
me ] [SL:TODO bring an extra pair of me ] [SL:TODO make a grocery list ] ]
|     |     | shoes | to  | the river | ] ] |     |     |     |     |     |     |     |
| --- | --- | ----- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
Utterance Remindmetoaddbottledwaterto Ineedtomakeagrocerylist;willyou
| Top-3 |     | grocerylist. |     |     |     |     |     | remindmewhenIgetoffworkat5:00 |     |     |     |     |
| ----- | --- | ------------ | --- | --- | --- | --- | --- | ----------------------------- | --- | --- | --- | --- |
p.m.?
Meaning
[IN:CREATE_REMINDER [SL:PERSON_REMINDED [IN:CREATE_REMINDER [SL:TODO make a
Representation
me ] [SL:TODO add bottled water to grocery list ] [SL:PERSON_REMINDED me ]
|     |     | grocery | list | ] ] |     |     |     | [SL:DATE_TIME |     |     | at 5 : | 00 p.m . ] ] |
| --- | --- | ------- | ---- | --- | --- | --- | --- | ------------- | --- | --- | ------ | ------------ |
Table9: AnexamplefromMTOPdevelopmentsetwhereEPRiscorrectandCBRisincorrectalongwiththetop-3
trainingexamplesretrievedfromeachretriever.
|         |           |                 |     | EPR |     |     |     |     |     | CBR |     |     |
| ------- | --------- | --------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Test    | Utterance | confirmedthanks |     |     |     |     |     |     |     |     |     |     |
| Example | Meaning   |                 |     |     |     |     |     |     |     |     |     |     |
(PleasantryAnythingElseCombined)
Representation
|       | Utterance | it’sokbye |     |     |     |     | Yes,butmakesuretoletmeknowthe |     |     |     |     |     |
| ----- | --------- | --------- | --- | --- | --- | --- | ----------------------------- | --- | --- | --- | --- | --- |
| Top-1 |           |           |     |     |     |     | weatherforthattime.           |     |     |     |     |     |
Meaning
|     |     | (PleasantryAnythingElseCombined) |     |     |     |     | (let | (x0 (Execute |     | (^(Dynamic) |     |     |
| --- | --- | -------------------------------- | --- | --- | --- | --- | ---- | ------------ | --- | ----------- | --- | --- |
Representation
|     |     |     |     |     |     |     | ConfirmAndReturnAction))) |                  |     |     | (do         | (Yield x0) |
| --- | --- | --- | --- | --- | --- | --- | ------------------------- | ---------------- | --- | --- | ----------- | ---------- |
|     |     |     |     |     |     |     | (Yield                    | (WeatherForEvent |     |     | (^(Dynamic) | item       |
x0)))))
|     | Utterance | It’sok |     |     |     |     | Awesome,perfect |     |     |     |     |     |
| --- | --------- | ------ | --- | --- | --- | --- | --------------- | --- | --- | --- | --- | --- |
Top-2
Meaning
|     |     | (PleasantryAnythingElseCombined) |     |     |     |     | (Yield | (Execute | (^(Dynamic) |     |     |     |
| --- | --- | -------------------------------- | --- | --- | --- | --- | ------ | -------- | ----------- | --- | --- | --- |
Representation
ConfirmAndReturnAction)))
|     | Utterance | It’sok |     |     |     |     | Perfect... |     |     |     |     |     |
| --- | --------- | ------ | --- | --- | --- | --- | ---------- | --- | --- | --- | --- | --- |
Top-3
Meaning
Representation (PleasantryAnythingElseCombined) (Yield (Execute (^(Dynamic)
ConfirmAndReturnAction)))
Table10: AnexamplefromSMCALFLOWdevelopmentsetwhereEPRiscorrectandCBRisincorrectalongwith
thetop-3trainingexamplesretrievedfromeachretriever.
2668

|                |                                  | EPR |     |     | CBR |     |
| -------------- | -------------------------------- | --- | --- | --- | --- | --- |
| Test Utterance | CreateameetingwithDavidCrimtoday |     |     |     |     |     |
Example Meaning
(Yield (CreateCommitEventWrapper
Representation
|     | (CreatePreflightEventWrapper |                    | (&       |     |     |     |
| --- | ---------------------------- | ------------------ | -------- | --- | --- | --- |
|     | (Event.start_?               | (DateTime.date_?   | (?=      |     |     |     |
|     | (Today))))                   | (Event.attendees_? |          |     |     |     |
|     | (AttendeeListHasRecipient    |                    | (Execute |     |     |     |
(refer (extensionConstraint
|     | (RecipientWithNameLike |     | (^(Recipient)     |     |     |     |
| --- | ---------------------- | --- | ----------------- | --- | --- | --- |
|     | EmptyStructConstraint) |     | (PersonName.apply |     |     |     |
"David Crim")))))))))))
Top-1 Utterance makeameetingwithjeritoday setupameetingwithbothofDavid
Crim’sreportstoday
Meaning
(Yield (CreateCommitEventWrapper (Yield (CreateCommitEventWrapper
Representation
(CreatePreflightEventWrapper (& (CreatePreflightEventWrapper (&
(Event.start_? (DateTime.date_? (?= (Event.start_? (DateTime.date_? (?=
|     | (Today)))) | (Event.attendees_? |     | (Today)))) | (Event.attendees_? |     |
| --- | ---------- | ------------------ | --- | ---------- | ------------------ | --- |
(AttendeeListHasRecipient (Execute (AttendeeListHasPeople (FindReports
(refer (extensionConstraint (Execute (refer (extensionConstraint
(RecipientWithNameLike (^(Recipient) (RecipientWithNameLike (^(Recipient)
EmptyStructConstraint) (PersonName.apply EmptyStructConstraint) (PersonName.apply
|     | "jeri"))))))))))) |     |     | "David | Crim")))))))))))) |     |
| --- | ----------------- | --- | --- | ------ | ----------------- | --- |
Utterance putmeetingwithemlimeontoday MakeameetingwithDavidLargenstopon
Top-2
the24th.
Meaning
(Yield (CreateCommitEventWrapper (Yield (CreateCommitEventWrapper
Representation
(CreatePreflightEventWrapper (& (CreatePreflightEventWrapper (&
(Event.start_? (DateTime.date_? (?= (Event.start_? (DateTime.date_? (?=
(Today)))) (Event.attendees_? (nextDayOfMonth (Today) 24L))))
|     | (AttendeeListHasRecipient |     | (Execute | (Event.attendees_? |     |     |
| --- | ------------------------- | --- | -------- | ------------------ | --- | --- |
(refer (extensionConstraint (AttendeeListHasRecipient (Execute
(RecipientWithNameLike (^(Recipient) (refer (extensionConstraint
EmptyStructConstraint) (PersonName.apply (RecipientWithNameLike (^(Recipient)
|     | "emlime"))))))))))) |     |     | EmptyStructConstraint) |     | (PersonName.apply |
| --- | ------------------- | --- | --- | ---------------------- | --- | ----------------- |
"David Largenstop")))))))))))
Utterance IwantmeetDrKennadyfromtoday createameetwithbobtoday
Top-3
Meaning
Representation (Yield (CreateCommitEventWrapper (Yield (CreateCommitEventWrapper
(CreatePreflightEventWrapper (& (CreatePreflightEventWrapper (&
(Event.start_? (DateTime.date_? (?= (Event.start_? (DateTime.date_? (?=
|     | (Today)))) | (Event.attendees_? |     | (Today)))) | (Event.attendees_? |     |
| --- | ---------- | ------------------ | --- | ---------- | ------------------ | --- |
(AttendeeListHasRecipient (Execute (AttendeeListHasRecipient (Execute
|     | (refer | (extensionConstraint |     | (refer | (extensionConstraint |     |
| --- | ------ | -------------------- | --- | ------ | -------------------- | --- |
(RecipientWithNameLike (^(Recipient) (RecipientWithNameLike (^(Recipient)
EmptyStructConstraint) (PersonName.apply EmptyStructConstraint) (PersonName.apply
|     | "Dr Kennady"))))))))))) |     |     | "bob"))))))))))) |     |     |
| --- | ----------------------- | --- | --- | ---------------- | --- | --- |
Table11: AnexamplefromSMCALFLOWdevelopmentsetwhereEPRiscorrectandCBRisincorrectalongwith
thetop-3trainingexamplesretrievedfromeachretriever.
| Utterance                         |                                                      | MeaningRepresentation |                  |                 |     |     |
| --------------------------------- | ---------------------------------------------------- | --------------------- | ---------------- | --------------- | --- | --- |
| which3seasborderphilippines?      |                                                      | 1#) return            | the philippines  |                 |     |     |
|                                   |                                                      | 2#) return            | seas that        | border #1       |     |     |
| whatthreeseassurroundphilippines? |                                                      | 1#) return            | seas             |                 |     |     |
|                                   |                                                      | 2#) return            | #1 that surround | the philippines |     |     |
| whatstatesdoeswestvirginiaborder? |                                                      | 1#) return            | west virginia    |                 |     |     |
|                                   |                                                      | 2#) return            | border states    | of #1           |     |     |
| whatstatesborderswestvirginia?    |                                                      | 1#) return            | west virginia    |                 |     |     |
|                                   |                                                      | 2#) return            | border states    | of #1           |     |     |
| whichstatesbordercolorado         |                                                      | 1#) return            | states           |                 |     |     |
|                                   |                                                      | 2#) return            | #1 that border   | colorado        |     |     |
| Table12:                          | Exampleofaclusterfromthet-SNEprojectionofEPRonBREAK. |                       |                  |                 |     |     |
2669

| Utterance                        | MeaningRepresentation |                |                     |                   |
| -------------------------------- | --------------------- | -------------- | ------------------- | ----------------- |
| Listthetotalscoresofbodybuilders | 1#) return            | body builders  |                     |                   |
| inascendingorder.                | 2#) return            | scores         | of #1               |                   |
|                                  | 3#) return            | sum of         | #2 for each #1      |                   |
|                                  | 4#) return            | #3 sorted      | by ascending        | order             |
| Whatarethenamesofbodybuildersin  | 1#) return            | body builders  |                     |                   |
| descendingorderoftotalscores?    | 2#) return            | names of       | #1                  |                   |
|                                  | 3#) return            | scores         | of #1               |                   |
|                                  | 4#) return            | sum of         | #3 for each #1      |                   |
|                                  | 5#) return            | #2 sorted      | by #4 in descending | order             |
| Listthetotalpointsofgymnastsin   | 1#) return            | gymnasts       |                     |                   |
| descendingorder.                 | 2#) return            | points         | of #1               |                   |
|                                  | 3#) return            | sum of         | #2 for each #1      |                   |
|                                  | 4#) return            | #3 sorted      | by descending       | order             |
| Whatarethetotalpointsforall      | 1#) return            | gymnasts       |                     |                   |
| gymnasts,orderedbytotalpoints    | 2#) return            | total points   | for all             | #1                |
| descending?                      | 3#) return            | #2 ordered     | by total            | points descending |
| Listthetotalpointsofgymnastsin   | 1#) return            | gymnasts       |                     |                   |
| descendingorderoffloorexercise   | 2#) return            | points         | of #1               |                   |
| points.                          | 3#) return            | sum of         | #2 for each #1      |                   |
|                                  | 4#) return            | floor exercise | points              | of #1             |
|                                  | 5#) return            | #3 sorted      | by #4 in descending | order             |
Table13: Exampleofaclusterfromthet-SNEprojectionofEPRonBREAK.
| Utterance                    | MeaningRepresentation |              |       |     |
| ---------------------------- | --------------------- | ------------ | ----- | --- |
| Showthelocationsthathaveboth | 1#) return            | performances |       |     |
| performanceswithmorethan2000 | 2#) return            | attendees    | of #1 |     |
attendeesandperformanceswithless 3#) return the number of #2 for each #1
|     | 4#) return | #1 where | #3 is more | than 2000 |
| --- | ---------- | -------- | ---------- | --------- |
than1000attendees.
|                                    | 5#) return | #1 where      | #3 is less     | than 1000 |
| ---------------------------------- | ---------- | ------------- | -------------- | --------- |
|                                    | 6#) return | the locations | of #4          |           |
|                                    | 7#) return | the locations | of #5          |           |
|                                    | 8#) return | the locations | in both        | #6 and #7 |
| Showthethemeforexhibitionswithboth | 1#) return | exhibitions   |                |           |
| recordsofanattendancebelow100and   | 2#) return | attendances   | of #1          |           |
| above500.                          | 3#) return | number        | of #2 for each | #1        |
|                                    | 4#) return | #1 where      | #3 is below    | 100       |
|                                    | 5#) return | #1 where      | #3 is above    | 500       |
|                                    | 6#) return | #1 of         | both #4 and #5 |           |
|                                    | 7#) return | themes        | for #6         |           |
| Whichthemeshavehadcorresponding    | 1#) return | themes        |                |           |
| exhibitionsthathavehadattendance   | 2#) return | exhibitions   | with #1        |           |
| bothbelow100andabove500?           | 3#) return | attendances   | of #2          |           |
|                                    | 4#) return | #1 where      | #3 is lower    | than 100  |
|                                    | 5#) return | #1 where      | #3 is higher   | than 500  |
|                                    | 6#) return | #1 of         | both #4 and #5 |           |
| Showthepublishersthathave          | 1#) return | publishers    |                |           |
| publicationswithpricehigherthan    | 2#) return | publications  | of #1          |           |
| 10000000andpublicationswithprice   | 3#) return | prices        | of #2          |           |
lowerthan5000000. 4#) return #1 where #3 is higher than 10000000
|                                   | 5#) return | #1 where | #3 is lower    | than 5000000 |
| --------------------------------- | ---------- | -------- | -------------- | ------------ |
|                                   | 6#) return | #1 of    | both #4 and #5 |              |
| Showthefamoustitlesoftheartists   | 1#) return | artists  |                |              |
| withbothvolumesthatlastedmorethan | 2#) return | volumes  | of #1          |              |
| 2weeksontopandvolumesthatlasted   | 3#) return | weeks    | on top that #2 | lasted       |
| lessthan2weeksontop.              | 4#) return | number   | of #3 for each | #2           |
|                                   | 5#) return | #1 where | #4 is more     | than 2       |
|                                   | 6#) return | #1 where | #4 is less     | than 2       |
|                                   | 7#) return | #1 in    | both #5 and #6 |              |
|                                   | 8#) return | famous   | titles of #7   |              |
Table14: Exampleofaclusterfromthet-SNEprojectionofEPRonBREAK.
2670

| Utterance                     | MeaningRepresentation |            |             |     |
| ----------------------------- | --------------------- | ---------- | ----------- | --- |
| Whatisthemetalthingnexttothe  | 1#) return            | the small  | cylinder    |     |
| smallcylinder?                | 2#) return            | things     |             |     |
|                               | 3#) return            | #2 that    | are metal   |     |
|                               | 4#) return            | #3 that    | are next to | #1  |
| Whatisthepurplethingnexttothe | 1#) return            | the brown  | thing       |     |
| brownthing?                   | 2#) return            | things     |             |     |
|                               | 3#) return            | #2 that    | are purple  |     |
|                               | 4#) return            | #3 that    | are next to | #1  |
| Whatisthegraythingnexttothe   | 1#) return            | gray thing |             |     |
|                               | 2#) return            | the block  |             |     |
block?
|                               | 3#) return | #1 next     | to #2       |       |
| ----------------------------- | ---------- | ----------- | ----------- | ----- |
| Whatistheshinythingnexttothe  | 1#) return | shiny thing |             |       |
| cylinder?                     | 2#) return | cylinder    |             |       |
|                               | 3#) return | #1 next     | to #2       |       |
| Whatisthethinginfrontofthered | 1#) return | things      |             |       |
| square?                       | 2#) return | squares     |             |       |
|                               | 3#) return | #2 that     | is red      |       |
|                               | 4#) return | #1 that     | is in front | of #3 |
Table15: Exampleofaclusterfromthet-SNEprojectionofEPRonBREAK.
| Utterance                       | MeaningRepresentation |         |       |     |
| ------------------------------- | --------------------- | ------- | ----- | --- |
| Isthepurplethingbehindthebigred | 1#) return            | purple  | thing |     |
|                                 | 2#) return            | big red | thing |     |
thing?
|                                | 3#) return | Is #1      | behind #2    |       |
| ------------------------------ | ---------- | ---------- | ------------ | ----- |
| isthepurplesphereinfrontofthe  | 1#) return | the purple | sphere       |       |
| bluecube?                      | 2#) return | the blue   | cube         |       |
|                                | 3#) return | if #1      | is in front  | of #2 |
| isthegrayspherebehindthegreen  | 1#) return | the green  | cylinder     |       |
| cylinder?                      | 2#) return | the gray   | sphere       |       |
|                                | 3#) return | if #2      | is behind #1 |       |
| istheredcubeinfrontoftheyellow | 1#) return | the red    | cube         |       |
| ball?                          | 2#) return | the yellow | ball         |       |
|                                | 3#) return | if #1      | is in front  | of #2 |
|                                | 1#) return | blue ball  |              |       |
Istheblueballinfrontofthesilver
| cube? | 2#) return | silver | cube        |     |
| ----- | ---------- | ------ | ----------- | --- |
|       | 3#) return | is #1  | in front of | #2  |
Table16: Exampleofaclusterfromthet-SNEprojectionofEPRonBREAK.
2671