import gradio as gr
import openai
import os
from datetime import datetime
import json
from pathlib import Path
import tempfile
import requests

# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from dotenv import load_dotenv


class BibleLanguageLearningSystem:
    """
    Agentic AI system for language learning through Bible study.
    Uses multiple specialized agents to create comprehensive lessons.
    """
    
    def __init__(self, api_key: str, target_language: str = "Spanish", model: str = "gpt-4o-mini", elevenlabs_key: str = None):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.target_language = target_language
        self.elevenlabs_key = elevenlabs_key
        
    def _call_gpt(self, system_prompt: str, user_message: str, temperature: float = 1.0) -> str:
        """Helper method to call OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=temperature,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def agent_verse_retriever(self, language_level: str) -> dict:
        """Agent 1: Retrieves verse of the day and meditation paragraph"""
        system_prompt = f"""You are a Bible study coordinator agent. Your role is to:
1. Select an appropriate verse of the day
2. Provide a short meditation paragraph (2-3 sentences) in both English and {self.target_language}
3. Ensure content is appropriate for {language_level} language learners

Return ONLY valid JSON with these exact keys:
- "verse_reference": The Bible verse reference
- "verse_text_english": The verse in English
- "verse_text_{self.target_language.lower()}": The verse in {self.target_language}
- "meditation_english": Meditation in English
- "meditation_{self.target_language.lower()}": Meditation in {self.target_language}"""

        user_message = f"Provide verse of the day with meditation for {self.target_language} at {language_level} level."
        
        response = self._call_gpt(system_prompt, user_message, temperature=0.7)
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except:
            return {
                "verse_reference": "John 3:16",
                "verse_text_english": "For God so loved the world...",
                f"verse_text_{self.target_language.lower()}": response[:100],
                "meditation_english": "God's love for humanity.",
                f"meditation_{self.target_language.lower()}": response[100:200] if len(response) > 100 else "Meditación"
            }
    
    def agent_content_creator(self, verse_data: dict, language_level: str) -> dict:
        """Agent 2: Creates reading comprehension paragraph"""
        system_prompt = f"""You are a language learning content creator.
Create a reading comprehension paragraph (150-200 words) in {self.target_language}.

Requirements:
- Appropriate for {language_level} level
- Include theological insights and practical applications
- Use clear, educational language
- Natural pronunciation-friendly text (avoid complex punctuation)

Return ONLY valid JSON with:
- "reading_text_{self.target_language.lower()}": Reading text in {self.target_language}
- "reading_text_english": Reading text in English
- "key_vocabulary": Array of important vocabulary words"""

        user_message = f"""Create content based on:
Verse: {verse_data.get('verse_reference', 'N/A')}
Text: {verse_data.get(f'verse_text_{self.target_language.lower()}', '')}"""

        response = self._call_gpt(system_prompt, user_message, temperature=0.8)
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except:
            return {
                f"reading_text_{self.target_language.lower()}": response[:300],
                "reading_text_english": "Reading comprehension text",
                "key_vocabulary": ["faith", "love", "grace"]
            }
    
    def agent_lesson_designer(self, verse_data: dict, reading_data: dict, language_level: str) -> dict:
        """Agent 3: Designs comprehensive lesson"""
        system_prompt = f"""You are an expert language lesson designer for {self.target_language}.
Create a comprehensive lesson for {language_level} level including:

1. READING: 4-5 comprehension questions about the reading text (in {self.target_language})
2. WRITING: 3 writing prompts related to the theme (in {self.target_language})
3. LISTENING: 4 questions about what students should listen for in the audio (in {self.target_language})
4. SPEAKING: 3 speaking prompts for oral practice (in {self.target_language})
5. FILLING: 3-4 fill-in-the-blank sentences using vocabulary from the reading (in {self.target_language})
   - Use ___ to indicate where the word should go
   - Make blanks appropriate for {language_level} level

Return ONLY valid JSON with:
- "reading_exercises": Array of objects with "question" field
- "writing_exercises": Array of objects with "question" field
- "listening_exercises": Array of objects with "question" field
- "speaking_exercises": Array of objects with "question" field
- "filling_exercises": Array of objects with "question" field (sentences with ___ for blanks)

Return ONLY the JSON object, no additional text."""

        user_message = f"""Design lesson based on:
Verse: {verse_data.get('verse_reference')}
Reading: {reading_data.get(f'reading_text_{self.target_language.lower()}', '')[:200]}
Vocabulary: {reading_data.get('key_vocabulary', [])}"""

        response = self._call_gpt(system_prompt, user_message, temperature=0.7)
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except:
            return {
                "reading_exercises": [{"question": "¿Cuál es el tema principal del texto?"}],
                "writing_exercises": [{"question": "Escribe sobre tu experiencia personal con este tema."}],
                "listening_exercises": [{"question": "¿Qué palabras clave escuchaste?"}],
                "speaking_exercises": [{"question": "Explica el significado del verso en tus propias palabras."}],
                "filling_exercises": [{"question": "La ___ es importante en la vida cristiana."}]
            }
    
    def agent_answer_key_generator(self, lesson_data: dict, verse_data: dict, reading_data: dict) -> dict:
        """Agent 4: Generates answer key"""
        system_prompt = f"""You are an answer key generator for {self.target_language}.
Provide detailed answers and model responses in {self.target_language}.

For filling exercises, provide ONLY the word(s) that should fill the blank(s).

Return ONLY valid JSON with:
- "reading_exercises": Array with "answer" and "explanation"
- "writing_exercises": Array with "answer" (model response) and "explanation"
- "listening_exercises": Array with "answer" (key points to listen for) and "explanation"
- "speaking_exercises": Array with "answer" (sample response) and "explanation"
- "filling_exercises": Array with "answer" (the missing word/phrase ONLY) and "explanation"
        
Return ONLY the JSON object, no additional text."""

        user_message = f"""Generate answers for:
Exercises: {json.dumps(lesson_data, ensure_ascii=False)[:500]}
Reading context: {reading_data.get(f'reading_text_{self.target_language.lower()}', '')[:300]}
Vocabulary: {reading_data.get('key_vocabulary', [])}"""

        response = self._call_gpt(system_prompt, user_message, temperature=0.5)
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except:
            return {
                "reading_exercises": [{"answer": "El tema principal es...", "explanation": "Se encuentra en el párrafo principal"}],
                "writing_exercises": [{"answer": "Ejemplo de respuesta modelo", "explanation": "Respuesta modelo"}],
                "listening_exercises": [{"answer": "Palabras clave: fe, amor, esperanza", "explanation": "Escuchar atentamente"}],
                "speaking_exercises": [{"answer": "El verso significa que...", "explanation": "Guía de conversación"}],
                "filling_exercises": [{"answer": "fe", "explanation": "La palabra correcta es 'fe' según el contexto"}]
            }
    
    def agent_tts_generator(self, reading_text: str) -> str:
        """Agent 5: Generates text-to-speech audio using ElevenLabs"""
        if not self.elevenlabs_key:
            return None
            
        try:
            # Map language to appropriate ElevenLabs voice
            voice_map = {
                "Spanish": "pNInz6obpgDQGcFmaJgB",  # Adam (multilingual)
                "French": "pNInz6obpgDQGcFmaJgB",
                "German": "pNInz6obpgDQGcFmaJgB",
                "Italian": "pNInz6obpgDQGcFmaJgB",
                "Portuguese": "pNInz6obpgDQGcFmaJgB",
                "Chinese": "pNInz6obpgDQGcFmaJgB",
                "Japanese": "pNInz6obpgDQGcFmaJgB",
                "Korean": "pNInz6obpgDQGcFmaJgB",
                "Arabic": "pNInz6obpgDQGcFmaJgB",
                "Hebrew": "pNInz6obpgDQGcFmaJgB"
            }
            
            voice_id = voice_map.get(self.target_language, "pNInz6obpgDQGcFmaJgB")
            
            # ElevenLabs API endpoint
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.elevenlabs_key
            }
            
            data = {
                "text": reading_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # Save audio to temporary file
                temp_dir = tempfile.gettempdir()
                audio_filename = f"reading_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                audio_path = os.path.join(temp_dir, audio_filename)
                
                with open(audio_path, 'wb') as f:
                    f.write(response.content)
                
                return audio_path
            else:
                print(f"ElevenLabs API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"TTS Generation Error: {str(e)}")
            return None
    
    def generate_pdf(self, lesson_content: dict, filename: str = None):
        """Generate PDF with all lesson content"""
        if filename is None:
            filename = f"bible_lesson_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # Use temporary directory for Hugging Face Spaces
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        
        elements = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='darkblue',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        # Title
        title = Paragraph(f"Bible Language Learning Lesson<br/>{self.target_language}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Date and Level
        date_text = f"Date: {datetime.now().strftime('%B %d, %Y')}<br/>Level: {lesson_content.get('level', 'B1')}"
        elements.append(Paragraph(date_text, styles['BodyText']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Verse
        verse_data = lesson_content.get('verse_data', {})
        elements.append(Paragraph("📖 Verse of the Day", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        verse_ref = verse_data.get('verse_reference', 'N/A')
        elements.append(Paragraph(f"<b>{verse_ref}</b>", styles['BodyText']))
        
        verse_text = verse_data.get(f'verse_text_{self.target_language.lower()}', 'N/A')
        elements.append(Paragraph(f"<i>{verse_text}</i>", styles['BodyText']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Meditation
        meditation = verse_data.get(f'meditation_{self.target_language.lower()}', '')
        if meditation:
            elements.append(Paragraph(f"<b>Meditation:</b> {meditation}", styles['BodyText']))
            elements.append(Spacer(1, 0.3*inch))
        
        # Reading
        reading_data = lesson_content.get('reading_data', {})
        elements.append(Paragraph("📚 Reading Comprehension", styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        reading_text = reading_data.get(f'reading_text_{self.target_language.lower()}', 'N/A')
        elements.append(Paragraph(reading_text, styles['BodyText']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Note about audio
        if lesson_content.get('audio_path'):
            elements.append(Paragraph("<b>🔊 Audio available for listening exercise</b>", styles['BodyText']))
            elements.append(Spacer(1, 0.2*inch))
        
        # Vocabulary
        vocab = reading_data.get('key_vocabulary', [])
        if vocab:
            elements.append(Paragraph("<b>Key Vocabulary:</b>", styles['BodyText']))
            vocab_text = ", ".join(vocab) if isinstance(vocab, list) else str(vocab)
            elements.append(Paragraph(vocab_text, styles['BodyText']))
            elements.append(Spacer(1, 0.3*inch))
        
        elements.append(PageBreak())
        
        # Exercises
        lesson_data = lesson_content.get('lesson_data', {})
        self._add_exercises(elements, "📖 Reading Exercises", 
                           lesson_data.get('reading_exercises', []), styles)
        self._add_exercises(elements, "✍️ Writing Exercises", 
                           lesson_data.get('writing_exercises', []), styles)
        self._add_exercises(elements, "👂 Listening Exercises", 
                           lesson_data.get('listening_exercises', []), styles)
        self._add_exercises(elements, "🗣️ Speaking Exercises", 
                           lesson_data.get('speaking_exercises', []), styles)
        self._add_exercises(elements, "✏️ Fill-in-the-Blank Exercises", 
                           lesson_data.get('filling_exercises', []), styles)
        
        elements.append(PageBreak())
        
        # Answers
        elements.append(Paragraph("✅ Answer Key", styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        answers = lesson_content.get('answers', {})
        self._add_answers(elements, "Reading Answers", answers.get('reading_exercises', []), styles)
        self._add_answers(elements, "Writing Answers", answers.get('writing_exercises', []), styles)
        self._add_answers(elements, "Listening Answers", answers.get('listening_exercises', []), styles)
        self._add_answers(elements, "Speaking Answers", answers.get('speaking_exercises', []), styles)
        self._add_answers(elements, "Fill-in-the-Blank Answers", answers.get('filling_exercises', []), styles)
        
        doc.build(elements)
        return filepath
    
    def _add_exercises(self, elements, title, exercises, styles):
        """Add exercise section to PDF"""
        elements.append(Paragraph(title, styles['Heading2']))
        elements.append(Spacer(1, 0.1*inch))
        
        if isinstance(exercises, list):
            for i, ex in enumerate(exercises, 1):
                question = ex.get('question', str(ex)) if isinstance(ex, dict) else str(ex)
                elements.append(Paragraph(f"{i}. {question}", styles['BodyText']))
                elements.append(Spacer(1, 0.15*inch))
        
        elements.append(Spacer(1, 0.3*inch))
    
    def _add_answers(self, elements, title, answers, styles):
        """Add answers section to PDF"""
        elements.append(Paragraph(f"<b>{title}</b>", styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        if isinstance(answers, list):
            for i, ans in enumerate(answers, 1):
                if isinstance(ans, dict):
                    answer = ans.get('answer', '')
                    explanation = ans.get('explanation', '')
                    text = f"{i}. <b>{answer}</b>"
                    if explanation:
                        text += f" <i>({explanation})</i>"
                else:
                    text = f"{i}. {str(ans)}"
                elements.append(Paragraph(text, styles['BodyText']))
                elements.append(Spacer(1, 0.1*inch))
        
        elements.append(Spacer(1, 0.2*inch))
    
    def run_full_lesson_generation(self, language_level: str = "B1", progress=gr.Progress()):
        """Generate complete lesson with progress updates"""
        progress(0, desc="Starting lesson generation...")
        
        # Step 1
        progress(0.15, desc="📖 Getting verse of the day...")
        verse_data = self.agent_verse_retriever(language_level)
        
        # Step 2
        progress(0.30, desc="📚 Creating reading comprehension...")
        reading_data = self.agent_content_creator(verse_data, language_level)
        
        # Step 3
        progress(0.45, desc="🎓 Designing lesson exercises...")
        lesson_data = self.agent_lesson_designer(verse_data, reading_data, language_level)
        
        # Step 4
        progress(0.60, desc="✅ Generating answer key...")
        answers = self.agent_answer_key_generator(lesson_data, verse_data, reading_data)
        
        # Step 5: Generate audio
        audio_path = None
        if self.elevenlabs_key:
            progress(0.75, desc="🔊 Generating audio (this may take a moment)...")
            reading_text = reading_data.get(f'reading_text_{self.target_language.lower()}', '')
            if reading_text:
                audio_path = self.agent_tts_generator(reading_text)
        
        # Step 6
        progress(0.90, desc="📄 Creating PDF...")
        lesson_content = {
            'level': language_level,
            'verse_data': verse_data,
            'reading_data': reading_data,
            'lesson_data': lesson_data,
            'answers': answers,
            'audio_path': audio_path
        }
        
        pdf_path = self.generate_pdf(lesson_content)
        progress(1.0, desc="✨ Complete!")
        
        return lesson_content, pdf_path, audio_path


def format_lesson_display(lesson_content):
    """Format lesson content for display"""
    verse_data = lesson_content.get('verse_data', {})
    reading_data = lesson_content.get('reading_data', {})
    lesson_data = lesson_content.get('lesson_data', {})
    
    # Dynamically get the language key
    lang_keys = [k for k in verse_data.keys() if k.startswith('verse_text_') and k != 'verse_text_english']
    verse_lang_key = lang_keys[0] if lang_keys else 'verse_text_english'
    meditation_lang_key = verse_lang_key.replace('verse_text_', 'meditation_')
    reading_lang_key = verse_lang_key.replace('verse_text_', 'reading_text_')
    
    output = f"""
# 📖 Verse of the Day

**{verse_data.get('verse_reference', 'N/A')}**

*{verse_data.get(verse_lang_key, verse_data.get('verse_text_english', 'N/A'))}*

**Meditation:**
{verse_data.get(meditation_lang_key, verse_data.get('meditation_english', 'N/A'))}

---

# 📚 Reading Comprehension

{reading_data.get(reading_lang_key, reading_data.get('reading_text_english', 'N/A'))}

**Key Vocabulary:** {', '.join(reading_data.get('key_vocabulary', []))}

---

# 📝 Exercises

## 📖 Reading Exercises
"""
    
    for i, ex in enumerate(lesson_data.get('reading_exercises', []), 1):
        output += f"{i}. {ex.get('question', str(ex))}\n"
    
    output += "\n## ✍️ Writing Exercises\n"
    for i, ex in enumerate(lesson_data.get('writing_exercises', []), 1):
        output += f"{i}. {ex.get('question', str(ex))}\n"
    
    output += "\n## 👂 Listening Exercises\n"
    for i, ex in enumerate(lesson_data.get('listening_exercises', []), 1):
        output += f"{i}. {ex.get('question', str(ex))}\n"
    
    output += "\n## 🗣️ Speaking Exercises\n"
    for i, ex in enumerate(lesson_data.get('speaking_exercises', []), 1):
        output += f"{i}. {ex.get('question', str(ex))}\n"

    output += "\n## ✏️ Fill-in-the-Blank Exercises\n"
    for i, ex in enumerate(lesson_data.get('filling_exercises', []), 1):
        output += f"{i}. {ex.get('question', str(ex))}\n"
    
    return output


def generate_lesson(api_key, elevenlabs_key, language, level, model, progress=gr.Progress()):
    """Main function called by Gradio interface"""
    if not api_key:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        elevenlabs_key = os.getenv("ELEVEN_API_KEY")
        if not api_key:
            return "⚠️ Please enter your OpenAI API key", None, None
    
    try:
        system = BibleLanguageLearningSystem(
            api_key=api_key,
            target_language=language,
            model=model,
            elevenlabs_key=elevenlabs_key
        )
        
        lesson_content, pdf_path, audio_path = system.run_full_lesson_generation(level, progress)
        
        display_text = format_lesson_display(lesson_content)
        
        return display_text, pdf_path, audio_path
        
    except Exception as e:
        return f"❌ Error: {str(e)}", None, None


# Create Gradio Interface
with gr.Blocks(title="Bible Language Learning System", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 📖 Bible Language Learning System
    ### Learn Languages Through Scripture with AI
    
    This agentic AI system creates personalized language lessons based on Bible study.
    Each lesson includes reading, writing, listening, speaking, and fill-in-the-blank exercises with complete answer keys.
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Settings")
            
            api_key = gr.Textbox(
                label="OpenAI API Key",
                placeholder="sk-...",
                type="password",
                info="Get your key from platform.openai.com"
            )
            
            elevenlabs_key = gr.Textbox(
                label="ElevenLabs API Key (Optional)",
                placeholder="Your ElevenLabs API key",
                type="password",
                info="For audio generation. Get free key from elevenlabs.io (10 requests/day)"
            )
            
            language = gr.Dropdown(
                choices=["Spanish", "French", "German", "Italian", "Portuguese", "Chinese", "Japanese", "Korean", "Arabic", "Hebrew"],
                value="Spanish",
                label="Target Language"
            )
            
            level = gr.Dropdown(
                choices=["A1", "A2", "B1", "B2", "C1", "C2"],
                value="B1",
                label="Language Level (CEFR)",
                info="A1=Beginner, B1=Intermediate, C1=Advanced"
            )
            
            model = gr.Dropdown(
                choices=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
                value="gpt-4o-mini",
                label="AI Model",
                info="gpt-4o-mini recommended for cost/quality balance"
            )
            
            generate_btn = gr.Button("🚀 Generate Lesson", variant="primary", size="lg")
            
            gr.Markdown("""
            ### 💡 How it works:
            1. **Agent 1** selects a Bible verse
            2. **Agent 2** creates reading content
            3. **Agent 3** designs exercises
            4. **Agent 4** generates answers
            5. **Agent 5** creates audio (if key provided)
            6. **PDF** is created automatically
            
            ### 💰 Estimated Cost per Lesson:
            - **OpenAI gpt-4o-mini**: ~$0.01-0.02
            - **OpenAI gpt-4o**: ~$0.10-0.20
            - **ElevenLabs TTS**: Free (10/day limit)
            
            ### 🎯 Features:
            - ✅ Fill-in-the-blank exercises
            - 🔊 Audio for listening practice
            - 📄 Complete PDF with answers
            """)
        
        with gr.Column(scale=2):
            gr.Markdown("### 📄 Your Lesson")
            
            lesson_output = gr.Markdown(
                value="Click 'Generate Lesson' to create your personalized Bible language lesson!",
                height=600
            )
            
            with gr.Row():
                pdf_output = gr.File(
                    label="📥 Download PDF Lesson",
                    file_types=[".pdf"]
                )
                
                audio_output = gr.Audio(
                    label="🔊 Download Listening Audio",
                    type="filepath"
                )
    
    generate_btn.click(
        fn=generate_lesson,
        inputs=[api_key, elevenlabs_key, language, level, model],
        outputs=[lesson_output, pdf_output, audio_output]
    )
    
    gr.Markdown("""
    ---
    ### 📚 About
    This app uses a multi-agent AI system to create comprehensive language learning lessons based on Bible study.
    Each lesson is tailored to your language level and includes all skill areas: reading, writing, listening, speaking, and vocabulary practice.
    
    ### 🔑 API Keys:
    - **OpenAI**: Required. Get one at [platform.openai.com](https://platform.openai.com/)
    - **ElevenLabs**: Optional. Get free key at [elevenlabs.io](https://elevenlabs.io/) for audio generation (10 requests/day on free tier)
    
    ### ✏️ Fill-in-the-Blank Exercises:
    These exercises help reinforce vocabulary by asking students to complete sentences with appropriate words from the reading.
    Answers are provided in the answer key section of the PDF.
    """)

# Launch the app
if __name__ == "__main__":
    demo.launch()
