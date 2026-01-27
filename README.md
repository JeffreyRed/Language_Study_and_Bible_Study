# Bible Language Learning System 📖🌍

An agentic AI system that creates personalized language lessons based on Bible study using OpenAI's ChatGPT API.

## Features

✨ **Multi-Agent Architecture**
- **Agent 1**: Verse Retriever - Gets daily verse and meditation
- **Agent 2**: Content Creator - Generates reading comprehension
- **Agent 3**: Lesson Designer - Creates comprehensive exercises
- **Agent 4**: Answer Key Generator - Provides detailed solutions

📚 **Four Skill Areas**
1. Reading Comprehension
2. Writing Exercises
3. Listening Comprehension
4. Speaking Practice

🎯 **CEFR Levels Supported**
- A1, A2, B1, B2, C1, C2

🤖 **Multiple AI Models**
- GPT-4o (most capable)
- GPT-4o-mini (faster, affordable)
- GPT-4-turbo
- GPT-3.5-turbo (cheapest)

📄 **PDF Generation**
- Complete lesson in professional PDF format
- Uses free ReportLab library

## Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set your OpenAI API key
export OPENAI_API_KEY='your-api-key-here'
```

## Usage
```bash
python bible_language_learning_openai.py
```

The system will:
1. Ask for your language level (default: B1)
2. Ask for target language (default: Spanish)
3. Ask for AI model preference
4. Generate a complete lesson with all agents
5. Create a PDF in the `lessons/` directory

## Example Output
```
📖 Verse of the Day: John 3:16
📚 Reading comprehension paragraph
✍️ Writing exercises
👂 Listening comprehension questions
🗣️ Speaking prompts
✅ Complete answer key
📄 PDF: lessons/bible_lesson_20240127_143022.pdf
```

## Cost Considerations

Approximate costs per lesson (as of 2024):
- **GPT-4o**: ~$0.10-0.20 per lesson
- **GPT-4o-mini**: ~$0.01-0.02 per lesson
- **GPT-3.5-turbo**: ~$0.002-0.005 per lesson

💡 **Tip**: Start with gpt-4o-mini for testing, then upgrade to gpt-4o for production quality.

## API Key Setup

Get your API key from: https://platform.openai.com/api-keys
```bash
# Linux/Mac
export OPENAI_API_KEY='sk-...'

# Windows (Command Prompt)
set OPENAI_API_KEY=sk-...

# Windows (PowerShell)
$env:OPENAI_API_KEY="sk-..."
```

## License

MIT License - Feel free to use and modify!