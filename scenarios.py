"""Project 8 evaluation scenarios for run_eval.py.

Human samples: ten separate paragraphs extracted from a paper supplied by the
student, "Algorithmic Aphasia" (May 12, 2026). The assistant cannot verify
whether any paragraph was generated or substantially rewritten by an AI.
USER: confirm that provenance before calling these "verified human" samples.
These samples all come from ONE document, not ten independent documents.

AI samples: ten original AI-generated comparison passages created by ChatGPT
for this testing exercise, November 16, 2026. Document that in the README.

Criterion 4 (appeals) requires a separate real submit-and-appeal test; this
scenario runner only calls POST /submit.
"""

HUMAN_TEXTS = ['In 1915, T. S. Eliot opened a poem with three lines that have remained, for over a century, '
 'among the most arresting images in modernist literature: “Let us go then, you and I, / When the '
 'evening is spread out against the sky / Like a patient etherized upon a table.” The figure is '
 'medical: it summons a consciousness that appears awake but unresponsive, laid out for '
 'inspection by an absent surgeon. Critics have read “The Love Song of J. Alfred Prufrock” as a '
 'study of modernist alienation, sexual paralysis, and the malaise of a fading bourgeoisie. None '
 'of these readings is wrong, but none is sufficient. Eliot did not depict a singular '
 'consciousness in pre-war London; he depicted the ontological condition of the '
 'twenty-first-century algorithmic subject, decades before the technology existed to produce him '
 'at scale. Through the work of Heidegger, Ricoeur, Foucault, Gadamer, Eco, Anderson, Simpson, '
 'Kuhn, and Turchin, a more devastating reading emerges. Prufrock is the prophetic literary '
 'diagnosis of a condition this paper will call *Algorithmic Aphasia* — modeled on clinical '
 'aphasia, the loss of language capacity following neurological damage — the systemic atrophy of '
 'hermeneutic capacity in populations whose interpretive lives have been mediated, smoothed, and '
 'ultimately replaced by algorithmic systems. If interpretation is constitutive of the human, '
 'then the elimination of hermeneutic friction by algorithmic mediation is not a pedagogical '
 'problem. It is the death of the subject, and we are watching it happen in real time.',
 'The diagnosis demands a foundation that post-Absolute-truth provides. I have argued in '
 '*Spirals* that Schleiermacher’s classical hermeneutic circle is not a closed loop but an open '
 'three-dimensional spiral, requiring both the temporal pressure of the present and the '
 'gravitational pull of the text’s resistance to maintain its productive shape. Procession along '
 'the spiral established the geometry of human thought. This paper takes up the next question: '
 'what happens when the spiral stops turning? Derrida demonstrates that meaning is endlessly '
 'deferred and that the transcendental signified is a fiction, Ricoeur exposes the ideological '
 'structures beneath every claim to neutral interpretation, and Kuhn shows that even scientific '
 'truth operates within paradigms that periodically collapse, the dream of a recoverable, '
 'universal meaning must be abandoned. Interpretation can no longer be a recovery operation. As '
 'Gadamer writes in *Truth and Method*, “the experience of the sociohistorical world cannot be '
 'raised to a science by the inductive procedure of the natural sciences.” Gadamer is not '
 'correcting a methodological error; he is rejecting the premise that understanding is an '
 'instrument humans pick up and use. Once the Absolute collapses, interpretation is no longer one '
 'activity among others. It becomes the condition of finite existence itself.',
 'The Absolute does not collapse cleanly, however, and the precise mechanism of its dissolution '
 'matters for what follows. Jacques Derrida, in *Of Grammatology*, identifies the structure that '
 'has held the West’s faith in stable meaning together: what he calls the “transcendental '
 'signified”—the imagined, fixed point outside language that guarantees that every signifier '
 'ultimately points to something real. The history of metaphysics, Derrida argues, is the history '
 'of this guarantee, and the guarantee has always been a fiction. There is no signifier that does '
 'not refer to other signifiers; meaning is constituted not by reference to a stable origin but '
 'by *différance* — the deferral and difference that operate within language itself. The '
 'implication for hermeneutics is decisive. If there is no transcendental signified, there is no '
 'recoverable authorial *Geist* that the reader can reconstruct. Schleiermacher’s project — to '
 'understand the utterance “first just as well and then better than its author” — collapses not '
 'because the author’s mind is hard to access but because there is no fixed mind to access. The '
 'text does not point to a meaning behind it; it generates meaning in the act of being read. The '
 'reader is therefore not an archaeologist excavating a buried truth but a participant in the '
 'text’s continuing existence. Without the guarantee of the Absolute, the labor of meaning-making '
 'falls, irreducibly, on the reader.',
 'If interpretation is the condition of finite existence rather than a method applied to it, then '
 'hermeneutics is not a methodology but an ontology. Heidegger proposes this idea in *Being and '
 'Time* with *Dasein*: the entity for whom its own being is an issue, and to be *Dasein* is, '
 'structurally, to interpret. “An interpretation,” Heidegger writes, “is never a '
 'presuppositionless apprehending of something presented to us.” Understanding does not arise '
 'from neutral confrontation with objects; it arises from the fore-structure — *Vorhabe*, '
 '*Vorsicht*, *Vorgriff* — that *Dasein *inherently carries into encounter with the world, with a '
 'text, or with another person. To interpret is to project meaning onto what is encountered '
 'before any deliberate operation can begin: to see the hammer as a hammer, the sentence as a '
 'claim, the face as a face. On this reading, the hermeneutic spiral is not a tool the subject '
 'picks up, because the subject does not precede the spiral. The spiral is the structure of human '
 'existence itself. There is no Dasein that first exists and then chooses to interpret. There is '
 'only the entity whose being unfolds as interpretation. “What is decisive,” Heidegger insists, '
 '“is not to get out of the circle but to come into it in the right way.” To stop interpreting is '
 'therefore not to fail at a task. It is to cease being *Dasein*. Heidegger establishes the '
 'ontology, but he does not specify what such cessation looks like at the level of the self, what '
 'the loss of projective activity does to the “I” that the projection was meant to constitute.',
 'Michel Foucault completes the triangulation by providing historical context for practices '
 'through which subjects come into being. In his late lectures, gathered as *The Hermeneutics of '
 'the Subject*, Foucault traces the genealogy of the “technologies of the self” — the practices, '
 'exercises, and discourses through which subjects have, across history, constituted themselves '
 'as selves. Christian confession produced the confessing subject. Nineteenth-century psychiatry '
 'produced the diagnosable subject. The journal, the examination of conscience, the dialogue with '
 'a master — each is a technology that does not merely describe selves but produces them. There '
 'is no “natural” self that exists prior to or independent of the technologies that constitute '
 'it. The diagnostic stakes of this triangulation become visible the moment one asks what '
 'technology of the self now dominates. Thanks to the rise of social media and artificial '
 'intelligence,\xa0 the algorithm is the dominant hermeneutic technology of the twenty-first '
 'century: it mediates not only what we read but how we narrate ourselves, what we remember, what '
 'we want, and how we encounter others. It is the new confessional, the new journal, the new '
 'master. The question that follows is therefore urgent, and it is the question to which we turn: '
 'can the subject produced by algorithmic mediation sustain the interpretive labor that '
 'Heidegger, Ricoeur, and Foucault identify as constitutive of the human?',
 'The answer depends on whether the algorithm provides what hermeneutic subjectivity requires. '
 'Understanding, Gadamer argues, occurs through the fusion of horizons. The reader approaches the '
 'text from within a particular historical horizon — a horizon constituted by tradition, '
 'prejudice, and language. The text approaches the reader from within its own horizon, separated '
 'by time and difference. Understanding is the event in which these two horizons fuse, a fusion '
 'that does not erase difference but transforms the reader’s horizon by integrating something '
 'previously alien. Crucially, this fusion requires resistance. If the text simply confirms the '
 'reader’s existing prejudices, no fusion has occurred — only mirror-reflection. Prejudices, on '
 'Gadamer’s account, are not obstacles to be eliminated but parameters of understanding, and they '
 'are productive only when challenged by the text’s alterity. Without resistance, there is no '
 'learning. Without learning, there is no *Bildung* — no maturation of the interpretive self. But '
 'the principle leaves the mechanism unspecified: what is it about a text that allows it to '
 'resist a reader at all?',
 'Umberto Eco specifies the resistance mechanism with precision. In *The Limits of '
 'Interpretation*, Eco argues that the text exerts what he calls *intentio operis* — the '
 'intention of the work — a structural resistance distinct from both the author’s intention and '
 'the reader’s projection. The text’s syntax, internal logic, and historical context constrain '
 'the range of interpretations it can plausibly support. The text pushes back. As Eco insists, '
 '“unlimited semiosis does not lead to the conclusion that interpretation has no criteria.” '
 'Interpretation, on this account, is the productive friction between reader and text. Without '
 'friction, the spiral cannot turn. With it, the reader is forced upward — horizon shifted, '
 'prejudice tested, self enlarged. The hermeneutic spiral is thus a friction engine. The question '
 'that follows naturally is whether the dominant technology of the twenty-first-century self '
 'provides this friction or eliminates it.',
 'Algorithmic feedback systems are engineered, with extraordinary technical precision, to '
 'eliminate cognitive friction. They are designed not to challenge the user but to mirror the '
 'user. The recommendation engine learns what you click and feeds you more of what you click; the '
 'large language model, prompted with your query, produces text optimized for the relevance you '
 'appear to want; the social-media feed surfaces the content that confirms what you already '
 'believe. Joshua Hooke captures the structural diagnosis in the most direct terms available: '
 '“Humans aim for relevance, not for truth,” he writes, and “algorithms provide relevance, not '
 'truth.” The two are not the same. Truth resists; relevance accommodates. A generation raised '
 'inside the algorithmic mirror does not develop the hermeneutic musculature that classical '
 'pedagogy produced. The algorithm does not surface texts that resist; it offers feeds that '
 'flatter. The individual then does not labor through ambiguity, but scrolls through curation. '
 'The *Bildung* Gadamer describes — the slow, painful, world-expanding maturation of the '
 'interpretive subject — requires precisely the conditions that the algorithm has been built to '
 'avoid. The objection might be raised that this is a theoretical worry: a phenomenologist’s '
 'anxiety unsupported by evidence. The recent empirical literature forecloses that objection.',
 'Lorenzo Simpson extends Anderson’s distributional analysis. In *Towards a Hermeneutics of '
 'Race*, Simpson argues that the dominant interpretive paradigm has historically refused to '
 'engage the racialized Other as a full hermeneutic interlocutor — reading the marginalized '
 'subject through reductive frames rather than through the labor of genuine encounter. When this '
 'paradigm is encoded into algorithmic systems trained on the texts, images, and patterns of the '
 'dominant culture, the lack of recognition becomes structural rather than habitual. The '
 'algorithm does not interpret the Other; it computes the Other within categories deemed most '
 'probable by the data set. The result is a hermeneutic regime in which the friction of genuine '
 'racial encounter is engineered away in favor of computational enforcement of the dominant '
 'horizon. The marginalized subject is Othered again — once by historical refusal, once by '
 'algorithmic codification. The political consequence is not merely that some interpretations are '
 'deemed less likely than others. These conditions of encounter have been rebuilt to make '
 'interpretation, in Gadamer’s sense, structurally unavailable for those whose horizons differ '
 'from the data set’s center of probability.',
 'The potential for discontent alone, however, has rarely transformed civilizations. Every '
 'renaissance has required not only a dissatisfied populace but a vanguard willing to perform the '
 'unromantic, sustained work of building institutional alternatives. The Italian Renaissance did '
 'not emerge from a peasant uprising; it emerged from the Florentine merchant class’s deliberate '
 'cultivation of classical learning, the *studio* as a physical and pedagogical space, and the '
 'patient labor of translation, transcription, and teaching across generations. Any renaissance '
 'is a generational institution-building project that takes a hundred years and depends on people '
 'willing to perform inefficient labor in the face of more efficient alternatives. The early '
 'signs of a counter-movement against algorithmic mediation are already visible: independent '
 'bookstores in the United States have grown nearly seventy percent since 2020, with more than '
 'four hundred new stores opening in 2025 alone; vinyl records outsold CDs in 2022 for the first '
 'time since 1987, driven largely by younger buyers seeking a tangible, attention-demanding '
 'format; and twenty-two states enacted bell-to-bell restrictions on student cellphone use in '
 'K-12 schools during 2025, bringing the total to thirty-five states plus the District of '
 'Columbia by year’s end. Hermeneutic friction is being recovered, or at least the attempt has '
 'begun.']

AI_TEXTS = ['Artificial intelligence is becoming an important part of modern communication. Organizations '
 'are increasingly using automated tools to manage information, support collaboration, and '
 'improve daily efficiency. These systems can help employees organize complex tasks and identify '
 'relevant materials more quickly. At the same time, their use raises questions about '
 'transparency, accountability, and human oversight. When introducing new technologies, '
 'institutions should develop clear policies and provide appropriate training. A balanced '
 'approach can preserve the benefits of automation while ensuring that individuals remain '
 'responsible for important decisions. In the coming years, successful organizations will likely '
 'be those that combine technological innovation with careful human judgment.',
 'The role of technology in education has expanded significantly over the past decade. Digital '
 'platforms now support many aspects of learning, including research, classroom discussion, '
 'assessment, and individualized feedback. These tools offer students new opportunities to '
 'explore unfamiliar topics and practice difficult skills. However, educational institutions must '
 'also consider the possibility that excessive reliance on automation can weaken independent '
 'reasoning. Instructors should therefore encourage students to question generated explanations, '
 'compare sources, and explain their own conclusions. By treating technology as a supplement '
 'rather than a replacement for learning, schools can help students develop both technical '
 'fluency and intellectual independence.',
 'Human understanding is shaped by the experiences, assumptions, and cultural traditions that '
 'individuals bring to every encounter. When people read a text, they do not simply retrieve a '
 'fixed meaning stored inside its words. Instead, they interpret the text through a perspective '
 'that changes over time. This process can produce disagreement, but disagreement is not '
 'necessarily a failure. Encountering unfamiliar ideas can challenge existing beliefs and lead to '
 'more complex forms of understanding. For this reason, education should create opportunities for '
 'careful interpretation, sustained discussion, and revision of prior assumptions. The '
 'development of understanding requires both openness to alternative perspectives and a '
 "willingness to examine one's own judgments.",
 'Recommendation systems influence how people discover music, news, entertainment, and '
 'information online. By analyzing earlier interactions, these systems predict which content a '
 'user is most likely to select. Personalization can make digital services more convenient, but '
 'it may also narrow the range of perspectives a person encounters. If a system consistently '
 'promotes familiar material, users may spend less time engaging with unfamiliar or challenging '
 'ideas. Designers can address this risk by introducing meaningful diversity into recommendations '
 'and making the reasons for suggested content easier to understand. Users also benefit from '
 'regularly seeking information beyond automated feeds and comparing sources independently.',
 'Questions of authorship have become more complicated as generative tools improve. A document '
 'may contain ideas proposed by a person, sentences revised by software, and sections drafted '
 'through several rounds of collaboration. In such cases, a simple distinction between human and '
 'machine writing may not describe the actual process. Institutions therefore need clear rules '
 'about disclosure, responsibility, and acceptable assistance. Automated classifiers can '
 'sometimes provide useful signals, but those signals should not be treated as conclusive proof '
 "of misconduct. Fair evaluation should consider the writer's process, the context of the "
 'assignment, and the possibility that a detector has made an error.',
 'Public institutions depend on procedures that allow people to challenge mistakes. A decision '
 'system may be fast and consistent while still reaching an incorrect conclusion in an individual '
 'case. When errors carry reputational or financial consequences, affected people should be able '
 'to review the evidence and request reconsideration. An effective appeal process should record '
 'the original decision, preserve the reasons for disagreement, and establish who is responsible '
 'for further review. Transparency matters because it helps distinguish a genuine correction from '
 'an unexplained change. Organizations that deploy automated systems should evaluate these '
 'procedures as carefully as they evaluate the accuracy of the underlying technology.',
 'The fairness of an automated writing detector cannot be evaluated through accuracy alone. Two '
 'systems may achieve the same overall percentage of correct classifications while making very '
 'different kinds of mistakes. One system could fail to identify some machine-generated passages, '
 'while another could wrongly accuse authentic writers of using automation. The second error may '
 "be especially harmful when a classification affects a student's academic record or a writer's "
 'professional reputation. Evaluation should therefore report false-positive rates separately, '
 'examine performance across different writing styles, and allow uncertain results when the '
 'evidence is weak. Clear communication of limitations is an essential part of responsible '
 'deployment.',
 'Writing style varies across genres, audiences, and individual preferences. A technical manual '
 'often uses short instructions and repeated terminology, while a personal essay may rely on long '
 'sentences, metaphor, and irregular structure. Neither style determines whether the author is '
 'human. Statistical features such as vocabulary diversity and sentence length can describe '
 'patterns in a passage, but those patterns may reflect the purpose of the document rather than '
 'its origin. A robust evaluation system should test many genres instead of assuming that one '
 'model of natural writing applies everywhere. The results should be interpreted as estimates '
 'rather than as direct observations of authorship.',
 'Many people use digital tools to reduce the amount of time spent on routine work. Automated '
 'calendars, search engines, and writing assistants can help organize information and simplify '
 'repetitive tasks. The benefit of these systems depends partly on how they are used. When '
 'automation frees time for more meaningful activity, it can improve the quality of work and '
 'personal life. When users begin to rely on it for every decision, they may lose opportunities '
 'to practice important skills. A thoughtful approach involves identifying tasks that benefit '
 'from assistance while preserving independent judgment in situations that require reflection, '
 'creativity, or responsibility.',
 'Democratic discussion requires citizens to encounter claims they do not already accept. In '
 'contemporary media environments, information often circulates through networks shaped by '
 'individual preferences and automated rankings. These systems can increase engagement, but they '
 'can also make common ground more difficult to establish. Productive disagreement depends on '
 'shared procedures for evaluating evidence and a willingness to consider the strongest form of '
 'an opposing argument. Technology alone cannot create those habits. Schools, public '
 'organizations, and individuals all have roles in supporting media literacy, transparent debate, '
 'and careful interpretation of competing claims. These practices can strengthen public trust '
 'even when agreement remains impossible.']

SCENARIOS = [
    {"name": "paper human passages", "criterion": 1, "texts": HUMAN_TEXTS},
    {"name": "separation human", "criterion": 2, "texts": HUMAN_TEXTS},
    {"name": "separation AI", "criterion": 2, "texts": AI_TEXTS},
    {"name": "label coverage", "criterion": 3, "texts": [
        "Late again. Coffee spilled. Still made it to class.",
        "The old library was quiet after the rain, and the stairs smelled like wood.",
        AI_TEXTS[0],
    ]},
    {"name": "invalid inputs", "criterion": 5, "bodies": [
        {"creator_id": "eval_missing_text"},
        {"text": "", "creator_id": "eval_empty_text"},
        {"text": "A valid piece of writing but no creator ID"},
        {"text": "x" * 5001, "creator_id": "eval_text_too_long"},
    ]},
]


def validate() -> list[str]:
    """Return scenario configuration errors, if any."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")
        texts = scenario.get("texts")
        bodies = scenario.get("bodies")
        if texts and bodies:
            problems.append(f"scenario {i} has both texts and bodies")
            continue
        if bodies:
            for j, body in enumerate(bodies, 1):
                if not isinstance(body, dict):
                    problems.append(f"scenario {i}, body {j} is not a dict")
            continue
        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue
        for j, value in enumerate(texts, 1):
            if not isinstance(value, str) or not value.strip():
                problems.append(f"scenario {i}, text {j} empty or not a string")
            elif value.startswith("REPLACE ME"):
                problems.append(f"scenario {i}, text {j} placeholder remains")
            elif len(value) > 5000:
                problems.append(f"scenario {i}, text {j} exceeds 5000 characters")
    return problems
