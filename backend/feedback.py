import anthropic

SYSTEM_PROMPT = """তুমি একজন Bengali-medium English pronunciation coach — Meliglossa-র পক্ষ থেকে।
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


def generate_feedback(transcript: str, errors: list[dict], prompt_text: str | None = None) -> tuple[str, float]:
    client = anthropic.Anthropic()

    if errors:
        error_summary = "\n".join([
            f"- Error type: {e['error_type']} ({e['target_phoneme']})\n"
            f"  Words: {', '.join(e['matched_words'])}\n"
            f"  Confidence: {e['confidence']}\n"
            f"  Linguistic note: {e['bengali_note']}"
            for e in errors
        ])
    else:
        error_summary = "No specific phoneme substitution errors detected by rule engine."

    prompt_context = f"\nThe speaker was reading this IELTS prompt: \"{prompt_text}\"" if prompt_text else ""

    user_message = (
        f"Whisper transcript: \"{transcript}\"\n"
        f"{prompt_context}\n\n"
        f"Detected errors ({len(errors)} টা — প্রতিটা আলাদাভাবে address করো):\n"
        f"{error_summary}\n\n"
        "উপরের প্রতিটা error-এর জন্য আলাদা করে বাংলায় explain করো। কোনোটা skip করা যাবে না।\n"
        "এই speaker-কে warm Bengali feedback দাও।"
    )

    message = client.messages.create(
        model="claude-sonnet-4-5-20251001",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    input_tokens = message.usage.input_tokens
    output_tokens = message.usage.output_tokens
    cost_usd = (input_tokens * 3 + output_tokens * 15) / 1_000_000

    return message.content[0].text, cost_usd
