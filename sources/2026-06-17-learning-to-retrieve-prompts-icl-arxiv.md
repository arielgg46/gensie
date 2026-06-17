---
type: source
source_type: paper
url: https://arxiv.org/pdf/2112.08633
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
|            |          |     |             |     |             |     |     |     | Retriever | What is the length of the  |     |
| ---------- | -------- | --- | ----------- | --- | ----------- | --- | --- | --- | --------- | -------------------------- | --- |
| In-context | learning |     |             |     |             |     |     |     |           | longest river in the usa?  |     |
|            |          |     | is a recent |     | paradigm in |     |     |     |           |                            |     |
Question
| naturallanguageunderstanding,wherealarge |     |     |     |     |     | Retriever Index |     |     |     |     |     |
| ---------------------------------------- | --- | --- | --- | --- | --- | --------------- | --- | --- | --- | --- | --- |
Similar examples
| pre-trained |     | language | model | (LM) | observes a |     |     |     |     |     |     |
| ----------- | --- | -------- | ----- | ---- | ---------- | --- | --- | --- | --- | --- | --- |
2202 yaM 8  ]LC.sc[  2v33680.2112:viXra What is the longest river in  Which states border the  Which states border the
|     |     |     |     |     |     | the smallest state in the usa? |     | shortest river in the usa? |     |  longest river in the usa? |     |
| --- | --- | --- | --- | --- | --- | ------------------------------ | --- | -------------------------- | --- | -------------------------- | --- |
testinstanceandafewtrainingexamplesasits
1) states
input,anddirectlydecodestheoutputwithout 1) the usa 1) the usa
|            |     |                    |     |          |      | 2) size of #1                |     | 2) rivers of #1              |     | 2) rivers of #1               |     |
| ---------- | --- | ------------------ | --- | -------- | ---- | ---------------------------- | --- | ---------------------------- | --- | ----------------------------- | --- |
| any update |     | to its parameters. |     | However, | per- | 3) #1 where #2 is the lowest |     |                              |     |                               |     |
|            |     |                    |     |          |      | 4) rivers of #3              |     | 3) how long are #2           |     | 3) how long are #2            |     |
|            |     |                    |     |          |      |                              |     | 4) #2 where #3 is the lowest |     | 4) #2 where #3 is the highest |     |
formance has been shown to strongly depend 5) how long are #4 5) border states of #4 5) border states of #4
6) #4 where #5 is the highest
| on the    | selected | training       |           | examples   | (termed     |     |     |           |              |     |     |
| --------- | -------- | -------------- | --------- | ---------- | ----------- | --- | --- | --------- | ------------ | --- | --- |
| prompts). |          | In this work,  |           | we propose | an ef-      |     |     |           | Inference LM |     |     |
| ficient   | method   | for retrieving |           | prompts    | for in-     |     |     |           |              |     |     |
| context   | learning | using          | annotated |            | data and an |     |     | 1) rivers |              |     |     |
2) #1 in the usa
| LM. | Given | an input-output |     | pair, | we estimate |     |     | 3) lengths of #2 |     |     |     |
| --- | ----- | --------------- | --- | ----- | ----------- | --- | --- | ---------------- | --- | --- | --- |
4) #2 where #3 is longest
| the probability |             | of             | the output | given    | the in-  |           |     | 5) length of #4 |           |            |         |
| --------------- | ----------- | -------------- | ---------- | -------- | -------- | --------- | --- | --------------- | --------- | ---------- | ------- |
| put and         | a candidate |                | training   | example  | as the   |           |     |                 |           |            |         |
|                 |             |                |            |          |          | Figure 1: | An  | overview        | of prompt | retrieval: | Given a |
| prompt,         | and         | label training |            | examples | as posi- |           |     |                 |           |            |         |
tiveornegativebasedonthisprobability. We questionfromBREAK,oneretrievessimilartrainingex-
|     |     |     |     |     |     | amplesfromanindexofthetrainingset. |     |     |     |     | Thequestion |
| --- | --- | --- | --- | --- | --- | ---------------------------------- | --- | --- | --- | --- | ----------- |
thentrainanefficientdenseretrieverfromthis
andtrainingexamples(theprompt)arepassedtoanin-
| data, | which | is used | to retrieve | training | exam- |     |     |     |     |     |     |
| ----- | ----- | ------- | ----------- | -------- | ----- | --- | --- | --- | --- | --- | --- |
ferenceLMthatdecodestheoutput.
| ples         | as prompts | at       | test time.           |     | We evaluate |     |     |     |     |     |     |
| ------------ | ---------- | -------- | -------------------- | --- | ----------- | --- | --- | --- | --- | --- | --- |
| our approach |            | on three | sequence-to-sequence |     |             |     |     |     |     |     |     |
taskswherelanguageutterancesaremappedto
(2021a)showedthatdownstreamperformancecan
| meaning | representations, |     | and | find | that it sub- |     |     |     |     |     |     |
| ------- | ---------------- | --- | --- | ---- | ------------ | --- | --- | --- | --- | --- | --- |
varywidelydependingonthechoiceofin-context
stantiallyoutperformspriorworkandmultiple
|     |     |     |     |     |     | examples. | Thishassparkedinterestinpromptre- |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --------- | --------------------------------- | --- | --- | --- | --- |
baselinesacrosstheboard.
|     |     |     |     |     |     | trieval | (see Fig. | 1), | where given | a   | test instance, |
| --- | --- | --- | --- | --- | --- | ------- | --------- | --- | ----------- | --- | -------------- |
1 Introduction
trainingexamplesarechosenforthepromptbased
Thestrikinglanguageskillsandworldknowledge onsomesimilaritymetric. Recentworkhaseither
embedded in large pre-trained language models usedoff-the-shelfunsupervisedsimilaritymetrics,
|     |     |     |     |     |     |     |     | prompt | retriever |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ------ | --------- | --- | --- |
(LMs)(Devlinetal.,2019;Petronietal.,2019;Raf- or trained a to select examples
feletal.,2020;Brownetal.,2020)haverecently basedonsurfacesimilarity(Dasetal.,2021).
ledtoin-contextlearning,anewparadigminnatu- In this work, we suggest to use language mod-
rallanguageunderstanding. Underthisparadigm, elsthemselvestolabelexamplesthatcanserveas
a language model is given a prompt, which typi- good prompts, and train a prompt retriever from
callycontainsafewtrainingexamples,aswellasa this signal. To train the retriever (see Fig. 2), we
testinstanceasinput,andgeneratestheoutputfor assumeaccesstoatrainingsetofinput-outputpairs
|     |     |     |     |     |     |     | scoring | LM, |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------- | --- | --- | --- | --- |
thetestinstancedirectly,withoutanyupdatetoits and to a i.e., a language model that
parameters. Thisapproachwasfirstintroducedin will be used to score prompts. For each training
GPT-3(Brownetal.,2020),buthasquicklyspread example (x,y), we go over other candidate train-
tootherLMs(Lieberetal.,2021;Duetal.,2021; ingexamples,andestimatetheprobability,accord-
| Raeetal.,2021). |     |     |     |     |     | ingtothescoringLM,ofy |     |     | conditionedonxand |     |     |
| --------------- | --- | --- | --- | --- | --- | --------------------- | --- | --- | ----------------- | --- | --- |
Anattractivepropertyofin-contextlearningis thecandidateprompt. Welabeltrainingexamples
that it provides a single model for multiple lan- that lead to high probability as positive and low
guage understanding tasks. However, Liu et al. probabilityasnegativeandtrainapromptretriever

D
Figure 2: An overview of our approach for training EPR. Given a training example, we use an unsupervised
retrieverR u toobtainasetofcandidates. WethenpassthecandidatestoascoringLMandlabelthetop-kandthe
bottom-kaspositiveandnegativeexamples,respectively. Last,weusethistrainingdatatotrainadenseretriever.
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
|     |     |     |     |     |     | for larger | LMs | (GPT-J, | GPT-3, | and CODEX), |     | we  |
| --- | --- | --- | --- | --- | --- | ---------- | --- | ------- | ------ | ----------- | --- | --- |
UsingascoringLMtotrainanefficientretriever
observesimilargains,whereperformanceimproves
| forapotentiallydifferenttesttimeinferenceLM |     |     |     |     |     | is  |     |     |     |     |     |     |
| ------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
substantiallyinallcases.
| beneficialintwoscenarios. |     |     | First,whenthescoring |     |     |     |     |     |     |     |     |     |
| ------------------------- | --- | --- | -------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Toconclude,weproposeanapproachforretriev-
LMissmallerthantheinferenceLMandservesas
|                         |         |              |            |            |               | ing training   | examples |          | for in-context |                  | learning | in     |
| ----------------------- | ------- | ------------ | ---------- | ---------- | ------------- | -------------- | -------- | -------- | -------------- | ---------------- | -------- | ------ |
| a proxy                 | for it. | This results | in         | cheap      | and efficient |                |          |          |                |                  |          |        |
|                         |         |              |            |            |               | large language |          | models,  | and show       | it substantially |          |        |
| data generation         |         | for the      | retriever, | accessible |               | to a           |          |          |                |                  |          |        |
|                         |         |              |            |            |               | outperforms    | prior    | methods. |                | Given recent     |          | devel- |
| widerangeofresearchers. |         |              | Second,    |            | ourapproach   |                |          |          |                |                  |          |        |
opmentsinscalingLMs,designingefficientmeth-
canbeusedevenwhenthescoringandinference
|            |           |          |          |             |            | ods for                   | interacting | with                   | LMs               | is an important |     | di- |
| ---------- | --------- | -------- | -------- | ----------- | ---------- | ------------------------- | ----------- | ---------------------- | ----------------- | --------------- | --- | --- |
| LMs are    | identical | (e.g.,   | both     | are GPT-3). | This       | is                        |             |                        |                   |                 |     |     |
|            |           |          |          |             |            | rectionforfutureresearch. |             |                        | Ourcodeanddataare |                 |     |     |
| beneficial | when      | we do    | not have | access      | to model   |                           |             |                        |                   |                 |     |     |
|            |           |          |          |             |            | publicly                  | available   | at https://github.com/ |                   |                 |     |     |
| parameters | and       | can only | use      | it as       | a service, | an                        |             |                        |                   |                 |     |     |
OhadRubin/EPR.
| increasinglypopularparadigm. |     |     |     | Inthiscase,weuse |     |     |     |     |     |     |     |     |
| ---------------------------- | --- | --- | --- | ---------------- | --- | --- | --- | --- | --- | --- | --- | --- |
theLMtotrainalight-weightretrieverthatisonly
|             |          |     |              |           |     | 2 Background: |     | PromptRetrieval |     |     |     |     |
| ----------- | -------- | --- | ------------ | --------- | --- | ------------- | --- | --------------- | --- | --- | --- | --- |
| tasked with | learning |     | a similarity | function. |     | More          |     |                 |     |     |     |     |
generally,giventhatthescaleofLMsislikelyto
|     |     |     |     |     |     | Problem | setup | Given | a   | training | set | D = |
| --- | --- | --- | --- | --- | --- | ------- | ----- | ----- | --- | -------- | --- | --- |
keepincreasingintheforeseeablefuture,onecan {(x ,y )}n of input-output sequences, and a
i i i=1
viewourapproachforEfficientPromptRetrieval, test example x , our goal is to train a retriever,
test
orEPR,asamethodforinterfacingandlearningto
|     |     |     |     |     |     | R(x ,D), | that | will retrieve |     | a subset | of training |     |
| --- | --- | --- | --- | --- | --- | -------- | ---- | ------------- | --- | -------- | ----------- | --- |
test
interactwithlargeLMs. examplesP = {(x ,y )}m ⊂ D,wherem (cid:28) n.
|     |     |     |     |     |     |     |     | j j |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
j=1
|                |     |      |     |          |            | WesuccinctlyrefertoP |     |     | astheprompt.1 |     |     |     |
| -------------- | --- | ---- | --- | -------- | ---------- | -------------------- | --- | --- | ------------- | --- | --- | --- |
| We empirically |     | test | EPR | on three | structured |                      |     |     |               |     |     |     |
GivenaninferenceLM,g,agoodpromptshould
| sequence-to-sequence |     |     | tasks, | where | input natural |     |     |     |     |     |     |     |
| -------------------- | --- | --- | ------ | ----- | ------------- | --- | --- | --- | --- | --- | --- | --- |
languageutterancesaremappedtoameaningrep- lead to the target output sequence when the test
| resentation: | MTOP |     | (Li et | al., 2021) | and | SM- |     |     |     |     |     |     |
| ------------ | ---- | --- | ------ | ---------- | --- | --- | --- | --- | --- | --- | --- | --- |
1Promptoftenreferstoanaturallanguagetemplatefilled
CALFLOW(Andreasetal.,2020),whichfocuson
byaninputexample(Liuetal.,2021b),buthereitdenotesthe
task-orienteddialogue,andBREAK(Wolfsonetal.,
sequenceoftrainingexamplesprovidedasinputtotheLM.

examplex test isconcatenatedtothepromptP and thatourgoalistoretrieveexamplesthataresimilar
passedasaprefixtog. Specifically,decodingfrom totheinputintermsoftheiroutputsequence,y.
theLMg([P;x ])shouldyieldy . Inthiswork, To obtain a high-quality candidate set of train-
|     |     | test | test |     |     |     |     |     |     |     |
| --- | --- | ---- | ---- | --- | --- | --- | --- | --- | --- | --- |
wefocusonstructuredtasks,suchassemanticpars- ing examples, we take advantage of an unsuper-
ing,wherexisanaturallanguageutteranceandy visedretriever,E¯= R ((x,y),D).
|     |     |     |     |     |     |     |     | u   | Forthechoice |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ------------ | --- |
isameaningrepresentationforthatutterance. oftheunsupervisedretriever,weexperimentwith
|            |     |            |                      |     | BM25 | (Robertson | and | Zaragoza, | 2009), a | sparse |
| ---------- | --- | ---------- | -------------------- | --- | ---- | ---------- | --- | --------- | -------- | ------ |
| Prior work |     | Liu et al. | (2021a) investigated |     | the  |            |     |           |          |        |
retrieverthatreliesonsurfacetextsimilarity,and
| effect of | different | prompts | on the | performance |     |     |     |     |     |     |
| --------- | --------- | ------- | ------ | ----------- | --- | --- | --- | --- | --- | --- |
SBERT(ReimersandGurevych,2019),whichis
| of GPT-3 | and | demonstrated | that the | choice | of in-   |       |          |           |           |     |
| -------- | --- | ------------ | -------- | ------ | -------- | ----- | -------- | --------- | --------- | --- |
|          |     |              |          |        | based on | dense | sentence | encoding. | For both, | we  |
contextexamplesstronglyaffectsdownstreamper-
experimentedwithpassingtheretrieverthetraining
| formance. | They | used | an unsupervised | sentence |     |     |     |     |     |     |
| --------- | ---- | ---- | --------------- | -------- | --- | --- | --- | --- | --- | --- |
pair(x,y)orthetargetsequencey
only,andfound
encodertoencodetrainingexamples,andretrieved
|     |     |     |     |     | thatusingy | leadstoslightlyhigherperformance. |     |     |     |     |
| --- | --- | --- | --- | --- | ---------- | --------------------------------- | --- | --- | --- | --- |
foreverytestinstanceitsnearestneighbors.
| Das | et al. (2021) | trained | a supervised | prompt |                        |     |     |                   |     |     |
| --- | ------------- | ------- | ------------ | ------ | ---------------------- | --- | --- | ----------------- | --- | --- |
|     |               |         |              |        | Scoringthecandidateset |     |     | Onceweretrievethe |     |     |
retrieverforknowledge-basequestionanswering. setofcandidatesE¯= {e¯ ,··· ,e¯}foratraining
|     |     |     |     |     |     |     |     | 1   | L   |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
E¯
Theretrieverwastrainedwithsupervisionthatis example (x,y),2 we score each candidate e¯ ∈
l
tailoredforknowledge-basequeries,andrelieson independentlywithascoringLM,gˆ,whichserves
surface similarity between formal queries. Con- as a proxy for the inference LM, g. Specifically,
versely,ourapproachtakesadvantageofthegener- thescoreforacandidatepromptis
ativeLMitselfandisthusmoregeneral.
Shinetal.(2021)usedGPT-3toselectexamples s(e¯ ) = Prob (y | e¯ ,x),
|                                         |     |     |     |     |      |     | l   | gˆ  | l   |     |
| --------------------------------------- | --- | --- | --- | --- | ---- | --- | --- | --- | --- | --- |
| forthepromptforfew-shotsemanticparsing. |     |     |     |     | How- |     |     |     |     |     |
whichistheprobabilityundertheLM,gˆ,oftheout-
ever,ratherthantrainingaretriever,theyrandomly
putsequenceconditionedonthecandidateprompt
samplealargesetofutterance-programpairsfrom
thetrainingset,andchoosethosethataresimilar andinputsequence. Thisindicateshowhelpfulthis
candidateisfordecodingthetarget(independent
tothetargetinstancequestionaccordingtoGPT-3.
|              |     |              |           |            | of all other | candidates). |     | We argue | this score | is a |
| ------------ | --- | ------------ | --------- | ---------- | ------------ | ------------ | --- | -------- | ---------- | ---- |
| This results | in  | an expensive | inference | procedure, |              |              |     |          |            |      |
whereGPT-3isrunhundredsoftimesforeachtest betterproxyfortheutilityofatrainingexampleat
inferencetimecomparedtopriorapproaches.
instance,unlikeourapproach,whichisbasedona
Weapplythisscoringfunctiontoalltrainingex-
light-weightsub-linearretriever.
amples,anddefineforeachtrainingexampleaset
3 EfficientPromptRetriever
|     |     |     |     |     | ofpositiveexamplesE |     |     | pos ,whichincludesthetop-k |     |     |
| --- | --- | --- | --- | --- | ------------------- | --- | --- | -------------------------- | --- | --- |
candidatesinE¯accordingtos(e¯),andasetofneg-
l
| We now | describe | our | method for training |     | EPR,           |     |                           |     |     |     |
| ------ | -------- | --- | ------------------- | --- | -------------- | --- | ------------------------- | --- | --- | --- |
|        |          |     |                     |     | ativeexamplesE |     | ,whichincludesthebottom-k |     |     |     |
neg
an efficient prompt retriever for in-context learn- candidatesinE¯accordingtos(e¯).
l Thisshouldlead
ing. Wefirstdescribehowtogeneratelabeleddata
torelevantpositiveexamples,assumingthattheset
| (§3.1), | and then | how to | use the training | data | for |     |     |     |     |     |
| ------- | -------- | ------ | ---------------- | ---- | --- | --- | --- | --- | --- | --- |
ofcandidates,E¯includesgoodpromptcandidates
| training | and inference | (§3.2). | Fig. 2 | provides | an  |     |     |     |     |     |
| -------- | ------------- | ------- | ------ | -------- | --- | --- | --- | --- | --- | --- |
andhardnegatives,sinceallcandidateshavehigh
overviewofthetrainingprocedure.
|     |     |     |     |     | similaritywith(x,y)accordingtoR |     |     |     | (y,D). |      |
| --- | --- | --- | --- | --- | ------------------------------- | --- | --- | --- | ------ | ---- |
|     |     |     |     |     |                                 |     |     |     | u      | With |
positiveandnegativeexamplesatourdisposal,we
3.1 GeneratingtheTrainingData
cannowapplycontrastivelearning,whichwede-
Ourapproachreliesonfindingwhichtrainingex-
scribenext.
amplescanserveasgoodpromptsforothertraining
examples. Scoringallpairsoftrainingexamplesis 3.2 TrainingandInference
quadraticin|D|,andthusprohibitive.
Hence,we
|     |     |     |     |     | Training | Our | training | procedure | proceeds | ex- |
| --- | --- | --- | --- | --- | -------- | --- | -------- | --------- | -------- | --- |
presentamethodforchoosingasetofcandidateex-
| amplesE¯⊂ |     |     |     |     | actlylikethecontrastivelearningprocedurefrom |     |     |     |     |     |
| --------- | --- | --- | --- | --- | -------------------------------------------- | --- | --- | --- | --- | --- |
D,fromwhichwewillchoosepositive
|                                             |          |     |               |              | DPR(Karpukhinetal.,2020). |     |     |                      | Thisprocedurere- |     |
| ------------------------------------------- | -------- | --- | ------------- | ------------ | ------------------------- | --- | --- | -------------------- | ---------------- | --- |
| and negative                                | examples |     | for training. | Importantly, |                           |     |     |                      |                  |     |
|                                             |          |     |               |              | sultsinaninputencoderE    |     |     | (·),whichreceivesthe |                  |     |
| sincewearenotattesttimeandareonlygenerating |          |     |               |              |                           |     |     | X                    |                  |     |
sequenceofinputtokens,x,andapromptencoder
| data for | training, | we can | use the target | sequence |                                             |     |     |     |     |     |
| -------- | --------- | ------ | -------------- | -------- | ------------------------------------------- | --- | --- | --- | --- | --- |
|          |           |        |                |          | E (·),whichreceivesacandidateprompt,namely, |     |     |     |     |     |
P
| y toretrieveagoodsetofcandidates. |     |     |     | Thiscanbe |     |     |     |     |     |     |
| --------------------------------- | --- | --- | --- | --------- | --- | --- | --- | --- | --- | --- |
approachedusingasimpleretrievalmethod,given 2WeomitthedependenceofE¯on(x,y)forsimplicity.

a concatenation of the tokens in an input-output 4 ExperimentalResults
pair. BothencodersareinitializedwithBERT-base
We now compare EPR to a wide range of unsu-
(Devlin etal.,2019), and theoutputvector repre-
pervisedandsupervisedbaselines,bothwhenthe
sentationisgivenbytheCLStoken,asusual. The
scoringLM,gˆ,issmallerthantheinferenceLM,g,
goaloftrainingistolearnasimilaritymetricsuch
andwhentheyareidentical.
thatgivenatestexamplex ,itwillbesimilarto
test
trainingexamplesthatleadtodecodingofy .
test 4.1 Datasets
Our training instances are of the form
(cid:104)x ,e+,e− ,...e− (cid:105). Where the positive ex- Wefocusontasksthatmaputterancestomeaning
i i i,1 i,2B−1
representations,wherein-contextexamplescanbe
ample e+ is sampled from the set E (i) , and our
i pos usedtolearnthemappingfrominputstooutputs.
negativeexamplesconsistofonehardnegativeex-
Examples from each dataset and the number of
(i)
amplesampledfromE ,B−1positiveexamples
neg examplesareinTable1.
from the other instances in the same mini-batch,
• BREAK (Wolfson et al., 2020): A dataset map-
andtheB−1hardnegativesfromthoseinstances.
pingcomplexnaturallanguagequestionsintoa
We define the similarity score between an input
language-basedmeaningrepresentation, where
and an input-output pair to be the inner product
a question is decomposed into an ordered list
sim(x,e) = E (x)(cid:62)E (e). We can now define
X P of atomic steps. We use the low-level BREAK
thetypicalcontrastivelearningobjectiveandmini-
subset, containing 44K/7K/8K examples in its
mizeforeachexamplethenegativeloglikelihood
training/development/testsets.
ofthepositiveexample:
• MTOP (Li et al., 2021): A semantic parsing
dataset,focusedontask-orienteddialogue,where
L(x ,e+,e− ,...e− ) (1)
i i i,1 i,2B−1 commandsaremappedtocomplexnestedqueries
esim(xi,e+ i ) across11domains. Similartopastwork(Pasu-
= −log .
esim(xi,e+
i
)+ (cid:80)2
j=
B
1
−1esim(xi,e−
i,j
) pat et al., 2021), we use the English subset of
MTOP, containing 16K/2K/4K examples in its
training/development/testsets.
Anadvantageofthisapproachisthatforbatchsize
B theeffectivebatchsizeisoforderB2,withthe • SMCALFLOW (Andreas et al., 2020): A large
in-batchnegativestrick(Hendersonetal.,2017). English-languagetask-orienteddatasetthatcov-
erstaskssuchascalendar,weather,places,and
Inference After training the input encoder and people. Themeaningrepresentationisadataflow
promptencoder,weencodetheentiresetoftrain- program,whichincludesAPIcalls,functioncom-
ingexampleswithE (·)inapre-processingstep positionandcomplexconstraints. SMCALFLOW
P
using FAISS (Johnson et al., 2017). At test time, includes 15K development set examples and
givenaninputsequence,x ,wecomputeitsen- 134Ktrainingexamples,fromwhichwesample
test
coding E (x ), and then use maximum inner- arandomsetof44Kexamplesfortraining.
X test
productsearchoverthetrainingdatatofindtheL
4.2 BaselinesandOracles
mostsimilartrainingexamples,sortedbytheirin-
nerproduct(fromhightolow): P = (e 1 ,...,e L ). Weconsiderthefollowingunsupervisedbaselines,
ThefinalpromptP(cid:48) isdeterminedbyC,themax- whichareappliedattesttimeonly.
imalcontextsizesupportedbytheinferenceLM, • RANDOM: werandomlysampleexamplesfrom
g. Specifically, L(cid:48) ≤ L is the largest L(cid:48) such thetrainingsetD.
(cid:80)L(cid:48) |e | + |x | + |y(cid:48)| ≤ C, where |y(cid:48)| is the
i=1 i test • SBERT:WeuseSentenceTransformers,
desiredmaximallengthofthegeneratedoutput. Fi-
a library providing BERT-based sen-
nally,wereturntheoutputofgreedydecodingon
tence embeddings.3 Specifically, we use
g([e ;e ;...;e ;x ]).
L(cid:48) L(cid:48)−1 1 test paraphrase-mpnet-base-v2, a 110M
Wenotethatwhileattrainingtimewescoreeach
parameter model to encode the test utterance
training example independently, at test time the
x and retrieve the examples with the most
test
languagemodelobservesaprompt,i.e.,asequence
similarutterancesasin-contextexamples.
ofexamples. Weleavemodelingthedependence
betweendifferenttrainingexamplestofuturework. 3https://www.sbert.net/index.html.

|     | Dataset | Size | Utterance                        |     |     |     | MeaningRepresentation |     |              |        |          |     |
| --- | ------- | ---- | -------------------------------- | --- | --- | --- | --------------------- | --- | ------------ | ------ | -------- | --- |
|     | BREAK   | 60K  | Therearemorebirdsintheimageon    |     |     |     | 1) return             |     | right image; |        |          |     |
|     |         |      | therightthanintheimageontheleft. |     |     |     | 2) return             |     | birds in     | #1;    |          |     |
|     |         |      |                                  |     |     |     | 3) return             |     | number of    | #2;    |          |     |
|     |         |      |                                  |     |     |     | 4) return             |     | left image;  |        |          |     |
|     |         |      |                                  |     |     |     | 5) return             |     | birds in     | #4     |          |     |
|     |         |      |                                  |     |     |     | 6) return             |     | number of    | #5;    |          |     |
|     |         |      |                                  |     |     |     | 7) return             |     | if #3 is     | higher | than #6; |     |
|     |         | MTOP | callZoey’swife.                  |     |     |     | [IN:CREATE_CALL       |     | =            |        |          |     |
22K
|     |     |     |     |     |     |     | [SL:CONTACT         |                   | = [IN:GET_CONTACT |            | =   |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------- | ----------------- | ----------------- | ---------- | --- | --- |
|     |     |     |     |     |     |     | [SL:CONTACT_RELATED |                   |                   | = Zoey]    |     |     |
|     |     |     |     |     |     |     |                     | [SL:TYPE_RELATION |                   | = wife]]]] |     |     |
SMCALFLOW Canyoucreatemeanewmeeting (Yield (CreateCommitEventWrapper
148K
|     |     |     | onthursdaymorning? |     |     |     | (CreatePreflightEventWrapper |     |     |     |     |     |
| --- | --- | --- | ------------------ | --- | --- | --- | ---------------------------- | --- | --- | --- | --- | --- |
(Event.start_?
|     |     |         |                                            |     |     |     |     | (DateTimeConstraint |                  | (Morning) |     |     |
| --- | --- | ------- | ------------------------------------------ | --- | --- | --- | --- | ------------------- | ---------------- | --------- | --- | --- |
|     |     |         |                                            |     |     |     |     | (NextDOW            | (Thursday))))))) |           |     |     |
|     |     | Table1: | Examplesfromeachofthedatasetsweevaluateon. |     |     |     |     |                     |                  |           |     |     |
• BM25: We use the classical sparse retrieval ofrelationsappearinginthoselogicalforms,and
methodBM25(RobertsonandZaragoza,2009), use this weight to softly label their data. Since
whichisanextensionofTF-IDF,toretrievefor in our setting we do not assume logical forms,
each test utterance x the training examples wedefinethescorebetweentwooutputsequence
test
withthemostsimilarutterance. y i and y j to be the F 1 between the two sets of
|               |     |          |            |     |           |     | tokensiny | andy | ,omittingstopwords. |     |     |     |
| ------------- | --- | -------- | ---------- | --- | --------- | --- | --------- | ---- | ------------------- | --- | --- | --- |
| • BRUTEFORCE: |     | We apply | the prompt |     | selection |     |           | i    | j                   |     |     |     |
methodforfew-shotsemanticparsingfromShin • EFFICIENT PROMPT RETRIEVAL (EPR): Our
etal.(2021). Givenatestexamplex test ,wesam- fullapproachfrom§3.
ple 200 training examples. For each training Last,wealsoconsidertwooraclemodels.
example(x ,y ),computeProb (x | x ),and • BM25-ORACLE: We score test examples
|     |     | i i |     | g test | i   |     |     |     |     |     |     |     |
| --- | --- | --- | --- | ------ | --- | --- | --- | --- | --- | --- | --- | --- |
usethehighestscoringexamplesfortheprompt. with BM25 using the gold output sequence
| Similar | to     | us, this approach | uses     | the | inference  |     |                              |         |      |          |                |        |
| ------- | ------ | ----------------- | -------- | --- | ---------- | --- | ---------------------------- | ------- | ---- | -------- | -------------- | ------ |
|         |        |                   |          |     |            |     | R                            | (y ,D). | This | provides | an upper-bound |        |
|         |        |                   |          |     |            |     | BM25                         | test    |      |          |                |        |
| LM to   | choose | prompts.          | However, | it  | does so at |     |                              |         |      |          |                |        |
|         |        |                   |          |     |            |     | onwhatcanbelearnedbyDR-BM25. |         |      |          |                | EPRcan |
testtime,whichresultsinslowinference. potentiallyoutperformthisoracle,sinceitstrain-
Next, we describe baselines that use the train- ingsignalgoesbeyondsurfacetextsimilarity.
| ing set,                               | D, to | train a prompt | retriever. |     | All super- |     |            |      |                              |       |        |         |
| -------------------------------------- | ----- | -------------- | ---------- | --- | ---------- | --- | ---------- | ---- | ---------------------------- | ----- | ------ | ------- |
|                                        |       |                |            |     |            | •   | LM-ORACLE: |      | Weusetheprocedureforlabeling |       |        |         |
| visedmethodssharethefollowingtemplate. |       |                |            |     | First,     |     |            |      |                              |       |        |         |
|                                        |       |                |            |     |            |     | training   | data | at test time.                | Given | a test | example |
acandidatesetE¯ofL
= 50examplesisretrieved
|                               |     |     |     |        |       |     | (x ,y | ),wefirstretrieveLcandidatetraining |     |     |     |     |
| ----------------------------- | --- | --- | --- | ------ | ----- | --- | ----- | ----------------------------------- | --- | --- | --- | --- |
| withtheunsupervisedretrieverR |     |     |     | (y,D). | Weuse |     | test  | test                                |     |     |     |     |
u
|     |     |     |     |     |     |     | exampleswithR |     | BM25 (y | test ,D),wethensortthe |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------- | --- | ------- | ---------------------- | --- | --- |
BM25asanunsupervisedretriever,sinceitoutper-
candidateswiththescoringLMgˆ,estimatingthe
| formedSBERT(see§4.4). |     |                              | Wethenscoreeachcan- |     |     |     |                |     |        |      |                 |     |
| --------------------- | --- | ---------------------------- | ------------------- | --- | --- | --- | -------------- | --- | ------ | ---- | --------------- | --- |
|                       |     |                              |                     |     |     |     | probabilityofy |     | givenx |      | andthecandidate |     |
| didateprompte¯        |     | ∈ E¯withsomescoringfunction, |                     |     |     |     |                |     | test   | test |                 |     |
l
|                  |     |                           |     |     |     |     | prompt. | ThisprovidesanupperboundforEPR, |     |     |     |     |
| ---------------- | --- | ------------------------- | --- | --- | --- | --- | ------- | ------------------------------- | --- | --- | --- | --- |
| andlabelthetop-k |     | promptsaspositiveexamples |     |     |     |     |         |                                 |     |     |     |     |
sinceEPRistrainedtoemulatethisbehaviour.
| and the | bottom-k | as negative | examples |     | (k = 5). |     |     |     |     |     |     |     |
| ------- | -------- | ----------- | -------- | --- | -------- | --- | --- | --- | --- | --- | --- | --- |
Different supervised methods only differ in the 4.3 ExperimentalDetails
scoringfunctionitself.4
|            |              |          |         |          |       | Language |       | models     | In          | this work, | we  | only train |
| ---------- | ------------ | -------- | ------- | -------- | ----- | -------- | ----- | ---------- | ----------- | ---------- | --- | ---------- |
| • DR-BM25: |              | Here, we | use the | original | BM25  |          |       |            |             |            |     |            |
|            |              |          |         |          |       | a        | dense | retriever, | but use     | scoring    | and | inference  |
| scores     | for labeling | positive | and     | negative | exam- |          |       |            |             |            |     |            |
|            |              |          |         |          |       | LMs.     | For   | our        | scoring LM, | gˆ, we     | use | GPT-NEO    |
plesandtrainingadenseretriever.
(Blacketal.,2021),a2.7B-parameterLMtrained
• CASE-BASED REASONING (CBR): We adapt onThePile(Gaoetal.,2021),an825GBEnglish
the scoring function from Das et al. (2021), textcorpus,constructedfromawiderangeofhigh-
| whichfocusedonknowledge-basequestionan- |     |     |     |     |     | qualityresources. |     |     |     |     |     |     |
| --------------------------------------- | --- | --- | --- | --- | --- | ----------------- | --- | --- | --- | --- | --- | --- |
swering. Theydefinetheweightforapairoflog- In addition, we consider the following infer-
icalformstobetheF scorebetweenthetwosets ence LMs: (a) GPT-J (Wang and Komatsuzaki,
1
|          |     |              |       |            |        | 2021): | a   | 6B-parameter |     | LM, also    | trained | on The     |
| -------- | --- | ------------ | ----- | ---------- | ------ | ------ | --- | ------------ | --- | ----------- | ------- | ---------- |
| 4Results | for | k ∈ {1,5,10} | and L | ∈ {50,100} | are in |        |     |              |     |             |         |            |
|          |     |              |       |            |        | Pile.  | The | advantage    | in  | this setup, | is      | that GPT-J |
AppendixA.

|          | Model      |     | BREAK | MTOP |     | SMCALFLOW |       |          | Model         |         | BREAK | MTOP   |         |
| -------- | ---------- | --- | ----- | ---- | --- | --------- | ----- | -------- | ------------- | ------- | ----- | ------ | ------- |
|          | RANDOM     |     | 1.7   | 7.3  |     | 8.9       |       | Unsuper. | BM25          |         | 17.6  | 49.0   |         |
| Unsuper. | SBERT      |     | 21.6  | 48.7 |     | 43.6      |       |          |               |         |       |        |         |
|          |            |     |       |      |     |           |       |          | CBR           |         | 18.4  | 57.5   |         |
|          | BM25       |     | 26.0  | 52.9 |     | 46.1      |       | Super.   |               |         | 23.9  | 64.4   |         |
|          | BRUTEFORCE |     | 7.7   | 18.1 |     | 11.1      |       |          | EPR(ours)     |         |       |        |         |
|          | DR-BM25    |     | 23.6  | 50.2 |     | 43.1      |       |          |               |         |       |        |         |
|          |            |     |       |      |     |           | Table | 3: Test  | results where | GPT-NEO |       | is the | scoring |
| Super.   | CBR        |     | 25.7  | 57.0 |     | 51.4      |       |          |               |         |       |        |         |
EPR(ours) 31.9 64.2 54.3 andinferenceLM.NumbersforBREAKareNEM,the
|     | BM25-ORACLE |     | 32.3 | 58.9 |     | 47.3 | officialmetric,andforMTOPareEM. |     |     |     |     |     |     |
| --- | ----------- | --- | ---- | ---- | --- | ---- | ------------------------------- | --- | --- | --- | --- | --- | --- |
Oracle
|                                             | LM-ORACLE   |     | 43.1    | 71.6 |         | 73.7   |     |        |     |     |          |              |     |
| ------------------------------------------- | ----------- | --- | ------- | ---- | ------- | ------ | --- | ------ | --- | --- | -------- | ------------ | --- |
|                                             |             |     |         |      |         |        |     | Model  |     |     | One-shot | Full-context |     |
| Table 2:                                    | Development |     | results | when | GPT-NEO | is the |     |        |     |     |          |              |     |
| scoringandinferenceLM.NumbersforBREAKareLF- |             |     |         |      |         |        |     | RANDOM |     |     | 1.1      | 1.7          |     |
Unsuper.
|     |     |     |     |     |     |     |     | BM25 |     |     | 15.2 | 26.0 |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ---- | --- | --- | ---- | ---- | --- |
EM,andforMTOPandSMCALFLOWareEM.
|     |     |     |     |     |     |     |        | DR-BM25 |     |     | 14.1 | 23.6 |     |
| --- | --- | --- | --- | --- | --- | --- | ------ | ------- | --- | --- | ---- | ---- | --- |
|     |     |     |     |     |     |     | Super. | CBR     |     |     | 14.5 | 25.7 |     |
|     |     |     |     |     |     |     |        | EPR     |     |     | 23.0 | 31.9 |     |
wastrainedonthesamecorpusas GPT-NEO. (b) BM25-ORACLE 18.0 32.3
|       |        |         |        |     |                |     | Oracle | LM-ORACLE         |     |     | 33.3 | 43.1 |     |
| ----- | ------ | ------- | ------ | --- | -------------- | --- | ------ | ----------------- | --- | --- | ---- | ---- | --- |
| GPT-3 | (Brown | et al., | 2020): | A   | 175B-parameter |     |        |                   |     |     |      |      |     |
|       |        |         |        |     |                |     |        | ANYCORRECT-ORACLE |     |     | 53.6 | -    |     |
model,trainedmostlyonafilteredsubsetofcom-
mon crawl. (c) CODEX (Chen et al., 2021): A Table 4: Development results on BREAK with GPT-
|     |     |     |     |     |     |     | NEO | in the | one-shot setting. |     | Numbers | are | LF-EM. |
| --- | --- | --- | --- | --- | --- | --- | --- | ------ | ----------------- | --- | ------- | --- | ------ |
GPT-3175B-parametermodelfinedtunedoncode
|              |     |       |     |               |     |         | Full-context |     | is the corresponding |     | numbers |     | from Ta- |
| ------------ | --- | ----- | --- | ------------- | --- | ------- | ------------ | --- | -------------------- | --- | ------- | --- | -------- |
| from GitHub. |     | Since | our | tasks involve |     | mapping |              |     |                      |     |         |     |          |
ble2.
fromutterancestoprogramsormeaningrepresen-
tations,CODEXmightpotentiallyperformwellat
in-contextlearning. 51.4 to 54.3 on SMCALFLOW. This shows that
ForallLMs,weuseamaximumcontextsizeof usingtheLMitselftolabelexamplesisaneffective
C =2,048tokens.
|            |     |           |     |     |          |         | approach | for     | obtaining    | a strong | prompt   |     | retriever. |
| ---------- | --- | --------- | --- | --- | -------- | ------- | -------- | ------- | ------------ | -------- | -------- | --- | ---------- |
|            |     |           |     |     |          |         | Table    | 3 shows | test results |          | on BREAK | and | MTOP       |
| Evaluation |     | On BREAK, |     | we  | evaluate | perfor- |          |         |              |          |          |     |            |
corroboratingthatEPRsubstantiallyimprovesper-
manceonthedevelopmentsetwithLF-EM(Has-
formancecomparedtoBM25andCBR.
| son and | Berant, | 2021), | which | is  | a better | metric |     |     |              |          |     |            |     |
| ------- | ------- | ------ | ----- | --- | -------- | ------ | --- | --- | ------------ | -------- | --- | ---------- | --- |
|         |         |        |       |     |          |        | For | the | unsupervised | methods, |     | the RANDOM |     |
comparedtoNormalizedExactMatch(NEM),the
officialmetric,asitmeasureswhethertwomean- baseline shows that random sampling of training
|                                              |      |        |      |         |     |         | examplesleadstopoorperformance. |       |     |        |            | BM25 | out-     |
| -------------------------------------------- | ---- | ------ | ---- | ------- | --- | ------- | ------------------------------- | ----- | --- | ------ | ---------- | ---- | -------- |
| ingrepresentationsaresemanticallyequivalent. |      |        |      |         |     | On      |                                 |       |     |        |            |      |          |
|                                              |      |        |      |         |     |         | performs                        | SBERT | for | prompt | retrieval, |      | and con- |
| the test                                     | set, | we use | NEM. | On MTOP |     | and SM- |                                 |       |     |        |            |      |          |
CALFLOW,weevaluatewithExactMatch(EM), sequently we use BM25 in all of our supervised
approachestoretrievethesetofcandidates,E¯.
| i.e.,whetherthestringoutputbytheinferenceLM |     |     |     |     |     |     |                                  |     |     |     |     |     | Last, |
| ------------------------------------------- | --- | --- | --- | --- | --- | --- | -------------------------------- | --- | --- | --- | --- | --- | ----- |
|                                             |     |     |     |     |     |     | BRUTEFORCEperformsworsethanBM25. |     |     |     |     |     | Weas- |
isidenticaltothereferencestring.
sumethisissincethetrainingsetsarelarge(∼14-
| WeevaluateEPRintwosettings: |     |     |     |     | (a)LM-as-a- |     |     |     |     |     |     |     |     |
| --------------------------- | --- | --- | --- | --- | ----------- | --- | --- | --- | --- | --- | --- | --- | --- |
service, and (b) LM-as-a-proxy. In the first set- 120Kexamples),andsampling200examplesdoes
|          |     |         |     |      |             |     | notcoverexamplesthatareusefulfor |     |     |     |     | GPT-NEO. |     |
| -------- | --- | ------- | --- | ---- | ----------- | --- | -------------------------------- | --- | --- | --- | --- | -------- | --- |
| ting, we | use | GPT-NEO | as  | both | the scoring | LM  |                                  |     |     |     |     |          |     |
Interestingly,EPRoutperformsBM25-ORACLE
andinferenceLM.Inthissetting,weevaluateon
thefulldevelopmentsetsof BREAK, MTOP,and onMTOPandSMCALFLOWandiscomparableon
SMCALFLOW. Inthelattersetting,asweaccess BREAK. ThisissurprisingsinceBM25-ORACLE
|                                       |     |     |     |     |     |     | hasaccesstotheoutputsequencey |     |     |     |     | attesttime, |     |
| ------------------------------------- | --- | --- | --- | --- | --- | --- | ----------------------------- | --- | --- | --- | --- | ----------- | --- |
| GPT-3andCODEXthroughapaidAPI,wesample |     |     |     |     |     |     |                               |     |     |     |     | test        |     |
illustratingthatthesignalprovidedbythescoring
| a random | subset | of  | 1,000 | development |     | examples |     |     |     |     |     |     |     |
| -------- | ------ | --- | ----- | ----------- | --- | -------- | --- | --- | --- | --- | --- | --- | --- |
fromeachdatasetandevaluateeachmodelonceon LMfortraininggoesbeyondsurfacetextsimilarity.
| thissubset. |     |     |     |     |     |     | TheperformanceofLM-ORACLEissubstantially |     |     |     |     |     |     |
| ----------- | --- | --- | --- | --- | --- | --- | ---------------------------------------- | --- | --- | --- | --- | --- | --- |
higherthanEPR,showingthatthesupervisionpro-
4.4 Results
videdbythescoringLMisstrong,andtraininga
LM-as-a-service Table 2 reports results where better retriever from this signal can substantially
enhanceperformance.
| the scoring |     | and inference |     | LMs | are | identical. |     |     |     |     |     |     |     |
| ----------- | --- | ------------- | --- | --- | --- | ---------- | --- | --- | --- | --- | --- | --- | --- |
EPRsubstantiallyoutperformsallotherbaselines. Wefurtherevaluateourmodelsintheone-shot
Specifically,whencomparingtothebestbaseline, setup,i.e.,whenthepromptgiventotheinference
it improves performance from 26.0 to 31.9 on LMincludesthehighestscoringexampleonly. In
BREAK, from 57.0 to 64.2 on MTOP, and from thissetup,theinferenceLMisappliedinthesame

|     | BREAK |     |     | MTOP |     |     |     | SMCALFLOW |     |     |
| --- | ----- | --- | --- | ---- | --- | --- | --- | --------- | --- | --- |
Method RANDOM BM25 CBR EPR RANDOM BM25 CBR EPR RANDOM BM25 CBR EPR
GPT-3 4.2 20.1 21.3 25.3 7.6 52.5 54.8 62.6 5.8 35.3 41.6 46.5
CODEX 8.9 24.5 24.2 29.5 10.8 60.6 59.4 66.1 7.2 45.1 48.7 50.3
GPT-J 3.3 26.7 26.7 31.5 8.8 56.6 58.0 65.4 10.6 50.4 50.9 57.4
GPT-NEO 1.0 22.8 25.8 29.9 7.6 52.8 55.4 63.6 8.0 46.1 50.1 53.5
Table 5: Results on a random sample of 1,000 examples from the development set when using GPT-Neo as a
scoringLMacrossdifferentinferenceLMsanddatasets.
|         |           |                                | EPR |     |     |     | CBR |     |     |     |
| ------- | --------- | ------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- |
| Test    | Utterance | Givethecodeoftheairportwiththe |     |     |     |     |     |     |     |     |
| Example |           | leastflights.                  |     |     |     |     |     |     |     |     |
Meaning
1) airports
|     | Representation | 2) flights                    | of #1     |        |                                   |     |     |     |     |     |
| --- | -------------- | ----------------------------- | --------- | ------ | --------------------------------- | --- | --- | --- | --- | --- |
|     |                | 3) number                     | of #2 for | each   | #1                                |     |     |     |     |     |
|     |                | 4) #1 where                   | #3 is     | lowest |                                   |     |     |     |     |     |
|     |                | 5) code                       | of #4     |        |                                   |     |     |     |     |     |
|     | Utterance      | Whatisthecodeofthecitywiththe |           |        | Whatdestinationhasthefewestnumber |     |     |     |     |     |
Top-1
|     |     | moststudents? |     |     | offlights? |     |     |     |     |     |
| --- | --- | ------------- | --- | --- | ---------- | --- | --- | --- | --- | --- |
Meaning
|     | Representation | 1) cities                        |           |         | 1) destinations                  |       |       |           |     |     |
| --- | -------------- | -------------------------------- | --------- | ------- | -------------------------------- | ----- | ----- | --------- | --- | --- |
|     |                | 2) students                      | in #1     |         | 2) flights                       |       | of #1 |           |     |     |
|     |                | 3) number                        | of #2 for | each    | #1 3) number                     |       | of #2 | for each  | #1  |     |
|     |                | 4) #1 where                      | #3 is     | highest | 4) #1                            | where | #3    | is lowest |     |     |
|     |                | 5) code                          | of #4     |         |                                  |       |       |           |     |     |
|     | Utterance      | Returnthecodeofthecitythathasthe |           |         | Whichdestinationhasleastnumberof |       |       |           |     |     |
Top-2
|     |         | moststudents. |     |     | flights?        |     |     |     |     |     |
| --- | ------- | ------------- | --- | --- | --------------- | --- | --- | --- | --- | --- |
|     | Meaning | 1) cities     |     |     | 1) destinations |     |     |     |     |     |
Representation
|     |           | 2) students                    | in #1     |         | 2) flights                   |       | to #1 |           |     |     |
| --- | --------- | ------------------------------ | --------- | ------- | ---------------------------- | ----- | ----- | --------- | --- | --- |
|     |           | 3) number                      | of #2 for | each    | #1 3) number                 |       | of #2 | for each  | #1  |     |
|     |           | 4) #1 where                    | #3 is     | highest | 4) #1                        | where | #3    | is lowest |     |     |
|     |           | 5) code                        | of #4     |         |                              |       |       |           |     |     |
|     | Utterance | Findthecountandcodeofthejobhas |           |         | Whatisthenumberofairportsper |       |       |           |     |     |
Top-3
|     |     | mostemployees. |     |     | country,orderedfrommosttoleast? |     |     |     |     |     |
| --- | --- | -------------- | --- | --- | ------------------------------- | --- | --- | --- | --- | --- |
Meaning
|     |     | 1) jobs |     |     | 1) countries |     |     |     |     |     |
| --- | --- | ------- | --- | --- | ------------ | --- | --- | --- | --- | --- |
Representation
|     |     | 2) employees | of #1     |         | 2) airports  |        | in    | #1       |          |     |
| --- | --- | ------------ | --------- | ------- | ------------ | ------ | ----- | -------- | -------- | --- |
|     |     | 3) number    | of #2 for | each    | #1 3) number |        | of #2 | for each | #1       |     |
|     |     | 4) #1 where  | #3 is     | highest | 4) #3        | sorted | by    | most     | to least |     |
|     |     | 5) employees | of #4     |         |              |        |       |          |          |     |
|     |     | 6) number    | of #5     |         |              |        |       |          |          |     |
|     |     | 7) code      | of #4     |         |              |        |       |          |          |     |
8) #6 , #7
Table 6: An example from BREAK development set where EPR is correct and CBR is incorrect along with the
top-3trainingexamplesretrievedfromeachretriever.
setting as when we generate labeled data, where LM-as-a-proxy Table5showsresultswhenthe
wegoovereachpromptcandidateindependently. scoringLMisGPT-NEOandtheinferenceLMisa
Sincetrainandtesttimearenowcloser,wecanex- largerLM.First,thetrendsaresimilartotheLM-as-
pecttheadvantageofEPRtobemorepronounced. a-servicesetup,i.e.,EPRsubstantiallyoutperforms
|     |     |     |     | prior | baselines, | including |     | our | best unsupervised |     |
| --- | --- | --- | --- | ----- | ---------- | --------- | --- | --- | ----------------- | --- |
baseline,BM25,andthebestsupervisedbaseline,
|               |              |         |          | CBR, | by 2-8 | points | on  | all datasets | and | all pre- |
| ------------- | ------------ | ------- | -------- | ---- | ------ | ------ | --- | ------------ | --- | -------- |
| Table 4 shows | the results. | Indeed, | EPR out- |      |        |        |     |              |     |          |
performs the best baseline by 8.5%, and BM25- trainedmodels. Thus, GPT-NEOservesasagood
ORACLE by 5%. In addition, we examine proxyforchoosingtrainingexamples.
ANYCORRECT-ORACLE,whichtestswhetherany Tofurthervalidatethisfinding,weevaluatethe
of the candidates returned by BM25 leads to the performanceofGPT-Jon BREAKwith GPT-NEO
correct output. ANYCORRECT-ORACLE reaches as the scoring LM compared to using GPT-J it-
53.6%,20pointsaboveLM-ORACLE. Thisshows self as the scoring LM. We find performance im-
thehighqualityofcandidatesprovidedbyBM25 proves slightly from 31.5 to 33.6. Analogously,
(appliedonthey),asonecanreachmorethan50% when using CODEX as the scoring LM and infer-
LF-EM with just a single prompt. Moreover, it enceLMperformanceremainsroughlythesame:
hintsthatabetterscoringfunctioncanpotentially 29.5→29.3. Thus,usingasmallerLM(GPT-NEO)
furtherimproveperformance. isaneffectivestrategyfortrainingaretrieverthat

8.0
2.0
0.5
0.125
0.0 0.2 0.4 0.6 0.8 1.0
Distance
Figure3: At-SNEprojectionandclusteringoftherep-
resentationslearnedbyEPRforthetrainingexamples
inBREAK.Aninteractiveversiondisplayingindividual
examplesisavailablehere.
willbeappliedonotherLMs. Zoominginondif-
ferentinferenceLMs,GPT-Jperformsslightlybet-
ter than GPT-NEO across the board, since it was
trained on the same data and using the same pro-
cedure as GPT-NEO. CODEX outperforms GPT-
3, which can be explained by the fact that it was
trained on code, and our datasets involve map-
pingtoprogramsormeaningrepresentations. Sur-
prisingly,GPT-J outperformsCODEX(excepton
MTOP)andGPT-3despitebeing30xsmaller. This
can perhaps be explained by the fact that GPT-J
was trained on a different dataset (The Pile (Gao
etal.,2021)).
Copied Novel Total
Pattern
Acc Rate Acc Rate Acc
Exact 55.1% 10.4% 29.7% 89.6%
BREAK
Abstract 58.0% 41.1% 14.5% 58.9%
32.3%
Exact 77.3% 25.3% 59.7% 74.7%
MTOP
Abstract 71.6% 84.5% 23.4% 15.5%
64.2%
Exact 62.5% 60.2% 42.4% 39.8% SMCAL
Abstract 62.4% 81.2% 20.6% 18.8%
54.5%
Table 7: Accuracy comparison between the decoded
instances that contained patterns from the prompt and
novelinstancesthosethatdon’t. Resultsshownareon
theLM-as-a-servicesetupusingGPT-NEO.
Analysis Table6showsanexamplefromBREAK
whereEPRdecodesthecorrectoutput,whileCBR
doesnot. AlltrainingexamplesretrievedbyEPR
perform an argmax (argmin in the original utter-
ance),andreturninthefinalstep“acode”,while
thethirdexampleretrievedbyCBRdoesnotper-
formanargmaxorargmin,anddonotinvolve“a
code”. WeprovideadditionalexamplesinApp.A.
Figure 3 shows a t-SNE (Hinton and Roweis,
2002)projectionoftheembeddingslearnedbyEPR
for the training examples of BREAK, with a link
%
Exact
Abstract
Figure4: Onthesubsetofcopiedpatternsweplotthe
distributionofthedistancefromthetestinstancetothe
examplecontainingthepattern. ShownontheBREAK
validation set using EPR in the LM-as-a-service setup
usingGPT-NEO. Notethatthey-axisisinlog-scale.
to an interactive version, where we applied the
OPTICS(Ankerstetal.,1999;SchubertandGertz,
2018) clustering algorithm. Examining clusters
showsthatEPRcapturesbothlexicalandstructure
similarity. Examplesforclustersarealsoavailable
inApp.A.
Prompt copying We analyze how the LM uti-
lizesin-contextprompts. Specifically,isthetarget
output copied from one of the prompts or is it a
compositionofdifferentpromptfragments,which
resultingeneralizationtonewstructures.
To achieve this, we define two types of copy-
ing. (a) Exact copying measures if the generated
outputexactlymatchesoneoftheexamplesinthe
prompt, and (b) Abstract copying, that quantifies
ifthestructureofthedecodedoutputmatchesany
ofthestructuresseenintheprompt. Specifically,
weeliminatetheeffectofnon-structuralelements
such as entities and function arguments. We re-
placeeverysequenceofwordsinthelogicalform
thatappearsintheinpututterancewiththestring
[MASKED] for both the target utterance and in-
contextexamples. Ifthemaskedlogicalformthat
theLMdecodedappearsinthesetofmaskedex-
amplesdefinedbytheprompt,wesaythattheLM
copiedthatabstractpattern.
Table 7 presents the results on the validation
set for each of our three datasets, as well as the
accuracy on each subset. We observe that the
rateofcopyingismuchhigherin MTOPandSM-
CALFLOWcomparedtoBREAK,whereinMTOP
and SMCALFLOW abstractcopyingreachesmore
than80%. Moreover,accuracyonexampleswhere
copyingoccurredismuchhighercomparedtoac-
curacy where no copying happened. For exam-

ple, on MTOP, 84.5% of the examples were ab- Borgeaudetal.,2021;Alonetal.,2022)andma-
stractly copied, and on that subset of examples, chinetranslation(Khandelwaletal.,2021).
EPRachieves71.6%EM,comparedto64.2%on
|                         |     |     |                         |     |     |     | Prompts  | Developing |            | methods |     | for interacting |     |
| ----------------------- | --- | --- | ----------------------- | --- | --- | --- | -------- | ---------- | ---------- | ------- | --- | --------------- | --- |
| theentirevalidationset. |     |     | Nevertheless,eventhough |     |     |     |          |            |            |         |     |                 |     |
|                         |     |     |                         |     |     |     | with LMs | and        | extracting | desired |     | behaviours      | has |
accuracyismuchlowerincaseswherenocopying
attractedconsiderableattention,undertheumbrella
occurred,accuracyisnotnegligible,whichshows
|     |     |     |     |     |     |     | termprompting. |     | Inthiswork,promptsareasetof |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | -------------- | --- | --------------------------- | --- | --- | --- | --- |
thatsomeformofgeneralizationtonewstructures
in-contexttrainingexamples,butsubstantialeffort
istakingplace.
hasalsobeendevotedtocastingnaturallanguage
Anotherfollow-upquestioniswhetherthemodel
|     |     |     |     |     |     |     | tasks as | language | modeling |     | by phrasing |     | the tar- |
| --- | --- | --- | --- | --- | --- | --- | -------- | -------- | -------- | --- | ----------- | --- | -------- |
copiespatternsfrompromptsuniformlyordoesit
|     |     |     |     |     |     |     | get task | in natural | language |     | (see | survey | in (Liu |
| --- | --- | --- | --- | --- | --- | --- | -------- | ---------- | -------- | --- | ---- | ------ | ------- |
attendmostlytotheoneswithhighretrievalscore.
|           |       |         |     |            |     |       | et al., 2021b)). |     | Such | approaches | include |     | prompt |
| --------- | ----- | ------- | --- | ---------- | --- | ----- | ---------------- | --- | ---- | ---------- | ------- | --- | ------ |
| To answer | this, | we look | at  | the subset | of  | exam- |                  |     |      |            |         |     |        |
engineeringthroughmanualpatterns(Petronietal.,
| pleswherecopyingoccurred. |     |     |     | Wethenidentifyfor |     |     |     |     |     |     |     |     |     |
| ------------------------- | --- | --- | --- | ----------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
2019;SchickandSchütze,2021),decodingmeth-
eachexamplethehighest-rankingpromptthatwas
ods(Minetal.,2021;Zhaoetal.,2021;Holtzman
copiedfrom,anddefinethedistanceofthatprompt
etal.,2021),andmethodsforextractingeitherhard
bydividingtherankbythenumberofpromptsthat
(Shinetal.,2020;Havivetal.,2021)orsoft(Liand
| fitinthatexample.   |     | Figure4showsthedistribution |     |     |           |     |        |             |     |               |     |     |         |
| ------------------- | --- | --------------------------- | --- | --- | --------- | --- | ------ | ----------- | --- | ------------- | --- | --- | ------- |
|                     |     |                             |     |     |           |     | Liang, | 2021; Zhong |     | et al., 2021; | Qin | and | Eisner, |
| overdistancesforthe |     | BREAKdataset.               |     |     | Weobserve |     |        |             |     |               |     |     |         |
2021)promptsautomatically.
| that copying | happens |     | mostly | from | highly-ranked |     |     |     |     |     |     |     |     |
| ------------ | ------- | --- | ------ | ---- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- |
prompts.
|     |     |     |     |     |     |     | Promptretrievalforsupervisedmodels |     |     |     |     |     | Inpar- |
| --- | --- | --- | --- | --- | --- | --- | ---------------------------------- | --- | --- | --- | --- | --- | ------ |
alleltothiswork,addingtrainingexamplesasaddi-
| 5 RelatedWork |     |     |     |     |     |     | tionalinputhasbeenshowntobeusefulforsuper- |     |     |                      |     |     |     |
| ------------- | --- | --- | --- | --- | --- | --- | ------------------------------------------ | --- | --- | -------------------- | --- | --- | --- |
|               |     |     |     |     |     |     | visedmodelsaswell.                         |     |     | Wangetal.(2022)andXu |     |     |     |
In-context learning Our understanding of in- etal.(2021)usedBM25toretrieveandaugmentthe
contextlearninghasgrownsubstantiallyrecently.
inputwithsimilarexamplesfromthetrainingset.
Saunshietal.(2021)suggeststhatbyconditioning
|     |     |     |     |     |     |     | Fine-tuning | the | model | with | the additional |     | inputs |
| --- | --- | --- | --- | --- | --- | --- | ----------- | --- | ----- | ---- | -------------- | --- | ------ |
onaprompt,thetaskofpredictingthenextword
improvedperformanceontaskssuchassummariza-
approaches linear separability. Xie et al. (2021) tion and question answering. Such methods can
suggeststhatin-contextlearningoccurswhenthe
alsopotentiallybenefitfromastrongerretriever.
| model infers   |              | a shared | latent        | concept | between   | ex-     |               |     |     |     |     |     |     |
| -------------- | ------------ | -------- | ------------- | ------- | --------- | ------- | ------------- | --- | --- | --- | --- | --- | --- |
| amples         | in a prompt. | Levine   |               | et al.  | (2021)    | present | 6 Conclusions |     |     |     |     |     |     |
| a pre-training |              | scheme   | theoretically |         | motivated | by      |               |     |     |     |     |     |     |
Largepre-trainedLMsarebecominganinsepara-
| the bias | of in-context |     | learning, | that | gives | signif- |     |     |     |     |     |     |     |
| -------- | ------------- | --- | --------- | ---- | ----- | ------- | --- | --- | --- | --- | --- | --- | --- |
blepartofthenaturallanguageunderstandingeco-
| icant improvements. |     |     | Recently, | Min | et al. | (2022) |         |                                       |     |     |     |     |     |
| ------------------- | --- | --- | --------- | --- | ------ | ------ | ------- | ------------------------------------- | --- | --- | --- | --- | --- |
|                     |     |     |           |     |        |        | system. | However,accessingtheirweightsorupdat- |     |     |     |     |     |
showedthatthemodeldoesnotrelyontheground
ingthemcanbeprohibitiveformanyresearchers.
truthinput-labelmappingprovidedinthedemon-
Inthiswork,weproposeEPR,amethodforlearn-
strationsasmuchaspreviouslythought.
ingtoretrievegoodpromptsforin-contextlearning,
byusinglanguagemodelsthemselvesasthescor-
| Retrieval       | Researchontrainingdenseretrievers |           |           |     |             |     |              |                                  |     |     |     |     |     |
| --------------- | --------------------------------- | --------- | --------- | --- | ----------- | --- | ------------ | -------------------------------- | --- | --- | --- | --- | --- |
|                 |                                   |           |           |     |             |     | ingfunction. | Thisallowsustotrainalight-weight |     |     |     |     |     |
| has skyrocketed |                                   | recently, | propelled |     | by interest |     |              |                                  |     |     |     |     |     |
in open-domain question answering (Chen et al., retrieverandsubstantiallyimproveperformanceon
threechallengingtasks.
2017;Leeetal.,2019;Karpukhinetal.,2020;Guu
Morebroadly,giventhatlargeLMsmodelsare
etal.,2020;KhattabandZaharia,2020;Quetal.,
|     |     |     |     |     |     |     | likely to | play a | prominent | role | in  | developing | lan- |
| --- | --- | --- | --- | --- | --- | --- | --------- | ------ | --------- | ---- | --- | ---------- | ---- |
2021). Workonretrieval-basedmethodshasalso
spreadmorewidelytootherknowledge-intensive guageunderstandingmodels,itisimportanttode-
velopapproachesforinteractingwithsuchmodels
| tasks (Lewis |     | et al., 2020), |     | e.g., fact | verification |     |              |     |     |           |     |        |         |
| ------------ | --- | -------------- | --- | ---------- | ------------ | --- | ------------ | --- | --- | --------- | --- | ------ | ------- |
|              |     |                |     |            |              |     | effectively. | EPR | can | be viewed | as  | a step | in this |
(Samarinasetal.,2021).
direction.
Similartous,Pasupatetal.(2021)proposedto
| useretrievalinsemanticparsing. |     |     |     | However,theyfo- |     |     |     |     |     |     |     |     |     |
| ------------------------------ | --- | --- | --- | --------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Acknowledgement
cusoncontrollingtheoutputgeneratedbyamodel.
Retrievalmethodshavealsobeensuccessfullyused WethankOriRamandItayItzhakforhelpfulsug-
in language modeling (Khandelwal et al., 2020; gestionsandmeaningfuldiscussions. Thisresearch

wassupportedinpartbyTheYandexInitiativefor Aditya Ramesh, Daniel M. Ziegler, Jeffrey Wu,
Machine Learning, and The European Research Clemens Winter, Christopher Hesse, Mark Chen,
|                         |          |       |                |                 |           |       | Eric Sigler, | Mateusz |                                 | Litwin,     | Scott      | Gray, | Benjamin  |
| ----------------------- | -------- | ----- | -------------- | --------------- | --------- | ----- | ------------ | ------- | ------------------------------- | ----------- | ---------- | ----- | --------- |
| Council                 | (ERC)    | under | the European   |                 | Union     | Hori- |              |         |                                 |             |            |       |           |
|                         |          |       |                |                 |           |       | Chess,       | Jack    | Clark,                          | Christopher | Berner,    |       | Sam Mc-   |
| zons 2020               | research |       | and innovation |                 | programme |       |              |         |                                 |             |            |       |           |
|                         |          |       |                |                 |           |       | Candlish,    | Alec    | Radford,                        | Ilya        | Sutskever, |       | and Dario |
| (grantERCDELPHI802800). |          |       |                | Thisworkwascom- |           |       |              |         |                                 |             |            |       |           |
|                         |          |       |                |                 |           |       | Amodei.2020. |         | Languagemodelsarefew-shotlearn- |             |            |       |           |
pletedinpartialfulfillmentforthePh.Ddegreeof ers. InAdvancesinNeuralInformationProcessing
|     |     |     |     |     |     |     | Systems33: |     | AnnualConferenceonNeuralInforma- |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ---------- | --- | -------------------------------- | --- | --- | --- | --- |
OhadRubin.
|     |     |     |     |     |     |     | tion Processing |     | Systems | 2020, | NeurIPS |     | 2020, De- |
| --- | --- | --- | --- | --- | --- | --- | --------------- | --- | ------- | ----- | ------- | --- | --------- |
cember6-12,2020,virtual.
References
|           |       |     |             |     |             |      | DanqiChen, | AdamFisch, |         | JasonWeston, |     | andAntoine |       |
| --------- | ----- | --- | ----------- | --- | ----------- | ---- | ---------- | ---------- | ------- | ------------ | --- | ---------- | ----- |
|           |       |     |             |     |             |      | Bordes.    | 2017.      | Reading | Wikipedia    |     | to answer  | open- |
| Uri Alon, | Frank | F.  | Xu, Junxian |     | He, Sudipta | Sen- |            |            |         |              |     |            |       |
gupta,DanRoth,andGrahamNeubig.2022. Neuro- domain questions. In Proceedings of the 55th An-
|                     |          |     |                       |     |      |            | nual Meeting |         | of the | Association | for      | Computational |       |
| ------------------- | -------- | --- | --------------------- | --- | ---- | ---------- | ------------ | ------- | ------ | ----------- | -------- | ------------- | ----- |
| symbolic            | language |     | modeling              |     | with | automaton- |              |         |        |             |          |               |       |
|                     |          |     |                       |     |      |            | Linguistics  | (Volume |        | 1: Long     | Papers), | pages         | 1870– |
| augmentedretrieval. |          |     | ArXiv,abs/2201.12431. |     |      |            |              |         |        |             |          |               |       |
1879,Vancouver,Canada.AssociationforComputa-
tionalLinguistics.
| Jacob Andreas, |      | John      | Bufe, | David     | Burkett, | Charles    |     |     |     |     |     |     |     |
| -------------- | ---- | --------- | ----- | --------- | -------- | ---------- | --- | --- | --- | --- | --- | --- | --- |
| Chen,          | Josh | Clausman, | Jean  | Crawford, |          | Kate Crim, |     |     |     |     |     |     |     |
Jordan DeLoach, Leah Dorner, Jason Eisner, Hao MarkChen,JerryTworek,HeewooJun,QimingYuan,
Fang, Alan Guo, David Hall, Kristin Hayes, Kellie Henrique Ponde, Jared Kaplan, Harrison Edwards,
Hill, Diana Ho, Wendy Iwaszuk, Smriti Jha, Dan YuraBurda,NicholasJoseph,GregBrockman,Alex
Klein, Jayant Krishnamurthy, Theo Lanman, Percy Ray, Raul Puri, Gretchen Krueger, Michael Petrov,
Liang,ChristopherH.Lin,IlyaLintsbakh,AndyMc- Heidy Khlaaf, Girish Sastry, Pamela Mishkin,
Govern,AleksandrNisnevich,AdamPauls,Dmitrij Brooke Chan, Scott Gray, Nick Ryder, Mikhail
Petters, Brent Read, Dan Roth, Subhro Roy, Jesse Pavlov, Alethea. Power, Lukasz Kaiser, Moham-
Rusak, Beth Short, Div Slomin, Ben Snyder, mad Bavarian, Clemens Winter, Philippe Tillet, Fe-
Stephon Striplin, Yu Su, Zachary Tellman, Sam lipe Petroski Such, David W. Cummings, Matthias
Thomson,AndreiVorobev,IzabelaWitoszko,Jason Plappert, Fotios Chantzis, Elizabeth Barnes, Ariel
Wolfe, Abby Wray, Yuchen Zhang, and Alexander Herbert-Voss, William H. Guss, Alex Nichol, Igor
Zotov. 2020. Task-oriented dialogue as dataflow Babuschkin, S. Arun Balaji, Shantanu Jain, An-
synthesis. TransactionsoftheAssociationforCom- drewCarr,JanLeike,JoshuaAchiam,VedantMisra,
putationalLinguistics,8:556–571. EvanMorikawa,AlecRadford,MatthewM.Knight,
|     |     |     |     |     |     |     | Miles | Brundage, | Mira | Murati, | Katie | Mayer, | Peter |
| --- | --- | --- | --- | --- | --- | --- | ----- | --------- | ---- | ------- | ----- | ------ | ----- |
Mihael Ankerst, Markus M. Breunig, Hans-Peter Welinder, Bob McGrew, Dario Amodei, Sam Mc-
Kriegel, and Jörg Sander. 1999. Optics: Ordering Candlish, Ilya Sutskever, and Wojciech Zaremba.
pointstoidentifytheclusteringstructure. SIGMOD 2021. Evaluatinglargelanguagemodelstrainedon
Rec.,28(2):49–60.
code. ArXivpreprint,abs/2107.03374.
Emily M. Bender, Timnit Gebru, Angelina McMillan- Rajarshi Das, Manzil Zaheer, Dung Thai, Ameya
| Major,                      | and | Shmargaret | Shmitchell. |                   | 2021. | On the |          |       |        |     |          |      |        |
| --------------------------- | --- | ---------- | ----------- | ----------------- | ----- | ------ | -------- | ----- | ------ | --- | -------- | ---- | ------ |
|                             |     |            |             |                   |       |        | Godbole, | Ethan | Perez, |     | Jay Yoon | Lee, | Lizhen |
| dangersofstochasticparrots: |     |            |             | Canlanguagemodels |       |        |          |       |        |     |          |      |        |
Tan,LazarosPolymenakos,andAndrewMcCallum.
| betoobig? |     | InProceedingsofthe2021ACMConfer- |     |     |     |     |       |            |     |           |     |         |          |
| --------- | --- | -------------------------------- | --- | --- | --- | --- | ----- | ---------- | --- | --------- | --- | ------- | -------- |
|           |     |                                  |     |     |     |     | 2021. | Case-based |     | reasoning | for | natural | language |
enceonFairness,Accountability,andTransparency,
|     |     |     |     |     |     |     | queries | over | knowledge | bases. | In  | Proceedings | of  |
| --- | --- | --- | --- | --- | --- | --- | ------- | ---- | --------- | ------ | --- | ----------- | --- |
FAccT’21,page610–623,NewYork,NY,USA.As- the2021ConferenceonEmpiricalMethodsinNatu-
sociationforComputingMachinery.
ralLanguageProcessing,pages9594–9611,Online
|            |     |      |            |        |     |            | and Punta | Cana, | Dominican |     | Republic. | Association |     |
| ---------- | --- | ---- | ---------- | ------ | --- | ---------- | --------- | ----- | --------- | --- | --------- | ----------- | --- |
| Sid Black, | Leo | Gao, | Phil Wang, | Connor |     | Leahy, and |           |       |           |     |           |             |     |
forComputationalLinguistics.
| Stella         | Biderman. | 2021.    |     | GPT-Neo: | Large | Scale |               |     |          |        |        |     |          |
| -------------- | --------- | -------- | --- | -------- | ----- | ----- | ------------- | --- | -------- | ------ | ------ | --- | -------- |
| Autoregressive |           | Language |     | Modeling | with  | Mesh- |               |     |          |        |        |     |          |
|                |           |          |     |          |       |       | Jacob Devlin, |     | Ming-Wei | Chang, | Kenton |     | Lee, and |
Tensorflow.
|           |           |     |        |         |        |       | Kristina           | Toutanova. |              | 2019. | BERT:  | Pre-training    | of     |
| --------- | --------- | --- | ------ | ------- | ------ | ----- | ------------------ | ---------- | ------------ | ----- | ------ | --------------- | ------ |
|           |           |     |        |         |        |       | deep bidirectional |            | transformers |       | for    | language        | under- |
| Sebastian | Borgeaud, |     | Arthur | Mensch, | Jordan | Hoff- |                    |            |              |       |        |                 |        |
|           |           |     |        |         |        |       | standing.          | In         | Proceedings  |       | of the | 2019 Conference |        |
mann,TrevorCai,ElizaRutherford,KatieMillican,
|        |     |                |     |               |     |          | of the | North | American | Chapter | of  | the Association |     |
| ------ | --- | -------------- | --- | ------------- | --- | -------- | ------ | ----- | -------- | ------- | --- | --------------- | --- |
| George | van | den Driessche, |     | Jean-Baptiste |     | Lespiau, |        |       |          |         |     |                 |     |
Bogdan Damoc, Aidan Clark, et al. 2021. Improv- for Computational Linguistics: Human Language
|              |     |        |               |     |      |              | Technologies, |     | Volume | 1 (Long | and | Short | Papers), |
| ------------ | --- | ------ | ------------- | --- | ---- | ------------ | ------------- | --- | ------ | ------- | --- | ----- | -------- |
| ing language |     | models | by retrieving |     | from | trillions of |               |     |        |         |     |       |          |
pages4171–4186,Minneapolis,Minnesota.Associ-
| tokens. | arXivpreprintarXiv:2112.04426. |     |     |     |     |     |     |     |     |     |     |     |     |
| ------- | ------------------------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
ationforComputationalLinguistics.
TomB.Brown,BenjaminMann,NickRyder,Melanie
Subbiah, Jared Kaplan, Prafulla Dhariwal, Arvind NanDu,YanpingHuang,AndrewM.Dai,DmitryLep-
Neelakantan,PranavShyam,GirishSastry,Amanda ikhin Simon Tong, Yuanzhong Xu, Maxim Krikun,
Askell, Sandhini Agarwal, Ariel Herbert-Voss, Yanqi Zhou, Adams Wei Yu, Orhan Firat, Bar-
Gretchen Krueger, Tom Henighan, Rewon Child, ret Zoph, Liam Fedus, Maarten Bosma, Zongwei

Zhou, Tao Wang, Yu Emma Wang, Kellie Web- Urvashi Khandelwal, Omer Levy, Dan Jurafsky, Luke
ster, Marie Pellat, Kevin Robinson, Kathy Meier- Zettlemoyer, and Mike Lewis. 2020. Generaliza-
Hellstern, Toju Duke, Lucas Dixon, Kun Zhang, tion through memorization: Nearest neighbor lan-
QuocVLe,YonghuiWu,ZhifengChen,andClaire guage models. In 8th International Conference on
Cui. 2021. GLaM: Efficient scaling of language LearningRepresentations,ICLR2020,AddisAbaba,
models with mixture-of-experts. arXiv preprint Ethiopia,April26-30,2020.OpenReview.net.
arXiv:2112.06905.
|          |        |           |     |        |          |       | Omar Khattab | and         | Matei   | Zaharia. | 2020.  | Colbert:        | Ef- |
| -------- | ------ | --------- | --- | ------ | -------- | ----- | ------------ | ----------- | ------- | -------- | ------ | --------------- | --- |
|          |        |           |     |        |          |       | ficient and  | effective   | passage |          | search | via contextual- |     |
| Leo Gao, | Stella | Biderman, | Sid | Black, | Laurence | Gold- |              |             |         |          |        |                 |     |
|          |        |           |     |        |          |       | ized late    | interaction | over    | bert.    | In     | Proceedings     | of  |
ing,TravisHoppe,CharlesFoster,JasonPhang,Ho-
|          |       |        |     |            |     |           | the 43rd | International |     | ACM | SIGIR | conference | on  |
| -------- | ----- | ------ | --- | ---------- | --- | --------- | -------- | ------------- | --- | --- | ----- | ---------- | --- |
| race He, | Anish | Thite, | Noa | Nabeshima, | et  | al. 2021. |          |               |     |     |       |            |     |
The pile: An 800gb dataset of diverse text for lan- research and development in Information Retrieval,
| guagemodeling. |              | ArXivpreprint,abs/2101.00027. |        |       |           |      | pages39–48.                      |        |     |       |           |               |         |
| -------------- | ------------ | ----------------------------- | ------ | ----- | --------- | ---- | -------------------------------- | ------ | --- | ----- | --------- | ------------- | ------- |
|                |              |                               |        |       |           |      | Diederik P                       | Kingma | and | Jimmy | Ba. 2015. |               | Adam: A |
| Kelvin Guu,    | Kenton       | Lee,                          | Zora   | Tung, | Panupong  | Pa-  |                                  |        |     |       |           |               |         |
|                |              |                               |        |       |           |      | methodforstochasticoptimization. |        |     |       |           | InProceedings |         |
| supat,         | and Ming-Wei |                               | Chang. | 2020. | Retrieval | aug- |                                  |        |     |       |           |               |         |
ofICLR.
| mentedlanguagemodelpre-training. |     |     |     |     | InICML. |     |     |     |     |     |     |     |     |
| -------------------------------- | --- | --- | --- | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
KentonLee,Ming-WeiChang,andKristinaToutanova.
| Matan Hasson                           |     | and Jonathan |     | Berant. | 2021. | Ques-  |              |          |            |            |                |     |        |
| -------------------------------------- | --- | ------------ | --- | ------- | ----- | ------ | ------------ | -------- | ---------- | ---------- | -------------- | --- | ------ |
|                                        |     |              |     |         |       |        | 2019. Latent |          | retrieval  | for weakly | supervised     |     | open   |
| tiondecompositionwithdependencygraphs. |     |              |     |         |       | ArXiv, |              |          |            |            |                |     |        |
|                                        |     |              |     |         |       |        | domain       | question | answering. |            | In Proceedings |     | of the |
abs/2104.08647.
|     |     |     |     |     |     |     | 57th Annual |              | Meeting | of the | Association |     | for Com-  |
| --- | --- | --- | --- | --- | --- | --- | ----------- | ------------ | ------- | ------ | ----------- | --- | --------- |
|     |     |     |     |     |     |     | putational  | Linguistics, |         | pages  | 6086–6096,  |     | Florence, |
Adi Haviv, Jonathan Berant, and Amir Globerson. Italy.AssociationforComputationalLinguistics.
| 2021. | BERTese: | Learning |     | to speak | to BERT. | In  |     |     |     |     |     |     |     |
| ----- | -------- | -------- | --- | -------- | -------- | --- | --- | --- | --- | --- | --- | --- | --- |
Proceedingsofthe16thConferenceoftheEuropean
|         |        |             |     |                   |     |      | Yoav Levine, | Noam  | Wies,   | Daniel    | Jannai, |          | Daniel I. |
| ------- | ------ | ----------- | --- | ----------------- | --- | ---- | ------------ | ----- | ------- | --------- | ------- | -------- | --------- |
| Chapter | of the | Association |     | for Computational |     | Lin- |              |       |         |           |         |          |           |
|         |        |             |     |                   |     |      | Navon,       | Yedid | Hoshen, | and Amnon |         | Shashua. | 2021.     |
guistics: Main Volume, pages 3618–3623, Online. The inductive bias of in-context learning: Re-
AssociationforComputationalLinguistics. thinking pretraining example design. ArXiv,
abs/2110.04541.
MatthewHenderson,RamiAl-Rfou,BrianStrope,Yun
|       |       |        |         |       |      |            | Patrick S. | H. Lewis, | Ethan | Perez, | Aleksandra |     | Pik- |
| ----- | ----- | ------ | ------- | ----- | ---- | ---------- | ---------- | --------- | ----- | ------ | ---------- | --- | ---- |
| hsuan | Sung, | Laszlo | Lukacs, | Ruiqi | Guo, | Sanjiv Ku- |            |           |       |        |            |     |      |
mar, Balint Miklos, and Ray Kurzweil. 2017. Effi- tus, Fabio Petroni, Vladimir Karpukhin, Naman
cientnaturallanguageresponsesuggestionforsmart Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih,
| reply.                               |     |     |         |     |     |          | Tim Rocktäschel,    |     | Sebastian           |        | Riedel, | and         | Douwe |
| ------------------------------------ | --- | --- | ------- | --- | --- | -------- | ------------------- | --- | ------------------- | ------ | ------- | ----------- | ----- |
|                                      |     |     |         |     |     |          | Kiela. 2020.        |     | Retrieval-augmented |        |         | generation  | for   |
|                                      |     |     |         |     |     |          | knowledge-intensive |     | NLP                 | tasks. | In      | Proceedings | of    |
| GeoffreyE.HintonandSamT.Roweis.2002. |     |     |         |     |     | Stochas- |                     |     |                     |        |         |             |       |
| ticneighborembedding.                |     |     | InNIPS. |     |     |          | NeurIPS.            |     |                     |        |         |             |       |
AriHoltzman,PeterWest,VeredShwartz,YejinChoi, Haoran Li, Abhinav Arora, Shuohui Chen, Anchit
|          |              |     |       |         |      |        | Gupta, | Sonal | Gupta, | and Yashar |     | Mehdad. | 2021. |
| -------- | ------------ | --- | ----- | ------- | ---- | ------ | ------ | ----- | ------ | ---------- | --- | ------- | ----- |
| and Luke | Zettlemoyer. |     | 2021. | Surface | form | compe- |        |       |        |            |     |         |       |
MTOP:Acomprehensivemultilingualtask-oriented
| tition:    | Why                              | the highest | probability |     | answer | isn’t al- |                           |     |        |          |                    |         |        |
| ---------- | -------------------------------- | ----------- | ----------- | --- | ------ | --------- | ------------------------- | --- | ------ | -------- | ------------------ | ------- | ------ |
|            |                                  |             |             |     |        |           | semanticparsingbenchmark. |     |        |          | InProceedingsofthe |         |        |
| waysright. | InProceedingsofthe2021Conference |             |             |     |        |           |                           |     |        |          |                    |         |        |
|            |                                  |             |             |     |        |           | 16th Conference           |     | of the | European |                    | Chapter | of the |
onEmpiricalMethodsinNaturalLanguageProcess-
ing, pages7038–7051, OnlineandPuntaCana, Do- Association for Computational Linguistics: Main
|         |           |             |     |     |                   |     | Volume, | pages | 2950–2962, | Online. |     | Association | for |
| ------- | --------- | ----------- | --- | --- | ----------------- | --- | ------- | ----- | ---------- | ------- | --- | ----------- | --- |
| minican | Republic. | Association |     |     | for Computational |     |         |       |            |         |     |             |     |
ComputationalLinguistics.
Linguistics.
|               |          |     |        |           |        |       | Xiang Lisa | Li and     | Percy | Liang.  | 2021. | Prefix-tuning: |     |
| ------------- | -------- | --- | ------ | --------- | ------ | ----- | ---------- | ---------- | ----- | ------- | ----- | -------------- | --- |
| Jeff Johnson, | Matthijs |     | Douze, | and Hervé | Jégou. | 2017. |            |            |       |         |       |                |     |
|               |          |     |        |           |        |       | Optimizing | continuous |       | prompts | for   | generation.    | In  |
Billion-scale similarity search with gpus. ArXiv Proceedings of the 59th Annual Meeting of the
preprint,abs/1702.08734.
|     |     |     |     |     |     |     | Association | for | Computational |     | Linguistics |     | and the |
| --- | --- | --- | --- | --- | --- | --- | ----------- | --- | ------------- | --- | ----------- | --- | ------- |
11thInternationalJointConferenceonNaturalLan-
VladimirKarpukhin,BarlasOguz,SewonMin,Patrick
|     |     |     |     |     |     |     | guage Processing |     | (Volume | 1:  | Long | Papers), | pages |
| --- | --- | --- | --- | --- | --- | --- | ---------------- | --- | ------- | --- | ---- | -------- | ----- |
Lewis,LedellWu,SergeyEdunov,DanqiChen,and 4582–4597, Online. Association for Computational
| Wen-tau                       | Yih.       | 2020.       | Dense        | passage           | retrieval       | for     | Linguistics.  |                      |             |       |           |         |      |
| ----------------------------- | ---------- | ----------- | ------------ | ----------------- | --------------- | ------- | ------------- | -------------------- | ----------- | ----- | --------- | ------- | ---- |
| open-domainquestionanswering. |            |             |              |                   | InProceedingsof |         |               |                      |             |       |           |         |      |
| the 2020                      | Conference |             | on Empirical |                   | Methods         | in Nat- |               |                      |             |       |           |         |      |
|                               |            |             |              |                   |                 |         | Opher Lieber, |                      | Or Sharir,  | Barak | Lenz,     | and     | Yoav |
| ural Language                 |            | Processing  |              | (EMNLP),          | pages           | 6769–   |               |                      |             |       |           |         |      |
|                               |            |             |              |                   |                 |         | Shoham.       | 2021.                | Jurassic-1: |       | Technical | details | and  |
| 6781,                         | Online.    | Association |              | for Computational |                 | Lin-    |               |                      |             |       |           |         |      |
|                               |            |             |              |                   |                 |         | evaluation.   | WhitePaper.AI21Labs. |             |       |           |         |      |
guistics.
JiachangLiu,DinghanShen,YizheZhang,BillDolan,
UrvashiKhandelwal, AngelaFan, DanJurafsky, Luke Lawrence Carin, and Weizhu Chen. 2021a. What
Zettlemoyer,andMikeLewis.2021. NearestNeigh- makes good in-context examples for gpt-3? ArXiv
borMachineTranslation. InProceedingsofICLR. preprint,abs/2101.06804.

PengfeiLiu,WeizheYuan,JinlanFu,ZhengbaoJiang, Nils Reimers and Iryna Gurevych. 2019. Sentence-
Hiroaki Hayashi, and Graham Neubig. 2021b. Pre- BERT:SentenceembeddingsusingSiameseBERT-
train, prompt, and predict: A systematic survey of networks. InProceedingsofthe2019Conferenceon
promptingmethodsinnaturallanguageprocessing. EmpiricalMethodsinNaturalLanguageProcessing
andthe9thInternationalJointConferenceonNatu-
| Sewon Min, | Mike | Lewis, | Hannaneh |     | Hajishirzi, | and |     |     |     |     |     |     |     |
| ---------- | ---- | ------ | -------- | --- | ----------- | --- | --- | --- | --- | --- | --- | --- | --- |
ralLanguageProcessing(EMNLP-IJCNLP),pages
| Luke Zettlemoyer. |     | 2021. |     | Noisy | channel | language |            |     |      |       |        |             |     |
| ----------------- | --- | ----- | --- | ----- | ------- | -------- | ---------- | --- | ---- | ----- | ------ | ----------- | --- |
|                   |     |       |     |       |         |          | 3982–3992, |     | Hong | Kong, | China. | Association | for |
model prompting for few-shot text classification. ComputationalLinguistics.
arXivpreprint.
|     |     |     |     |     |     |     | Stephen | Robertson | and | Hugo | Zaragoza. | 2009. | The |
| --- | --- | --- | --- | --- | --- | --- | ------- | --------- | --- | ---- | --------- | ----- | --- |
Sewon Min, Xinxi Lyu, Ari Holtzman, Mikel Artetxe, probabilistic relevance framework: Bm25 and be-
| MikeLewis, | HannanehHajishirzi, |            |     |          | andLukeZettle- |     |       |             |     |            |     |                |     |
| ---------- | ------------------- | ---------- | --- | -------- | -------------- | --- | ----- | ----------- | --- | ---------- | --- | -------------- | --- |
|            |                     |            |     |          |                |     | yond. | Foundations |     | and Trends |     | in Information | Re- |
| moyer.     | 2022.               | Rethinking |     | the role | of demonstra-  |     |       |             |     |            |     |                |     |
trieval,3:333–389.
| tions:Whatmakesin-contextlearningwork? |     |     |     |     |     | ArXiv, |     |     |     |     |     |     |     |
| -------------------------------------- | --- | --- | --- | --- | --- | ------ | --- | --- | --- | --- | --- | --- | --- |
abs/2202.12837.
ChrisSamarinas,WynneHsu,andMongLiLee.2021.
Improvingevidenceretrievalforautomatedexplain-
PanupongPasupat,YuanZhang,andKelvinGuu.2021.
|     |     |     |     |     |     |     | ablefact-checking. |     |     | InProceedingsofthe2021Con- |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ------------------ | --- | --- | -------------------------- | --- | --- | --- |
Controllablesemanticparsingviaretrievalaugmen-
ferenceoftheNorthAmericanChapteroftheAsso-
|         | Proceedings |     | of  | the 2021 | Conference | on  |                                     |     |     |     |     |           |     |
| ------- | ----------- | --- | --- | -------- | ---------- | --- | ----------------------------------- | --- | --- | --- | --- | --------- | --- |
| tation. | In          |     |     |          |            |     |                                     |     |     |     |     |           |     |
|         |             |     |     |          |            |     | ciationforComputationalLinguistics: |     |     |     |     | HumanLan- |     |
EmpiricalMethodsinNaturalLanguageProcessing,
|                 |     |                     |     |     |     |         | guageTechnologies: |     |     | Demonstrations, |     | pages84–91, |     |
| --------------- | --- | ------------------- | --- | --- | --- | ------- | ------------------ | --- | --- | --------------- | --- | ----------- | --- |
| pages7683–7698, |     | OnlineandPuntaCana, |     |     |     | Domini- |                    |     |     |                 |     |             |     |
Online.AssociationforComputationalLinguistics.
| can Republic. |     | Association |     | for Computational |     | Lin- |     |     |     |     |     |     |     |
| ------------- | --- | ----------- | --- | ----------------- | --- | ---- | --- | --- | --- | --- | --- | --- | --- |
guistics.
|     |     |     |     |     |     |     | Nikunj Saunshi, |     | Sadhika | Malladi, |     | and Sanjeev | Arora. |
| --- | --- | --- | --- | --- | --- | --- | --------------- | --- | ------- | -------- | --- | ----------- | ------ |
2021. Amathematicalexplorationofwhylanguage
| Fabio Petroni, |     | Tim Rocktäschel, |     |     | Sebastian | Riedel, |     |     |     |     |     |     |     |
| -------------- | --- | ---------------- | --- | --- | --------- | ------- | --- | --- | --- | --- | --- | --- | --- |
Patrick Lewis, Anton Bakhtin, Yuxiang Wu, and models help solve downstream tasks. In Interna-
AlexanderMiller.2019. Languagemodelsasknowl- tionalConferenceonLearningRepresentations.
| edge bases? |           | In Proceedings |                   | of         | the 2019 | Confer-  |                 |          |            |          |      |                |            |
| ----------- | --------- | -------------- | ----------------- | ---------- | -------- | -------- | --------------- | -------- | ---------- | -------- | ---- | -------------- | ---------- |
|             |           |                |                   |            |          |          | Timo Schick     | and      | Hinrich    | Schütze. |      | 2021.          | Exploiting |
| ence on     | Empirical |                | Methods           | in Natural |          | Language |                 |          |            |          |      |                |            |
|             |           |                |                   |            |          |          | cloze-questions |          | for        | few-shot | text | classification | and        |
| Processing  | and       | the            | 9th International |            | Joint    | Confer-  |                 |          |            |          |      |                |            |
|             |           |                |                   |            |          |          | natural         | language | inference. |          | In   | Proceedings    | of the     |
| ence on     | Natural   | Language       |                   | Processing |          | (EMNLP-  |                 |          |            |          |      |                |            |
16thConferenceoftheEuropeanChapteroftheAs-
IJCNLP),pages2463–2473,HongKong,China.As-
|     |     |     |     |     |     |     | sociation | for | Computational |     | Linguistics: |     | Main Vol- |
| --- | --- | --- | --- | --- | --- | --- | --------- | --- | ------------- | --- | ------------ | --- | --------- |
sociationforComputationalLinguistics.
|     |     |     |     |     |     |     | ume, | pages 255–269, |     | Online. | Association |     | for Com- |
| --- | --- | --- | --- | --- | --- | --- | ---- | -------------- | --- | ------- | ----------- | --- | -------- |
Guanghui Qin and Jason Eisner. 2021. Learning how putationalLinguistics.
toask:QueryingLMswithmixturesofsoftprompts.
|     |     |     |     |     |     |     | Erich Schubert |     | and Michael |     | Gertz. | 2018. | Improving |
| --- | --- | --- | --- | --- | --- | --- | -------------- | --- | ----------- | --- | ------ | ----- | --------- |
InProceedingsofthe2021ConferenceoftheNorth
|          |              |         |                 |             |               |          | the cluster | structure |     | extracted | from | optics | plots. In |
| -------- | ------------ | ------- | --------------- | ----------- | ------------- | -------- | ----------- | --------- | --- | --------- | ---- | ------ | --------- |
| American | Chapter      | of      | the Association |             | for           | Computa- |             |           |     |           |      |        |           |
| tional   | Linguistics: | Human   |                 | Language    | Technologies, |          | LWDA.       |           |     |           |      |        |           |
| pages    | 5203–5212,   | Online. |                 | Association | for           | Compu-   |             |           |     |           |      |        |           |
RichardShin,ChristopherLin,SamThomson,Charles
tationalLinguistics.
|     |     |     |     |     |     |     | Chen, | Subhro | Roy, | Emmanouil |     | Antonios | Platanios, |
| --- | --- | --- | --- | --- | --- | --- | ----- | ------ | ---- | --------- | --- | -------- | ---------- |
Yingqi Qu, Yuchen Ding, Jing Liu, Kai Liu, Ruiyang AdamPauls,DanKlein,JasonEisner,andBenjamin
|             |     |           |         |           |       |          | Van Durme. |          | 2021.    | Constrained |     | language       | models |
| ----------- | --- | --------- | ------- | --------- | ----- | -------- | ---------- | -------- | -------- | ----------- | --- | -------------- | ------ |
| Ren, Wayne  |     | Xin Zhao, | Daxiang |           | Dong, | Hua Wu,  |            |          |          |             |     |                |        |
|             |     |           |         |           |       |          | yield      | few-shot | semantic | parsers.    |     | In Proceedings | of     |
| and Haifeng |     | Wang.     | 2021.   | RocketQA: |       | An opti- |            |          |          |             |     |                |        |
mized training approach to dense passage retrieval the2021ConferenceonEmpiricalMethodsinNatu-
for open-domain question answering. In Proceed- ralLanguageProcessing,pages7699–7715,Online
ings of the 2021 Conference of the North Ameri- and Punta Cana, Dominican Republic. Association
can Chapter of the Association for Computational forComputationalLinguistics.
| Linguistics: | Human   |     | Language    | Technologies, |               | pages |                                  |         |     |          |        |             |           |
| ------------ | ------- | --- | ----------- | ------------- | ------------- | ----- | -------------------------------- | ------- | --- | -------- | ------ | ----------- | --------- |
|              |         |     |             |               |               |       | Taylor Shin,                     | Yasaman |     | Razeghi, | Robert | L.          | Logan IV, |
| 5835–5847,   | Online. |     | Association | for           | Computational |       |                                  |         |     |          |        |             |           |
|              |         |     |             |               |               |       | EricWallace,andSameerSingh.2020. |         |     |          |        | AutoPrompt: |           |
Linguistics.
|     |     |     |     |     |     |     | Eliciting | Knowledge |     | from | Language | Models | with |
| --- | --- | --- | --- | --- | --- | --- | --------- | --------- | --- | ---- | -------- | ------ | ---- |
Jack W Rae, Sebastian Borgeaud, Trevor Cai, Katie Automatically Generated Prompts. In Proceed-
Millican, Jordan Hoffmann, Francis Song, John ings of the 2020 Conference on Empirical Methods
Aslanides, Sarah Henderson, Roman Ring, Susan- in Natural Language Processing (EMNLP), pages
nah Young, et al. 2021. Scaling language models: 4222–4235, Online. Association for Computational
| Methods, | analysis | &   | insights | from | training | gopher. | Linguistics. |     |     |     |     |     |     |
| -------- | -------- | --- | -------- | ---- | -------- | ------- | ------------ | --- | --- | --- | --- | --- | --- |
arXivpreprintarXiv:2112.11446.
|     |     |     |     |     |     |     | Ben Wang | and | Aran | Komatsuzaki. |     | 2021. | GPT- |
| --- | --- | --- | --- | --- | --- | --- | -------- | --- | ---- | ------------ | --- | ----- | ---- |
Colin Raffel, Noam Shazeer, Adam Roberts, Kather- J-6B: A 6 Billion Parameter Autoregressive
ine Lee, Sharan Narang, Michael Matena, Yanqi Language Model. https://github.com/
Zhou, Wei Li, and Peter J. Liu. 2020. Exploring kingoflolz/mesh-transformer-jax.
thelimitsoftransferlearningwithaunifiedtext-to-
text transformer. Journal of Machine Learning Re- Shuo Wang, Yichong Xu, Yuwei Fang, Yang Liu,
| search,21(140):1–67. |     |     |     |     |     |     | S.Sun,RuochenXu,ChenguangZhu,andMichael |     |     |     |     |     |     |
| -------------------- | --- | --- | --- | --- | --- | --- | --------------------------------------- | --- | --- | --- | --- | --- | --- |

Zeng.2022. Trainingdataismorevaluablethanyou Trainingdetails TotrainEPR,weusetheAdam
think: A simple and effective method by retrieving optimizer(KingmaandBa,2015)withbatchsize
| fromtrainingdata. |     | ArXiv,abs/2203.08773. |     |     |     |     |     |     |     |     |
| ----------------- | --- | --------------------- | --- | --- | --- | --- | --- | --- | --- | --- |
120andlearningrate1e-4oneightRTX3090. We
Tomer Wolfson, Mor Geva, Ankit Gupta, Matt Gard- run training for 30 epochs. We used the default
ner, Yoav Goldberg, Daniel Deutch, and Jonathan DPRhyperparameterswithouttuning. Weusedthe
| Berant.  | 2020.      | Break | it down:     | A   | question        | under- |             |        |                  |              |
| -------- | ---------- | ----- | ------------ | --- | --------------- | ------ | ----------- | ------ | ---------------- | ------------ |
|          |            |       |              |     |                 |        | final epoch | of the | model to perform | model selec- |
| standing | benchmark. |       | Transactions |     | of the Associa- |        |             |        |                  |              |
tion,andappliedminimallearningratetuningon
tionforComputationalLinguistics,8:183–198.
|              |      |       |              |     |       |        | thevalidationsetof |     | BREAK. |     |
| ------------ | ---- | ----- | ------------ | --- | ----- | ------ | ------------------ | --- | ------ | --- |
| Sang Michael | Xie, | Aditi | Raghunathan, |     | Percy | Liang, |                    |     |        |     |
andTengyuMa.2021. Anexplanationofin-context Risk assessment Large language models have
| learning | as implicit |     | bayesian | inference. |     | ArXiv, |     |     |     |     |
| -------- | ----------- | --- | -------- | ---------- | --- | ------ | --- | --- | --- | --- |
beenshowntoexhibitvariouskindsofbias(Bender
abs/2111.02080.
|     |     |     |     |     |     |     | et al., 2021), | since | EPR is trained | on the signal |
| --- | --- | --- | --- | --- | --- | --- | -------------- | ----- | -------------- | ------------- |
Yichong Xu, Chenguang Zhu, Shuohang Wang, Siqi obtainedfromsuchlargeLMs,itmightalsoexhibit
| Sun, Hao | Cheng, | Xiaodong |     | Liu, | Jianfeng | Gao, |     |     |     |     |
| -------- | ------ | -------- | --- | ---- | -------- | ---- | --- | --- | --- | --- |
thesebiases.
PengchengHe,MichaelZeng,andXuedongHuang.
2021. Humanparityoncommonsenseqa: Augment- Additional examples Tables 9, 10, and 11 pro-
ingself-attentionwithexternalattention.
|     |     |     |     |     |     |     | vide more | examples | for cases where | EPR is cor- |
| --- | --- | --- | --- | --- | --- | --- | --------- | -------- | --------------- | ----------- |
Zihao Zhao, Eric Wallace, Shi Feng, Dan Klein, and rect while CBR is incorrect along with the top-3
SameerSingh.2021. Calibratebeforeuse: Improv- promptsforeachmethod.
| ing few-shot | performance |     | of  | language | models. | In  |     |     |     |     |
| ------------ | ----------- | --- | --- | -------- | ------- | --- | --- | --- | --- | --- |
ICML,pages12697–12706.
ZexuanZhong,DanFriedman,andDanqiChen.2021.
| Factual                   | probing                            | is [MASK]: |                    | Learning | vs. learning |     |     |     |     |     |
| ------------------------- | ---------------------------------- | ---------- | ------------------ | -------- | ------------ | --- | --- | --- | --- | --- |
| torecall.                 | InProceedingsofthe2021Conferenceof |            |                    |          |              |     |     |     |     |     |
| the North                 | American                           | Chapter    |                    | of the   | Association  | for |     |     |     |     |
| ComputationalLinguistics: |                                    |            | HumanLanguageTech- |          |              |     |     |     |     |     |
nologies,pages5017–5033,Online.Associationfor
ComputationalLinguistics.
A Appendix
| Distribution | of the | number |     | of in-context |     | exam- |     |     |     |     |
| ------------ | ------ | ------ | --- | ------------- | --- | ----- | --- | --- | --- | --- |
ples Sincetheselectionprocedureforin-context
examplesisdynamic,thenumberofin-contextex-
| amplesdiffersforeachtestinstance. |     |     |     |     | InFigure5, |     |     |     |     |     |
| --------------------------------- | --- | --- | --- | --- | ---------- | --- | --- | --- | --- | --- |
weplotthehistogramofthenumberofexamples
| wefitinC                | = 2,048tokens. |         |         |                   |             |     |     |     |     |     |
| ----------------------- | -------------- | ------- | ------- | ----------------- | ----------- | --- | --- | --- | --- | --- |
| Effectofhyperparameters |                |         |         | Wetesttheeffectof |             |     |     |     |     |     |
| k, the number           | of             | prompts | labeled |                   | as positive | or  |     |     |     |     |
negative,andL,thenumberofpromptsretrieved
| bytheunsupervisedretriever. |     |     |     | Table8showsthat |     |     |     |     |     |     |
| --------------------------- | --- | --- | --- | --------------- | --- | --- | --- | --- | --- | --- |
performanceisisgenerallyrobustw.r.tthesehyper-
parameters.
|       | BREAK |     | MTOP  | SMCALFLOW |     |     |     |     |     |     |
| ----- | ----- | --- | ----- | --------- | --- | --- | --- | --- | --- | --- |
| k =1  | 31.5% |     | 63.0% | 54.5%     |     |     |     |     |     |     |
| k =5  | 31.9% |     | 64.2% | 54.3%     |     |     |     |     |     |     |
| k =10 | 31.0% |     | 64.1% | 52.2%     |     |     |     |     |     |     |
| L=50  | 31.9% |     | 64.2% | 54.3%     |     |     |     |     |     |     |
| L=100 | 32.3% |     | 63.7% | 51.0%     |     |     |     |     |     |     |
Table8: IntheLM-as-a-servicesetup,usingGPT-Neo,
| we search | for other | values | for | L and | k, and note | that |     |     |     |     |
| --------- | --------- | ------ | --- | ----- | ----------- | ---- | --- | --- | --- | --- |
thechoiceofourhyperparametersisrobust.

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
Top-2 Utterance Remindmetobringanextrapairof Remindmetomakeagrocerylist
shoestotheriver.
Meaning
[IN:CREATE_REMINDER [SL:PERSON_REMINDED [IN:CREATE_REMINDER [SL:PERSON_REMINDED
Representation
me ] [SL:TODO bring an extra pair of me ] [SL:TODO make a grocery list ] ]
|     |     | shoes | to  | the river | ] ] |     |     |     |     |     |     |     |
| --- | --- | ----- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
Top-3 Utterance Remindmetoaddbottledwaterto Ineedtomakeagrocerylist;willyou
|     |     | grocerylist. |     |     |     |     |     | remindmewhenIgetoffworkat5:00 |     |     |     |     |
| --- | --- | ------------ | --- | --- | --- | --- | --- | ----------------------------- | --- | --- | --- | --- |
p.m.?
Meaning
[IN:CREATE_REMINDER [SL:PERSON_REMINDED [IN:CREATE_REMINDER [SL:TODO make a
Representation
me ] [SL:TODO add bottled water to grocery list ] [SL:PERSON_REMINDED me ]
|     |     | grocery | list | ] ] |     |     |     | [SL:DATE_TIME |     |     | at 5 : | 00 p.m . ] ] |
| --- | --- | ------- | ---- | --- | --- | --- | --- | ------------- | --- | --- | ------ | ------------ |
Table9:AnexamplefromMTOPdevelopmentsetwhereEPRiscorrectandCBRisincorrectalongwiththetop-3
trainingexamplesretrievedfromeachretriever.
|         |           |                 |     | EPR |     |     |     |     |     | CBR |     |     |
| ------- | --------- | --------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Test    | Utterance | confirmedthanks |     |     |     |     |     |     |     |     |     |     |
| Example | Meaning   |                 |     |     |     |     |     |     |     |     |     |     |
(PleasantryAnythingElseCombined)
Representation
| Top-1 | Utterance | it’sokbye |     |     |     |     | Yes,butmakesuretoletmeknowthe |     |     |     |     |     |
| ----- | --------- | --------- | --- | --- | --- | --- | ----------------------------- | --- | --- | --- | --- | --- |
weatherforthattime.
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
Meaning (PleasantryAnythingElseCombined) (Yield (Execute (^(Dynamic)
Representation
ConfirmAndReturnAction)))
Table10:AnexamplefromSMCALFLOWdevelopmentsetwhereEPRiscorrectandCBRisincorrectalongwith
thetop-3trainingexamplesretrievedfromeachretriever.

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
Utterance makeameetingwithjeritoday setupameetingwithbothofDavid
Top-1
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
Representation (CreatePreflightEventWrapper (& (CreatePreflightEventWrapper (&
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
Meaning (Yield (CreateCommitEventWrapper (Yield (CreateCommitEventWrapper
Representation
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
Table11:AnexamplefromSMCALFLOWdevelopmentsetwhereEPRiscorrectandCBRisincorrectalongwith
thetop-3trainingexamplesretrievedfromeachretriever.
| Utterance |     | MeaningRepresentation |                 |     |     |     |
| --------- | --- | --------------------- | --------------- | --- | --- | --- |
|           |     | 1#) return            | the philippines |     |     |     |
which3seasborderphilippines?
|                                   |     | 2#) return | seas that        | border #1       |     |     |
| --------------------------------- | --- | ---------- | ---------------- | --------------- | --- | --- |
| whatthreeseassurroundphilippines? |     | 1#) return | seas             |                 |     |     |
|                                   |     | 2#) return | #1 that surround | the philippines |     |     |
| whatstatesdoeswestvirginiaborder? |     | 1#) return | west virginia    |                 |     |     |
|                                   |     | 2#) return | border states    | of #1           |     |     |
|                                   |     | 1#) return | west virginia    |                 |     |     |
whatstatesborderswestvirginia?
|                           |                                                      | 2#) return | border states  | of #1    |     |     |
| ------------------------- | ---------------------------------------------------- | ---------- | -------------- | -------- | --- | --- |
| whichstatesbordercolorado |                                                      | 1#) return | states         |          |     |     |
|                           |                                                      | 2#) return | #1 that border | colorado |     |     |
| Table12:                  | Exampleofaclusterfromthet-SNEprojectionofEPRonBREAK. |            |                |          |     |     |

| Utterance                        | MeaningRepresentation |               |                     |                   |
| -------------------------------- | --------------------- | ------------- | ------------------- | ----------------- |
| Listthetotalscoresofbodybuilders | 1#) return            | body builders |                     |                   |
| inascendingorder.                | 2#) return            | scores        | of #1               |                   |
|                                  | 3#) return            | sum of        | #2 for each #1      |                   |
|                                  | 4#) return            | #3 sorted     | by ascending        | order             |
| Whatarethenamesofbodybuildersin  | 1#) return            | body builders |                     |                   |
| descendingorderoftotalscores?    | 2#) return            | names of      | #1                  |                   |
|                                  | 3#) return            | scores        | of #1               |                   |
|                                  | 4#) return            | sum of        | #3 for each #1      |                   |
|                                  | 5#) return            | #2 sorted     | by #4 in descending | order             |
| Listthetotalpointsofgymnastsin   | 1#) return            | gymnasts      |                     |                   |
| descendingorder.                 | 2#) return            | points        | of #1               |                   |
|                                  | 3#) return            | sum of        | #2 for each #1      |                   |
|                                  | 4#) return            | #3 sorted     | by descending       | order             |
| Whatarethetotalpointsforall      | 1#) return            | gymnasts      |                     |                   |
| gymnasts,orderedbytotalpoints    | 2#) return            | total points  | for all             | #1                |
| descending?                      | 3#) return            | #2 ordered    | by total            | points descending |
| Listthetotalpointsofgymnastsin   | 1#) return            | gymnasts      |                     |                   |
|                                  | 2#) return            | points        | of #1               |                   |
descendingorderoffloorexercise
| points. | 3#) return | sum of         | #2 for each #1      |       |
| ------- | ---------- | -------------- | ------------------- | ----- |
|         | 4#) return | floor exercise | points              | of #1 |
|         | 5#) return | #3 sorted      | by #4 in descending | order |
Table13: Exampleofaclusterfromthet-SNEprojectionofEPRonBREAK.
| Utterance                    | MeaningRepresentation |              |       |     |
| ---------------------------- | --------------------- | ------------ | ----- | --- |
| Showthelocationsthathaveboth | 1#) return            | performances |       |     |
| performanceswithmorethan2000 | 2#) return            | attendees    | of #1 |     |
attendeesandperformanceswithless 3#) return the number of #2 for each #1
| than1000attendees.                 | 4#) return | #1 where      | #3 is more     | than 2000 |
| ---------------------------------- | ---------- | ------------- | -------------- | --------- |
|                                    | 5#) return | #1 where      | #3 is less     | than 1000 |
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
|                                    | 3#) return | prices        | of #2          |           |
10000000andpublicationswithprice
lowerthan5000000. 4#) return #1 where #3 is higher than 10000000
|                                 | 5#) return | #1 where | #3 is lower    | than 5000000 |
| ------------------------------- | ---------- | -------- | -------------- | ------------ |
|                                 | 6#) return | #1 of    | both #4 and #5 |              |
| Showthefamoustitlesoftheartists | 1#) return | artists  |                |              |
|                                 | 2#) return | volumes  | of #1          |              |
withbothvolumesthatlastedmorethan
| 2weeksontopandvolumesthatlasted | 3#) return | weeks    | on top that #2 | lasted |
| ------------------------------- | ---------- | -------- | -------------- | ------ |
| lessthan2weeksontop.            | 4#) return | number   | of #3 for each | #2     |
|                                 | 5#) return | #1 where | #4 is more     | than 2 |
|                                 | 6#) return | #1 where | #4 is less     | than 2 |
|                                 | 7#) return | #1 in    | both #5 and #6 |        |
|                                 | 8#) return | famous   | titles of #7   |        |
Table14: Exampleofaclusterfromthet-SNEprojectionofEPRonBREAK.

| Utterance                     | MeaningRepresentation |             |             |       |
| ----------------------------- | --------------------- | ----------- | ----------- | ----- |
| Whatisthemetalthingnexttothe  | 1#) return            | the small   | cylinder    |       |
| smallcylinder?                | 2#) return            | things      |             |       |
|                               | 3#) return            | #2 that     | are metal   |       |
|                               | 4#) return            | #3 that     | are next to | #1    |
| Whatisthepurplethingnexttothe | 1#) return            | the brown   | thing       |       |
| brownthing?                   | 2#) return            | things      |             |       |
|                               | 3#) return            | #2 that     | are purple  |       |
|                               | 4#) return            | #3 that     | are next to | #1    |
| Whatisthegraythingnexttothe   | 1#) return            | gray thing  |             |       |
| block?                        | 2#) return            | the block   |             |       |
|                               | 3#) return            | #1 next     | to #2       |       |
| Whatistheshinythingnexttothe  | 1#) return            | shiny thing |             |       |
| cylinder?                     | 2#) return            | cylinder    |             |       |
|                               | 3#) return            | #1 next     | to #2       |       |
| Whatisthethinginfrontofthered | 1#) return            | things      |             |       |
| square?                       | 2#) return            | squares     |             |       |
|                               | 3#) return            | #2 that     | is red      |       |
|                               | 4#) return            | #1 that     | is in front | of #3 |
Table15: Exampleofaclusterfromthet-SNEprojectionofEPRonBREAK.
| Utterance                       | MeaningRepresentation |            |             |       |
| ------------------------------- | --------------------- | ---------- | ----------- | ----- |
| Isthepurplethingbehindthebigred | 1#) return            | purple     | thing       |       |
| thing?                          | 2#) return            | big red    | thing       |       |
|                                 | 3#) return            | Is #1      | behind #2   |       |
| isthepurplesphereinfrontofthe   | 1#) return            | the purple | sphere      |       |
| bluecube?                       | 2#) return            | the blue   | cube        |       |
|                                 | 3#) return            | if #1      | is in front | of #2 |
|                                 | 1#) return            | the green  | cylinder    |       |
isthegrayspherebehindthegreen
| cylinder?                       | 2#) return | the gray   | sphere       |       |
| ------------------------------- | ---------- | ---------- | ------------ | ----- |
|                                 | 3#) return | if #2      | is behind #1 |       |
| istheredcubeinfrontoftheyellow  | 1#) return | the red    | cube         |       |
| ball?                           | 2#) return | the yellow | ball         |       |
|                                 | 3#) return | if #1      | is in front  | of #2 |
| Istheblueballinfrontofthesilver | 1#) return | blue ball  |              |       |
| cube?                           | 2#) return | silver     | cube         |       |
|                                 | 3#) return | is #1      | in front of  | #2    |
Table16: Exampleofaclusterfromthet-SNEprojectionofEPRonBREAK.