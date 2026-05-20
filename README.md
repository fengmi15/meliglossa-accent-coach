# Meliglossa Accent Coach

AI-powered English pronunciation coach built specifically for Bengali speakers.

## What it does
Records spoken English → detects Bengali L1 phoneme interference errors 
(using Whisper + rule-based detection) → generates warm coaching feedback 
in Bengali via Claude API.

## Why Bengali-specific?
Bengali speakers make predictable, linguistically explainable errors in 
English — /v/→/b/ substitution, article omission, schwa deletion — caused 
by L1 transfer, not ignorance. Generic apps give scores. This gives causes.

## Stack
- OpenAI Whisper (ASR)
- Rule-based Bengali phoneme error detection
- Claude API (anthropic) — Bengali-medium feedback generation
- Python / FastAPI (backend, coming in v2)

## Status
Level 1 POC — CLI pipeline validated. Level 2 (web app) in progress.

## Run it
pip install openai-whisper anthropic python-dotenv
python accent_coach_v1.py your_recording.mp3