# Meliglossa Accent Coach

AI-powered English pronunciation coach built specifically for Bengali speakers.

## What it does

Records spoken English → detects Bengali L1 phoneme interference errors (using Whisper + rule-based detection) → generates warm coaching feedback in Bengali via Claude API.

## Why Bengali-specific?

Bengali speakers make predictable, linguistically explainable errors in English — /v/→/b/ substitution, article omission, schwa deletion — caused by L1 transfer, not ignorance. Generic apps give scores. This gives causes.

## Stack

- OpenAI Whisper (ASR)
- Rule-based Bengali phoneme error detection
- Claude API (anthropic) — Bengali-medium feedback generation
- Python / FastAPI (backend, coming in v2)

## Status

**Level 1 POC — CLI pipeline validated.** Level 2 (web app + frontend) in progress.

### What's working
- Whisper transcribes accurately in noisy conditions
- Bengali L1 error detection flags 5 major interference patterns
- Claude generates warm, actionable Bengali feedback (not clinical reports)
- Cost tracking on every API call

### Known limitations (being fixed)
- Rule-based detection flags false positives (e.g., "answer is" when article is present). Fixed in v0.2 with article verification logic.
- Vowel quality errors are flagged as "possible" not "confirmed" — Whisper can't detect vowel colour, only text. Requires human ear to validate. Feedback adjusted accordingly.
- No user persistence yet — sessions logged to local `sessions_log.jsonl`, not a database.

## Run it

```bash
pip install -r requirements.txt
python accent_coach_v1.py your_recording.mp3 "your English sentence"
```

## Project structure
accent_coach/
├── accent_coachv1.py       # CLI pipeline
├── requirements.txt        # Dependencies
├── README.md              # This file
└── sessions_log.jsonl     # Local session data (gitignored)
## Challenges encountered (and how they were solved)

**CUDA GPU compatibility** — RTX 5050 (Blackwell arch, sm_120) not supported by PyTorch cu121 build. Solution: upgraded to cu128 build with sm_120 support.

**UTF-8 Bengali text garbled in VS Code terminal** — PowerShell encoding issue. Solution: added `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` at script top.

**Article omission false positive** — regex pattern matching "X is" without checking if article precedes it. Solution: added verification logic in `detect_errors()` to check preceding text before flagging.

**Git merge conflict on first push** — GitHub auto-generated `.gitignore` conflicted with local version. Solution: `git checkout --ours .gitignore` to keep local, then merge.

## Next (Level 2)

- [ ] FastAPI backend with Supabase database
- [ ] React frontend with browser audio recording
- [ ] User accounts and session persistence
- [ ] Expanded Bengali L1 error detection rules
- [ ] Stress pattern and discourse marker detection

## Why this project

I'm a Bengali speaker who crossed to C2 English. Every error pattern in this tool I've personally made and fixed. The moat isn't generic IELTS coaching — it's contrastive linguistics rooted in lived experience.