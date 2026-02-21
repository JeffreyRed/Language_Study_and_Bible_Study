---
title: Bible Language Learning System
emoji: 📖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
---

# Bible Language Learning System 📖🌍

An agentic AI system that creates personalised daily language lessons grounded in Bible study. Every lesson is built from the **real verse of the day** fetched from [discoverybiblestudy.org](https://discoverybiblestudy.org), then processed by a pipeline of specialised AI agents to produce reading, grammar, role-play, listening, writing, speaking, and fill-in-the-blank exercises — plus a complete audio recording and a downloadable PDF.

---

## Agent Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BIBLE LANGUAGE LEARNING SYSTEM                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
              ┌───────────────────────────────────┐
              │  discoverybiblestudy.org  API      │
              │  → verse text, reference, date     │
              └───────────────┬───────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │  AGENT 1 — Verse Retriever               │
        │  • Receives today's real verse           │
        │  • Translates it into target language    │
        │  • Writes meditation paragraph           │
        │  Output: verse_data {}                   │
        └──────────────────┬──────────────────────┘
                           │
                           ▼
        ┌─────────────────────────────────────────┐
        │  AGENT 2 — Content Creator               │
        │  • Writes 150-200 word reading text      │
        │  • Extracts key vocabulary               │
        │  • Generates vocabulary definitions      │
        │  Output: reading_data {}                 │
        └──────────────────┬──────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│  AGENT 3                │  │  AGENT 5                 │
│  Lesson Designer        │  │  Grammar Lesson          │
│  • Reading questions    │  │  • Identifies 1-2 grammar│
│  • Writing prompts      │  │    points from the text  │
│  • Listening questions  │  │  • Explains rules        │
│  • Speaking prompts     │  │  • Gives examples        │
│  • Fill-in-the-blank    │  │  • Creates exercises     │
│  Output: lesson_data {} │  │  Output: grammar_data {} │
└────────────┬────────────┘  └─────────────────────────┘
             │
             ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│  AGENT 4                │  │  AGENT 6                 │
│  Answer Key Generator   │  │  Role Play Creator       │
│  • Model answers for    │  │  • Everyday scenario     │
│    all exercise types   │  │    inspired by the theme │
│  • Fill-in solutions    │  │  • Sample dialogue       │
│  Output: answers {}     │  │  • Useful phrases        │
└────────────┬────────────┘  │  • Conversation tasks    │
             │               │  Output: roleplay_data {}│
             │               └─────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│  AGENT 7 — TTS Generator                                 │
│  • Sends reading text to OpenAI TTS (gpt-4o-mini-tts)   │
│  • Generates MP3 audio file for listening practice      │
│  Output: audio_path                                     │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  PDF Builder                                             │
│  Assembles all agent outputs into a structured PDF:     │
│  1. Verse of the Day + Meditation                       │
│  2. Reading Comprehension + Vocabulary & Meanings       │
│  3. Exercises (Reading / Writing / Listening /          │
│     Speaking / Fill-in-the-blank)                       │
│  4. Grammar Lesson                                      │
│  5. Role Play Scenario + Dialogue + Useful Phrases      │
│  6. Complete Answer Key                                 │
│  Output: lesson_YYYY-MM-DD.pdf                         │
└─────────────────────────────────────────────────────────┘
```

---

## Features

**Multi-Agent Architecture** — 7 specialised agents each handle one part of the lesson so each task is focused and high quality.

**Real Daily Verse** — fetched live from [discoverybiblestudy.org](https://discoverybiblestudy.org/daily/api/) so every lesson is different.

**Five Skill Areas**
- Reading Comprehension
- Writing Exercises
- Listening Comprehension (with audio)
- Speaking Practice
- Fill-in-the-Blank Vocabulary

**Grammar Mini-Lesson** — extracted from the reading text and tailored to the learner's CEFR level.

**Role Play Scenario** — realistic everyday conversation inspired by the day's spiritual theme.

**CEFR Levels** — A1 through C2.

**Multiple AI Models** — GPT-4o, GPT-4o-mini, GPT-4-turbo.

**PDF Export** — complete lesson with answer key, ready to print or share.

**Audio** — OpenAI TTS reads the comprehension text aloud for listening practice.

---

## Repository Files

| File | Description |
|------|-------------|
| `app.py` | Main Hugging Face Spaces app (Gradio UI) |
| `app_improved.py` | Alternative version with OpenAI TTS audio |
| `test.ipynb` | End-to-end test notebook including audio |
| `Agentic AI Bible and Language Study.ipynb` | Original prototype notebook |
| `Agents_verse_reading_speaking_writing_excercise_rolePlay_grammarLesson.ipynb` | Full multi-agent version with grammar + role play |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |

---

## How to Use (Hugging Face Spaces)

1. Open the Space at [huggingface.co/spaces](https://huggingface.co/spaces)
2. Enter your **OpenAI API key** (get one at [platform.openai.com](https://platform.openai.com/))
3. Select your **target language** (Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Arabic, Hebrew)
4. Choose your **language level** (A1–C2)
5. Select the **AI model**
6. Click **Generate Lesson**
7. Read the lesson in the panel, then download the **PDF** and **MP3 audio**

---

## Deploy Your Own Copy

### 1. Create the Space

Go to [huggingface.co/spaces](https://huggingface.co/spaces) → **Create new Space**

| Setting | Value |
|---------|-------|
| Name | `bible-language-learning` |
| License | MIT |
| SDK | Gradio |
| Hardware | CPU basic (free tier) |

### 2. File Structure

```
bible-language-learning/
├── app.py
├── requirements.txt
└── README.md
```

### 3. requirements.txt

```
openai>=1.0.0
gradio>=4.0.0
reportlab>=4.0.0
requests>=2.28.0
python-dotenv>=1.0.0
```

### 4. Environment Variables (optional)

If you want to pre-fill the API key on a private Space, add a secret in **Settings → Repository secrets**:

```
OPENAI_API_KEY=sk-...
```

---

## Running Locally

```bash
git clone https://github.com/YOUR_USERNAME/bible-language-learning
cd bible-language-learning
pip install -r requirements.txt
cp .env.example .env        # add your OPENAI_API_KEY
python app.py
```

---

## Cost per Lesson

| Model | Approximate cost |
|-------|-----------------|
| gpt-4o-mini | ~$0.01–0.02 |
| gpt-4o | ~$0.10–0.20 |
| gpt-4-turbo | ~$0.05–0.15 |

*TTS audio uses `gpt-4o-mini-tts` and is included in the above estimate.*

---

## Privacy

Your API key is never stored. It is used only for the duration of the current session and is not logged or transmitted anywhere other than the OpenAI API.

---

## License

MIT License — see [LICENSE](LICENSE) for details.