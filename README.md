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

[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4189321317629119,
    "model_score": 0.477,
    "style_score": 0.36086426352582385,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "In 1915, T. S. Eliot opened a poem with three lines that have remained"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.36203647267053907,
    "model_score": 0.2976,
    "style_score": 0.4264729453410781,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The diagnosis demands a foundation that post-Absolute-truth provides. "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5233979445302617,
    "model_score": 0.4915,
    "style_score": 0.5552958890605234,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The Absolute does not collapse cleanly, however, and the precise mecha"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5377248953180376,
    "model_score": 0.5759,
    "style_score": 0.49954979063607513,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "If interpretation is the condition of finite existence rather than a m"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5336007652051187,
    "model_score": 0.5523,
    "style_score": 0.5149015304102372,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Michel Foucault completes the triangulation by providing historical co"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5155485006209006,
    "model_score": 0.4939,
    "style_score": 0.5371970012418011,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The answer depends on whether the algorithm provides what hermeneutic "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3691843812489079,
    "model_score": 0.3051,
    "style_score": 0.4332687624978158,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Umberto Eco specifies the resistance mechanism with precision. In *The"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3641169693217561,
    "model_score": 0.2671,
    "style_score": 0.4611339386435122,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Algorithmic feedback systems are engineered, with extraordinary techni"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4442873802519298,
    "model_score": 0.3298,
    "style_score": 0.5587747605038597,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Lorenzo Simpson extends Anderson\u2019s distributional analysis. In *Toward"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.42336021798745754,
    "model_score": 0.4672,
    "style_score": 0.3795204359749151,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The potential for discontent alone, however, has rarely transformed ci"
  }
]

[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4189321317629119,
    "model_score": 0.477,
    "style_score": 0.36086426352582385,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "In 1915, T. S. Eliot opened a poem with three lines that have remained"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.36203647267053907,
    "model_score": 0.2976,
    "style_score": 0.4264729453410781,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The diagnosis demands a foundation that post-Absolute-truth provides. "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5233979445302617,
    "model_score": 0.4915,
    "style_score": 0.5552958890605234,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The Absolute does not collapse cleanly, however, and the precise mecha"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5377248953180376,
    "model_score": 0.5759,
    "style_score": 0.49954979063607513,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "If interpretation is the condition of finite existence rather than a m"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5336007652051187,
    "model_score": 0.5523,
    "style_score": 0.5149015304102372,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Michel Foucault completes the triangulation by providing historical co"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5155485006209006,
    "model_score": 0.4939,
    "style_score": 0.5371970012418011,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The answer depends on whether the algorithm provides what hermeneutic "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3691843812489079,
    "model_score": 0.3051,
    "style_score": 0.4332687624978158,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Umberto Eco specifies the resistance mechanism with precision. In *The"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3641169693217561,
    "model_score": 0.2671,
    "style_score": 0.4611339386435122,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Algorithmic feedback systems are engineered, with extraordinary techni"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4442873802519298,
    "model_score": 0.3298,
    "style_score": 0.5587747605038597,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Lorenzo Simpson extends Anderson\u2019s distributional analysis. In *Toward"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.42336021798745754,
    "model_score": 0.4672,
    "style_score": 0.3795204359749151,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The potential for discontent alone, however, has rarely transformed ci"
  }
]

### Before improvement

Five acceptance criteria were tested against three trials, using `run_eval.py`, direct score-boundary checks, and a separate appeal test.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. False positives | At most 1/10 human passages labeled AI | 0/10 | 0/10 | 0/10 | MET |
| 2. Score separation | AI mean at least 0.30 above human mean | 0.0916 | 0.0916 | 0.0916 | MISSED |
| 3. Label coverage | 3/3 labels reachable | 3/3 | 3/3 | 3/3 | MET |
| 4. Appeal reliability | 5/5 valid appeals successful | 5/5 | 5/5 | 5/5 | MET |
| 5. Invalid inputs | 4/4 rejected correctly | 4/4 | 4/4 | 4/4 | MET |

**Criterion 1 — False positives**

All ten tested passages came from my own paper, *Algorithmic Aphasia*. None received an AI classification in any trial. All were classified as `unsure`.

This meets the stated numerical criterion, but the sample is limited because all ten passages came from one piece of academic writing. The staff attack set exposed six false positives in other human-writing styles.

**Criterion 2 — Score separation**

The average signal values from the baseline evaluation were:

| Signal | Human mean | AI mean | Difference |
|---|---:|---:|---:|
| GPT-2 model signal | 0.4257 | 0.5019 | 0.0762 |
| Stylometry signal | 0.4727 | 0.5798 | 0.1071 |
| Combined score | 0.4492 | 0.5409 | 0.0916 |

The required gap was 0.30. The measured gap was only 0.0916 in all three trials.

**Verdict: MISSED.**

The failure begins in the two signals, which produce only weakly separated distributions for the chosen human and AI examples. GPT-2 perplexity does not reliably identify authorship, and the stylometry heuristic treats patterns such as vocabulary repetition and sentence regularity as evidence of AI writing.

The combining rule weights each signal equally. Averaging two weakly separated signals cannot create a substantially larger separation. The label-mapping stage is not the underlying cause of this criterion's failure.

**Criterion 3 — Label coverage**

Direct tests of `scoring.py::score_to_label` verified the human, uncertain, and AI score ranges across three trials. The boundary tests showed every tested boundary mapped to one label.

The chosen live submission probes produced only `human` and `unsure`, but the independent staff attack set also produced `ai` classifications. Therefore, all three labels were demonstrably reachable, even though the original three live probes did not cover them all.

**Verdict: MET.**

**Criterion 4 — Appeal reliability**

Fifteen valid appeals were tested in three groups of five.

```text
Trial 1: 5/5
Trial 2: 5/5
Trial 3: 5/5
Overall: MET
```

Every appeal returned HTTP 200, confirmed `under_review`, and had a matching audit entry with its reasoning.

**Criterion 5 — Invalid input handling**

```text
Trial 1: [400, 400, 400, 413]
Trial 2: [400, 400, 400, 413]
Trial 3: [400, 400, 400, 413]
Overall: MET
```

Missing text, empty text, and missing creator IDs returned HTTP 400. Text exceeding 5,000 characters returned HTTP 413. All returned structured JSON errors without crashing.

### Baseline conclusion

Four of the five acceptance criteria were met.

The major numerical failure was score separation. The staff attack set independently demonstrated that meeting the false-positive criterion on one collection of human writing does not guarantee good behavior across other writing styles.

The largest practical concern was the six high-confidence AI accusations against staff-designated human-written passages.

---

<!-- PROJECT8_RAW_EVIDENCE -->
### Real Evaluation Output — Before and After

The JSON below is actual output from the first trial of each scenario.
All three trials are preserved in the committed `results/` files.

#### Before — Trial 1

**paper human passages**

```json
[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4189321317629119,
    "model_score": 0.477,
    "style_score": 0.36086426352582385,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "In 1915, T. S. Eliot opened a poem with three lines that have remained"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.36203647267053907,
    "model_score": 0.2976,
    "style_score": 0.4264729453410781,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The diagnosis demands a foundation that post-Absolute-truth provides. "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5233979445302617,
    "model_score": 0.4915,
    "style_score": 0.5552958890605234,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The Absolute does not collapse cleanly, however, and the precise mecha"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5377248953180376,
    "model_score": 0.5759,
    "style_score": 0.49954979063607513,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "If interpretation is the condition of finite existence rather than a m"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5336007652051187,
    "model_score": 0.5523,
    "style_score": 0.5149015304102372,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Michel Foucault completes the triangulation by providing historical co"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5155485006209006,
    "model_score": 0.4939,
    "style_score": 0.5371970012418011,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The answer depends on whether the algorithm provides what hermeneutic "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3691843812489079,
    "model_score": 0.3051,
    "style_score": 0.4332687624978158,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Umberto Eco specifies the resistance mechanism with precision. In *The"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3641169693217561,
    "model_score": 0.2671,
    "style_score": 0.4611339386435122,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Algorithmic feedback systems are engineered, with extraordinary techni"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4442873802519298,
    "model_score": 0.3298,
    "style_score": 0.5587747605038597,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Lorenzo Simpson extends Anderson\u2019s distributional analysis. In *Toward"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.42336021798745754,
    "model_score": 0.4672,
    "style_score": 0.3795204359749151,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The potential for discontent alone, however, has rarely transformed ci"
  }
]
```

**separation human**

```json
[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4189321317629119,
    "model_score": 0.477,
    "style_score": 0.36086426352582385,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "In 1915, T. S. Eliot opened a poem with three lines that have remained"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.36203647267053907,
    "model_score": 0.2976,
    "style_score": 0.4264729453410781,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The diagnosis demands a foundation that post-Absolute-truth provides. "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5233979445302617,
    "model_score": 0.4915,
    "style_score": 0.5552958890605234,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The Absolute does not collapse cleanly, however, and the precise mecha"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5377248953180376,
    "model_score": 0.5759,
    "style_score": 0.49954979063607513,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "If interpretation is the condition of finite existence rather than a m"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5336007652051187,
    "model_score": 0.5523,
    "style_score": 0.5149015304102372,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Michel Foucault completes the triangulation by providing historical co"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5155485006209006,
    "model_score": 0.4939,
    "style_score": 0.5371970012418011,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The answer depends on whether the algorithm provides what hermeneutic "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3691843812489079,
    "model_score": 0.3051,
    "style_score": 0.4332687624978158,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Umberto Eco specifies the resistance mechanism with precision. In *The"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3641169693217561,
    "model_score": 0.2671,
    "style_score": 0.4611339386435122,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Algorithmic feedback systems are engineered, with extraordinary techni"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4442873802519298,
    "model_score": 0.3298,
    "style_score": 0.5587747605038597,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Lorenzo Simpson extends Anderson\u2019s distributional analysis. In *Toward"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.42336021798745754,
    "model_score": 0.4672,
    "style_score": 0.3795204359749151,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The potential for discontent alone, however, has rarely transformed ci"
  }
]
```

**separation AI**

```json
[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6399781984254715,
    "model_score": 0.7007,
    "style_score": 0.5792563968509431,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Artificial intelligence is becoming an important part of modern commun"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6258687182226467,
    "model_score": 0.6726,
    "style_score": 0.5791374364452934,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The role of technology in education has expanded significantly over th"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6395812523705194,
    "model_score": 0.6555,
    "style_score": 0.6236625047410389,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Human understanding is shaped by the experiences, assumptions, and cul"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5131149371959687,
    "model_score": 0.434,
    "style_score": 0.5922298743919373,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Recommendation systems influence how people discover music, news, ente"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.48716542383560757,
    "model_score": 0.408,
    "style_score": 0.5663308476712152,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Questions of authorship have become more complicated as generative too"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5405581793485781,
    "model_score": 0.4665,
    "style_score": 0.6146163586971563,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Public institutions depend on procedures that allow people to challeng"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.45674712383249283,
    "model_score": 0.3314,
    "style_score": 0.5820942476649856,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The fairness of an automated writing detector cannot be evaluated thro"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4557025395680702,
    "model_score": 0.3912,
    "style_score": 0.5202050791361404,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Writing style varies across genres, audiences, and individual preferen"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6179450476748454,
    "model_score": 0.6308,
    "style_score": 0.6050900953496908,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Many people use digital tools to reduce the amount of time spent on ro"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4319348831825891,
    "model_score": 0.3286,
    "style_score": 0.5352697663651782,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Democratic discussion requires citizens to encounter claims they do no"
  }
]
```

**label coverage**

```json
[
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.16201907278212122,
    "model_score": 0.0459,
    "style_score": 0.27813814556424243,
    "label": "We think this was probably written by a person.",
    "sent": "Late again. Coffee spilled. Still made it to class."
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4734484126984127,
    "model_score": 0.3215,
    "style_score": 0.6253968253968254,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The old library was quiet after the rain, and the stairs smelled like "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6399781984254715,
    "model_score": 0.7007,
    "style_score": 0.5792563968509431,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Artificial intelligence is becoming an important part of modern commun"
  }
]
```

**invalid inputs**

```json
[
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"creator_id\": \"eval_missing_text\"}"
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "(empty text)"
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"text\": \"A valid piece of writing but no creator ID\"}"
  },
  {
    "status": 413,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
]
```

**Appeal reliability — Trial 1**

```json
[
  {
    "case": 1,
    "content_id": "a6015987-f306-4ce1-8746-310e08f9061f",
    "reasoning": "Review requested for trial 1, case 1.",
    "submit_status": 200,
    "appeal_status": 200,
    "appeal_response": {
      "content_id": "a6015987-f306-4ce1-8746-310e08f9061f",
      "message": "Your appeal has been recorded.",
      "status": "under_review"
    },
    "passed": true
  },
  {
    "case": 2,
    "content_id": "71ab8f83-6c22-4fae-b159-b2f06792b6c9",
    "reasoning": "Review requested for trial 1, case 2.",
    "submit_status": 200,
    "appeal_status": 200,
    "appeal_response": {
      "content_id": "71ab8f83-6c22-4fae-b159-b2f06792b6c9",
      "message": "Your appeal has been recorded.",
      "status": "under_review"
    },
    "passed": true
  },
  {
    "case": 3,
    "content_id": "312e3f7a-26b1-471d-a0fb-5ce4b9449bb5",
    "reasoning": "Review requested for trial 1, case 3.",
    "submit_status": 200,
    "appeal_status": 200,
    "appeal_response": {
      "content_id": "312e3f7a-26b1-471d-a0fb-5ce4b9449bb5",
      "message": "Your appeal has been recorded.",
      "status": "under_review"
    },
    "passed": true
  },
  {
    "case": 4,
    "content_id": "f4a8291c-b8b7-475a-adf6-2ac9383f2152",
    "reasoning": "Review requested for trial 1, case 4.",
    "submit_status": 200,
    "appeal_status": 200,
    "appeal_response": {
      "content_id": "f4a8291c-b8b7-475a-adf6-2ac9383f2152",
      "message": "Your appeal has been recorded.",
      "status": "under_review"
    },
    "passed": true
  },
  {
    "case": 5,
    "content_id": "31e38787-3337-4b41-8b3d-a33944c1db61",
    "reasoning": "Review requested for trial 1, case 5.",
    "submit_status": 200,
    "appeal_status": 200,
    "appeal_response": {
      "content_id": "31e38787-3337-4b41-8b3d-a33944c1db61",
      "message": "Your appeal has been recorded.",
      "status": "under_review"
    },
    "passed": true
  }
]
```

#### After — Trial 1

**paper human passages**

```json
[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4189321317629119,
    "model_score": 0.477,
    "style_score": 0.36086426352582385,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "In 1915, T. S. Eliot opened a poem with three lines that have remained"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.36203647267053907,
    "model_score": 0.2976,
    "style_score": 0.4264729453410781,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The diagnosis demands a foundation that post-Absolute-truth provides. "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5233979445302617,
    "model_score": 0.4915,
    "style_score": 0.5552958890605234,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The Absolute does not collapse cleanly, however, and the precise mecha"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5377248953180376,
    "model_score": 0.5759,
    "style_score": 0.49954979063607513,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "If interpretation is the condition of finite existence rather than a m"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5336007652051187,
    "model_score": 0.5523,
    "style_score": 0.5149015304102372,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Michel Foucault completes the triangulation by providing historical co"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5155485006209006,
    "model_score": 0.4939,
    "style_score": 0.5371970012418011,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The answer depends on whether the algorithm provides what hermeneutic "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3691843812489079,
    "model_score": 0.3051,
    "style_score": 0.4332687624978158,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Umberto Eco specifies the resistance mechanism with precision. In *The"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3641169693217561,
    "model_score": 0.2671,
    "style_score": 0.4611339386435122,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Algorithmic feedback systems are engineered, with extraordinary techni"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4442873802519298,
    "model_score": 0.3298,
    "style_score": 0.5587747605038597,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Lorenzo Simpson extends Anderson\u2019s distributional analysis. In *Toward"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.42336021798745754,
    "model_score": 0.4672,
    "style_score": 0.3795204359749151,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The potential for discontent alone, however, has rarely transformed ci"
  }
]
```

**separation human**

```json
[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4189321317629119,
    "model_score": 0.477,
    "style_score": 0.36086426352582385,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "In 1915, T. S. Eliot opened a poem with three lines that have remained"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.36203647267053907,
    "model_score": 0.2976,
    "style_score": 0.4264729453410781,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The diagnosis demands a foundation that post-Absolute-truth provides. "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5233979445302617,
    "model_score": 0.4915,
    "style_score": 0.5552958890605234,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The Absolute does not collapse cleanly, however, and the precise mecha"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5377248953180376,
    "model_score": 0.5759,
    "style_score": 0.49954979063607513,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "If interpretation is the condition of finite existence rather than a m"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5336007652051187,
    "model_score": 0.5523,
    "style_score": 0.5149015304102372,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Michel Foucault completes the triangulation by providing historical co"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5155485006209006,
    "model_score": 0.4939,
    "style_score": 0.5371970012418011,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The answer depends on whether the algorithm provides what hermeneutic "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3691843812489079,
    "model_score": 0.3051,
    "style_score": 0.4332687624978158,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Umberto Eco specifies the resistance mechanism with precision. In *The"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.3641169693217561,
    "model_score": 0.2671,
    "style_score": 0.4611339386435122,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Algorithmic feedback systems are engineered, with extraordinary techni"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4442873802519298,
    "model_score": 0.3298,
    "style_score": 0.5587747605038597,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Lorenzo Simpson extends Anderson\u2019s distributional analysis. In *Toward"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.42336021798745754,
    "model_score": 0.4672,
    "style_score": 0.3795204359749151,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The potential for discontent alone, however, has rarely transformed ci"
  }
]
```

**separation AI**

```json
[
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6399781984254715,
    "model_score": 0.7007,
    "style_score": 0.5792563968509431,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Artificial intelligence is becoming an important part of modern commun"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6258687182226467,
    "model_score": 0.6726,
    "style_score": 0.5791374364452934,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The role of technology in education has expanded significantly over th"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6395812523705194,
    "model_score": 0.6555,
    "style_score": 0.6236625047410389,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Human understanding is shaped by the experiences, assumptions, and cul"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5131149371959687,
    "model_score": 0.434,
    "style_score": 0.5922298743919373,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Recommendation systems influence how people discover music, news, ente"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.48716542383560757,
    "model_score": 0.408,
    "style_score": 0.5663308476712152,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Questions of authorship have become more complicated as generative too"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.5405581793485781,
    "model_score": 0.4665,
    "style_score": 0.6146163586971563,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Public institutions depend on procedures that allow people to challeng"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.45674712383249283,
    "model_score": 0.3314,
    "style_score": 0.5820942476649856,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The fairness of an automated writing detector cannot be evaluated thro"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4557025395680702,
    "model_score": 0.3912,
    "style_score": 0.5202050791361404,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Writing style varies across genres, audiences, and individual preferen"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6179450476748454,
    "model_score": 0.6308,
    "style_score": 0.6050900953496908,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Many people use digital tools to reduce the amount of time spent on ro"
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4319348831825891,
    "model_score": 0.3286,
    "style_score": 0.5352697663651782,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Democratic discussion requires citizens to encounter claims they do no"
  }
]
```

**label coverage**

```json
[
  {
    "status": 200,
    "guess": "human",
    "confidence": 0.16201907278212122,
    "model_score": 0.0459,
    "style_score": 0.27813814556424243,
    "label": "We think this was probably written by a person.",
    "sent": "Late again. Coffee spilled. Still made it to class."
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.4734484126984127,
    "model_score": 0.3215,
    "style_score": 0.6253968253968254,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "The old library was quiet after the rain, and the stairs smelled like "
  },
  {
    "status": 200,
    "guess": "unsure",
    "confidence": 0.6399781984254715,
    "model_score": 0.7007,
    "style_score": 0.5792563968509431,
    "label": "We cannot confidently tell whether this was written by a person or AI.",
    "sent": "Artificial intelligence is becoming an important part of modern commun"
  }
]
```

**invalid inputs**

```json
[
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"creator_id\": \"eval_missing_text\"}"
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "(empty text)"
  },
  {
    "status": 400,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "{\"text\": \"A valid piece of writing but no creator ID\"}"
  },
  {
    "status": 413,
    "guess": null,
    "confidence": null,
    "model_score": null,
    "style_score": null,
    "label": null,
    "sent": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
  }
]
```

**Appeal reliability — Trial 1**

```json
[
  {
    "content_id": "6c24f138-bcc8-48d4-8af7-e13d53fb4097",
    "reasoning": "After-test appeal, trial 1, case 1.",
    "http_status": 200,
    "response": {
      "content_id": "6c24f138-bcc8-48d4-8af7-e13d53fb4097",
      "message": "Your appeal has been recorded.",
      "status": "under_review"
    },
    "passed": true
  },
  {
    "content_id": "ec4cfb04-895f-46b6-8b28-959ff1e19ed7",
    "reasoning": "After-test appeal, trial 1, case 2.",
    "http_status": 200,
    "response": {
      "content_id": "ec4cfb04-895f-46b6-8b28-959ff1e19ed7",
      "message": "Your appeal has been recorded.",
      "status": "under_review"
    },
    "passed": true
  },
  {
    "content_id": "40e01f64-ecb0-49a8-9d56-d168d3d18ad6",
    "reasoning": "After-test appeal, trial 1, case 3.",
    "http_status": 200,
    "response": {
      "content_id": "40e01f64-ecb0-49a8-9d56-d168d3d18ad6",
      "message": "Your appeal has been recorded.",
      "status": "under_review"
    },
    "passed": true
  },
  {
    "content_id": "27fa0bbf-46b7-4d4d-bcfa-8da613f26408",
    "reasoning": "After-test appeal, trial 1, case 4.",
    "http_status": 200,
    "response": {
      "content_id": "27fa0bbf-46b7-4d4d-bcfa-8da613f26408",
      "message": "Your appeal has been recorded.",
      "status": "under_review"
    },
    "passed": true
  },
  {
    "content_id": "7fc95c17-ffff-4e2c-aeb6-eea2167a9072",
    "reasoning": "After-test appeal, trial 1, case 5.",
    "http_status": 200,
    "response": {
      "content_id": "7fc95c17-ffff-4e2c-aeb6-eea2167a9072",
      "message": "Your appeal has been recorded.",
      "status": "under_review"
    },
    "passed": true
  }
]
```


## The Improvement

### What I changed

I changed exactly one configuration value in `config.py`:

```python
AI_THRESHOLD = 0.75
```

Previously:

```python
AI_THRESHOLD = 0.65
```

The human threshold remained 0.35. Both signals, their 50/50 weights, the input validation, and the label text remained unchanged.

### Why I made this change

The staff attack set included six human-written passages classified as AI, with combined scores between approximately 0.683 and 0.718.

The existing threshold of 0.65 treated these scores as sufficient for a high-confidence accusation. Raising the threshold to 0.75 moves them into the uncertain category instead.

This is a change to the **decision policy**, not an improvement in the underlying accuracy of the scores.

I selected it because wrongly accusing a human writer has greater consequences than declining to make a confident classification.

### Measured results

| Measure | Before | After |
|---|---|---|
| Human-writing probes falsely labeled AI | 6/8 | 0/8 |
| Evasion probes avoiding AI label | 9/10 | 9/10 |
| Unusual malformed text confidently classified | 5/8 | 3/8 |
| Malformed HTTP requests correctly rejected | 12/12 | 12/12 |
| Flood requests blocked after limit | 2/12 | 2/12 |
| AI-vs-human average score gap | 0.0916 | 0.0916 |
| Valid appeals successful | 15/15 | 15/15 |

Under the original attack-verdict convention, broken attacks decreased from **20/56 to 12/56**.

### Attack Run — After

Command:

```bash
python run_attacks.py --set attack_set --label after
```

Output file: `results/attack_run_2026-11-16_1728_after.md`

| ID | HTTP | Classification | Verdict |
|---|---:|---|---|
| EV01 | 200 | unsure | BROKE |
| EV02 | 200 | unsure | BROKE |
| EV03 | 200 | unsure | BROKE |
| EV04 | 200 | unsure | BROKE |
| EV05 | 200 | unsure | BROKE |
| EV06 | 200 | unsure | BROKE |
| EV07 | 200 | unsure | BROKE |
| EV08 | 200 | unsure | BROKE |
| EV09 | 200 | unsure | BROKE |
| EV10 | 200 | ai | HELD |
| FP01 | 200 | unsure | HELD |
| FP02 | 200 | unsure | HELD |
| FP03 | 200 | unsure | HELD |
| FP04 | 200 | unsure | HELD |
| FP05 | 200 | unsure | HELD |
| FP06 | 200 | unsure | HELD |
| FP07 | 200 | unsure | HELD |
| FP08 | 200 | human | HELD |
| PI01 | 200 | unsure | HELD* |
| PI02 | 200 | human | HELD* |
| PI03 | 200 | unsure | HELD* |
| PI04 | 200 | unsure | HELD* |
| PI05 | 200 | unsure | HELD* |
| PI06 | 200 | unsure | HELD* |
| MF01 | 400 | — | HELD |
| MF02 | 400 | — | HELD |
| MF03 | 200 | human | BROKE |
| MF04 | 200 | human | BROKE |
| MF05 | 200 | ai | BROKE |
| MF06 | 200 | unsure | HELD |
| MF07 | 200 | unsure | HELD |
| MF08 | 413 | — | HELD |
| RQ01 | 400 | — | HELD |
| RQ02 | 400 | — | HELD |
| RQ03 | 400 | — | HELD |
| RQ04 | 400 | — | HELD |
| RQ05 | 400 | — | HELD |
| RQ06 | 400 | — | HELD |
| RQ07 | 400 | — | HELD |
| RQ08 | 400 | — | HELD |
| RQ09 | 400 | — | HELD |
| RQ10 | 400 | — | HELD |
| RQ11 | 400 | — | HELD |
| RQ12 | 400 | — | HELD |
| FL01_01 | 200 | human | HELD |
| FL01_02 | 200 | human | HELD |
| FL01_03 | 200 | human | HELD |
| FL01_04 | 200 | human | HELD |
| FL01_05 | 200 | human | HELD |
| FL01_06 | 200 | human | HELD |
| FL01_07 | 200 | human | HELD |
| FL01_08 | 200 | human | HELD |
| FL01_09 | 200 | human | HELD |
| FL01_10 | 200 | human | HELD |
| FL01_11 | 429 | — | HELD |
| FL01_12 | 429 | — | HELD |

*Prompt-injection verdicts remain provisional. The responses did not establish that injected instructions controlled the service; PI02 returned `human`, but its numerical score did not match the attack's requested value.*

### After-improvement acceptance criteria

| Criterion | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|
| 1. False positives, target ≤1/10 | 0/10 | 0/10 | 0/10 | MET |
| 2. Score separation, target ≥0.30 | 0.0916 | 0.0916 | 0.0916 | MISSED |
| 3. Label coverage, target 3/3 | 3/3 | 3/3 | 3/3 | MET |
| 4. Appeals, target 5/5 | 5/5 | 5/5 | 5/5 | MET |
| 5. Invalid inputs, target 4/4 | 4/4 | 4/4 | 4/4 | MET |

The threshold change left the average score-separation gap unchanged, as expected. The same underlying model and stylometry scores were being calculated.

The five appeals succeeded in each after-improvement trial. Score-boundary tests also confirmed that all three classifications remained reachable.

### Did the improvement help?

**Yes, for the problem it was designed to address.**

The staff false-positive count dropped from six to zero without reducing the service's ability to accept valid requests, reject invalid request structures, record appeals, or enforce rate limits.

However, the improvement did not increase the detector's ability to distinguish AI from human writing. It simply required stronger evidence before the service returned a confident AI accusation.

---

## What's Still Broken

### AI-generated writing can evade classification

Nine of ten AI-evasion probes still avoided an AI label. The detector classified them as uncertain.

These attacks involved typos, sentence restructuring, pasted quotations, changes in vocabulary, punctuation manipulation, short text, and added human-style introductions.

**Diagnosis:** The model and stylometry signals respond to the statistical properties of the submitted text, not directly to how it was produced. Edits can shift those properties without changing the text's origin.

The combining rule then averages the affected scores, often leaving them in the uncertain band.

**What I would fix next:** Evaluate stronger detection signals with a more diverse dataset and measure the effects of editing and paraphrasing. I would also consider provenance evidence rather than relying entirely on text classification.

### Score separation remains below target

The average difference between AI and human scores remains 0.0916, far below my required 0.30.

**Diagnosis:** Both signals individually show weak separation. Changing the final classification threshold cannot repair that.

**What I would fix next:** Develop a better evaluation dataset with more varied writing, then reconsider feature selection, signal calibration, and whether perplexity is useful for this task.

### Meaningless inputs can receive confident labels

MF03 returned `human` for control characters, MF04 returned `human` for punctuation-only text, and MF05 returned `ai` for an extremely long single word.

**Diagnosis:** The route permits some inputs that contain insufficient meaningful language. The scoring pipeline then attempts to interpret them as writing anyway.

**What I would fix next:** Introduce input validation for meaningful linguistic content, while avoiding overly restrictive rules that would reject legitimate unusual writing.

The Arabic-language probe, MF07, is especially important to distinguish from meaningless text. Arabic is valid human language. Its original confident AI classification showed that an English-oriented detector may behave unfairly on multilingual inputs. After the threshold change it became uncertain, but the underlying language-support problem remains.

### Audit logging is incomplete for some rejected requests

The first extracted audit log contained identifiable rejection events for only five of the twelve malformed HTTP requests.

**Diagnosis:** Some validation paths appear to return HTTP errors without calling the audit logger.

**What I would fix next:** Log rejected requests consistently, including requests that fail before normal submission validation, while ensuring sensitive or malformed payloads are not unnecessarily stored.

### Security and operational limitations

The rate limiter uses caller-supplied creator IDs when available, which a malicious caller could change. Its in-memory counters also do not survive service restarts.

These are design limitations rather than demonstrated compromises in the attack run.

I would eventually use authenticated identities and durable rate-limit storage for a deployed service.

### Why I stopped here

The assignment called for one controlled improvement and a before-and-after measurement. I changed only the AI classification threshold so the results could be meaningfully compared.

Making additional changes to validation, model scoring, or rate limiting during the same experiment would make it harder to determine which change produced which outcome.

### The production tradeoff

If Provenance Guard were used in a real writing platform, I would prioritize avoiding false accusations over confidently detecting every AI-written passage.

The cost is that more AI-generated text receives an uncertain classification. I consider that preferable to treating weak statistical evidence as proof that a person did not write their own work.

**I would not use this detector's classification alone as evidence of academic misconduct or dishonesty.** It should support cautious review, not substitute for reliable provenance evidence and human judgment.

---

### Unit 8 — How I Used AI

I used ChatGPT as a learning and debugging assistant during the red-teaming process.

It helped me interpret the attack-run results, organize the evaluation scenarios, calculate the numerical acceptance-criterion outcomes, and understand how different scoring stages contributed to failures. I supplied my own writing from *Algorithmic Aphasia* as human-authored test material, while AI-generated samples were used as comparison data.

ChatGPT also suggested changing the AI classification threshold from 0.65 to 0.75 after we examined the original false-positive results. I made and tested that single change, ran the actual before-and-after evaluations, and reviewed the measured tradeoff.

AI also assisted with formatting and drafting the README documentation. The reported test results came from the project scripts and actual service responses, not invented examples.

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
