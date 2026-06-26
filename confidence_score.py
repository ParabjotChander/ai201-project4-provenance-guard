from signal1 import signal1_response
from signal2 import signal2_response

def compute_confidence_score(llm_score: float, stylometric_score: float) -> float:
    return round((llm_score + stylometric_score) / 2, 2)

if __name__ == "__main__":
    print("Confidence Score Test")
    print("\n")
    # Clearly AI-generated (should score high)
    clear_AI_sample = """Artificial intelligence represents a transformative paradigm shift in modern society. 
    It is important to note that while the benefits of AI are numerous, it is equally 
    essential to consider the ethical implications. Furthermore, stakeholders across 
    various sectors must collaborate to ensure responsible deployment."""
    s1_output_t1 = signal1_response(clear_AI_sample)
    s2_output_t1 = signal2_response(clear_AI_sample)
    t1_confidence_score = compute_confidence_score(s1_output_t1['llm_confidence_score'], s2_output_t1['stylometric_score'])
    print("Signal 1:", s1_output_t1['classification'], s1_output_t1["llm_confidence_score"])
    print("Signal 2:", s2_output_t1['classification'], s2_output_t1["stylometric_score"])
    print("Clearly AI-generated [0.61 - 1.0]", t1_confidence_score)
    print("\n")

    # Clearly human-written (should score low)
    clear_human_sample = """ok so i finally tried that new ramen place downtown and honestly? 
    underwhelming. the broth was fine but they put WAY too much sodium in it and 
    i was thirsty for like three hours after. my friend got the spicy version and 
    said it was better. probably won't go back unless someone drags me there"""
    s1_output_t2 = signal1_response(clear_human_sample)
    s2_output_t2 = signal2_response(clear_human_sample)
    t2_confidence_score = compute_confidence_score(s1_output_t2['llm_confidence_score'], s2_output_t2['stylometric_score'])
    print("Signal 1:", s1_output_t2['classification'], s1_output_t2["llm_confidence_score"])
    print("Signal 2:", s2_output_t2['classification'], s2_output_t2["stylometric_score"])
    print("Clearly Human [0.0 - 0.39]", t2_confidence_score)
    print("\n") 

    # Borderline: formal human writing (may score mid-high on stylometrics)
    borderline_sample = """The relationship between monetary policy and asset price inflation has been 
    extensively studied in the literature. Central banks face a fundamental tension 
    between their mandate for price stability and the unintended consequences of 
    prolonged low interest rates on equity and real estate valuations."""
    s1_output_t3 = signal1_response(borderline_sample)
    s2_output_t3 = signal2_response(borderline_sample)
    t3_confidence_score = compute_confidence_score(s1_output_t3['llm_confidence_score'], s2_output_t3['stylometric_score'])
    print("Signal 1:", s1_output_t3['classification'], s1_output_t3["llm_confidence_score"])
    print("Signal 2:", s2_output_t3['classification'], s2_output_t3["stylometric_score"])
    print("Uncertain [0.4 - 0.6]", t3_confidence_score)
    print("\n")

    # Borderline: lightly edited AI output (should ideally score mid-range)
    borderline_2_sample = """I've been thinking a lot about remote work lately. There are genuine tradeoffs — 
    flexibility and no commute on one side, isolation and blurred work-life boundaries 
    on the other. Studies show productivity varies widely by individual and role type."""
    s1_output_t4 = signal1_response(borderline_2_sample)
    s2_output_t4 = signal2_response(borderline_2_sample)
    t4_confidence_score = compute_confidence_score(s1_output_t4['llm_confidence_score'], s2_output_t4['stylometric_score'])
    print("Signal 1:", s1_output_t4['classification'], s1_output_t4["llm_confidence_score"])
    print("Signal 2:", s2_output_t4['classification'], s2_output_t4["stylometric_score"])
    print("Uncertain [0.4 - 0.6]", t4_confidence_score)

"""
Test Results:
Confidence Score Test

# 1 Clearly AI-generated [0.61 - 1.0] 0.67 
# 2 Clearly Human [0.0 - 0.39] 0.23 
# 3 Uncertain [0.4 - 0.6] 0.63 
# 4 Uncertain [0.4 - 0.6] 0.26 
"""