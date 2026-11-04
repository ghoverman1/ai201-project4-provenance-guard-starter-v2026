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

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



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
