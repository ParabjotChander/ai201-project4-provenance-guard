# ai201-project4-provenance-guard

## Project Domain:
Objective: To establish a verifiable framework for distinguishing human-authored creative works from AI-generated content on digital platforms.

Principles:

Creator Protection: Safeguarding the intellectual property and visibility of human artists, writers, and musicians.

Platform Trust: Maintaining ecosystem integrity by ensuring content transparency.Audience 

Context: Providing consumers with clear, verifiable information regarding the origin of digital assets.

## Architecture overview:
<!-- 
the path a submission takes from input to transparency label
-->

### Submission Workflow 
```
User
  |
Flask API: POST /submit
  |
Raw Text
  |
+----------------+
| Groq Signal    |
+----------------+
       |
       +---- classification, llm score
       |
+----------------+
| Stylometry     |
+----------------+
       |
       +---- classification, stylometric score
       |
Confidence Engine ---- (llm score + stylometric score) / 2 
       |
Transparency Label
       |
Audit Log
       |
API Response --- JSON Object
```

### POST /submit Request Audit Log Example

```
{
    "content_id": "aa34a1f6-e9dd-4b99-801f-9a07b6673d8a", 
    "creator_id": "test-user-1", 
    "timestamp": "2026-06-26T23:13:36.304995+00:00", 
    "attribution": "Uncertain", 
    "confidence": 0.47, 
    "llm_score": 0.25, 
    "stylometric_score": 0.69, 
    "status": "classified"
}

```

### Appeal Workflow
```
User
    |
POST /appeal
    |
Appeal Reason and Content ID
    |
Status = Under Review
    |
GET /log
    |
Audit Log
    |
Response --- JSON Object
```

### POST /appeal Request Audit Log Example

```
{
    "content_id": "aa34a1f6-e9dd-4b99-801f-9a07b6673d8a",
    "creator_id": "test-user-1", 
    "event": "appeal_submitted", 
    "status": "under_review", 
    "original_attribution": "Uncertain", 
    "original_confidence": 0.47, 
    "llm_score": 0.25, 
    "stylometric_score": 0.69, 
    "creator_reasoning": "I wrote this myself from personal experience I am a non-native English speaker and my writing style may appear more formal than typical.", 
    "timestamp": "2026-06-26T23:56:16.989277+00:00"
}
```

## Detection signals:
<!-- 
what each signal measures, why you chose it, and what it misses
-->

### Detection Signal 1: LLM-based Classification

Measures: 

Semantics, Tone, Context

Choice Reason: 

Captures semantic and stylistic coherence holistically. Humans tend to be more informal in terms of tone, grammar is more loose, slang can be used. AI writing has a more formal tone, less emotion, grammar correct, usually answering an question!

What it Misses: Word Structure 

### Detection Signal 2: Stylometric Heuristics

Measures: 

Type-Token Ratio (unique words / total words) \
Sentence Length Variation (standard deviation) \
Punctuation Variation (standard deviation)

Choice Reason: 

Measures statistical properties that differ between human and AI writing. High type-token ratio, sentence and punctuation variations are a good indicator for human writing. AI tends to use common words, punctuations and sentence lengths.

What it Misses: Semantics, Tone, Context

## Confidence scoring
<!-- 
how you combined signals into a score, how you validated it's meaningful, and two example submissions with noticeably different confidence scores (one high-confidence, one lower-confidence) showing the actual scores
-->

Scores Threshold:
Score: Range is 0.0 to 1.0 (float number) \
0.0-0.39 => Likely Human \
0.4-0.60 => Uncertain \
0.61-1.0 => Likely AI 

Signal 1 => LLM score, LLM Model generates this score (threshold, system prompt given)

Signal 2 => Stylometric score

1. Type Token Ratio => Unique Words / Total Words  
2. Sentence Length Variation (Standard Deviation) 
3. Punctuation Variation Per Sentence (Standard Deviation)

Normailized & Inverted these 3 values into an stylometric score 

Confidence Score = (LLM Score + Stylometric Score) / 2 
Average of both signal scores = Weight of each signal score is 50% 

I validated it's meaningful by doing some research & looking over the class lecture slides. Both mentioned having weighted averages, my weight averages are NOT BIASED since each signal score weight is 50%.

### 2 POST /Submit Requests Audit Logs Examples

Likely AI Text \
"Artificial intelligence represents a transformative paradigm shift in modern society. 
    It is important to note that while the benefits of AI are numerous, it is equally 
    essential to consider the ethical implications. Furthermore, stakeholders across 
    various sectors must collaborate to ensure responsible deployment."

```
{
    "content_id": "c89a3c3a-000e-4e8d-8434-c1a473494bfe", 
    "creator_id": "test-user-1", 
    "timestamp": "2026-06-26T23:15:49.726792+00:00", 
    "attribution": "Likely AI", 
    "confidence": 0.68, 
    "llm_score": 0.85, 
    "stylometric_score": 0.51, 
    "status": "classified"
}
```

Likely Human Text \
"ok so i finally tried that new ramen place downtown and honestly? 
underwhelming. the broth was fine but they put WAY too much sodium in it and 
i was thirsty for like three hours after. my friend got the spicy version and 
said it was better. probably won't go back unless someone drags me there"

```
{
    "content_id": "d685a3c3-2f05-4fbd-8b20-808226565455", 
    "creator_id": "test-user-1", 
    "timestamp": "2026-06-26T23:40:18.164441+00:00", 
    "attribution": "Likely Human", 
    "confidence": 0.24, 
    "llm_score": 0.05, 
    "stylometric_score": 0.43, 
    "status": "classified"
}
```

## Transparency label:
<!-- 
typed description of all three variants (high-confidence AI, human, uncertain) showing the exact text each one displays; screenshot or mockup optional
-->
Likely AI 

```
This content was classified as AI-generated with high confidence
```

Likely Human
```
This content appears to be human-written with low confidence.
```

Uncertain
```
The system could not confidently determine the origin of this content.
```

## Rate limiting: 
<!-- 
the limits you chose and your reasoning for those specific values
-->
### 10 /submit & /appeal requests per minute, 100 per day
Reasoning: I don't want users to have too many requests to the point where the server gets flooded, slows down or even shuts down. 10 requests per minute & 100 per day is reasonable and realistic for users.

Applied on /submit Workflow
```
@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
```

Applied on /appeal Workflow
```
@app.route("/appeal", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
```

Rate Test Limiting 

CLI Command 

```
for i in $(seq 1 12); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:5000/submit \
    -H "Content-Type: application/json" \
    -d '{"text": "This is a test submission for rate limit testing purposes only.", "creator_id": "ratelimit-test"}'
done
```

CLI Output

```
200
200
200
200
200
200
200
200
200
200
429
429
```

## Known limitations:
<!-- 
at least one specific type of content your system would likely misclassify and why
-->
One specific type of text my system will misclassify is short (less than 100 characters) human text for AI, examples include excerpts from literary works(poems, novels). The flaws appear in signal 2, type-token ratio is highly sensitive to text length. In a tiny sample of 49 words, it is incredibly easy to maintain a high TTR because the text ends before repeated common vocabulary appear in the literary work. Less sentences means less sentence length variation and same goes for punctuation variation per sentence.


## Spec reflection:
<!-- 
one way the spec helped you, one way implementation diverged from it and why
-->
One way the spec helped me by giving me an idea of what to start with. I know I had to implement the signal methods first and than wire them to the API request methods. Got an better understanding of FLASK Python.
One way my implementation diverged from it was that I originally thought of combining the signals by doing an majority vote where each signal votes on a label, the majority wins. The problem with approach is that there are only 2 signals and each signal has flaws so it was better to do a 50 50 weight average.

## AI Usage:
<!-- 
at least 2 specific instances describing what you directed the AI to do and what you revised or overrode
-->

**Instance 1** Detection Tool Signal 1 LLM Model, Better System Prompt (Milestone 4)

- *What I gave the AI:* My original system prompt, Transparency Labels, Detection Signal Description (planning.md), test cases provided in milestone 4 where I got bad results.
 
- *What it produced:*
Modified System Prompt
```
You are a forensic linguist trained to distinguish human-written text from AI-generated text. Your classifications must be calibrated — most text is human-written, so default skepticism should lean toward human.

---

## Core Principle: Absence of AI signals is not proof of AI

Short, simple, or unremarkable writing is NOT evidence of AI generation. AI-generated text has specific, detectable patterns. Human text is often messy, inconsistent, and contextually grounded in ways AI rarely replicates.

---

## Evaluate these AI-positive signals (each raises the score):

- **Structural symmetry**: Does every paragraph follow the same arc? Does the text feel assembled rather than written?
- **Hedging inflation**: Excessive qualifiers ("it is worth noting", "it is important to consider") with no personal stance.
- **Generic specificity**: Details that sound concrete but are interchangeable (e.g., "a bustling city street", "a complex and nuanced issue").
- **Smooth transitions**: AI over-uses connector phrases ("Furthermore,", "In conclusion,", "Building on this idea,").
- **Tonal flatness**: No register shifts — no moment of frustration, humor, digression, or personality bleed.
- **Lexical optimization**: Word choices that are consistently "correct" but never idiosyncratic, slangy, or surprising.

## Evaluate these Human-positive signals (each lowers the score):

- **Colloquialisms and informal register**: slang, contractions, run-ons, or sentence fragments used naturally.
- **Emotional specificity**: Reactions tied to a concrete moment ("i was thirsty for like three hours after").
- **Opinionated asymmetry**: The writer cares more about some things than others in a way that feels unplanned.
- **Idiosyncratic detail**: Details that are oddly specific in a human way — not the kind an AI would invent to seem authentic.
- **Inconsistency**: Tonal shifts, imperfect grammar, or self-correction mid-thought.
- **Genuine uncertainty or ambivalence** that isn't performative.

---

## Calibration anchors

**Score ~0.05 — Clearly human**: "ok so i finally tried that ramen place and honestly? underwhelming. broth was fine but WAY too salty, was thirsty for hours. probably won't go back"
→ Informal register, emotional reaction, idiosyncratic capitalization, casual fragmentation.

**Score ~0.30 — Likely human**: A personal email or blog post with mostly clear sentences but some personality, opinion, and informal phrasing.

**Score ~0.50 — Uncertain**: Clean, competent writing with no strong signals either way. Could be a careful human or lightly edited AI output.

**Score ~0.75 — Likely AI**: Well-structured essay or explanation with smooth transitions, balanced hedging, and no personality bleed.

**Score ~0.95 — Clearly AI**: "In today's rapidly evolving landscape, it is essential to consider the multifaceted dimensions of this issue. By examining both the opportunities and the challenges, we can arrive at a more nuanced understanding."
```

- *What I changed or overrode:*
Changed my original system prompt for the new system prompt.

**Instance 2** Appeal Workflow (Milestone 5)

- *What I gave the AI:* Appeal workflow description, Appeal Architecture, Transparency Labels (planning.md)
 
- *What it produced:*
Appeal workflow function and explanation (Pseudocode)

- *What I changed or overrode:*
I tested the appeal API request, thought I fully checked it but got an error.

```
File "/Users/parabjotchander/Desktop/CodePath/Week 4/Project/ai201-project4-provenance-guard/.venv/lib/python3.12/site-packages/flask/app.py", line 902, in dispatch_request
    return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
```

The Problem: Classic Python slice behavior — lines[-None:] is invalid.

Quick Fix in read_log method: The if limit is None branch needs to come before any slicing attempt — lines[-None:] never gets evaluated that way. Swap that in and the appeal endpoint will work.
```
def read_log(limit=20):
    try:
        with open(LOG_PATH) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []
    if limit is None:
        return [json.loads(line) for line in lines]
    return [json.loads(line) for line in lines[-limit:]]
```

## Demo Video URL: 

