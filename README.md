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

An agentic AI system that creates personalized language lessons based on Bible study using OpenAI's ChatGPT.

## Files

* **app.py** is the huggingFace code
* **app_improved.py** it is also the huggingFace code with audio using text to speech elevenlabs free api
* **test.ipynb** - is the test of the complete code including audio.
* **Agentic AI Bible and Language Study.ipynb** is the first code I created and tested.

## Features

✨ **Multi-Agent Architecture**
- Agent 1: Verse Retriever
- Agent 2: Content Creator
- Agent 3: Lesson Designer
- Agent 4: Answer Key Generator
- Agent 5: Text to speech Generator using Eleven app

📚 **Four Skill Areas**
- Reading Comprehension
- Writing Exercises
- Listening Comprehension
- Speaking Practice

🎯 **CEFR Levels**: A1-C2

🤖 **Multiple AI Models**: GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo

📄 **PDF Generation**: Download complete lessons

## How to Use

1. Enter your OpenAI API key (get one at [platform.openai.com](https://platform.openai.com/))
2. Select your target language
3. Choose your language level (A1-C2)
4. Select AI model
5. Click "Generate Lesson"
6. Download your personalized PDF

## Privacy

Your API key is never stored and is only used for the current session.

## Cost

Approximate costs per lesson:
- GPT-4o: ~$0.10-0.20
- GPT-4o-mini: ~$0.01-0.02
- GPT-3.5-turbo: ~$0.002

## License

MIT License
```

## Steps to Deploy on Hugging Face:

### 1. **Create the Space**

Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click "Create new Space"

- **Name**: `bible-language-learning`
- **License**: MIT
- **SDK**: Gradio
- **Space hardware**: CPU basic (free tier)

### 2. **Upload Files**

Create these files in your Space:

**File structure:**
```
bible-language-learning/
├── app.py                 (the main Gradio app code above)
├── requirements.txt       (dependencies)
└── README.md             (Space description)
