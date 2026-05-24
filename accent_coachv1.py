"""
Meliglossa — Bengali Accent Coach
Level 1 Proof of Concept

Usage:
    python accent_coach_v1.py <audio_file>

    Example:
        python accent_coach_v1.py my_recording.mp3
        python accent_coach_v1.py my_recording.wav

Supported formats: mp3, wav, m4a, ogg, flac

Setup (run once):
    pip install openai-whisper anthropic

Set your API key:
    export ANTHROPIC_API_KEY="your-key-here"
    (Get it from https://console.anthropic.com)
"""

import sys
import io #Added because utf error was coming to render Bengali feedback 
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import os
import re
import json
import anthropic
import whisper
from dotenv import load_dotenv
load_dotenv()

# ─────────────────────────────────────────────
# BENGALI L1 INTERFERENCE RULES
# Each rule: (pattern_in_transcript, expected, error_type, bengali_explanation)
# These are the most common Bengali→English transfer errors.
# Expand this list as you discover more from your own recordings.
# ─────────────────────────────────────────────

PHONEME_RULES = [

    # ── RULE 1: Article omission ──────────────────────────────────────
    # Bengali has no articles. The/a/an are systematically dropped.
    # Whisper transcribes what it hears — if article is missing, it shows.
    # Pattern: common noun phrases that always need an article before them.
    {
    "pattern": r"\b(problem is|reason is|answer is|result is|point is|fact is|issue is|question is|solution is|difference is|main thing|only way|best way|real issue)\b",
    "error_type": "article_omission",
    "target_phoneme": "article omission (the / a / an)",
    "bengali_note": "বাংলায় article নেই — 'the' বা 'a' বলার অভ্যাস নেই আমাদের। তাই 'the problem is' বলতে গিয়ে শুধু 'problem is' বেরিয়ে আসে।",
    "drill": "এখন বলো: 'The problem is...' / 'A reason is...' / 'The main issue is...' — article-টা জোর দিয়ে বলো প্রথম কয়েকবার।"
    },

    # ── RULE 3: Vowel elongation ──────────────────────────────────────
    # Bengali vowels are inherently long and pure (monophthongs held fully).
    # English short vowels /ɪ/, /ʊ/, /e/, /ɒ/ get Bengali full-vowel treatment.
    # Whisper occasionally reflects elongation as repeated letters.
    # More importantly — flag the TARGET WORDS where Bengali speakers
    # consistently elongate, so Claude can address them in feedback.
    {
        "pattern": r"\b(veery|goood|baad|niice|fiine|coool|loong|shooort|reead|seee|feeel)\b",
        "error_type": "vowel_elongation",
        "target_phoneme": "vowel elongation — Bengali pure vowels in English short vowel slots",
        "bengali_note": "বাংলার vowel-গুলো স্বভাবতই টানা এবং পরিষ্কার। কিন্তু English-এর short vowel — যেমন 'bit', 'hot', 'cut' — এগুলো ছোট এবং 'lax'। আমরা এগুলোকেও বাংলার মতো টেনে বলি।",
        "drill": "'bit / beat', 'hot / heart', 'cut / cart' — pair-গুলো পাশাপাশি বলো। প্রথমটা ছোট, দ্রুত। দ্বিতীয়টা টানা।"
    },

    # ── RULE 4: Vowel quality substitution ───────────────────────────
    # The "aww" pattern you described — Bengali open back vowel bleeding
    # into English words like 'because' (bec-AWZ), 'hot', 'not', 'was'.
    # Whisper may transcribe 'because' correctly but the vowel colour is wrong.
    # We flag the high-frequency words where this substitution is most damaging
    # in IELTS — because Whisper won't catch quality, only Claude can address it.
    {
        "pattern": r"\b(because|not|was|what|want|watch|wash|got|lot|hot|top|stop|problem|common|possible|obvious)\b",
        "error_type": "vowel_quality_substitution",
        "confidence": "possible",
        "target_phoneme": "open back vowel — Bengali /ɑ/ bleeding into English short /ɒ/ and /ʌ/",
        "bengali_note": "বাংলায় 'অ' ধ্বনি open এবং full — 'because', 'not', 'was' বলার সময় এই 'অ'-টা চলে আসে। কিন্তু English-এর এই vowel-গুলো আলাদা — কোনোটা /ɒ/ (গোলাকার), কোনোটা /ʌ/ (মাঝামাঝি)। সব এক রকম শোনায় না।",
        "drill": "'not' এবং 'nut' — দুটো আলাদা vowel। 'hot' এবং 'hut' — আলাদা। এই pair-গুলো আয়নার সামনে বলো, ঠোঁটের shape দেখো।"
    },

    # ── RULE 5: /w/ onset difficulty ─────────────────────────────────
    # Not a substitution — a coordination issue.
    # Bengali /w/-like sounds don't have the same bilabial rounding release.
    # Whisper sometimes catches 'oo-ater' or misreads the onset.
    # Flag high /w/ words that appear in IELTS prompts.
    {
        "pattern": r"\b(owater|oword|owork|oworld|owoman|owonder|uwater|uword)\b",
        "error_type": "approximant_onset",
        "target_phoneme": "/w/ onset — bilabial rounding not releasing into vowel smoothly",
        "bengali_note": "বাংলায় /w/-এর মতো ধ্বনি আছে, কিন্তু English /w/-এ ঠোঁট গোল করে শুরু করে vowel-এ মিশিয়ে দিতে হয় — একটা glide। আমাদের উচ্চারণে এই glide-টা কম থাকে।",
        "drill": "'water, word, work, wonder' — /u/ দিয়ে শুরু করো মনে মনে, তারপর সরাসরি vowel-এ চলে যাও। ঠোঁট গোল, দাঁত দূরে।"
    },
]

# ─────────────────────────────────────────────
# IELTS PROMPTS — for controlled recording tests
# ─────────────────────────────────────────────

IELTS_PROMPTS = [
    # Article omission + /ð/ test
    "The problem is that the result was not what they expected.",
    # Vowel quality — not, was, because, common
    "It was not possible because the problem was quite common.",
    # /w/ onset + vowel quality
    "Water is important and the weather was wonderful last winter.",
    # Mixed — article + vowel elongation targets
    "The answer is that the issue is a lot more complex than expected.",
    # /ð/ heavy — they, that, the, them
    "They said that the result was because of the environment.",
    # Free speech — spontaneous, shows natural interference
    "Describe your hometown in three sentences.",
]


def load_whisper_model(model_size="small"):
    """Load Whisper model. 'small' is fast and good enough for MVP."""
    print(f"\n⏳ Loading Whisper ({model_size}) model...")
    print("   (First run downloads ~460MB. Subsequent runs are instant.)\n")
    model = whisper.load_model(model_size)
    print("✅ Whisper loaded.\n")
    return model


def transcribe_audio(model, audio_path):
    """Transcribe audio file using Whisper."""
    print(f"🎙️  Transcribing: {audio_path}")
    result = model.transcribe(audio_path, language="en")
    transcript = result["text"].strip()
    print(f"\n📝 Whisper transcript:\n   \"{transcript}\"\n")
    return transcript

def detect_errors(transcript):
    """
    Rule-based Bengali L1 interference error detection.
    Returns list of detected errors.
    """
    errors = []
    transcript_lower = transcript.lower()

    for rule in PHONEME_RULES:
        matches = re.findall(rule["pattern"], transcript_lower)
        if not matches:
            continue

        # Article omission: verify the article is actually missing
        if rule["error_type"] == "article_omission":
            real_misses = []
            for match in matches:
                # Find position of this match in transcript
                match_pos = transcript_lower.find(match)
                if match_pos == -1:
                    continue
                # Check what comes before it (up to 5 chars)
                preceding = transcript_lower[max(0, match_pos - 5):match_pos].strip()
                # If preceded by the/a/an, article was NOT dropped — skip
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
            "matched_words": list(set(matches))
        })

    return errors

def generate_bengali_feedback(transcript, errors, prompt=None):
    """
    Call Claude API to generate warm Bengali coaching feedback.
    """
    client = anthropic.Anthropic()

    # Build the error summary for Claude
    if errors:
        error_summary = "\n".join([
            f"- Error type: {e['error_type']} ({e['target_phoneme']})\n"
            f"  Words: {', '.join(e['matched_words'])}\n"
            f"  Linguistic note: {e['bengali_note']}"
            for e in errors
        ])
    else:
        error_summary = "No specific phoneme substitution errors detected by rule engine."

    prompt_context = f"\nThe speaker was reading this IELTS prompt: \"{prompt}\"" if prompt else ""

    system_prompt = """তুমি একজন Bengali-medium English pronunciation coach — Meliglossa-র পক্ষ থেকে।
তোমার কাজ হলো Bengali speaker-দের English pronunciation-এর ভুল ধরিয়ে দেওয়া — কিন্তু এমনভাবে যেন মনে হয় একজন বন্ধু বলছে, কোনো examiner না।

তোমাকে দেওয়া হবে:
1. Whisper-এর transcript
2. Detected error list (rule-based)

তোমার response হবে শুধু Bengali-তে (target English words ছাড়া)। Format:

---
🎯 কী শুনলাম:
[Transcript সম্পর্কে ১ লাইন]

⚠️ কোথায় সমস্যা:
[প্রতিটা error-এর জন্য — কেন হচ্ছে এটা, Bengali phonology থেকে কারণটা explain করো। Maximum 2-3 টা error নাও, সব একসাথে না।]

💪 এখন এটা করো:
[একটাই drill। শুধু একটা। Specific এবং actionable।]

🌟 ভালো দিক:
[একটা genuine positive observation]
---
CRITICAL: তোমাকে অবশ্যই detected errors-এর প্রতিটা উল্লেখ করতে হবে।    
যদি vowel_quality_substitution detect হয়, তাহলে সেটা feedback-এ আলাদা করে বলতে হবে।
কোনো error skip করা যাবে না।
Rules:
- Bengali-তে লেখো। English word শুধু যখন target pronunciation দেখাচ্ছ।
- Score দিও না। Numbers দিও না।  
- "ভুল" শব্দটা avoid করো — "transfer" বা "আমাদের অভ্যাস" বলো।
- Maximum 150 words।
যদি কোনো error-এর confidence "possible" হয়, তাহলে definitive বলো না — 
বরং বলো "এই শব্দগুলোতে সাবধান থাকো" টোনে। নিশ্চিত না হলে accuse করো না।"""
#User messages are harder to ignore for the model 
    user_message = f"""Whisper transcript: "{transcript}"
{prompt_context}

Detected errors ({len(errors)} টা — প্রতিটা আলাদাভাবে address করো):
{error_summary}

উপরের প্রতিটা error-এর জন্য আলাদা করে বাংলায় explain করো। কোনোটা skip করা যাবে না।
এই speaker-কে warm Bengali feedback দাও।"""

    print("🤖 Generating Bengali feedback via Claude...\n")

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )

    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    cost_usd = (input_tokens * 3 + output_tokens * 15) / 1_000_000
    print(f"💰 API cost this call: ${cost_usd:.4f} ({input_tokens} in / {output_tokens} out)")

    return message.content[0].text


def save_session_log(audio_path, transcript, errors, feedback, prompt=None):
    """
    Save session to a local JSON log file.
    This is your seed dataset — every session logged from Day 1.
    """
    log_file = "sessions_log.jsonl"
    session = {
        "audio_file": audio_path,
        "prompt_used": prompt,
        "transcript": transcript,
        "errors_detected": errors,
        "feedback_generated": feedback,
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(session, ensure_ascii=False) + "\n")
    print(f"\n💾 Session saved to {log_file}")


def print_separator():
    print("\n" + "─" * 60 + "\n")


def main():
    # ── Check arguments ──
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n📌 IELTS Practice Prompts (read these aloud and record):")
        for i, p in enumerate(IELTS_PROMPTS, 1):
            print(f"   {i}. {p}")
        sys.exit(0)

    audio_path = sys.argv[1]

    if not os.path.exists(audio_path):
        print(f"❌ File not found: {audio_path}")
        sys.exit(1)

    # Optional: pass the prompt you were reading as second argument
    prompt_used = sys.argv[2] if len(sys.argv) > 2 else None

    # ── Check API key ──
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not set.")
        print("   Run: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    print_separator()
    print("🗣️  MELIGLOSSA — Bengali Accent Coach (Level 1 POC)")
    print_separator()

    if prompt_used:
        print(f"📖 Prompt you read: \"{prompt_used}\"\n")

    # ── Pipeline ──
    model = load_whisper_model("small")
    transcript = transcribe_audio(model, audio_path)

    print("🔍 Running Bengali L1 error detection...\n")
    errors = detect_errors(transcript)

    if errors:
        print(f"Found {len(errors)} error pattern(s):")
        for e in errors:
            print(f"   → {e['error_type']} ({e['target_phoneme']}): {e['matched_words']}")
    else:
        print("   Rule engine found no substitution errors in transcript.")
        print("   (Whisper may have auto-corrected. Check audio manually.)")
        print("   Sending to Claude for deeper analysis anyway...\n")

    print_separator()
    feedback = generate_bengali_feedback(transcript, errors, prompt_used)

    print("=" * 60)
    print("📣 FEEDBACK (Bengali):\n")
    print(feedback)
    print("=" * 60)

    save_session_log(audio_path, transcript, errors, feedback, prompt_used)

    print_separator()
    print("✅ Done. Next: record another prompt and run again.")
    print("   Your sessions are building your dataset in sessions_log.jsonl")


if __name__ == "__main__":
    main()