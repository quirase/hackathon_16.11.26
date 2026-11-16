# Product Context — LexisTube (YouTube English Level Analyzer)

## Purpose
An interactive web tool that analyzes any English YouTube video by URL and detects its CEFR English proficiency level (A1–C2), giving language learners, teachers, and self-studiers an immediate, scannable breakdown of *why* a video is at that level.

## Scope & Architecture
- **Frontend only** (React + Vite + TypeScript): All actual ML/NLP/audio detection and backend processing will be built separately by the user.
- **Typed Backend Adapter**: Clean `src/api/analyzer.ts` contract (`POST /api/analyze`) with a built-in realistic mock mode (`VITE_USE_MOCK=true` by default) and rich sample presets so the UI works out of the box and swaps to the user's real endpoint with a single env var.
- **English-only**: No language selector; streamlined single YouTube URL input.

## Core User Flows & Features
1. **URL Submission & Sample Presets**: Paste any YouTube URL (supports `youtube.com/watch?v=`, `youtu.be/`, `/shorts/`) or pick a curated sample video (A2, B2, C1) to test immediately.
2. **Hero CEFR Level Verdict**: Clear A1–C2 level badge, confidence percentage, and plain-English summary of who this video suits.
3. **Sub-Metric Breakdown**: Four core linguistic/delivery dimensions:
   - Speech Rate (WPM & pacing label)
   - Vocabulary Difficulty (lexical tier & rare-word ratio)
   - Grammar Complexity (clause depth & tense variety)
   - Accent / Clarity (enunciation & audio clarity score)
4. **Embedded YouTube Player + Timestamped Vocabulary**: Clicking any flagged difficult word/phrase jumps the embedded YouTube iframe directly to that timestamp.
5. **Interactive CEFR-Highlighted Transcript Excerpt**: Transcript segment with B1/B2/C1/C2 words underlined/tagged; clicking or selecting a highlighted word reveals its CEFR tier, part of speech, and concise definition.
6. **Analysis History (`localStorage`)**: Persists recent video analyses so users can compare levels across videos or reopen past results instantly.

## Visual Direction
- **Crisp Editorial Studio**: Warm alabaster/ivory paper canvas, deep ink typography, sharp Swiss-grid hairlines, tabular numerals, and semantic CEFR tier accents (A1–C2).
- **Mode**: Operate (utility workbench).
