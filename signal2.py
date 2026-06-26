import string
import re
from collections import Counter

def signal2_response(text: str) -> dict:
    if not text or not text.strip():
        return {
        "classification": "uncertain",
        "stylometric_score": 0.5,
        "input": text
    }
    
    # Type Token Ratio Computed 
    # 1. Clean the text: lowercase it and remove punctuation
    cleaned_text = text.lower().translate(str.maketrans("", "", string.punctuation)).split()

    # 2. Split into a list of words
    words = cleaned_text.split()

    # 3. Get frequencies using a dictionary (Counter)
    word_frequencies = Counter(words)

    # 4. Calculate Type-Token Ratio
    unique_words = len(word_frequencies)  # Number of keys in the dictionary
    total_words = len(words)              # Total number of elements in the list

    ttr = unique_words / total_words if total_words > 0 else 0

    print(f"Unique words (Types): {unique_words}, Total words (Tokens): {total_words}, Type-Token Ratio (TTR): {ttr:.4f}")
    
    # Sentence Length Variation
    # 1. Split the text into sentences using regex (splits on ., !, or ? followed by a space or end of string)
    # The [?!.] matches any of those punctuation marks, and \s* handles trailing spaces.
    sentences = [s.strip() for s in re.split(r'[?!.]\s*', text) if s.strip()]

    # 2. Calculate the length of each sentence (number of characters)
    # We use a dictionary (Counter) to track the frequencies of these lengths.
    sentence_lengths = [len(sentence) for sentence in sentences]
    length_frequencies = Counter(sentence_lengths)

    # 3. Display the results nicely, sorted by sentence length
    print(f"{'Sentence Length':<20} | {'Frequency':<10}")
    print("-" * 35)
    for length in sorted(length_frequencies.keys()):
        print(f"{length:<20} | {length_frequencies[length]:<10}")

    #(Standard Deviation)
    if len(sentence_lengths) > 1:
        mean_len = sum(sentence_lengths) / len(sentence_lengths)
        variance = sum((x - mean_len) ** 2 for x in sentence_lengths) / len(sentence_lengths)
        std_dev = variance ** 0.5
        print( "\n" + "-" * 35)
        print(f"Average Sentence Length: {mean_len:.2f} chars")
        print(f"Sentence Length Variation (Std Dev): {std_dev:.2f}")

    #  Length Variation
    # 1. Define what counts as punctuation
    # string.punctuation includes: !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~
    punctuation_set = set(string.punctuation)

    # 2. Count punctuation per sentence
    punctuation_counts = []
    for sentence in sentences:
        # Count how many characters in the sentence are punctuation marks
        punc_count = sum(1 for char in sentence if char in punctuation_set)
        punctuation_counts.append(punc_count)

    # 3. Create the frequency dictionary (Key: punc count, Value: how many sentences)
    punc_frequencies = Counter(punctuation_counts)

    # 4. Display the dictionary results
    print(f"{'Punctuation Count':<20} | {'Sentence Frequency':<10}")
    print("-" * 38)
    for count in sorted(punc_frequencies.keys()):
        print(f"{count:<20} | {punc_frequencies[count]:<10}")

    # 5. Calculate the Standard Deviation Metric
    if len(punctuation_counts) > 1:
        mean_punc = sum(punctuation_counts) / len(punctuation_counts)
    
        # Variance is the average of the squared differences from the Mean
        variance = sum((x - mean_punc) ** 2 for x in punctuation_counts) / len(punctuation_counts)
    
        # Standard deviation is the square root of variance
        std_dev_punc = variance ** 0.5
    
        print("\n" + "-" * 38)
        print(f"Average Punctuation/Sentence: {mean_punc:.2f}")
        print(f"Punctuation Variation (Std Dev): {std_dev_punc:.2f}")
    
    return {
        "classification": "uncertain",
        "stylometric_score": 0.5,
        "input": text
    }

def calculate_stylometric_score(ttr, sentence_sd, punc_sd):
    """
    Combines TTR, Sentence SD, and Punctuation SD into a 0.0 - 1.0 AI-likelihood score.
    Higher score = lower variation = Higher AI likelihood.
    """
    # 1. Define typical human baselines for normalization (Min, Max)
    # These bounds map raw scores onto a uniform 0.0 to 1.0 scale.
    ttr_bounds = (0.3, 0.8)       # AI often clusters low; diverse human text goes high
    sent_bounds = (2.0, 25.0)     # Standard deviation of sentence character lengths
    punc_bounds = (0.1, 2.5)      # Standard deviation of punctuation counts

    def normalize_and_invert(val, bounds):
        # Clip values to bounds so we don't exceed 0 or 1
        val = max(bounds[0], min(val, bounds[1]))
        # Standard Min-Max formula: (val - min) / (max - min)
        normalized = (val - bounds[0]) / (bounds[1] - bounds[0])
        # Invert it: High variation (Human) becomes close to 0, Low variation (AI) becomes close to 1
        return 1.0 - normalized

    # 2. Normalize and invert all three metrics
    ttr_score = normalize_and_invert(ttr, ttr_bounds)
    sent_score = normalize_and_invert(sentence_sd, sent_bounds)
    punc_score = normalize_and_invert(punc_sd, punc_bounds)

    # 3. Apply weights based on feature reliability
    # TTR and Sentence Structure are historically the strongest indicators
    weights = {
        'ttr': 0.35,
        'sentence': 0.40,
        'punctuation': 0.25
    }

    final_score = (
        (ttr_score * weights['ttr']) +
        (sent_score * weights['sentence']) +
        (punc_score * weights['punctuation'])
    )

    # 4. Determine Classification Category
    if final_score <= 0.39:
        category = "Human Likely"
    elif 0.40 <= final_score <= 0.60:
        category = "Uncertain"
    else:
        category = "AI Likely"

    return final_score, category


# --- EXAMPLE RUNS ---

# Example A: High variation across the board (Typical human text)
metrics_human = {"ttr": 0.72, "sentence_sd": 18.4, "punc_sd": 1.6}
score, cat = calculate_stylometric_score(**metrics_human)
print(f"Human Sample -> Score: {score:.2f} | Classification: {cat}")

# Example B: Uniform, repetitive variation (Typical AI text)
metrics_ai = {"ttr": 0.41, "sentence_sd": 4.1, "punc_sd": 0.2}
score, cat = calculate_stylometric_score(**metrics_ai)
print(f"AI Sample    -> Score: {score:.2f} | Classification: {cat}")

if __name__ == "__main__":
    print("Signal 2 Testing")