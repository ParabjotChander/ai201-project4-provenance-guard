import os
import json
import re
from groq import Groq
from config import LLM_MODEL

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a forensic linguist trained to distinguish human-written text from AI-generated text. Your classifications must be calibrated — most text is human-written, so default skepticism should lean toward human.

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

---

## Output format

Respond ONLY with a valid JSON object:
{
  "confidence": <float 0.0–1.0, where 1.0 = certainly AI>,
  "classification": "<Likely Human | Uncertain | Likely AI>",
  "reasoning": "<2–3 sentences citing the specific signals that drove your score>"
}

Thresholds: 0.00–0.39 = Likely Human · 0.40–0.60 = Uncertain · 0.61–1.00 = Likely AI

Do not include any text outside the JSON object."""


def signal1_response(text: str) -> dict:
    """
    LLM-based AI text detection signal using Groq's llama-3.3-70b-versatile.

    Args:
        text: The input text to classify.

    Returns:
        A dict with keys:
            - confidence (float): Score from 0.0 (human) to 1.0 (AI).
            - classification (str): "Likely Human", "Uncertain", or "Likely AI".
            - reasoning (str): Brief explanation from the model.
            - raw_response (str): The raw model output for auditing.
    """
    if not text or not text.strip():
        return {
            "llm_confidence_score": 0.5,
            "classification": "Uncertain",
            "reasoning": "Empty or blank input provided.",
            "raw_response": "",
        }

    completion = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze the following text:\n\n{text}"},
        ],
        temperature=0.0,
        max_tokens=256,
    )

    raw = completion.choices[0].message.content.strip()

    # Strip markdown code fences if present
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.DOTALL).strip()

    parsed = json.loads(clean)

    confidence = float(parsed["confidence"])
    confidence = max(0.0, min(1.0, confidence))

    # Normalize classification against threshold table
    if confidence <= 0.39:
        classification = "Likely Human"
    elif confidence <= 0.60:
        classification = "Uncertain"
    else:
        classification = "Likely AI"

    return {
        "llm_confidence_score": round(confidence, 2),
        "classification": classification,
        "reasoning": parsed.get("reasoning", ""),
        "raw_response": raw,
    }

if __name__ == "__main__":
    print("Signal 1 Testing")
    # Empty String
    test_string0 = ""
    signal1_test0 = signal1_response(test_string0)
    print(signal1_test0["classification"], signal1_test0["llm_confidence_score"])

    # Human Response
    test_string = "The sun dipped below the horizon, painting the sky in hues of amber and rose. I sat on the porch, coffee in hand, watching the neighborhood slowly go quiet."
    signal1_test1 = signal1_response(test_string)
    print(signal1_test1["classification"], signal1_test1["llm_confidence_score"])
    
    # AI response
    test_string2 = """
    Discover the future of everyday convenience with our revolutionary smart-home device. 
    Seamlessly designed to integrate into your busy lifestyle, this product harnesses advanced automation to save you time and energy. 
    Whether you are managing your daily schedule or enjoying a quiet evening, our innovation ensures a truly elevated experience.
    """
    signal1_test2 = signal1_response(test_string2)
    print(signal1_test2["classification"], signal1_test2["llm_confidence_score"])

