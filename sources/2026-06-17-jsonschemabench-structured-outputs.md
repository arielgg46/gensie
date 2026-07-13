---
type: source
source_type: paper
url: https://arxiv.org/pdf/2501.10868
title: "JSONSchemaBench: A Rigorous Benchmark of Structured Outputs for Language Models"
fetched_at: 2026-06-17T15:17:31-05:00
fetcher: markitdown
---
JSONSchemaBench: A Rigorous Benchmark
of Structured Outputs for Language Models
Saibo Geng1∗ Hudson Cooper2 Michał Moskal2 Samuel Jenkins2
Julian Berman3 Nathan Ranchin1 Robert West1,2
Eric Horvitz2 Harsha Nori2
1EPFL 2Microsoft 3JSONSchema
{saibo.geng,nathan.ranchin,robert.west@epfl.ch}@epfl.ch
{julian}@grayvines.com
{hanori,hudsoncooper,michal.moskal,sajenkin,horvitz}@microsoft.com
Abstract
Reliablygeneratingstructuredoutputshasbecomeacriticalcapability
for modern language model (LM) applications. Constrained decoding
hasemergedasthedominanttechnologyacrosssectorsforenforcing
structured outputs during generation. Despite its growing adoption,
little has been done with the systematic evaluation of the behaviors
andperformanceofconstraineddecoding. Constraineddecodingframe-
works have standardized around JSON Schema as a structured data
format, with most uses guaranteeing constraint compliance given a
schema. However, there is poor understanding of the effectiveness
of the methods in practice. We present an evaluation framework to
assess constrained decoding approaches across three critical dimen-
sions: efficiencyingeneratingconstraint-compliantoutputs,coverage
of diverse constraint types, and quality of the generated outputs. To
facilitatethisevaluation,weintroduceJSONSchemaBench,abenchmark
for constrained decoding comprising 10K real-world JSON schemas
that encompass a wide range of constraints with varying complexity.
We pair the benchmark with the existing official JSON Schema Test
Suiteandevaluatesixstate-of-the-artconstraineddecodingframeworks,
includingGuidance,Outlines,Llamacpp,XGrammar,OpenAI,andGem-
ini. Through extensive experiments, we find that JSONSchemaBench
presentsasignificantchallengeforbothLLMsandconstraineddecod-
ingframeworks,highlightingampleroomforimprovementandexpos-
ing gaps in the existing solutions. We release JSONSchemaBench at
https://github.com/guidance-ai/jsonschemabench.
1 Introduction
The rapid advancements in LMs in recent years have significantly broadened their
applications,extendingbeyondnaturallanguagetaskstomorecomplexchallengessuch
∗WorkdoneduringinternshipatMicrosoft.
Preprint. Underreview.
5202
beF
72
]LC.sc[
3v86801.1052:viXra

Figure 1: Comparison across various constrained-decoding frameworks by efficiency
(speedofoutputgeneration),coverage(supportforJSONSchemafeatures),andquality
(effectsonunderlyingtaskaccuracy). Guidanceoutperformsotherframeworksonthese
dimensions.
aswebnavigation[Yaoetal.,2023b],dataextraction[Polak&Morgan,2024],andtool
use [Schick et al., 2023]. Unlike traditional natural language processing (NLP) tasks
where the output is aimed at review by humans, output in these applications is often
consumedbymachinessuchascontrollerandserviceAPIs. Themachine-orientednature
oftheseapplicationsrequiresLMstogeneratestructuredoutputsthatstrictlyadhereto
predefinedformatsandconstraints. However,theLMgenerationprocessisprobabilistic
and does not provide guarantees on the output’s structure, making it challenging to
deployLMsinapplicationsrequiringstructuredinputsandhighreliability.
Themethodologyofconstraineddecoding,atechniquethatintegratesconstraintsinto
the decoding process of LMs, has been developed to address the need to adapt LM
generations to the challenge of providing structured output. Constrained decoding
intervenesinthedecodingprocessofLMsbymaskingoutinvalidtokensbasedongiven
constraintsandprefixtokens. ThisinterventionguidestheLMtosampleonlyfromvalid
tokens,ensuringthatthefinaloutputperfectlyconformstoapredefinedstructure.
Thestrongdemandforstructuredgeneration[Liuetal.,2024]hasledtothedevelopment
ofvariousconstrained-decodingframeworks2,suchasGuidance[GuidanceAI,2023],
Outlines [Willard & Louf, 2023], XGrammar [Dong et al., 2024] and the grammar
moduleofLlamacpp[Gerganov&al.,2023]Theseframeworksprovidebroadsupport
fordifferenttypesofconstraints,minimaloverhead,andcompatibilitywithvariousLM
ecosystems,facilitatingtheadoptionofconstraineddecodinginreal-worldapplications.
JSON Schema offers a high level, domain-specific way to define constraints for JSON
data,awidelyadopteddatainterchangeformat. Asaresult,JSONSchemahasemerged
as a key specification language for constrained decoding. Commercial LM providers,
suchasOpenAI,haveembracedconstraineddecodingbyincorporatingsupportforJSON
SchemadirectlyintotheirAPIs. TheseintegrationshighlighttheemergenceofJSON
2Weusethetermsconstraineddecodingframework andgrammarengine interchangeably.
2

Schemaasanindustry-widestandardforspecifyingconstraintsonstructuredoutputs,
ensuringcompatibilityacrossdiverseapplications.
Despitethegrowingadoptionofconstraineddecodingforstructuredgeneration,several
issuesandquestionspersist:
Q1: Efficiency: Does constrained decoding slow down or speed up the generation
process? Whichframeworkisthemostefficient?
Q2: Coverage: TheJSONSchemaspecificationhasanevolvingandexpansivefeature
set. Howwelldoexistingconstraineddecodingframeworkssupportthesefeatures?
Q3: Quality: While constrained decoding guarantees that LM outputs conform to a
desiredstructure,doesitnegativelyaffectthesemanticqualityofoutputs?
To answer these questions, we need to study constrained-decoding methods with a
large-scale,diverse,andreal-worldcollectionofuser-definedstructures. Toevaluatethe
performanceofconstraineddecodingframeworks,weintroduceJSONSchemaBench,
acollectionof10Kreal-worldJSONschemasfromvarioussources,Organizedinto10
datasetsofvaryingcomplexityanddiversity,thebenchmarkspansdomainssuchasfunc-
tionsignatures,serviceAPIs,andsystemconfigurations. Weevaluatesixstate-of-the-art
constraineddecodingframeworks,includingGuidance,Outlines,Llamacpp,XGrammar,
OpenAI, and Gemini, on JSONSchemaBench. We pair this real-world schema dataset
withtheofficialJSONSchemaTestSuite[JSONSchemaOrg,2024]inordertoextract
detailedinsightsintocoverageofJSONSchemafunctionalityacrosstheseframeworks,
and to further evaluate them with considerations of end-to-end task accuracy in the
contextofmultiplereal-worldtasks. Altogether,ourevaluationtakesthreeaspectsinto
consideration: efficiency,coverage,andquality. Wedefinespecificmetricstomeasure
thesethreefunctionalaspectsandevaluateconstraineddecodingframeworksagainst
them. Throughextensiveexperiments,weconvergeonthefollowingfindingsasillus-
tratedinFigure1. (1)Constraineddecodingcanspeedupthegenerationprocessby
50% compared to unconstrained decoding. (2) Frameworks demonstrate significant
differencesintheiractualsupportforreal-worldJSONschemas,withthebestframework
supportingtwiceasmanyschemasastheworst. (3)Constraineddecodingconsistently
improvestheperformanceofdownstreamtasksupto4%,evenfortaskswithminimal
structurelikeGSM8k.
Contributions Ourcontributionsarethree-fold:
• We assemble JSON schemas from various sources and organize them into a
benchmark,JSONSchemaBench,tofacilitatetheevaluationofconstrainedde-
codingframeworksonJSONschema.
• We propose a fine-grained evaluation framework to assess the versatility of
constraineddecodingframeworksinhandlingdiverseJSONschemafeatures,
includingdeclaredcoverage,empiricalcoverage,andcompliancerate.
• We evaluate six state-of-the-art constrained decoding frameworks on JSON-
SchemaBench,uncoveringtheirstrengthsandlimitationsingeneratingschema-
compliantJSONoutputsandanalyzingtheirimpactondownstreamtasks.
2 Background and Related Work
JSONSchema isameta-languagethatdescribesthestructureofJSONdata. Itiscapable
ofexpressingawidevarietyofconstraints,suchasthetypesofJSONobjectproperties,
the length of JSON arrays or the pattern that a JSON string must match. The syntax
andcapabilitiesofJSONSchemaaredefinedintheJSONSchemaspecification[Wright
et al., 2022], which defines a large number of keywords, each of which may be used
orcombinedwithotherkeywordswithinaschematoenforceconstraintsliketheones
mentioned. JSONSchemaiswidelyusedinthesoftwareecosystem,andpreviouswork
has been done to collect extensive examples of JSON Schemas with a focus both on
real-worlduseaswellasonoverallcorrectness.
3

Baazizietal.[2021]collectedover6,000JSONschemasfrompubliclyavailableGitHub
repositories. Attoucheetal.[2022]useditalongsideadditionalcollectedJSONschemas
inordertoevaluateawitnessgenerationalgorithmforJSONSchema. Separately,the
officialJSONSchemaTestSuite[JSONSchemaOrg,2024]isacollectionofmanually
createdtestcases,maintainedbytheJSONSchemacoreteam,whichexercisesalarge
portionofthefunctionalitydefinedintheJSONSchemaspecification. Itwasoriginally
writtentoassistimplementersofJSONSchemavalidationtoolswithtestingtheircompli-
anceagainstthespecification,andthereforecontainsawidevarietyofexamplesforeach
ofJSONSchema’skeywords,includinginedgecasescenarios. Notably,Bowtie[Bowtie,
2025]leveragesthetestsuiteasafoundationforcomparingandunderstandingdifferent
implementations of the JSON Schema specification across programming languages.
Taken together, these two datasets form a large number of examples both of JSON
Schema’sdiversefeaturesetaswellasitsuseinthewild.
| Constrained | decoding           | [Deutsch |      | et al., |
| ----------- | ------------------ | -------- | ---- | ------- |
| 2019;       | Shin et al., 2021; | Scholak  |      | et al., |
| 2021;       | Poesia et al.,     | 2022;    | Wang | et al.; |
Algorithm 1 ConstrainedDecoding
| Geng | et al., 2023] | refers | to methods |     |
| ---- | ------------- | ------ | ---------- | --- |
Require: ConstraintC,LLMf,Promptx
thatguidethegenerationprocessoflan-
OutputoadheringtoC
| guage | models (LMs) | by masking |     | out to- Ensure: |
| ----- | ------------ | ---------- | --- | --------------- |
1: o←[]
| kens that | do not adhere | to  | predefined |     |
| --------- | ------------- | --- | ---------- | --- |
2: loop
| constraintsateachstep. |     | Recently,highly |     |     |
| ---------------------- | --- | --------------- | --- | --- |
C.update(o) ▷advancestateofC
| optimizedgrammar-constraineddecoding |     |     |     | 3:  |
| ------------------------------------ | --- | --- | --- | --- |
frameworks [Guidance AI, 2023; Beurer- 4: m←C.mask() ▷computemask
5: v ←f(x+o) ▷computelogits
Kellneretal.,2023;Willard&Louf,2023;
6: v′ ←m⊙v′
| Kuchnik | et al., 2023; | Zheng | et al., | 2024; |
| ------- | ------------- | ----- | ------- | ----- |
t←decode(α′) ▷sample
| Dong et | al., 2024] have | been | developed | 7:  |
| ------- | --------------- | ---- | --------- | --- |
8: ift=EOSthen
toimprovetheefficiencyandusabilityof
9: break
constraineddecoding.
endif
10:
| The evaluation | of constrained |     | decoding |     |
| -------------- | -------------- | --- | -------- | --- |
11: o.append(t)
| remainsanunder-exploredtopic,withno |     |     |     | 12: endloop |
| ----------------------------------- | --- | --- | --- | ----------- |
consensus on what defines the effective- 13: returno ▷ output
| nessofconstraineddecoding. |     |     | Whilesome |     |
| -------------------------- | --- | --- | --------- | --- |
researchhaspursuedcomparisonsofcon-
straineddecodingwithunconstrainedLMs[Royetal.,2024;Tangetal.,2024;Yaoetal.,
2023a],thestudiestodatefailtoprovidecomparisonsacrossdifferentconstrainedde-
codingframeworks. Thebenchmarksemployedhaveeithernarrowlyfocusedonspecific
tasksorrelyonformal-grammar–basedartificialsetups,thathaveunclearrelevanceto
real-worldusecases.
| 3 The | JSONSchemaBench |     |     |     |
| ----- | --------------- | --- | --- | --- |
Ourgoalistodesignabenchmarkthatis(1)diverseenoughtocoverthemostcommon
constrainttypesencounteredinreal-worldapplications,(2)largeenoughtoprovidea
reliableevaluation,and(3)equippedwithfairandmultidimensionalmetricstoensure
comprehensiveassessments.
| 3.1 Data | Collection |     |     |     |
| -------- | ---------- | --- | --- | --- |
We start with the 6K JSON schemas collected by Baazizi et al. [2021] from publicly
available GitHub repositories, and with the set of schemas from the JSON Schema
Test Suite [JSON Schema Org, 2024]. We further collect JSON schemas from other
sources, such as the JSON Schema Store [Schema Store Org, 2014], the GlaiveAI
functioncallingdatasetV2[GlaiveAI,2024],andfromKubernetesconfigurationfiles[Ku-
4

bernetes, 2022]. We filter out invalid schemas and standardize the schemas to en-
sure that they conform to the version of JSON Schema declared3 in each schema
| The GitHub | JSON schemas | collec- |     |     |     |
| ---------- | ------------ | ------- | --- | --- | --- |
tion from Baazizi et al. [2021] contains Table1: Schemacollectionmetadata.
schemasofvaryingcomplexityanddiver-
sity,rangingfromsimpletypeconstraints
|     |     |     | Dataset | Category | Count |
| --- | --- | --- | ------- | -------- | ----- |
tocomplexconstraintswithnestedobjects
|            |                            |     | GlaiveAI-2K    | FunctionCall | 1707 |
| ---------- | -------------------------- | --- | -------------- | ------------ | ---- |
| andarrays. | Formorefine-grainedevalua- |     |                |              |      |
|            |                            |     | Github-Trivial | Misc         | 444  |
tion,wesplitthedataintofivecollections
|     |     |     | Github-Easy | Misc | 1943 |
| --- | --- | --- | ----------- | ---- | ---- |
based on the schema size: trivial, small, Snowplow OperationalAPI 403
medium, large, ultra. The suites final- Github-Medium Misc 1976
izedafterallcollectionandprocessingare Kubernetes KubernetesAPI 1064
listed in Table ??. We excluded GitHub- WashingtonPost ResourceAccessAPI 125
|     |     |     | Github-Hard | Misc | 1240 |
| --- | --- | --- | ----------- | ---- | ---- |
TrivialandGitHub-Ultrafromtheexperi-
|     |     |     | JSONSchemaStore | Misc | 492 |
| --- | --- | --- | --------------- | ---- | --- |
mentsastheyweretooeasyortoohard.
|                |                     |             | Github-Ultra | Misc | 164  |
| -------------- | ------------------- | ----------- | ------------ | ---- | ---- |
| However,       | we retained these   | datasets in |              |      |      |
|                |                     |             | Total        |      | 9558 |
| the benchmark, | with GitHub-Ultra   | serv-       |              |      |      |
| ing as an      | aspirational target | for future  |              |      |      |
advancements. Formoreinformationonpost-processinganddatasetsplitting,werefer
thereadertoAppendixA.
4 Efficiency
NaïveimplementationsofconstraineddecodingaddoverheadtothestandardLMinfer-
enceprocess,includingaper-stepmaskcomputationandanoptionalone-timegrammar
compilation. However, several optimizations can significantly reduce this overhead.
For instance, mask computation can run in parallel with the LM’s forward pass, and
grammarcompilationcanbeperformedconcurrentlywithpre-fillingcomputations[Guid-
anceAI,2023;Dongetal.,2024]. Otheroptimizationssuchasgrammarcachingand
constraint-basedspeculativedecoding[GuidanceAI,2024b;Beurer-Kellneretal.,2023;
Kurt,2024a]canfurtherreduceoverhead.
Metrics Webreakdowntheefficiencyevaluationintothefollowingcomponents:
• Grammar Compilation Time (GCT):Thetimespentongrammarcompilation,
ifapplicable.
• Time to First Token (TTFT):Timefromthestartofgenerationtotheproduc-
tionofthefirsttoken.
• Time per Output Token (TPOT):Averagetimetogenerateeachoutputtoken
afterthefirst.
4.1 Setup
The efficiency experiment depends on both the size of the model and the tokenizer’s
vocabularysize. WeusedLlama-3.1-8B-InstructwiththeLlamacppinferenceengine
as backend for Outlines, Guidance, and Llamacpp. As XGrammar doesn’t support
Llamacpp as backend , we add an additional experiment with the Hugging Face
Transformers inference engine for XGrammar. All experiments are conducted on a
singleNVIDIA A100-SXM4-80GB GPUwithAMD EPYC 7543 (12 cores)CPU.The
batchsizeissetto1forallexperiments. Additionaldetailsaboutsetupareprovidedin
theAppendixE.WealsoprovideasnippetofhowwecalleachengineintheAppendixG.
Addressing coverage bias. Theefficiencymetricsaremeaningfulonlyforinstances
thatagrammarenginecanprocess. Differentenginesexhibitvaryinglevelsofschema
3The$schemakeyword,definedintheJSONSchemaspecification,allowsanyschematoself-
identifywhichversionofJSONSchemaitiswrittenfor.
5

coverage,withsomeengineshandlingawiderrangeofschemasthanothers. Engines
withlowercoverageoftenprocesssimpler,shorterschemas,whichnaturallycompile
andgeneratefaster. Asaresult,averagingefficiencymetricsacrosscoveredinstances
canintroducebiasfavoringengineswithlowercoverage. Foramoredetaileddiscussion
oncoverage,seeSection5. Toensurefairness,wecalculateefficiencymetricsonthe
intersectionofcoveredinstancesacrossallengines.
Table 2: Efficiency metrics for different engines with LlamaCpp as the inference
engine. GCT:GrammarCompilationTime,TTFT:TimetoFirstToken,TPOT:TimePer
OutputToken. BoldvaluesindicatethesmallestineachcolumnforGCT,TTFT,andTPOT.
Allvaluesaremedianofthesamples. ResultsfortheGitHubHardandWashingtonPost
datasetsareprovidedinAppendixE.
| Dataset      | Framework | GCT(s) TTFT(s) | TPOT(ms) |       |
| ------------ | --------- | -------------- | -------- | ----- |
| GlaiveAI     | LMonly    | NA             | 0.10     | 15.40 |
|              | Guidance  | 0.00           | 0.24     | 6.37  |
|              | Llamacpp  | 0.05           | 0.20     | 29.98 |
|              | Outlines  | 3.48           | 3.65     | 30.33 |
| GitHubEasy   | LMonly    | NA             | 0.10     | 15.83 |
|              | Guidance  | 0.00           | 0.34     | 7.44  |
|              | Llamacpp  | 0.05           | 0.18     | 27.22 |
|              | Outlines  | 3.71           | 3.97     | 39.78 |
| Snowplow     | LMonly    | NA             | 0.11     | 16.23 |
|              | Guidance  | 0.00           | 0.28     | 6.55  |
|              | Llamacpp  | 0.05           | 0.20     | 28.90 |
|              | Outlines  | 3.91           | 4.14     | 42.66 |
| GitHubMedium | LMonly    | NA             | 0.20     | 16.68 |
|              | Guidance  | 0.01           | 0.54     | 7.57  |
|              | Llamacpp  | 0.06           | 0.30     | 29.08 |
|              | Outlines  | 8.05           | 8.38     | 46.57 |
| Kubernetes   | LMonly    | NA             | 0.16     | 15.32 |
|              | Guidance  | 0.01           | 0.45     | 9.47  |
|              | Llamacpp  | 0.05           | 0.28     | 28.04 |
|              | Outlines  | 5.29           | 5.55     | 46.10 |
Grammar compilation time. Therearenotabledifferencesingrammarcompilation
times between the engines. Both Guidance and Llamacpp dynamically compute their
constraintsduringtokengeneration,leadingtominimalgrammarcompilationtime. In
themiddle,XGrammardoesincludeanon-trivialcompilationstep,buttheyareableto
largely mitigate its impact by running it concurrently with prompt pre-filling. Finally
Outlines,whichconvertsJSONschemasintoregular-expressionbasedconstraints,has
significantlyhighercompilationtime.
Time per output token. While Outlines and Llamacpp demonstrate substantially
lowerthroughputthantheLM-onlyapproach,Guidanceachievesevenhigherefficiency,
fast-forwarding4
which it accomplishes by certain generation steps with its guidance
acceleration [GuidanceAI,2024b]. ComparingGuidanceandXGrammarwiththeHF
TransformersbackendshowsthatGuidancehasasignificantlybetterTPOT.
5 Coverage
Each constrained decoding framework has limitations when it comes to translating
JSONschemasintoasetofconstraintsthatcanreliablyguaranteethevalidityofLM
outputs. To systematically evaluate the effectiveness of these frameworks, we define
threenotionsofcoverage:
4SeeTables13and14forthenumberoftokensfast-forwardedintheexperiments.
6

Table 3: As XGrammar doesn’t support llama.cpp, we add an additional experiment
withtheHugging Face TransformersinferenceengineforXGrammarandGuidance.
Allvaluesaremedianoftheresultsamples.
| Dataset       | Framework |     | GCT (s) | TTFT (s) | TPOT (ms) |     |
| ------------- | --------- | --- | ------- | -------- | --------- | --- |
| GlaiveAI      | Guidance  |     | 0.01    | 0.36     | 36.92     |     |
|               | XGrammar  |     | 0.12    | 0.30     | 66.78     |     |
| GitHub Easy   | Guidance  |     | 0.01    | 0.37     | 42.03     |     |
|               | XGrammar  |     | 0.11    | 0.33     | 65.57     |     |
| GitHub Medium | Guidance  |     | 0.01    | 0.55     | 44.21     |     |
|               | XGrammar  |     | 0.20    | 0.48     | 65.51     |     |
| GitHub Hard   | Guidance  |     | 0.01    | 0.73     | 35.88     |     |
|               | XGrammar  |     | 0.30    | 0.65     | 65.20     |     |
Definition 5.1 (Declared Coverage) Aschemaisconsidereddeclaredcoveredifthe
frameworkprocessestheschemawithoutexplicitlyrejectingitorencounteringruntime
errorssuchasexceptionsorcrashes.
Definition 5.2 (Empirical Coverage) Aschemaisconsideredempiricallycoveredif
our experiments show that the constraints generated by the framework result in LM
outputsthatareschema-compliant.
Definition 5.3 (True Coverage) A schema is considered truly covered if the frame-
workproducesconstraintsthatarepreciselyequivalenttotheoriginalJSONSchema
definition,i.e.,permittingallschema-compliantgenerationswhilerejectingallschema-
noncompliantgenerations.
C
The most ideal coverage metric is the true coverage, denoted as True . However, due
totheinfinitenumberofJSONinstancesthatcouldbevalidatedagainstaschema,itis
difficulttomeasureinpracticewithoutaformalverificationmethodthatiscapableof
exhaustivelycomparingtheschema’ssemanticsagainsttheframework’simplementation.
C isanapproximationofC asitonlycheckswhetherthefinitelymanyoutputs
| Empirical | True |     |     |     |     |     |
| --------- | ---- | --- | --- | --- | --- | --- |
seenduringourexperimentsconformtoagivenschema5.
While C is not an estimate of C per se, it is an upper-bound of both C
| Declared |     | True |     |     |     | Empirical |
| -------- | --- | ---- | --- | --- | --- | --------- |
and C True and is useful in deriving an additional metric from the coverage evaluation:
Compliance Rate=C /C . TheComplianceRate estimatesthereliability
Empirical Declared
oftheconstraineddecodingframeworkinguaranteeingcompliancegivenitacceptsa
givenschema.
5.1 Setup
To measure empirical coverage, we conduct all experiments using the Llama-3.2-1B-
Instructmodelasitissmallenoughtorunefficientlywhilestillproducinghigh-quality
outputs. Thepromptconsistsofasimpleinstructionwithtwo-shotexamples(Figure3),
andvalidationisperformedusingthejsonschemaPythonlibrary(Berman[2025])(using
JSONSchemaDraft2020-12)withstring-formatchecksenabled. Weusegreedydecoding
with zero-temperature, performing a single generation run, and enforce a 40-second
timeoutforgrammarcompilationandanadditional40secondsforgeneration. Exceeding
theselimitsistreatedasaschemaprocessingfailure. Additionaldetailsareprovidedin
AppendixB.
5Additionally,wedefinetheoreticalcoverage
astheproportionofschemaswhosefeaturesare
fullysupportedbythegrammarengine,withdetailsprovidedinAppendixC.
7

5.2 Results
Empirical Coverage Guidanceshowsthehighestempiricalcoverageonsixoutofthe
eightdatasets,withLlamacpptakingtheleadontheremainingtwo: thedomain-specific
WashingtonPostandnotablyhardJSONSchemaStore. Ontheotherhand,closed-source
grammarenginesconsistentlyhavethelowestcoverage;theycameinlastonallbutone
dataset. LM-only6 approachesachieveacceptablecoverageoneasy-to-mediumdatasets
butshowsignificantperformancedropsonharderdatasets,suchasGithubHardand
JSONSchemaStore,aswellasdomain-specificdatasetslikeWashingtonPost. Wenote
that while empirical coverage is a reasonable indicator of a framework’s real-world
performance, it is influenced by factors such as the LM being used and the sampling
methodsemployed.
Compliance Rate Amongopen-sourceengines,guidanceconsistentlydemonstrates
thehighestcompliancerateacrossalldatasets,makingitthemostreliableoptionfor
ensuring schema compliance. Outlines has a comparatively lower compliance rate,
primarilyduetotimeoutsduringgeneration. OuranalysisrevealsthatJSONSchema
features like ‘minItems‘, ‘maxItems‘, ‘enum‘, and ‘Array’, while supported, often take
40secondsto10minutesforOutlinestoprocess. LM-onlyexhibitsthelowestcompli-
ance rate, highlighting its unreliability as a standalone solution. While closed-source
implementations have low empirical coverage, they have very high compliance rates,
indicatingthattheirprovidershavetakenamoreconservativestrategy,implementing
onlyasubsetofJSONSchemafeaturesthattheycanreliablysupport.
5.3 JSON Schema Test Suite: Complementary Evaluation
OriginallydesignedtotestthecorrectnessandcomplianceofJSONSchemavalidation
implementations, the official JSON Schema Test Suite [JSON Schema Org, 2024] is a
comprehensivecollectionoftestcasesspanningthemanyfeaturesoftheJSONSchema
specification. Webelievethatthetestsuiteisanidealtoolforassessingthecorrectness
ofgrammarengines.
Thetestsuiteorganizesitstestcasesinto45categories,eachofwhichcorrespondsto
a feature of JSON Schema, typically a specific keyword such as required or group of
tightlyrelatedkeywordssuchasif-then-else. Asmallnumberofadditionalcategories
testbroaderbehaviors,suchasinfinite-loop-detection. Eachtestcasecontainsa
singleschemapairedwithacollectionofJSONinstancesthataremarkedaseithervalid
orinvalidunderthatschema. Forthepurposeofevaluatingcoverage,weassertthat
anenginemustsuccessfullygenerateeachvalidinstanceandblockgenerationofeach
invalidinstanceto“pass”atestcase. Inadditiontocompilationfailures,wedefinetwo
failuremodesthatagrammarenginecanexhibit:
Definition 5.4 (Over-constrained) Aframeworkis over-constrainedifitrejectsJSON
instancesthatarevalidaccordingtoagivenJSONSchema. Thismeanstheengineis
toostrictandexcludesoutputsthatshouldbeallowed.
Definition 5.5 (Under-constrained) A framework is under-constrained if it allows
JSON instances that are invalid according to a given JSON Schema. This means the
engineisoverlypermissiveandallowsoutputsthatshouldberejected.
AnillustrationisgiveninFigure5inAppendixD.Over-constrained grammarengines
risk limiting the expressive power of LMs, potentially preventing the generation of
valid responses andnegatively impacting downstream task performance. Conversely,
under-constrained engines cannot guarantee that all responses will be valid, often
necessitatingadditionalpost-processingorretrylogic.
6TheLlama3.1modelshavebeenspecificallyfine-tunedtoadheretoJSONschemas[Grattafiori
etal.,2024]
8

Table4: Coverage of all the frameworksonJSONSchemaBench. Empiricalcoverage
betweenOpenSourceenginesandOpenAI/Geminiarenotdirectlycomparabledueto
differencesintheunderlyingmodel(Llama3.2-1Bvs. proprietarymodels).
∗ Geminiresultsareommittedfordatasetsuiteswith<1%support.
| Dataset    | Framework | Declared | Empirical | ComplianceRate |      |
| ---------- | --------- | -------- | --------- | -------------- | ---- |
| GlaiveAI   | LMonly    | 1.00     | 0.90      |                | 0.90 |
|            | Guidance  | 0.98     | 0.96      |                | 0.98 |
|            | Llamacpp  | 0.98     | 0.95      |                | 0.97 |
|            | Outlines  | 0.99     | 0.95      |                | 0.96 |
|            | XGrammar  | 1.00     | 0.93      |                | 0.93 |
|            | OpenAI    | 0.89     | 0.89      |                | 1.00 |
|            | Gemini    | 0.86     | 0.86      |                | 1.00 |
| GitHubEasy | LMonly    | 1.00     | 0.65      |                | 0.65 |
|            | Guidance  | 0.90     | 0.86      |                | 0.96 |
|            | Llamacpp  | 0.85     | 0.75      |                | 0.88 |
|            | Outlines  | 0.86     | 0.59      |                | 0.83 |
|            | XGrammar  | 0.91     | 0.79      |                | 0.87 |
|            | OpenAI    | 0.30     | 0.29      |                | 0.97 |
|            | Gemini    | 0.08     | 0.07      |                | 0.88 |
Snowplow∗
|     | LMonly   | 1.00 | 0.46 |     | 0.46 |
| --- | -------- | ---- | ---- | --- | ---- |
|     | Guidance | 0.87 | 0.82 |     | 0.94 |
|     | Llamacpp | 0.92 | 0.74 |     | 0.81 |
|     | Outlines | 0.95 | 0.36 |     | 0.61 |
|     | XGrammar | NA   | NA   |     | NA   |
|     | OpenAI   | 0.21 | 0.21 |     | 1.00 |
GitHubMedium∗
|                 | LMonly   | 1.00 | 0.38 |     | 0.38 |
| --------------- | -------- | ---- | ---- | --- | ---- |
|                 | Guidance | 0.79 | 0.69 |     | 0.87 |
|                 | Llamacpp | 0.77 | 0.57 |     | 0.74 |
|                 | Outlines | 0.72 | 0.29 |     | 0.40 |
|                 | XGrammar | 0.79 | 0.52 |     | 0.66 |
|                 | OpenAI   | 0.13 | 0.12 |     | 0.92 |
| Kubernetes∗     | LMonly   | 1.00 | 0.56 |     | 0.56 |
|                 | Guidance | 0.98 | 0.91 |     | 0.92 |
|                 | Llamacpp | 0.98 | 0.76 |     | 0.78 |
|                 | Outlines | 0.98 | 0.57 |     | 0.58 |
|                 | XGrammar | 0.12 | 0.07 |     | 0.58 |
|                 | OpenAI   | 0.21 | 0.21 |     | 1.00 |
| WashingtonPost∗ | LMonly   | 1.00 | 0.40 |     | 0.40 |
|                 | Guidance | 0.86 | 0.86 |     | 1.00 |
|                 | Llamacpp | 0.97 | 0.94 |     | 0.97 |
|                 | Outlines | 0.97 | 0.22 |     | 0.23 |
|                 | XGrammar | 0.85 | 0.64 |     | 0.75 |
|                 | OpenAI   | 0.13 | 0.13 |     | 1.00 |
GitHubHard∗
|     | LMonly   | 1.00 | 0.13 |     | 0.13 |
| --- | -------- | ---- | ---- | --- | ---- |
|     | Guidance | 0.60 | 0.41 |     | 0.69 |
|     | Llamacpp | 0.61 | 0.39 |     | 0.63 |
|     | Outlines | 0.47 | 0.03 |     | 0.06 |
|     | XGrammar | 0.69 | 0.28 |     | 0.41 |
|     | OpenAI   | 0.09 | 0.09 |     | 1.00 |
JsonSchemaStore∗
|     | LMonly   | 1.00 | 0.21 |     | 0.21 |
| --- | -------- | ---- | ---- | --- | ---- |
|     | Guidance | 0.35 | 0.30 |     | 0.88 |
|     | Llamacpp | 0.54 | 0.38 |     | 0.69 |
|     | Outlines | 0.38 | 0.09 |     | 0.24 |
|     | XGrammar | 0.76 | 0.33 |     | 0.43 |
|     | OpenAI   | 0.06 | 0.06 |     | 1.00 |
9

5.3.1 Results
Coverage Analysis For each grammar engine and category in the test suite, we
calculatetestcoverage astheproportionofpassingtestcases,reportedinFigure6in
Appendix D Additionally, Table 5 aggregates these metrics, counting categories with
minimalcoverage(>0%),partialcoverage(>25%),moderatecoverage(>50%),high
coverage(>75%),andfullcoverage(100%). Weindicatethenumberofcategoriesfor
whicheachframeworkachievesthehighesttestcoverage(eitherasthesinglehighest
orasthesoleleader)aswellasthenumberofcategoriesforwhicheachframeworkis
thesoleleader.
• Overall Performance: Guidance outperforms other engines at all coverage
levels,achievingfullcoverageon13categoriesandmoderatecoverageon21. In
comparison,LlamacppandXGrammarhavefullcoverageononlyonecategory
andmoderatecoverageonfiveandthreecategories,respectively,whileOutlines
hasnofullcoverageonanycategoryandmoderatecoverageontwocategories.
• Single Highest: Guidance has the single highest coverage in 19 categories,
followedbyXGrammarwith10,andOutlineswithone,andLlamacppwithnone.
Table 5: Number of categories with a given level of coverage. Each row represents
a cumulative coverage threshold, with higher thresholds indicating stricter levels of
success. Boldnumbersindicatetheframeworkwiththehighestvalueinthatrow.
| Coverage               |     | Outlines | Llamacpp |     | XGrammar | Guidance |
| ---------------------- | --- | -------- | -------- | --- | -------- | -------- |
| Minimalcoverage(>0%)   |     | 20       |          | 21  | 28       | 30       |
| Partialcoverage(>25%)  |     | 11       |          | 11  | 16       | 25       |
| Moderatecoverage(>50%) |     | 2        |          | 5   | 3        | 21       |
| Highcoverage(>75%)     |     | 0        |          | 2   | 1        | 17       |
| Fullcoverage(100%)     |     | 0        |          | 1   | 1        | 13       |
| Tiedforhighest(>0%)    |     | 4        |          | 6   | 14       | 25       |
| Singlehighest          |     | 1        |          | 0   | 10       | 19       |
Failure Analysis Table6providesabreakdownoffailuremodesforeachframework
acrossthetestsuite,detailingthenumberofcategorieswithcompilationerrors,failures
togeneratepositiveinstances(over-constrained),andfailurestoblocknegativeinstances
(under-constrained).
Table 6: Number of categories for which each failure type occurred at least once.
Columnsdonotnecessarilysumtothetotalnumberofcategories,assomecategories
may have more than one failure type or no failures at all. Bold numbers indicate the
frameworkwiththefewestnumberoffailuresofagiventype.
| Failuretype       | Outlines |     | Llamacpp | XGrammar |     | Guidance |
| ----------------- | -------- | --- | -------- | -------- | --- | -------- |
| CompileError      | 42       |     | 37       |          | 3   | 25       |
| Over-constrained  | 16       |     | 18       |          | 5   | 7        |
| Under-constrained |          | 8   | 7        | 38       |     | 1        |
Overall,Guidancedemonstratesthefewesttotalfailures,inparticularminimizingunder-
constrainederrors. Outlines,Llamacpp,andGuidancefollowaconsistentfailurepattern,
withmosterrorsoccurringduringcompilationandover-constrainedfailuresbeingmore
frequentthanunder-constrainedones. Incontrast,XGrammarminimizescompilation
errorsbutshowsthehighestnumberofunder-constrainedfailures,indicatingatrade-off
favoringpermissiveness.
We acknowledge that there is no straightforward correspondence between test suite
performance and empirical coverage. One reason for this is that not all features are
10

equally represented in real-world schemas. As a result, strong or weak performance
onspecificfeaturescanhavedisproportionateimpactsdependingontheirprevalence.
Another reason is under-constraining effectively delegates responsibility to the LM,
whichmayproducevalidoutputdespitealackofstrictconstraints. Weemphasizethat
whileunder-constrainingcanbealegitimatestrategy,itrequirescarefulimplementation
andtransparencytoensurereliability.
6 Quality
Inprinciple,constraineddecodingshouldnotaffectthequalityofthegeneratedoutput
asitonlyfiltersouttheinvalidtokens. However,thingsbecomemorecomplicateddueto
ambiguityoftokenization[Vivien,2024;GuidanceAI,2024a;Gengetal.,2024]andthe
distributionalshiftscausedbytheintervention[Gengetal.,2023;Tametal.,2024]. As
ahypotheticaltoyexample,anLMmightanswer‘89,000’insteadofthecorrect‘89000’
inaGSM8Kquestion. Constraineddecodingcanblocktheinvalidtoken‘,’,enforcing
structural compliance but potentially may cause the LM to go out of distribution and
generate‘890000’instead. Kurt[2024b]arguedthattheperformancedeclineobserved
in previous studies [Tam et al., 2024] comes from inadequate prompting, insufficient
contextualinformation,andpoorlycraftedschemas.
6.1 Setup
Kurt[2024b];Tametal.[2024]haveintroducedaseriesoftaskstoinvestigatepoten-
tial quality concerns in constrained decoding, which we leverage and extend in this
benchmark. Specifically, we adopt the three reasoning tasks from these studies to
evaluatetheimpactofconstraineddecodingontaskaccuracy,asdetailedinTable7. The
simpleoutputstructureofthesetaskswasdesignedtoisolatetheeffectsofconstrained
decodingonreasoning,asoutlinedbyTametal.[2024].
Forourexperiments,weusetheLlama-3.1-8B-Instructmodeltomeasuretaskperfor-
mance. WefollowtheoriginalsetupandpromptspecificationsfromKurt[2024b],with
fulldetailsprovidedinAppendixF.
Table7: TaskDescriptionsandStructures
| Task        |     | Example                | Structure    | Metric    |
| ----------- | --- | ---------------------- | ------------ | --------- |
| Last Letter |     | Input: IanPeterBernard | CoTreasoning | Case-     |
|             |     | Stephen                | +answerin    | sensitive |
a−z
|     |     | Output: nrdn |     | exactmatch |
| --- | --- | ------------ | --- | ---------- |
Shuffle Objects Input: Sequenceofexchanges CoTreasoning Exactmatch
|       |     | amongindividuals+choices | +answerin    |            |
| ----- | --- | ------------------------ | ------------ | ---------- |
|       |     | Output: A-E              | A−E          |            |
| GSM8K |     | Input: Basiccaculation   | CoTreasoning | Number     |
|       |     | problems                 | +answeras    | exactmatch |
|       |     | Output: Number,e.g.      | 8 integer    |            |
We implement the following constraints for the first three tasks: (1) Last Letter the
outputneedstobeaconcatenationoflettersfroma-z;(2) Shuffle Objectstheoutput
needs to be a single letter from A-E enclosed in parentheses; (3) GSM8K the output
is an valid integer or float number. The outputs for all three tasks are structured as
JSONobjectswithtwofields: "reasoning"and"answer",formattedas{"reasoning":
| <reasoning | about the | answer>, "answer": | <final answer>}. |     |
| ---------- | --------- | ------------------ | ---------------- | --- |
11

6.2 Results
TheresultsinTable8showthattheconstraineddecoding,regardlessoftheframework,
achieveshigherperformancethantheunconstrainedsetting. Amongtheframeworks
evaluated,Guidanceconsistentlydeliversthebestperformanceacrossalltasks,with
approximatelya3%improvementovertheLM-onlyapproachineverytask. Webelieve
thismaybeattributedtoitstoken-healingimplementation[GuidanceAI,2024a].
Table8: PerformancePercentagesforVariousModels
Last Letters Shuffle Objects GSM8K
LM only 50.7% 52.6% 80.1%
XGrammar 51.2% 52.7% 83.7%
Llamacpp 52.0% 52.6% 82.4%
Outlines 53.3% 53.0% 81.6%
Guidance 54.0% 55.9% 83.8%
7 Conclusion
We have proposed a comprehensive evaluation framework for constrained decoding
frameworkswithJSONschemas,focusingonefficiency,coverage,andoutputquality. We
introducedJSONSchemaBench,abenchmarkcomprising10Kreal-worldJSONschemas,
to enable robust assessment under realistic conditions. Our evaluation highlights
boththeadvancementsandlimitationsofcurrentstate-of-the-artconstraineddecoding
frameworks. Wehopethatourfindingsandbenchmarkwillinformfutureresearchin
structuredgenerationandprovidevaluableinsightstohelpthecommunityidentifythe
mosteffectivetoolsandtoextendcapabilitieswithconstraineddecoding.
Acknowledgements WewouldliketoexpressourgratitudetoJundaChen(UCSD),
Paul Koch (Microsoft), and Shuqi Wang (EPFL) for their valuable help and insightful
discussions,Ana-MariaIndreias(EPFL)forherassistancewithdatavisualization,and
ZhengZhou(independentresearcher)forresolvingGPU-relatedissues.
References
SnowplowAnalytics. Iglucentral. https://github.com/snowplow/iglucentral,2022.
Commithash726168e.Retrieved19September2022.
Lyes Attouche, Mohamed-Amine Baazizi, Dario Colazzo, Giorgio Ghelli, Carlo Sar-
tiani, and Stefanie Scherzinger. Witness Generation for JSON Schema. Proceed-
ingsoftheVLDBEndowment,15(13):4002–4014,September2022. ISSN2150-8097.
doi: 10.14778/3565838.3565852.URLhttps://dl.acm.org/doi/10.14778/3565838.
3565852.
Mohamed Amine Baazizi, Dario Colazzo, Giorgio Ghelli, Carlo Sartiani, and Ste-
fanieScherzinger. Ajsonschemacorpus,2021. https://github.com/sdbs-uni-p/
json-schema-corpus.
Julian Berman. python-jsonschema. https://github.com/python-jsonschema/
jsonschema,2025. URLhttps://github.com/python-jsonschema/jsonschema. Ac-
cessed: 2025-01-05.
LucaBeurer-Kellner,MarcFischer,andMartinVechev. PromptingIsProgramming: A
QueryLanguageforLargeLanguageModels.ProceedingsoftheACMonProgramming
Languages,7(PLDI):1946–1969,June2023. ISSN2475-1421. doi: 10.1145/3591300.
URLhttp://arxiv.org/abs/2212.06094. arXiv:2212.06094[cs].
12

Bowtie. Bowtie: Ameta-validatorofthejsonschemaspecification,2025. URLhttps:
//github.com/bowtie-json-schema/bowtie/. DOI:10.5281/zenodo.14646449.
Daniel Deutsch, Shyam Upadhyay, and Dan Roth. A General-Purpose Algorithm for
Constrained Sequential Inference. In Proceedings of the 23rd Conference on Com-
putational Natural Language Learning (CoNLL), pp. 482–492, Hong Kong, China,
2019. Association for Computational Linguistics. doi: 10.18653/v1/K19-1045. URL
https://www.aclweb.org/anthology/K19-1045.
Yixin Dong, Charlie F. Ruan, Yaxing Cai, Ruihang Lai, Ziyi Xu, Yilong Zhao, and
Tianqi Chen. XGrammar: Flexible and Efficient Structured Generation Engine for
LargeLanguageModels,November2024. URLhttp://arxiv.org/abs/2411.15100.
arXiv:2411.15100[cs].
SaiboGeng,MartinJosifoski,MaximePeyrard,andRobertWest. Grammar-constrained
decodingforstructuredNLPtaskswithoutfinetuning. InHoudaBouamor,JuanPino,
andKalikaBali(eds.),Proceedingsofthe2023ConferenceonEmpiricalMethodsin
NaturalLanguageProcessing,pp.10932–10952,Singapore,December2023.Asso-
ciationforComputationalLinguistics. doi: 10.18653/v1/2023.emnlp-main.674. URL
https://aclanthology.org/2023.emnlp-main.674.
SaiboGeng,SankalpGambhir,ChrisWendler,andRobertWest. Bytebpetokenizationas
aninversestringhomomorphism,2024. URLhttps://arxiv.org/abs/2412.03160.
GeorgiGerganovandal. Llama.cpp: Aportoffacebook’sllamamodelinc++. https:
//github.com/ggerganov/llama.cpp,2023. Accessed: 2025-01-16.
GlaiveAI. Glaive function calling dataset. https://huggingface.co/datasets/
glaiveai/glaive-function-calling,2024. Accessed: 2024-12-21.
AaronGrattafiori,AbhimanyuDubey,AbhinavJauhri,AbhinavPandey,AbhishekKadian,
AhmadAl-Dahle,AieshaLetman,AkhilMathur,AlanSchelten,andAlexVaughanetal.
Thellama3herdofmodels,2024. URLhttps://arxiv.org/abs/2407.21783.
Guidance AI. Guidance: A language model programming framework, 2023. URL
https://github.com/guidance-ai/guidance. Accessed: 2024-12-18.
GuidanceAI.Promptboundariesandtokenhealing.https://github.com/guidance-ai/
guidance/blob/main/notebooks/art_of_prompt_design/prompt_boundaries_
and_token_healing.ipynb,2024a. Accessed: 2024-12-21.
GuidanceAI. Guidanceaccelerationtutorial. https://guidance.readthedocs.io/en/
stable/example_notebooks/tutorials/guidance_acceleration.html, 2024b. Ac-
cessed: 2025-01-16.
JSON Schema Org. Json schema test suite. https://github.com/json-schema-org/
JSON-Schema-Test-Suite, 2024. URL https://github.com/json-schema-org/
JSON-Schema-Test-Suite. Accessed: 2024-12-19.
Kubernetes. Kubernetes json schemas. https://github.com/instrumenta/
kubernetes-json-schema,2022. Commithash133f848.
Michael Kuchnik, Virginia Smith, and George Amvrosiadis. Validating Large Lan-
guage Models with ReLM, May 2023. URL http://arxiv.org/abs/2211.15458.
arXiv:2211.15458[cs].
Will Kurt. Coalescence: Making llm inference 5x faster. https://blog.dottxt.co/
coalescence.html,2024a. Accessed: 2024-12-21.
WillKurt. Saywhatyoumean: Aresponseto’letmespeakfreely’,2024b. URLhttps:
//.txt.co/blog/say-what-you-mean-a-response-to-let-me-speak-freely.
13

Michael Xieyang Liu, Frederick Liu, Alexander J. Fiannaca, Terry Koo, Lucas Dixon,
Michael Terry, and Carrie J. Cai. "We Need Structured Output": Towards User-
centered Constraints on Large Language Model Output. In Extended Abstracts
of the CHI Conference on Human Factors in Computing Systems, pp. 1–9, May
2024. doi: 10.1145/3613905.3650756. URL http://arxiv.org/abs/2404.07362.
arXiv:2404.07362[cs].
Gabriel Poesia, Oleksandr Polozov, Vu Le, Ashish Tiwari, Gustavo Soares, Christo-
pher Meek, and Sumit Gulwani. Synchromesh: Reliable code generation from pre-
trained language models, January 2022. URL http://arxiv.org/abs/2201.11227.
arXiv:2201.11227[cs].
Maciej P. Polak and Dane Morgan. Extracting accurate materials data from research
paperswithconversationallanguagemodelsandpromptengineering. NatureCommu-
nications,15(1),February2024. ISSN2041-1723. doi: 10.1038/s41467-024-45914-8.
URLhttp://dx.doi.org/10.1038/s41467-024-45914-8.
TheWashingtonPost. ans-schema. https://github.com/washingtonpost/ans-schema,
2022. Commithashabdd6c211.Retrieved19September2022.
SubhroRoy,SamThomson,TongfeiChen,RichardShin,AdamPauls,JasonEisner,and
BenjaminVanDurme. BenchCLAMP:ABenchmarkforEvaluatingLanguageModels
onSyntacticandSemanticParsing,January2024. URLhttp://arxiv.org/abs/2206.
10668. arXiv:2206.10668[cs].
Schema Store Org. The largest collection of independent json schemas in the world.
https://www.schemastore.org/json/,2014. AuniversalJSONschemastorewhere
schemasforpopularJSONdocumentscanbefound.Contributionsarewelcome;see
CONTRIBUTING.mdformoreinformation.
Timo Schick, Jane Dwivedi-Yu, Roberto Dessi, Roberta Raileanu, Maria Lomeli, Eric
Hambro, Luke Zettlemoyer, Nicola Cancedda, and Thomas Scialom. Toolformer:
Language Models Can Teach Themselves to Use Tools. In A. Oh, T. Naumann,
A. Globerson, K. Saenko, M. Hardt, and S. Levine (eds.), Advances in Neu-
ral Information Processing Systems, volume 36, pp. 68539–68551. Curran Asso-
ciates, Inc., 2023. URL https://proceedings.neurips.cc/paper_files/paper/
2023/file/d842425e4bf79ba039352da0f658a906-Paper-Conference.pdf.
Torsten Scholak, Nathan Schucher, and Dzmitry Bahdanau. PICARD: Parsing incre-
mentallyforconstrainedauto-regressivedecodingfromlanguagemodels. InMarie-
FrancineMoens,XuanjingHuang,LuciaSpecia,andScottWen-tauYih(eds.),Proceed-
ingsofthe2021ConferenceonEmpiricalMethodsinNaturalLanguageProcessing,
pp.9895–9901,OnlineandPuntaCana,DominicanRepublic,November2021.Asso-
ciationforComputationalLinguistics. doi: 10.18653/v1/2021.emnlp-main.779. URL
https://aclanthology.org/2021.emnlp-main.779/.
RichardShin,ChristopherLin,SamThomson,CharlesChen,SubhroRoy,EmmanouilAn-
tonios Platanios, Adam Pauls, Dan Klein, Jason Eisner, and Benjamin Van Durme.
Constrained Language Models Yield Few-Shot Semantic Parsers. In Proceedings
ofthe2021ConferenceonEmpiricalMethodsinNaturalLanguageProcessing,pp.
7699–7715, Online and Punta Cana, Dominican Republic, November 2021. Associ-
ation for Computational Linguistics. doi: 10.18653/v1/2021.emnlp-main.608. URL
https://aclanthology.org/2021.emnlp-main.608.
ZhiRuiTam,Cheng-KuangWu,Yi-LinTsai,Chieh-YenLin,Hung-yiLee,andYun-Nung
Chen. Let me speak freely? a study on the impact of format restrictions on large
language model performance. In Franck Dernoncourt, Daniel Preo¸tiuc-Pietro, and
AnastasiaShimorina(eds.),Proceedingsofthe2024ConferenceonEmpiricalMethods
inNaturalLanguageProcessing: IndustryTrack,pp.1218–1236,Miami,Florida,US,
14

November2024.AssociationforComputationalLinguistics. doi: 10.18653/v1/2024.
emnlp-industry.91. URLhttps://aclanthology.org/2024.emnlp-industry.91/.
Xiangru Tang, Yiming Zong, Jason Phang, Yilun Zhao, Wangchunshu Zhou, Arman
Cohan, and Mark Gerstein. Struc-Bench: Are Large Language Models Good at
Generating Complex Structured Tabular Data? In Kevin Duh, Helena Gomez, and
Steven Bethard (eds.), Proceedings of the 2024 Conference of the North Ameri-
can Chapter of the Association for Computational Linguistics: Human Language
Technologies (Volume 2: Short Papers), pp. 12–34, Mexico City, Mexico, June 2024.
AssociationforComputationalLinguistics. doi: 10.18653/v1/2024.naacl-short.2. URL
https://aclanthology.org/2024.naacl-short.2.
Vivien. Llm decoding with regex constraints. https://vivien000.github.io/blog/
journal/llm-decoding-with-regex-constraints.html,2024. Accessed: 2024-12-
21.
BailinWang,ZiWang,XuezhiWang,YuanCao,RifASaurous,andYoonKim. Grammar
PromptingforDomain-SpecificLanguageGenerationwithLargeLanguageModels.
Brandon T. Willard and Rémi Louf. Efficient Guided Generation for Large Language
Models,August2023. URLhttp://arxiv.org/abs/2307.09702. arXiv:2307.09702
[cs].
Austin Wright, Henry Andrews, Ben Hutton, and Greg Dennis. Draft 2020-
12: Json schema core specification. https://json-schema.org/draft/2020-12/
json-schema-core.html, 2022. Published 16 June 2022. Metaschema available at
https://json-schema.org/draft/2020-12/schema.
Shunyu Yao, Howard Chen, Austin W. Hanjie, Runzhe Yang, and Karthik Narasimhan.
COLLIE:SystematicConstructionofConstrainedTextGenerationTasks,July2023a.
URLhttp://arxiv.org/abs/2307.08689. arXiv:2307.08689[cs].
ShunyuYao,JeffreyZhao,DianYu,NanDu,IzhakShafran,KarthikNarasimhan,andYuan
Cao. ReAct: Synergizingreasoningandactinginlanguagemodels. InInternational
ConferenceonLearningRepresentations(ICLR),2023b.
LianminZheng,LiangshengYin,ZhiqiangXie,ChuyueSun,JeffHuang,CodyHaoYu,
ShiyiCao,ChristosKozyrakis,IonStoica,JosephE.Gonzalez,ClarkBarrett,andYing
Sheng. SGLang: EfficientExecutionofStructuredLanguageModelPrograms,June
2024. URLhttp://arxiv.org/abs/2312.07104. arXiv:2312.07104[cs].
A JSON Schema Collections Details
JSONSchemaBench includes a diverse collection of schemas curated from multiple
real-worldapplicationsAttoucheetal.[2022],designedtorepresentawiderangeofuse
cases:
Sources:
• GitHub [Baazizi et al., 2021]: Extractedfromopen-sourcerepositoriescon-
taining schema definitions, representing practical, widely-used applications.
SchemasfromGitHubareofvariouscomplexities,totaling6,000schemas. We
splitthecollectionintotrivial(fewerthan10fields),easy(10–30fields),medium
(30–100fields),hard(100–500fields),andultra(morethan500fields),basedon
thetotalnumberoffieldsineachJSONschematoreflectincreasingcomplexity
andscale.
• Snowplow [Analytics, 2022]: Sourcedfromevent-basedanalyticsframeworks,
showcasingschemastailoredforevent-drivendatastructures.
15

• Kubernetes [Kubernetes, 2022]: Schemas defining configurations for con-
tainerorchestrationsystems,highlightingschemaswithintricatehierarchical
structures.
• WashingtonPost [Post, 2022]: SchemasforTheWashingtonPost’sANSspeci-
fication.
• GlaiveAI2K GlaiveAI [2024]: 2,000schemasextractedfromafunction-calling
| dataset. Eachschemarepresentsafunctionsignature. |     |     |     |     |
| ------------------------------------------------ | --- | --- | --- | --- |
• JSON Schema Store [Schema Store Org, 2014]: The largest collection of
independentJSONschemasintheworld.
| Table9:         | Baiscstatisticsofthedatasetsusedintheexperiments. |            |            |             |
| --------------- | ------------------------------------------------- | ---------- | ---------- | ----------- |
| Dataset         | Count Size(KB)                                    | FieldCount | MaxFan-Out | SchemaDepth |
|                 | Med/Max                                           | Med/Max    | Med/Max    | Med/Max     |
| GlaiveAI-2K     | 1707 0.5/1.2                                      | 21/44      | 4/7        | 5/8         |
| Github-Trivial  | 444 0.2/10.8                                      | 6/9        | 4/9        | 2/6         |
| Github-Easy     | 1943 0.5/20.3                                     | 18/29      | 5/19       | 4/10        |
| Snowplow        | 403 0.9/15.6                                      | 37/450     | 7/131      | 3/13        |
| Github-Medium   | 1976 1.5/58.3                                     | 51/99      | 8/42       | 6/15        |
| Kubernetes      | 1064 2.7/818.6                                    | 41/11720   | 5/600      | 5/7         |
| WashingtonPost  | 125 1.7/81.1                                      | 44/2093    | 7/84       | 4/10        |
| Github-Hard     | 1240 5.1/136.1                                    | 175/498    | 18/133     | 8/25        |
| JSONSchemaStore | 492 5.9/2934.8                                    | 155/108292 | 14/6543    | 6/22        |
| Github-Ultra    | 164 25.8/359.6                                    | 694/6919   | 37/412     | 8/23        |
A.1 Data Processing
To ensure the quality and reliability of JSONSchemaBench, we applied the following
preprocessingsteps:
1. Validation
• Verified schemas conform to the JSON Schema specification using the
jsonschemalibraryinPython,specificallytargetingtheDraft2020-12version.
Dropinvalidschemas.
• IdentifiedadditionalinvalidschemasusingvalidatorsfromRustandJavaScript
libraries.
2. Cleaning
• Deduplicate: Removedduplicateschemastoeliminateredundancyandmain-
tain a diverse dataset. Key ordering within schemas was ignored when deter-
miningduplicates.
• Empty Schema: Excludedschemasthatwerelackingmeaningfulconstraints,
effectively“empty.”
• Unresolved References: Removedschemascontainingunresolved$refrefer-
encestoexternalURLs.
• Schema Version Fixes: Correctedmismatchedormissingdraftversions.
• Extraneous Field Removal: Eliminated unrelated fields such as command,
config,path,andcontrols.
• RegexEscaping: Fixedescapingissuesinregularexpressionstoensurevalidity.
16

• Schema Extraction: Extracted schemas embedded within non-root levels of
JSONfiles.
| A.2 Draft versions |              |          |                              |          |         |         |     |         |
| ------------------ | ------------ | -------- | ---------------------------- | -------- | ------- | ------- | --- | ------- |
|                    | Table10:     |          | JSONSchemaDraftVersionCounts |          |         |         |     |         |
|                    |              | draft-04 | draft-06                     | draft-07 | 2019-09 | 2020-12 |     | unknown |
| Github-easy        |              | 1310     |                              | 54       | 136     | 0       | 5   | 438     |
| Github-hard        |              | 841      |                              | 30       | 87      | 0       | 23  | 259     |
| Github-medium      |              | 1221     |                              | 80       | 140     | 0       | 7   | 528     |
| JsonSchemaStore    |              | 199      |                              | 5        | 268     | 5       | 11  | 4       |
| Kubernetes         |              | 0        |                              | 0        | 0       | 0       | 0   | 1087    |
| Snowplow           |              | 0        |                              | 0        | 0       | 0       | 0   | 408     |
| WashingtonPost     |              | 125      |                              | 0        | 0       | 0       | 0   | 0       |
| Glaiveai2K         |              | 0        |                              | 0        | 0       | 0       | 0   | 1707    |
| total              |              | 4097     |                              | 193      | 706     | 5       | 50  | 5155    |
| A.3 Feature        | Distribution |          |                              |          |         |         |     |         |
Wecounttheappearanceofeachfeature(keyword)inthe10Kschemasandshowthe
mostfrequentfeaturesinFigure2a. Weseparatelyplotusageoftheformatkeyword,
whichisusedtospecifyformatofstringsuchasdate-time,email,uri. Thisisworth
highlighted because each of these formats can be quite complex to implement on its
ownThedistributionofformatsusedisshowninFigure2b.
| (a)FeatureCountinthe10KSchemas |            |                                         |         |     |     | (b)Formatkeyworddistribution |     |     |
| ------------------------------ | ---------- | --------------------------------------- | ------- | --- | --- | ---------------------------- | --- | --- |
|                                | Figure2:   | FeatureandFormatconstraintdistribution. |         |     |     |                              |     |     |
| B Coverage                     | Experiment |                                         | Details |     |     |                              |     |     |
ThepromptingtemplateusedforthecoverageexperimentisshowninFigure3.
17

| Prompt | Template for | JSON Generation |     |
| ------ | ------------ | --------------- | --- |
| System | Message:     |                 |     |
YouneedtogenerateaJSONobjectthatmatchestheschemabelow.
| Demo Examples: |              |         |                      |
| -------------- | ------------ | ------- | -------------------- |
| ## Input       | Schema:[JSON | schema] |                      |
| ## Expected    | Output:[JSON | object  | matching the schema] |
...
Figure3: PrompttemplateusedtogenerateJSONobjectsinthecoverageexperiment.
Decoding Method We use greedy decoding with no top P or top K sampling for all
theexperiments. Weonlygetoneoutputfromthemodel,whichwewillusetovalidate
theschemacompliance. It’stotallyplausibletosamplemoreoutputsandvalidatethem
all,anditmightdetectmoreschemaviolations. Thefactthatweonlysamplethetop1
outputmayquantifyourempiricalcoverage asTop1EmpiricalCoverage.
Validation WeusethejsonschemalibrarywiththeDraft-2020-12versionoftheJSON
Schema standard to validate the generated JSON object. We turn on the ‘format’
checks,whicharenotenabledbydefaultinPython. Strictlyspeaking,thejsonschema
library doesn’t guarantee the validation of all the schema constraints, even with the
‘format’ checks enabled. It is possible, though very rare, for a schema-noncompliant
output to be validated as compliant by the jsonschema library, leading to a slight
overestimationofempiricalcoverage. However,suchoccurrencesarecornercasesand
happeninfrequently.
| C Theoretical | Coverage | Details |     |
| ------------- | -------- | ------- | --- |
Definition C.1 (Theoretical Coverage) Aschemaisconsideredtheoreticallycovered
ifallofitsfeaturesaresupportedbythegrammarengine.
Thetheoreticalcoverage,notedasC
|     |     | Theoretical | ,measurestheproportionofJSONschemas |
| --- | --- | ----------- | ----------------------------------- |
that a grammar engine supports based on its implementation. It doesn’t involve any
modelinferenceorexperimentsandissolelybasedonthegrammarengine’simplemen-
tation. C isanupperbound ofthetruecoverage,whichcannotbeempirically
Theoretical
measured due to the infinite number of possible generations under the schema con-
straints.
Overall,thetheoreticalcoverageprovidesagoodindicationofthegrammarengine’s
capabilitytosupportawiderangeofschemaconstraints.
Inourexperiment,thetheoreticalcoverageforeachframeworkwasdeterminedbased
onthedocumentationandresourceslistedinTable11.
|     | Table11: GrammarEngineDocumentationandResources |     |     |
| --- | ----------------------------------------------- | --- | --- |
Frameworks LibVersion ReleaseDate JSONSchemaSupportDocumentation
| Guidance | 0.2.0rc | 2024.11.26 | LLGuidanceDocumentation |
| -------- | ------- | ---------- | ----------------------- |
Llamacpp 0.3.2 2024.11.16 llama.cppJSONSchematogbnfConversion
| XGrammar | 0.1.6 | 2024.12.07 | XGrammarJSONSchematogbnfConversion |
| -------- | ----- | ---------- | ---------------------------------- |
Outlines 0.1.8 2024.12.06 OutlinesJSONSchematoRegexConversion
| OpenAI | UNK   | UNK        | OpenAIStructuredOutputAPI          |
| ------ | ----- | ---------- | ---------------------------------- |
| Gemini | 0.8.3 | 2024.10.31 | GeminiStructuredOutputContentTypes |
18

| Figure4: | Featurechecklistfordifferentstructuredoutputengines |     |     |     |
| -------- | --------------------------------------------------- | --- | --- | --- |
ThetheoreticalsupportforeachfeatureinJSONSchemaissummarizedinFigure4
Table12: Theoreticalcoverageacrossdatasets.
Dataset LMonly Guidance Llamacpp Outlines XGrammar OpenAI Gemini
| GlaiveAI        | 0.00 0.96 | 0.95 0.95 | 0.87 0.87 | 0.87 |
| --------------- | --------- | --------- | --------- | ---- |
| GitHubEasy      | 0.00 0.87 | 0.83 0.75 | 0.65 0.31 | 0.31 |
| Snowplow        | 0.00 0.80 | 0.74 0.58 | NA 0.29   | NA   |
| GitHubMedium    | 0.00 0.73 | 0.69 0.57 | 0.49 0.22 | NA   |
| Kubernetes      | 0.00 0.58 | 0.58 0.58 | 0.58 0.40 | NA   |
| WashingtonPost  | 0.00 0.70 | 0.64 0.63 | 0.62 0.29 | NA   |
| GitHubHard      | 0.00 0.54 | 0.49 0.38 | 0.33 0.00 | NA   |
| JsonSchemaStore | 0.00 0.31 | 0.24 0.20 | 0.13 0.00 | NA   |
ThetheoreticalcoverageofeachgrammarengineissummarizedinTable12.
19

D JSON Schema Test Suite Experiment Details
Figure5: Illustrationofover-constrainedandunder-constrained.
Weevaluatedeachconstraineddecodingframework’sperformanceontheJSONSchema
TestSuiteusingthefollowingcriteria: aframeworkisconsideredtopassatestcaseifit
permitsgeneratingeveryvalidinstanceinthetestcasewhilepreventingthegeneration
ofeveryinvalidinstance. Sometestcasesconsistexclusivelyofinvalidinstances,such
asthoseinvolvingunsatisfiable schemas,i.e.,schemasforwhichnovalidinstancesexist.
Inthesecases,enginesraisingcompile-timeerrorswereallowedtopass.
Cleaning We removed the ’format’ category of tests, as the current JSON Schema
standardmandatesthatthiskeywordbeignoredentirelybydefault. Thetestsuitecomes
bundledwithan’optional’setoftests,includingtestsforeachofficiallyrecognizedvalue
ofthe’format’keyword. Wehopetoextendthisworktoincludetheseoptionaltestsina
follow-up.
Furthermore, some tests require external resources in the form of JSON schemas
availableataremoteURL.Wedroppedthesetestsfromtheanalysis,astheconstrained
decodinglibrariesdiscussedinthecurrentworkdonotfetchtheseresourcesbydefault.
Afterfilteringoutthesetests,weareleftwith43oftheoriginal45testcategories.
Implementation Tocheckwhetheragivenframeworkacceptsorblocksthegenera-
tionofaparticularJSONinstance,wetokenize7 JSON-serializedformoftheinstance
andwalktheframework’sconstraintsforwardonetokenatatime,essentiallysimulating
thegenerationprocessofanLLMattemptingtoproducethegiventokensequence:
• XGrammardirectlyexposeaninterfaceforupdatingthetokenmaskafterinsert-
ingatokenandcheckingvalidity.
• Outlinesdoesnotexposeapublicinterfaceforinteractingwiththetokenmask,
butoutlines-core,whichoutlinesisbuiltontopof,iseasilyadaptedforthis
purpose.
• Similarly,Guidancedoesnotexposeapublicinterfaceforinteractingwiththe
tokenmask,butllguidance,whichguidanceisbuiltontopof,iseasilyadapted
forthispurpose.
• Llamacpp does not expose this interface, but it shares a common grammar-
specification language with XGrammar. We use llamacpp to generate GGML
BNFandchecktoken-sequencevalidityusingxgrammar’sinterface.
7The particular choice of tokenizer is not particularly important, but we use the Llama 3.1
tokenizerforconsistencywithourotherexperiments.
20

Figure 6: JSON Schema test suite coverage by category. Each cell represents the
proportion of passing tests for a given category-framework pair, with darker shades
indicatinghighercoverage. Asingleasterisk(*)marksframeworkstiedforthehighest
(non-zero)coverage,whileadoubleasterisk(**)markstheframeworkwiththesingle
highestcoverageinthecategory.
21

WeprovidecodesnippetsthatshowtheuseoftheJSONSchemaTestSuitetoassess
the test coverage of each constrained decoding framework. For each framework, we
implementeda‘testharness’accordingtothebaseclassesshowedinlisting1.
Listing2showsthecriteriaforatestcasetopass,whichdependsonalltestsinthecase
topass(listing3). WeshowthedefinitionofTestCaseandTestinlisting4.
Concreteimplementationsofthetestharnessforeachframeworkarereportedinlistings
5,6,7,and8.
class Compiler:
| def __init__(self, |     | model_id: |     | str): |     |     |
| ------------------ | --- | --------- | --- | ----- | --- | --- |
"""
model_id
| Builds        | a Compiler, |             | taking | a huggingface |                  | to provide |
| ------------- | ----------- | ----------- | ------ | ------------- | ---------------- | ---------- |
| configuration |             | information |        | about         | the model and/or | tokenizer. |
"""
| def compile(self, |     | schema: |     | str) -> | Masker: |     |
| ----------------- | --- | ------- | --- | ------- | ------- | --- |
"""
| Compiles | a schema  |     | into   | a masker | used to validate | a stream of |
| -------- | --------- | --- | ------ | -------- | ---------------- | ----------- |
| tokens   | according |     | to the | schema.  |                  |             |
Raises an exception if the framework cannot compile the schema.
"""
class Masker:
| def advance(self, |     | token: | int): |     |     |     |
| ----------------- | --- | ------ | ----- | --- | --- | --- |
"""
| Advances | the          | masker | by  | one token. |                |              |
| -------- | ------------ | ------ | --- | ---------- | -------------- | ------------ |
| Raises   | an exception |        | if  | the token  | is not allowed | by the mask. |
"""
def assert_done(self):
"""
| Asserts | that | the | masker | is either | in a terminal | state or will |
| ------- | ---- | --- | ------ | --------- | ------------- | ------------- |
accept an EOS token, after which it will be in a terminal state.
| Raises | an exception |     | if  | otherwise. |     |     |
| ------ | ------------ | --- | --- | ---------- | --- | --- |
"""
|     |     | Listing1: |     | Abstracttestharness |     |     |
| --- | --- | --------- | --- | ------------------- | --- | --- |
22

do_test_case(test_case:
| def                  |     |       | TestCase, | compiler: | Compiler, | tokenizer: |
| -------------------- | --- | ----- | --------- | --------- | --------- | ---------- |
| (cid:44)→ Tokenizer) | ->  | bool: |           |           |           |            |
try:
|     | masker = | compiler.compile(json.dumps(test_case.schema)) |     |     |     |     |
| --- | -------- | ---------------------------------------------- | --- | --- | --- | --- |
except:
|     | if all(not | test.valid | for test | in test_case.tests): |              |           |
| --- | ---------- | ---------- | -------- | -------------------- | ------------ | --------- |
|     | # Pass:    | compile    | error on | a case with          | only invalid | test data |
|     | return     | True       |          |                      |              |           |
else:
|     | # Fail:   | compile          | error but | schema | has at least | one valid test |
| --- | --------- | ---------------- | --------- | ------ | ------------ | -------------- |
|     | (cid:44)→ | datum            |           |        |              |                |
|     | return    | False            |           |        |              |                |
| for | test in   | test_case.tests: |           |        |              |                |
do_test(test,
|     | passed = |     | tokenizer, | masker.copy()) |     |     |
| --- | -------- | --- | ---------- | -------------- | --- | --- |
if not passed:
|        | # Fail:   | a test       | failed           |     |     |     |
| ------ | --------- | ------------ | ---------------- | --- | --- | --- |
|        | return    | False        |                  |     |     |     |
| #      | Pass: all | tests passed |                  |     |     |     |
| return | True      |              |                  |     |     |     |
|        |           | Listing2:    | Runningatestcase |     |     |     |
def do_test(test: Test, tokenizer: Tokenizer, masker: Masker) -> bool:
| tokens | = tokenizer(json.dumps(test.data),               |     |     |     |     |     |
| ------ | ------------------------------------------------ | --- | --- | --- | --- | --- |
|        | (cid:44)→ add_special_tokens=False)["input_ids"] |     |     |     |     |     |
try:
|     | for token | in tokens: |     |     |     |     |
| --- | --------- | ---------- | --- | --- | --- | --- |
masker.advance(token)
masker.assert_done()
except:
if test.valid:
|     | # Fail: | valid | data was | rejected |     |     |
| --- | ------- | ----- | -------- | -------- | --- | --- |
|     | return  | False |          |          |     |     |
else:
|     | # Pass: | invalid | data was | rejected |     |     |
| --- | ------- | ------- | -------- | -------- | --- | --- |
|     | return  | True    |          |          |     |     |
else:
if test.valid:
|     | # Pass: | valid | data was | accepted |     |     |
| --- | ------- | ----- | -------- | -------- | --- | --- |
|     | return  | True  |          |          |     |     |
else:
|     | # Fail: | invalid | data was  | accepted     |     |     |
| --- | ------- | ------- | --------- | ------------ | --- | --- |
|     | return  | False   |           |              |     |     |
|     |         |         | Listing3: | Runningatest |     |     |
23

| from | pydantic import | BaseModel  |     |     |
| ---- | --------------- | ---------- | --- | --- |
| from | typing import   | Any, Union |     |     |
class TestCase(BaseModel):
| schema: | Union[bool, | dict] |     |     |
| ------- | ----------- | ----- | --- | --- |
| tests:  | list[Test]  |       |     |     |
class Test(BaseModel):
| data:  | Any  |           |                       |     |
| ------ | ---- | --------- | --------------------- | --- |
| valid: | bool |           |                       |     |
|        |      | Listing4: | TestCasespecification |     |
import outlines
outlines_core
import
class OutlinesCompiler(Compiler):
| def | __init__(self, | model_id: | str): |     |
| --- | -------------- | --------- | ----- | --- |
self.tokenizer = outlines.models.transformers(model_id).tokenizer
| def | compile(self, | schema:                         | str) -> "OutlinesMasker": |     |
| --- | ------------- | ------------------------------- | ------------------------- | --- |
|     | regex =       | build_regex_from_schema(schema) |                           |     |
outlines.fsm.guide.RegexGuide.from_regex(
guide =
|     | regex, | self.tokenizer |     |     |
| --- | ------ | -------------- | --- | --- |
)
return OutlinesMasker(guide,
eos_token_id=self.tokenizer.eos_token_id)
(cid:44)→
class OutlinesMasker(Masker):
|     | __init__(self,    |                            | eos_token_id=None): |     |
| --- | ----------------- | -------------------------- | ------------------- | --- |
| def |                   | guide,                     |                     |     |
|     | self.guide        | = guide                    |                     |     |
|     | self.state        | = self.guide.initial_state |                     |     |
|     | self.eos_token_id | eos_token_id               |                     |     |
=
| def | advance(self, | token: int): |     |     |
| --- | ------------- | ------------ | --- | --- |
|     | assert token  | in           |     |     |
self.guide.get_next_instruction(self.state).tokens
(cid:44)→
|     | self.state | = self.guide.get_next_state(self.state, |     | token) |
| --- | ---------- | --------------------------------------- | --- | ------ |
assert_done(self):
def
if not self.guide.is_final_state(self.state):
|     | assert | self.eos_token_id | in  |     |
| --- | ------ | ----------------- | --- | --- |
self.guide.get_next_instruction(self.state).tokens
(cid:44)→
self.advance(self.eos_token_id)
assert self.guide.is_final_state(self.state)
|     |     | Listing5: ConcretetestharnessforOutlines |     |     |
| --- | --- | ---------------------------------------- | --- | --- |
24

import guidance
import llguidance
class GuidanceCompiler(Compiler):
| __init__(self,  | model_id: |       |
| --------------- | --------- | ----- |
| def             |           | str): |
| self.gtokenizer | =         |       |
guidance.models.transformers.TransformersTokenizer(model_id,
(cid:44)→
(cid:44)→ None)
| self.lltokenizer | =   |     |
| ---------------- | --- | --- |
llguidance.LLTokenizer(llguidance.TokenizerWrapper(self.gtokenizer))
(cid:44)→
| def compile(self,                      | schema: str)                | -> GuidanceMasker: |
| -------------------------------------- | --------------------------- | ------------------ |
| grammar = guidance.json(schema=schema) |                             |                    |
| llinterpreter                          | = llguidance.LLInterpreter( |                    |
tokenizer=self.lltokenizer,
llguidance_json=json.dumps(grammar.ll_serialize()),
enable_backtrack=False,
enable_ff_tokens=False,
)
| return GuidanceMasker(llinterpreter, |     |     |
| ------------------------------------ | --- | --- |
self.gtokenizer.eos_token_id)
(cid:44)→
class GuidanceMasker(Masker):
| def __init__(self, | llinterpreter,  | eos_token_id): |
| ------------------ | --------------- | -------------- |
| self.llinterpreter | = llinterpreter |                |
| self.eos_token_id  | eos_token_id    |                |
=
| def advance(self, | token: int): |     |
| ----------------- | ------------ | --- |
_ self.llinterpreter.compute_mask()
| bytemask,              | =   |     |
| ---------------------- | --- | --- |
| assert bytemask[token] | >   | 0   |
self.llinterpreter.commit_token(token)
assert_done(self):
def
if self.llinterpreter.stop_reason() == "NotStopped":
bytemask, _ = self.llinterpreter.compute_mask()
| if bytemask | is not None: |     |
| ----------- | ------------ | --- |
assert bytemask[self.eos_token_id] > 0
self.llinterpreter.commit_token(self.eos_token_id)
|     | _ self.llinterpreter.compute_mask() |     |
| --- | ----------------------------------- | --- |
bytemask, =
| assert                                  | bytemask | is None            |
| --------------------------------------- | -------- | ------------------ |
| assert self.llinterpreter.stop_reason() |          | in {"NoExtension", |
(cid:44)→ "EndOfSentence"}
Listing6: ConcretetestharnessforGuidance
25

| import xgrammar   | as     | xgr         |     |               |
| ----------------- | ------ | ----------- | --- | ------------- |
| from transformers | import | AutoConfig, |     | AutoTokenizer |
class XGrammarCompiler(Compiler):
| __init__(self, |     | model_id: |     |       |
| -------------- | --- | --------- | --- | ----- |
| def            |     |           |     | str): |
tokenizer = AutoTokenizer.from_pretrained(model_id)
config = AutoConfig.from_pretrained(model_id)
| self.eos_token_id |     |     | tokenizer.eos_token_id |     |
| ----------------- | --- | --- | ---------------------- | --- |
=
| self.tokenizer_info |            |                              | = xgr.TokenizerInfo.from_huggingface( |     |
| ------------------- | ---------- | ---------------------------- | ------------------------------------- | --- |
|                     | tokenizer, | vocab_size=config.vocab_size |                                       |     |
)
| self.compiler |     | = xgr.GrammarCompiler( |     |     |
| ------------- | --- | ---------------------- | --- | --- |
tokenizer_info=self.tokenizer_info,
)
| def compile(self, |     | schema: | str)                                      | -> "XGrammarMasker": |
| ----------------- | --- | ------- | ----------------------------------------- | -------------------- |
| compiled_grammar  |     | =       | self.compiler.compile_json_schema(schema, |                      |
strict_mode=False)
(cid:44)→
xgr_matcher xgr.GrammarMatcher(compiled_grammar)
=
return XGrammarMasker(xgr_matcher, self.eos_token_id)
class XGrammarMasker(Masker):
| def __init__(self, |     | xgr_matcher, |     | eos_token_id): |
| ------------------ | --- | ------------ | --- | -------------- |
xgr_matcher
self.matcher =
| self.eos_token_id |     |     | eos_token_id |     |
| ----------------- | --- | --- | ------------ | --- |
=
| def advance(self, |     | token: | int): |     |
| ----------------- | --- | ------ | ----- | --- |
self.matcher.accept_token(token)
assert
| def assert_done(self): |     |     |     |     |
| ---------------------- | --- | --- | --- | --- |
self.matcher.is_terminated():
if not
self.advance(self.eos_token_id)
assert self.matcher.is_terminated()
|                 | Listing7: |              | ConcretetestharnessforxGrammar |     |
| --------------- | --------- | ------------ | ------------------------------ | --- |
| from llama_cpp  | import    | LlamaGrammar |                                |     |
| import xgrammar | as        | xgr          |                                |     |
class LlamacppCompiler(XGrammarCompiler):
| def compile(self, |     | schema) | ->  | XGrammarMasker: |
| ----------------- | --- | ------- | --- | --------------- |
grammar_bnf = LlamaGrammar.from_json_schema(schema)._grammar
| compiled_grammar |     | =   | self.compiler.compile_grammar(grammar_bnf) |     |
| ---------------- | --- | --- | ------------------------------------------ | --- |
xgr_matcher xgr.GrammarMatcher(compiled_grammar)
=
return XGrammarMasker(xgr_matcher, self.eos_token_id)
Listing8: ConcretetestharnessforLlamacpp,inheritingfromtheXGrammarharness
forallfunctionalityafterusingllamacpptoconverttheschematoGGMLBNF.
| E Efficiency | Experiment |     | Details |     |
| ------------ | ---------- | --- | ------- | --- |
For efficiency experiments, the results depend on both the size of the model and the
tokenizer’svocabularysize. WeusedLlama-3.1-8B-Instruct(quantizedtoQ8bit)with
26

a 128K token vocabulary to achieve a balance between computational efficiency and
modelcapability.
Below,weoutlinespecificconsiderationsrelatedtogrammarandprefixcaching:
• Grammar Cache (Compilation): Sinceeachschemainthedatasetisunique,
cachinggrammarcompilationsdoesnotofferanybenefits.
• Prefix Cache (LLM Inference): We implement prefix caching during LLM
inferenceforallcasestoenhanceefficiencybyreusingcomputedresultswhere
applicable.
Table 13: Efficiency metrics for different engines with LlamaCpp as the inference
engine. GCT:GrammarCompilationTime,TTFT:TimetoFirstToken,TPOT:TimePer
Output Token, TGT: Total Generation Time, FF: Fast-Forwarded output tokens. Bold
valuesindicatethesmallestineachcolumnforGCT,TTFT,TPOT,andTGT.Allvaluesare
medianofthesamples.
Dataset Framework GCT(s) TTFT(s) TPOT(ms) TGT(s) OutputTokens(FF)
| GlaiveAI     | LLMonly  | NA 0.10   | 15.40 1.08  | 64.94(00.00)  |
| ------------ | -------- | --------- | ----------- | ------------- |
|              | Guidance | 0.00 0.24 | 6.37 0.50   | 41.56(15.70)  |
|              | Llamacpp | 0.05 0.20 | 29.98 1.47  | 43.18(00.00)  |
|              | Outlines | 3.48 3.65 | 30.33 4.84  | 40.39(00.00)  |
| GitHubEasy   | LLMonly  | NA 0.10   | 15.83 0.95  | 53.91(00.00)  |
|              | Guidance | 0.00 0.34 | 7.44 0.60   | 34.92(10.02)  |
|              | Llamacpp | 0.05 0.18 | 27.22 1.10  | 33.93(00.00)  |
|              | Outlines | 3.71 3.97 | 39.78 5.29  | 34.19(00.00)  |
| Snowplow     | LLMonly  | NA 0.11   | 16.23 1.01  | 55.31(00.00)  |
|              | Guidance | 0.00 0.28 | 6.55 0.51   | 36.77(14.50)  |
|              | Llamacpp | 0.05 0.20 | 28.90 1.24  | 37.21(00.00)  |
|              | Outlines | 3.91 4.14 | 42.66 5.65  | 35.65(00.00)  |
| GitHubMedium | LLMonly  | NA 0.20   | 16.68 2.56  | 142.10(00.00) |
|              | Guidance | 0.01 0.54 | 7.57 1.29   | 99.66(31.42)  |
|              | Llamacpp | 0.06 0.30 | 29.08 2.85  | 87.71(00.00)  |
|              | Outlines | 8.05 8.38 | 46.57 12.23 | 84.64(00.00)  |
| Kubernetes   | LLMonly  | NA 0.16   | 15.32 0.84  | 44.38(00.00)  |
|              | Guidance | 0.01 0.45 | 9.47 0.71   | 28.75(04.40)  |
|              | Llamacpp | 0.05 0.28 | 28.04 1.06  | 28.09(00.00)  |
|              | Outlines | 5.29 5.55 | 46.10 6.56  | 22.26(00.00)  |
Table14: Efficiency metricsfordifferentengineswithHugging Face Transformers
| astheinferenceengine. | Allvaluesaremedianofthesamples. |     |     |     |
| --------------------- | ------------------------------- | --- | --- | --- |
Dataset Framework GCT(s) TTFT(s) TPOT(ms) TGT(s) OutputTokens(FF)
| GlaiveAI     | Guidance   | 0.01 0.36 | 36.92 1.87  | 41.45(16.76)   |
| ------------ | ---------- | --------- | ----------- | -------------- |
|              | XGrammar   | 0.12 0.30 | 66.78 2.87  | 39.47(00.00)   |
| GitHubEasy   | Guidance   | 0.01 0.37 | 42.03 1.60  | 27.67(06.75)   |
|              | XGrammar   | 0.11 0.33 | 65.57 4.07  | 59.45(00.00)   |
| GitHubMedium | Guidance   | 0.01 0.55 | 44.21 4.84  | 96.31(26.93)   |
|              | XGrammar   | 0.20 0.48 | 65.51 6.53  | 92.93(00.00)   |
| GitHubHard   | Guidance   | 0.01 0.73 | 35.88 10.25 | 211.40(101.40) |
|              | XGrammar   | 0.30 0.65 | 65.20 14.99 | 221.40(00.00)  |
| F Quality    | Experiment | Details   |             |                |
Prompt and JSON Schema ForthetaskofShuffle Objects,andGSM8K,weusethe
samepromptandJSONschemafromthedottxt’s"letmespeakfreely"rebuttal.
ForthetaskofLast Letter,wemakeaslightmodificationbecausetheoriginalprompt
used was a bad example as pointed out by Kurt [2024b]. We also put it into a JSON
formattobetteralignwiththeothertasks.
27

Prompt Template for GSM8K
System Message:
You are an expert in solving grade school math tasks. You will be presented
with a grade-school math word problem and be asked to solve it. Before
answering, you should reason about the problem (using the "reasoning" field
in the JSON response format described below). Always respond with JSON
in the format: {"reasoning": <reasoning about the answer>, "answer":
<final answer>}. The "reasoning" field contains your logical explanation, and
the"answer"fieldcontainsthefinalnumericresult.
Demo Examples:
## Input:"[example question]"
## Output: "reasoning": "[example reasoning]", "answer": [example
answer]
...
Figure7: PrompttemplateforsolvingGSM8KwithJSONresponses.
Figure8revealsnon-emptyexclusiveregionsforeachengine,indicatingthatnosingle
engineoutperformstheothersacrossallinstances.
Figure8: OverlapofCorrectInstancesAcrossModelsonGSM8K
G Engine calling Snippet
We provide a snippet of the engine code used in our experiments. The generation
method of each engine has two main components: “compile_grammar” and
“call_engine”.
28

import time
import stopit
class BaseModel:
@stopit.threading_timeoutable(timeout=40)
| def compile_grammar(self, |     | json_schema): |     |     |
| ------------------------- | --- | ------------- | --- | --- |
| status = "unknown"        |     |               |     |     |
try:
| compiled_grammar |             | = self._compile_grammar(json_schema) |     |     |
| ---------------- | ----------- | ------------------------------------ | --- | --- |
| status           | = "success" |                                      |     |     |
| except Exception | as          |                                      |     |     |
e:
| # Any | exception in | this block | will be caught | and considered |
| ----- | ------------ | ---------- | -------------- | -------------- |
| as    | schema not   | supported  |                |                |
(cid:44)→
| compiled_grammar |     | = None |     |     |
| ---------------- | --- | ------ | --- | --- |
"schema_not_supported"
| status                   | =   |        |     |     |
| ------------------------ | --- | ------ | --- | --- |
| return compiled_grammar, |     | status |     |     |
json_schema=None):
| def generate(self, | prompt, |     |     |     |
| ------------------ | ------- | --- | --- | --- |
compile_start_time
|                        | =                                   | time.time()          |     |     |
| ---------------------- | ----------------------------------- | -------------------- | --- | --- |
| compiled_grammar       | = self.compile_grammar(json_schema) |                      |     |     |
| compile_end_time       | = time.time()                       |                      |     |     |
| # GCT (Grammar         | Compilation                         | Time)                |     |     |
| gct = compile_end_time |                                     | - compile_start_time |     |     |
gen_start_time
= time.time()
| first_tok_arr_time |     | self._call_engine(prompt, |     |     |
| ------------------ | --- | ------------------------- | --- | --- |
| output,            |     | =                         |     |     |
compiled_grammar)
(cid:44)→
| # TTFT (Time           | to First      | Token)             |     |     |
| ---------------------- | ------------- | ------------------ | --- | --- |
| first_tok_arr_time     |               | gen_start_time     |     |     |
| ttft =                 |               | -                  |     |     |
| gen_end_time           | = time.time() |                    |     |     |
| # TGT (Total           | Generation    | Time)              |     |     |
| gen_end_time           |               | gen_start_time     |     |     |
| tgt =                  | -             |                    |     |     |
| return output,         | gct, ttft,    | tgt                |     |     |
| def _call_engine(self, | prompt,       | compiled_grammar): |     |     |
raise NotImplementedError
Listing9: AbstractBaseModelinterfacedefiningthecallingofstructuredgeneration,
includinggrammarcompilationandtextgenerationtimingmetrics.
WeusetheListing10tovalidatethegeneratedJSONsagainsttheschema. Thevalidation
isdonebythejsonschemalibrarywithformatcheckingenabled.
We provide a snippet of how the engines are called in our experiments in List-
ings11,12,13,and14.
29

import jsonschema
| from | jsonschema | import Draft202012Validator, |     | FormatChecker, |
| ---- | ---------- | ---------------------------- | --- | -------------- |
ValidationError
(cid:44)→
| format_checker |     | = FormatChecker() |     |     |
| -------------- | --- | ----------------- | --- | --- |
def is_json_schema_valid(schema:
dict):
try:
jsonschema.Draft202012Validator.check_schema(schema)
return True
| except | jsonschema.SchemaError |     | as e: |     |
| ------ | ---------------------- | --- | ----- | --- |
return False
| validate_json_against_schema(json_obj, |     |     |     | json_schema): |
| -------------------------------------- | --- | --- | --- | ------------- |
def
is_json_schema_valid(json_schema):
if not
|           | raise ValidationError("The |                                   | JSON schema | is invalid.") |
| --------- | -------------------------- | --------------------------------- | ----------- | ------------- |
| validator | =                          | Draft202012Validator(json_schema, |             |               |
format_checker=format_checker)
(cid:44)→
| return | validator.validate(json_obj) |                                                |     |     |
| ------ | ---------------------------- | ---------------------------------------------- | --- | --- |
|        | Listing10:                   | ValidationofthegeneratedJSONsagainsttheschema. |     |     |
import guidance
class GuidanceModel(BaseModel):
|     | compile_grammar(self, | json_schema): |     |     |
| --- | --------------------- | ------------- | --- | --- |
def
|     | return | guidance.json( |     |     |
| --- | ------ | -------------- | --- | --- |
schema=json_schema,
)
| def | _call_engine(self, | prompt,                        | compiled_grammar): |            |
| --- | ------------------ | ------------------------------ | ------------------ | ---------- |
|     | generator          | = self.guidance_model.stream() |                    | + prompt + |
compiled_grammar
(cid:44)→
|     | for i, | state in enumerate(generator): |               |     |
| --- | ------ | ------------------------------ | ------------- | --- |
|     | if     | i == 0:                        |               |     |
|     |        | first_state_arr_time           | = time.time() |     |
|     | output | = state                        |               |     |
|     | return | output, first_state_arr_time   |               |     |
Listing11: Invocationoftheguidanceengine.
30

import llama_cpp
class LlamaCppModel(BaseModel):
def compile_grammar(self, json_schema):
return
(cid:44)→
llama_cpp.llama_grammar.LlamaGrammar.from_json_schema(json_schema)
def _call_engine(self, prompt, compiled_grammar):
generator = self.llama_cpp_model.create_chat_completion(prompt,
(cid:44)→ grammar=compiled_grammar, stream=True)
output = ""
for i, token in enumerate(generator):
if i == 0:
first_tok_arr_time = time.time()
output += token
return output, first_tok_arr_time
Listing12: InvocationoftheLlamaCppengine.
import outlines
class OutlinesModel(BaseModel):
def compile_grammar(self, json_schema):
return outlines.generate.json(
schema_object=json_schema
)
def _call_engine(self, prompt, compiled_grammar):
generator = self.generator.stream(prompt)
output = ""
for i, token in enumerate(generator):
if i == 0:
first_tok_arr_time = time.time()
output += token
return output, first_tok_arr_time
Listing13: InvocationoftheOutlinesengine.
31

import xgrammar
class TimingLogitsProcessor(LogitsProcessor):
def __init__(self):
super().__init__()
self.timestamps = []
def __call__(self, input_ids, scores):
current_time = time.time()
self.timestamps.append(current_time)
return scores
class XGrammarModel(BaseModel):
def compile_grammar(self, json_schema):
return
(cid:44)→
xgrammar.GrammarCompiler().compile_json_schema(json_schema)
def _call_engine(self, prompt, compiled_grammar):
output = self.hf_model.generate(prompt,
(cid:44)→
logits_processor=[compiled_grammar, timeit_logit_processor])
first_tok_arr_time = timeit_logit_processor.timestamps[0]
return output, first_tok_arr_time
Listing14: InvocationoftheXGrammarengine.
32