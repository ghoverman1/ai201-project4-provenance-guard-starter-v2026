# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---

## 1. False Positive Rate

Of 10 independently written human passages, no more than **1 out of 10 (10%)** may receive a high-confidence AI-generated label.

**Why this target:**

Falsely accusing a real writer of using AI can damage their reputation and credibility. Failing to detect some AI-generated writing is less harmful than incorrectly accusing a human. Therefore, the system should prioritize avoiding false positives rather than treating both types of errors equally.

---

## 2. Score Separation

Across 10 verified human-written passages and 10 AI-generated passages, the average AI-likelihood score for AI-generated writing must be at least **0.30 higher** than the average score for human-written writing.

**Why this target:**

A model should meaningfully distinguish between human and AI-generated writing. A difference of only 0.05 between average scores would indicate very little separation. I chose 0.30 because it represents a more substantial difference on a 0–1 scale while still recognizing that neither group will necessarily receive scores near the extremes.

---

## 3. Label Coverage

All **3 out of 3** classification labels—high-confidence AI, high-confidence human, and uncertain—must be reachable through their defined score ranges. Every score between 0 and 1 must map to exactly one label.

**Why this target:**

A confidence score is only useful if the system can communicate its meaning clearly. The uncertain category is especially important because AI detection is not perfectly reliable. Every possible score should have an appropriate interpretation, and no label should be impossible to produce.

---

## 4. Appeal Reliability

**5 out of 5 valid appeals (100%)** must successfully change the corresponding submission's status to `under_review`, record the appeal and its reasoning, and return confirmation.

**Why this target:**

If a writer is incorrectly accused of using AI, they must have a reliable opportunity to challenge the classification. Allowing even two out of five appeals to fail would mean 40% of writers could be denied that opportunity. Unlike the detector's predictions, recording a valid appeal is a backend operation that should work consistently.

---

## 5. Invalid Input Handling

The backend must correctly reject **4 out of 4** invalid input cases: missing text, empty text, missing `creator_id`, and text exceeding a **5,000-character limit**.

Each invalid request must return a structured JSON error response with an appropriate HTTP error status without crashing the server.

**Why this target:**

A backend should not crash because a user sends incomplete or excessively large data. Clear error messages let users understand what went wrong and correct their submissions. A character limit also prevents unexpectedly large requests from consuming excessive processing resources. I chose 5,000 characters as an initial limit that can be adjusted if real usage demonstrates a need.

---

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
