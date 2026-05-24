import re

PHONEME_RULES = [
    {
        "pattern": r"\b(problem is|reason is|answer is|result is|point is|fact is|issue is|question is|solution is|difference is|main thing|only way|best way|real issue)\b",
        "error_type": "article_omission",
        "target_phoneme": "article omission (the / a / an)",
        "bengali_note": "বাংলায় article নেই — 'the' বা 'a' বলার অভ্যাস নেই আমাদের। তাই 'the problem is' বলতে গিয়ে শুধু 'problem is' বেরিয়ে আসে।",
        "drill": "এখন বলো: 'The problem is...' / 'A reason is...' / 'The main issue is...' — article-টা জোর দিয়ে বলো প্রথম কয়েকবার।"
    },
    {
        "pattern": r"\b(veery|goood|baad|niice|fiine|coool|loong|shooort|reead|seee|feeel)\b",
        "error_type": "vowel_elongation",
        "target_phoneme": "vowel elongation — Bengali pure vowels in English short vowel slots",
        "bengali_note": "বাংলার vowel-গুলো স্বভাবতই টানা এবং পরিষ্কার। কিন্তু English-এর short vowel — যেমন 'bit', 'hot', 'cut' — এগুলো ছোট এবং 'lax'। আমরা এগুলোকেও বাংলার মতো টেনে বলি।",
        "drill": "'bit / beat', 'hot / heart', 'cut / cart' — pair-গুলো পাশাপাশি বলো। প্রথমটা ছোট, দ্রুত। দ্বিতীয়টা টানা।"
    },
    {
        "pattern": r"\b(because|not|was|what|want|watch|wash|got|lot|hot|top|stop|problem|common|possible|obvious)\b",
        "error_type": "vowel_quality_substitution",
        "confidence": "possible",
        "target_phoneme": "open back vowel — Bengali /ɑ/ bleeding into English short /ɒ/ and /ʌ/",
        "bengali_note": "বাংলায় 'অ' ধ্বনি open এবং full — 'because', 'not', 'was' বলার সময় এই 'অ'-টা চলে আসে। কিন্তু English-এর এই vowel-গুলো আলাদা — কোনোটা /ɒ/ (গোলাকার), কোনোটা /ʌ/ (মাঝামাঝি)। সব এক রকম শোনায় না।",
        "drill": "'not' এবং 'nut' — দুটো আলাদা vowel। 'hot' এবং 'hut' — আলাদা। এই pair-গুলো আয়নার সামনে বলো, ঠোঁটের shape দেখো।"
    },
    {
        "pattern": r"\b(owater|oword|owork|oworld|owoman|owonder|uwater|uword)\b",
        "error_type": "approximant_onset",
        "target_phoneme": "/w/ onset — bilabial rounding not releasing into vowel smoothly",
        "bengali_note": "বাংলায় /w/-এর মতো ধ্বনি আছে, কিন্তু English /w/-এ ঠোঁট গোল করে শুরু করে vowel-এ মিশিয়ে দিতে হয় — একটা glide। আমাদের উচ্চারণে এই glide-টা কম থাকে।",
        "drill": "'water, word, work, wonder' — /u/ দিয়ে শুরু করো মনে মনে, তারপর সরাসরি vowel-এ চলে যাও। ঠোঁট গোল, দাঁত দূরে।"
    },
]


def detect_errors(transcript: str) -> list[dict]:
    errors = []
    transcript_lower = transcript.lower()

    for rule in PHONEME_RULES:
        matches = re.findall(rule["pattern"], transcript_lower)
        if not matches:
            continue

        if rule["error_type"] == "article_omission":
            real_misses = []
            for match in matches:
                match_pos = transcript_lower.find(match)
                if match_pos == -1:
                    continue
                preceding = transcript_lower[max(0, match_pos - 5):match_pos].strip()
                if re.search(r'\b(the|a|an)$', preceding):
                    continue
                real_misses.append(match)
            if not real_misses:
                continue
            matches = real_misses

        errors.append({
            "error_type": rule["error_type"],
            "target_phoneme": rule["target_phoneme"],
            "confidence": rule.get("confidence", "confirmed"),
            "bengali_note": rule["bengali_note"],
            "drill": rule["drill"],
            "matched_words": list(set(matches)),
        })

    return errors
