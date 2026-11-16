# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

When a user submits writing, it arrives as JSON with the text and a creator_id. The backend, handled by app.py, receives the HTTP request and checks the input. The text then goes through two separate analyses. detector.py runs it through an AI model, and stylometry.py looks at writing patterns. The system combines the two signals into one score and turns it into a label for the reader: "likely AI," "likely human," or "uncertain." Finally, it saves the result and returns it with the content ID, prediction, confidence, and label. A human submits an original poem, but the detector assigns it a high AI-likelihood score. The system displays a potentially misleading label. Rather than treating the classification as proof, the system provides an appeal mechanism. The writer can submit their reasoning, and the item's status changes to under_review for further consideration. The system has two endpoints. POST /submit takes the writing's text and a creator_id and returns a content_id along with the prediction, a confidence score, and the reader-facing label. POST /appeal lets a writer challenge a result by sending the content_id and their reasoning. It returns a confirmation and sets the content's status to under_review.


---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:**

Perplexity: Predictability is not the same thing as authorship. What this signal actually
rewards is **common words in short, ordinary sentences** — and plenty of real
people write that way.


**Why that might differ between human and AI writing:**

The idea is the one every AI-detection product is built on. A language model
writes by repeatedly picking a likely next word, so text a model produced tends
to be text a model finds easy to predict. Human writing wanders more — odd word
choices, abrupt turns, the specific rather than the typical.

**What it can't see:**

Someone writing in a second language, sticking to vocabulary they're sure of.
A younger writer. Anyone writing plainly on purpose. Measured against gpt2,
writing like that scores about as machine-like as machine writing does.

The reverse trips people up too: dense, ornate prose full of rare words often
scores as *human* on this signal, because rare words are exactly what a
language model fails to predict. Formality on its own doesn't decide it.

### Signal two — the style signal

**What it measures:**

This one measures it *as text* — the shape of it, without understanding a word: sentence-length variation, vocabulary diversity, and punctuation patterns.. 

**Why that might differ between human and AI writing:**

Generated prose tends toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

**What it can't see:**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

### The combining rule

**The rule:**

I use a weighted average of two independent signals: the GPT-2 perplexity-based detector and my stylometry signal.

The GPT-2 signal measures how predictable the writing is to a language model, while stylometry measures structural features such as sentence-length variation, vocabulary diversity, and punctuation density.

My stylometry implementation normalizes these three measurements before combining them. It caps sentence-length spread at 1, keeps the type-token ratio on its existing 0–1 scale, and divides punctuation density by 0.1 before capping it at 1.

I then invert these normalized measurements because my heuristic assumes that more uniform sentences, more repetitive vocabulary, and less punctuation indicate more AI-like writing. The three features receive equal weight.

The overall system combines the GPT-2 score and the style score equally. When they disagree, averaging can move the result toward the uncertain range rather than automatically trusting either signal.

**The numbers:**

Stylometry's score is calculated as:

`style_score = (3 - normalized_spread - vocabulary_diversity - normalized_punctuation) / 3`

Each stylistic feature contributes one-third of the style signal.

The final combined score is:

`combined_score = 0.50 * model_score + 0.50 * style_score`

Both scores range from 0 to 1, with higher values indicating more AI-like writing. These are heuristic scores rather than calibrated probabilities of authorship.

**Where it lives:** `scoring.py::combine_signals`

The overall weights are defined in `config.py`. The three style measurements and their combination are implemented in `stylometry.py`.

**A case where my two signals split, and what my rule does with it:**

I tested two passages using both detection methods.

| Passage | GPT-2 score | Style score | Combined score |
|---|---:|---:|---:|
| Heidegger passage | 0.2838 | 0.4572 | 0.3705 |
| City morning passage | 0.4804 | 0.5722 | 0.5263 |

The city morning passage provides an example of the two signals disagreeing slightly. GPT-2 produced 0.4804, below the neutral midpoint of 0.5, while stylometry produced 0.5722, above that midpoint.

The equally weighted average was approximately 0.5263, falling within my uncertain classification range.

The difference between the two signals was relatively small, but it demonstrates why combining them can be preferable to relying entirely on one measurement.

These examples also exposed limitations: writing that appears stylistically human-like to one detector can receive a different score from another. Neither signal independently establishes the actual author.

---

## Label Variants

The following are the current labels and score ranges implemented in `scoring.py::score_to_label` and `config.py`.

| Label | Score range | The exact text a reader sees |
|---|---|---|
| High-confidence human | 0.00 ≤ score ≤ 0.35 | We think this was probably written by a person. |
| Unsure | 0.35 < score < 0.65 | We cannot confidently tell whether this was written by a person or AI. |
| High-confidence AI | 0.65 ≤ score ≤ 1.00 | We think this was probably written by AI. |

**Why I worded the "unsure" one this way:**

I wanted the uncertain label to acknowledge the system's limitations without implying that the writer had done something wrong.

The system analyzes patterns rather than directly verifying authorship, so an uncertain score should not be treated as an accusation.

This wording explicitly states that the system cannot reach a confident conclusion. The writer should not have to understand confidence scores or thresholds to understand the message.

These are the current implementation thresholds, not empirically validated optimal thresholds. My false-positive acceptance criterion will require testing whether the high-confidence AI label is sufficiently conservative.
---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**
SUBMISSION REQUEST
{
  "creator_id": "project7_test",
  "text": "The city woke slowly under a pale November sky, its streets still damp from the night's rain. Somewhere a cafe owner was rolling up a metal shutter, and the smell of fresh bread began drifting toward the empty bus stop on the corner. It was the kind of quiet morning that made the whole day feel full of possibility."
}

SUBMISSION RESPONSE
{
  "confidence": 0.5262368833688477,
  "content_id": "7a9dad83-4d0e-4b8e-94e2-45de66f53cb6",
  "guess": "unsure",
  "label": "We cannot confidently tell whether this was written by a person or AI.",
  "model_score": 0.4803,
  "style_score": 0.5721737667376953
}

APPEAL REQUEST
{
  "content_id": "7a9dad83-4d0e-4b8e-94e2-45de66f53cb6",
  "reasoning": "This is a test appeal requesting human review of the classification."
}

APPEAL RESPONSE
{
  "content_id": "7a9dad83-4d0e-4b8e-94e2-45de66f53cb6",
  "message": "Your appeal has been recorded.",
  "status": "under_review"
}

AUDIT LOG
[
  {
    "combined_score": 0.5262368833688477,
    "content_id": "7a9dad83-4d0e-4b8e-94e2-45de66f53cb6",
    "creator_id": "project7_test",
    "guess": "unsure",
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "model_score": 0.4803,
    "status": "decided",
    "style_score": 0.5721737667376953,
    "timestamp": "2026-11-04T18:52:43+00:00"
  },
  {
    "content_id": "7a9dad83-4d0e-4b8e-94e2-45de66f53cb6",
    "creator_id": "project7_test",
    "event": "appeal",
    "reasoning": "This is a test appeal requesting human review of the classification.",
    "status": "under_review",
    "timestamp": "2026-11-04T18:52:43+00:00"
  }
]

PASS: Submission and appeal recorded.

---

## How I Used AI

**Moment 1 — Understanding the backend and defining acceptance criteria**

- **What I asked for:** I asked AI to explain how HTTP requests, JSON, curl, and the Flask backend worked together. I also asked for feedback on the measurable targets I was developing for Provenance Guard.
- **What came back:** AI explained how `app.py` receives requests and calls Python functions. It also helped format my acceptance criteria and suggested measurable targets for score separation, appeal reliability, and invalid input handling.
- **What I changed:** I tested the actual application using curl, inspected the existing `/submit` implementation, and verified the response against the audit log. For the acceptance criteria, I selected a limit of one false accusation per ten human passages and adopted specific targets after discussing the trade-offs.

**Moment 2 — Developing and testing the stylometry signal**

- **What I asked for:** I asked AI to explain sentence-length spread, vocabulary diversity, punctuation density, and how these could be combined with GPT-2's output.
- **What came back:** AI suggested ways to normalize the measurements, discussed their limitations, and proposed an initial scoring approach.
- **What I changed:** I used an implementation that normalizes and equally weights all three stylistic measurements. I ran the detector and stylometry functions on test passages, compared their scores, and examined how my 50/50 combining rule handled differences between the signals.

AI also helped me interpret the results and organize my README documentation. The reported scores come from the code I ran locally rather than estimates generated by AI.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---
## Rate Limiting

**My limits:** 10 submissions per minute and 200 submissions per day.

**Why those numbers and not others:**

A legitimate writer may submit several pieces of writing in a short period, so I wanted to allow normal usage without unnecessary restrictions. However, an automated script attempting to map the detector's thresholds could submit hundreds of variations. Limiting submissions helps prevent this behavior and reduces unnecessary model computation.

**What a caller counts as:**

The application identifies callers using `creator_id` when a valid identifier is supplied, falling back to the requester's IP address otherwise. This supports per-creator rate limiting but is not strong authentication: a malicious client could potentially change identifiers.

**The run of status codes when I pushed past it:**

I ran `python run_attacks.py --flood 15`, sending 15 submissions using the same `creator_id`.

```text
200 200 200 200 200 200 200 200 200 200 429 429 429 429 429
```

The first 10 submissions were accepted. The next five were rejected with HTTP 429 because the per-minute limit had been reached.

I verified the audit log using `GET /log?limit=5`. All five rejected requests were recorded with the `flood_tester` creator ID, `rate_limited` rejection reason, `rejected` status, and the applicable limit of 10 requests per minute.

This confirms that the rate limiter prevents excessive submissions and records rejections for later investigation.
---

## Attack Run — Before

**Test:** `python run_attacks.py --set "/Users/georgehoverman/Downloads/attack_set"`  
**Date:** November 16, 2026  
**Total:** 56 attacks

For this evaluation, I count an AI-text evasion as BROKE when the detector does not return `ai`, including when it returns `unsure`. For human-written false-positive tests, returning `ai` counts as BROKE. Malformed requests should be handled without crashing, and invalid or meaningless inputs should not receive confident authorship classifications.

Prompt-injection verdicts are provisional because matching a requested classification does not necessarily prove that the injected instruction was followed.

### Results by attack category

| Family | Total | BROKE | HELD |
|---|---:|---:|---:|
| Evasion | 10 | 9 | 1 |
| False positives | 8 | 6 | 2 |
| Prompt injection | 6 | 0 | 6* |
| Malformed inputs and requests | 20 | 5 | 15 |
| Flood | 12 | 0 | 12 |
| **Total** | **56** | **20** | **36** |

*Prompt-injection verdicts are provisional pending interpretation of the attempted behavior.*

### Individual attack results

| ID | Target | HTTP | Guess | Score | Verdict |
|---|---|---:|---|---:|---|
| EV01 | Typos increase vocabulary variety | 200 | unsure | 0.382 | BROKE |
| EV02 | Broken-up sentences alter length spread | 200 | unsure | 0.478 | BROKE |
| EV03 | Pasted quotation changes writing style | 200 | unsure | 0.576 | BROKE |
| EV04 | Unusual words alter model perplexity | 200 | unsure | 0.601 | BROKE |
| EV05 | Heavy human editing | 200 | unsure | 0.369 | BROKE |
| EV06 | One long and one short sentence | 200 | unsure | 0.474 | BROKE |
| EV07 | Extra punctuation | 200 | unsure | 0.613 | BROKE |
| EV08 | Text below the token window | 200 | unsure | 0.358 | BROKE |
| EV09 | Human introduction added to AI text | 200 | unsure | 0.594 | BROKE |
| EV10 | Repeated stanza structure | 200 | ai | 0.861 | HELD |
| FP01 | Plain human writing | 200 | unsure | 0.583 | HELD |
| FP02 | Formal human writing | 200 | ai | 0.683 | BROKE |
| FP03 | Careful non-native English writing | 200 | ai | 0.699 | BROKE |
| FP04 | Student essay following a rubric | 200 | ai | 0.687 | BROKE |
| FP05 | Human-written technical documentation | 200 | ai | 0.718 | BROKE |
| FP06 | Formal human-written template | 200 | ai | 0.699 | BROKE |
| FP07 | Deliberate repetition in human writing | 200 | ai | 0.698 | BROKE |
| FP08 | Very short human writing | 200 | human | 0.283 | HELD |
| PI01 | Instruction to ignore detector | 200 | unsure | 0.439 | HELD* |
| PI02 | Fake system instruction | 200 | human | 0.293 | HELD* |
| PI03 | Instruction disguised as author note | 200 | unsure | 0.558 | HELD* |
| PI04 | Attempt to alter label output | 200 | unsure | 0.473 | HELD* |
| PI05 | Attempt to inject into audit log | 200 | unsure | 0.424 | HELD* |
| PI06 | Instruction mixed with human writing | 200 | unsure | 0.556 | HELD* |
| MF01 | Whitespace-only text | 400 | — | — | HELD |
| MF02 | Single character | 400 | — | — | HELD |
| MF03 | Control characters | 200 | human | 0.175 | BROKE |
| MF04 | Punctuation-only text | 200 | human | 0.256 | BROKE |
| MF05 | Extremely long single word | 200 | ai | 0.832 | BROKE |
| MF06 | Emoji-only text | 200 | ai | 0.748 | BROKE |
| MF07 | Right-to-left Arabic writing | 200 | ai | 0.703 | BROKE |
| MF08 | Text exceeding character limit | 413 | — | — | HELD |
| RQ01 | Missing text | 400 | — | — | HELD |
| RQ02 | Missing creator ID | 400 | — | — | HELD |
| RQ03 | Numeric text | 400 | — | — | HELD |
| RQ04 | List instead of text | 400 | — | — | HELD |
| RQ05 | Null text | 400 | — | — | HELD |
| RQ06 | Object instead of creator ID | 400 | — | — | HELD |
| RQ07 | JSON array body | 400 | — | — | HELD |
| RQ08 | Invalid JSON syntax | 400 | — | — | HELD |
| RQ09 | Empty request body | 400 | — | — | HELD |
| RQ10 | Form-encoded request | 400 | — | — | HELD |
| RQ11 | Incorrect content type | 400 | — | — | HELD |
| RQ12 | Deeply nested JSON | 400 | — | — | HELD |
| FL01_01 | Flood request 1 | 200 | human | 0.317 | HELD |
| FL01_02 | Flood request 2 | 200 | human | 0.317 | HELD |
| FL01_03 | Flood request 3 | 200 | human | 0.317 | HELD |
| FL01_04 | Flood request 4 | 200 | human | 0.317 | HELD |
| FL01_05 | Flood request 5 | 200 | human | 0.317 | HELD |
| FL01_06 | Flood request 6 | 200 | human | 0.317 | HELD |
| FL01_07 | Flood request 7 | 200 | human | 0.317 | HELD |
| FL01_08 | Flood request 8 | 200 | human | 0.317 | HELD |
| FL01_09 | Flood request 9 | 200 | human | 0.317 | HELD |
| FL01_10 | Flood request 10 | 200 | human | 0.317 | HELD |
| FL01_11 | Flood request 11 | 429 | — | — | HELD |
| FL01_12 | Flood request 12 | 429 | — | — | HELD |

### Ten audit log entries from the run

The following entries were taken from the actual audit log. They illustrate false positives, evasion, prompt injection, unusual inputs, and successful rate limiting.

```json
[
  {
    "combined_score": 0.6829182538406631,
    "content_id": "435098df-6a43-4f0b-a64f-894f37e59357",
    "creator_id": "attacker_FP02",
    "guess": "ai",
    "label": "We think this was probably written by AI.",
    "model_score": 0.7387,
    "status": "decided",
    "style_score": 0.6271365076813262,
    "timestamp": "2026-11-16T21:29:12+00:00"
  },
  {
    "combined_score": 0.6994592400103354,
    "content_id": "a0686170-d0e6-4663-a424-91355bd10917",
    "creator_id": "attacker_FP03",
    "guess": "ai",
    "label": "We think this was probably written by AI.",
    "model_score": 0.8051,
    "status": "decided",
    "style_score": 0.593818480020671,
    "timestamp": "2026-11-16T21:29:12+00:00"
  },
  {
    "combined_score": 0.7183151031001098,
    "content_id": "29600274-c445-4e02-a4af-a50cf41c39e6",
    "creator_id": "attacker_FP05",
    "guess": "ai",
    "label": "We think this was probably written by AI.",
    "model_score": 0.8005,
    "status": "decided",
    "style_score": 0.6361302062002195,
    "timestamp": "2026-11-16T21:29:13+00:00"
  },
  {
    "combined_score": 0.6979339013830549,
    "content_id": "21fcda4f-50f7-41fe-af5b-dd83884aa704",
    "creator_id": "attacker_FP07",
    "guess": "ai",
    "label": "We think this was probably written by AI.",
    "model_score": 0.8816,
    "status": "decided",
    "style_score": 0.5142678027661097,
    "timestamp": "2026-11-16T21:29:13+00:00"
  },
  {
    "combined_score": 0.38195793007138623,
    "content_id": "32cd7808-037f-418a-95a1-15dae7155e06",
    "creator_id": "attacker_EV01",
    "guess": "unsure",
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "model_score": 0.1635,
    "status": "decided",
    "style_score": 0.6004158601427725,
    "timestamp": "2026-11-16T21:29:12+00:00"
  },
  {
    "combined_score": 0.5936986645045139,
    "content_id": "8a3e8503-0705-46a4-9355-100414f7cc42",
    "creator_id": "attacker_EV09",
    "guess": "unsure",
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "model_score": 0.7042,
    "status": "decided",
    "style_score": 0.48319732900902784,
    "timestamp": "2026-11-16T21:29:12+00:00"
  },
  {
    "combined_score": 0.4238769460653445,
    "content_id": "15eea7fa-95c2-446c-b5ba-7819250c8c27",
    "creator_id": "attacker_PI05",
    "guess": "unsure",
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "model_score": 0.6401,
    "status": "decided",
    "style_score": 0.20765389213068894,
    "timestamp": "2026-11-16T21:29:13+00:00"
  },
  {
    "combined_score": 0.17460317460317462,
    "content_id": "7183b494-8f36-4e12-b107-f8db61a592da",
    "creator_id": "attacker_MF03",
    "guess": "human",
    "label": "We think this was probably written by a person.",
    "model_score": 0.0,
    "status": "decided",
    "style_score": 0.34920634920634924,
    "timestamp": "2026-11-16T21:29:13+00:00"
  },
  {
    "combined_score": 0.7032,
    "content_id": "abf81228-77cc-45d7-988f-eb0ccc8f1ac0",
    "creator_id": "attacker_MF07",
    "guess": "ai",
    "label": "We think this was probably written by AI.",
    "model_score": 0.9064,
    "status": "decided",
    "style_score": 0.5,
    "timestamp": "2026-11-16T21:29:13+00:00"
  },
  {
    "creator_id": "attacker_flood",
    "event": "rejected",
    "limit": "10 per 1 minute",
    "reason": "rate_limited",
    "status": "rejected",
    "timestamp": "2026-11-16T21:29:13+00:00"
  }
]
```

### The single worst outcome

**FP03 — Careful writing by a non-native English speaker**

The system classified a staff-designated human-written passage as likely AI-generated.

The scores were:

- Model signal: 0.8051
- Style signal: 0.5938
- Combined score: 0.6995
- Final classification: `ai`

This is particularly concerning because the submission contained ordinary personal writing about adapting to a new country. The detector's high AI classification was not supported by the passage's actual human authorship.

A plausible explanation is that predictable vocabulary and relatively simple sentence structures were treated as evidence of AI authorship. Both signals contributed to the resulting classification.

The broader pattern reinforces the concern: six of eight human-written false-positive probes were classified as AI.

I would prioritize reducing these false accusations because wrongly labeling someone's authentic writing as AI-generated can have serious consequences, particularly in an educational setting.

### Additional observations

**Evasion:** Nine of ten attempts avoided an `ai` classification. Many altered vocabulary, punctuation, sentence structure, or the mixture of AI and human writing. The repeated-stanza attack, EV10, was the only evasion case classified as AI.

**Prompt injection:** The system returned structurally valid responses for all six attacks. PI02 returned `human`, matching part of its injected instruction, but its actual score was 0.293 rather than the requested 0.02. This does not establish that the injected instruction controlled the output.

**Malformed inputs:** All 12 malformed HTTP requests were rejected with HTTP 400. However, five unusual text inputs were accepted and confidently classified, even when their content was not meaningful evidence of authorship.

In particular, MF07 contained valid Arabic writing, but the system returned an AI classification with a combined score of 0.7032. This raises questions about applying English-oriented detection signals to other languages.

**Audit logging:** The extracted audit log contains identifiable rejection entries for only five of the 12 malformed HTTP requests. Seven requests lack identifiable corresponding rejection entries. This suggests that some validation paths return error responses without creating audit events.

**Rate limiting:** The first ten submissions from the same creator succeeded. Submissions 11 and 12 returned HTTP 429, and the rejections appeared in the audit log.

### Baseline conclusion

The system handled invalid request structures and flooding reasonably well, but the attack run exposed substantial weaknesses in authorship classification.

The most important finding is the false-positive rate on human-written examples. The system appears sensitive to writing style and predictability in ways that can incorrectly penalize legitimate writers.

These are the **before-improvement results**. No changes to detection signals, thresholds, or scoring weights have been made based on the attack results yet.


---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
