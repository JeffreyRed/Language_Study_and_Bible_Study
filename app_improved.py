import openai
import os
from datetime import datetime
import json
import tempfile
import requests
import html
import gradio as gr

# PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from dotenv import load_dotenv

# ─────────────────────────────────────────────
# Discovery Bible Study API helper
# ─────────────────────────────────────────────

DISCOVERY_API_URL = "https://discoverybiblestudy.org/daily/api/"

def fetch_verse_of_the_day() -> dict:
    try:
        response = requests.get(DISCOVERY_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        data["text"] = html.unescape(data.get("text", ""))
        return data
    except Exception as e:
        print(f"[DiscoveryBibleStudy API] Could not fetch verse: {e}")
        return None


class BibleLanguageLearningSystem:

    def __init__(self, api_key: str, target_language: str = "Spanish", model: str = "gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.target_language = target_language

    # ──────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────

    def _call_gpt(self, system_prompt: str, user_message: str, temperature: float = 1.0) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=4000,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def _parse_json(response: str, fallback: dict) -> dict:
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            return json.loads(json_str)
        except Exception:
            return fallback

    # ──────────────────────────────────────────
    # Agent 1 – Verse Retriever
    # ──────────────────────────────────────────

    def agent_verse_retriever(self, language_level: str) -> dict:
        lang = self.target_language
        lang_lower = lang.lower()

        api_data = fetch_verse_of_the_day()
        if api_data:
            verse_ref     = api_data.get("ref", "Unknown")
            verse_english = api_data.get("text", "").strip()
            verse_date    = api_data.get("date", datetime.now().strftime("%d %b %Y"))
            verse_source_url = api_data.get("verseUrl", "")
        else:
            verse_ref     = "John 3:16"
            verse_english = "For God so loved the world that he gave his one and only Son."
            verse_date    = datetime.now().strftime("%d %b %Y")
            verse_source_url = ""

        system_prompt = f"""You are a Bible study coordinator and language teacher.
You will receive a Bible verse in English. Your tasks:
1. Translate the verse accurately into {lang}.
2. Write a short meditation paragraph (2-3 sentences) in English appropriate for {language_level} learners.
3. Write the same meditation in {lang} at {language_level} level.
4. Keep total word count under 1000 words.

Return ONLY valid JSON with these exact keys:
- "verse_text_english": the English verse as provided
- "verse_text_{lang_lower}": the verse translated into {lang}
- "meditation_english": meditation in English
- "meditation_{lang_lower}": meditation in {lang}"""

        user_message = (
            f"Verse reference: {verse_ref}\n"
            f"English verse text: {verse_english}\n"
            f"Target language level: {language_level}"
        )

        response = self._call_gpt(system_prompt, user_message, temperature=0.7)
        fallback = {
            "verse_text_english": verse_english,
            f"verse_text_{lang_lower}": verse_english,
            "meditation_english": "Reflect on this verse and apply it to your daily life.",
            f"meditation_{lang_lower}": "Reflexiona sobre este verso y aplícalo a tu vida diaria.",
        }
        result = self._parse_json(response, fallback)
        result["verse_reference"]  = verse_ref
        result["verse_date"]       = verse_date
        result["verse_source_url"] = verse_source_url
        return result

    # ──────────────────────────────────────────
    # Agent 2 – Content Creator
    # ──────────────────────────────────────────

    def agent_content_creator(self, verse_data: dict, language_level: str) -> dict:
        lang_lower = self.target_language.lower()

        system_prompt = f"""You are a language learning content creator.
Create a reading comprehension paragraph (150-200 words) in {self.target_language}.

Requirements:
- Appropriate for {language_level} level
- Include theological insights and practical applications
- Use clear, educational language

Return ONLY valid JSON with:
- "reading_text_{lang_lower}": Reading text in {self.target_language}
- "reading_text_english": Reading text in English
- "key_vocabulary": Array of important vocabulary words (strings only)
- "vocabulary_meaning": A JSON object where each key is a vocabulary word and its value is the definition in {self.target_language} followed by the English translation in parentheses"""

        user_message = (
            f"Verse: {verse_data.get('verse_reference', 'N/A')}\n"
            f"Text: {verse_data.get(f'verse_text_{lang_lower}', '')}"
        )

        response = self._call_gpt(system_prompt, user_message, temperature=0.8)
        return self._parse_json(
            response,
            {
                f"reading_text_{lang_lower}": response[:300],
                "reading_text_english": "Reading comprehension text",
                "key_vocabulary": ["faith", "love", "grace"],
                "vocabulary_meaning": {
                    "faith": "Confiance en Dieu. (Trust in God)",
                    "love":  "Amour envers les autres. (Love for others)",
                    "grace": "Faveur divine non meritee. (Undeserved divine favour)",
                },
            },
        )

    # ──────────────────────────────────────────
    # Agent 3 – Lesson Designer
    # ──────────────────────────────────────────

    def agent_lesson_designer(self, verse_data: dict, reading_data: dict, language_level: str) -> dict:
        lang_lower = self.target_language.lower()

        system_prompt = f"""You are an expert language lesson designer for {self.target_language}.
Create a comprehensive lesson for {language_level} level including:

1. READING: 4-5 comprehension questions (in {self.target_language})
2. WRITING: 3 writing prompts (in {self.target_language})
3. LISTENING: 4 listening questions (in {self.target_language})
4. SPEAKING: 3 speaking prompts (in {self.target_language})
5. FILLING: 3-4 fill-in-the-blank sentences using ___ for blanks (in {self.target_language})

Return ONLY valid JSON with:
- "reading_exercises": Array of objects with "question" field
- "writing_exercises": Array of objects with "question" field
- "listening_exercises": Array of objects with "question" field
- "speaking_exercises": Array of objects with "question" field
- "filling_exercises": Array of objects with "question" field"""

        user_message = (
            f"Verse: {verse_data.get('verse_reference')}\n"
            f"Reading: {reading_data.get(f'reading_text_{lang_lower}', '')[:200]}\n"
            f"Vocabulary: {reading_data.get('key_vocabulary', [])}"
        )

        response = self._call_gpt(system_prompt, user_message, temperature=0.7)
        return self._parse_json(
            response,
            {
                "reading_exercises":  [{"question": "Quel est le theme principal du texte?"}],
                "writing_exercises":  [{"question": "Ecris sur ton experience personnelle avec ce theme."}],
                "listening_exercises":[{"question": "Quels mots cles as-tu entendus?"}],
                "speaking_exercises": [{"question": "Explique le sens du verset dans tes propres mots."}],
                "filling_exercises":  [{"question": "La ___ est importante dans la vie chretienne."}],
            },
        )

    # ──────────────────────────────────────────
    # Agent 4 – Answer Key Generator
    # ──────────────────────────────────────────

    def agent_answer_key_generator(self, lesson_data: dict, verse_data: dict, reading_data: dict) -> dict:
        lang_lower = self.target_language.lower()

        system_prompt = f"""You are an answer key generator for {self.target_language}.
Provide detailed answers in {self.target_language}.
For filling exercises, provide ONLY the missing word(s).

Return ONLY valid JSON with:
- "reading_exercises": Array with "answer" and "explanation"
- "writing_exercises": Array with "answer" and "explanation"
- "listening_exercises": Array with "answer" and "explanation"
- "speaking_exercises": Array with "answer" and "explanation"
- "filling_exercises": Array with "answer" and "explanation""""

        user_message = (
            f"Exercises: {json.dumps(lesson_data, ensure_ascii=False)[:500]}\n"
            f"Reading context: {reading_data.get(f'reading_text_{lang_lower}', '')[:300]}\n"
            f"Vocabulary: {reading_data.get('key_vocabulary', [])}"
        )

        response = self._call_gpt(system_prompt, user_message, temperature=0.5)
        return self._parse_json(
            response,
            {
                "reading_exercises":  [{"answer": "Le theme principal est...", "explanation": "Voir le paragraphe principal"}],
                "writing_exercises":  [{"answer": "Exemple de reponse",        "explanation": "Reponse modele"}],
                "listening_exercises":[{"answer": "Mots cles: foi, amour",     "explanation": "Ecouter attentivement"}],
                "speaking_exercises": [{"answer": "Le verset signifie que...", "explanation": "Guide de conversation"}],
                "filling_exercises":  [{"answer": "foi",                       "explanation": "Mot correct selon le contexte"}],
            },
        )

    # ──────────────────────────────────────────
    # Agent 5 – Grammar Lesson
    # ──────────────────────────────────────────

    def agent_grammar_lesson(self, reading_data: dict, language_level: str) -> dict:
        lang = self.target_language
        lang_lower = lang.lower()
        reading_text = reading_data.get(f"reading_text_{lang_lower}", "")

        system_prompt = f"""You are an expert {lang} grammar teacher for {language_level} learners.
Identify 1-2 grammar points present in the reading text that are useful for {language_level} learners.

Return ONLY valid JSON with:
- "grammar_points": Array of objects, each with:
    - "name": Short name of the grammar point
    - "explanation": Clear explanation in English (2-4 sentences)
    - "rule": The rule in simple terms
    - "examples": Array of objects with "sentence_{lang_lower}" and "sentence_english"
- "grammar_exercises": Array of objects with "instruction" and "exercise" fields
- "grammar_tips": A helpful tip string for {language_level} learners in English"""

        user_message = (
            f"Reading text in {lang}:\n{reading_text}\n\n"
            f"Learner level: {language_level}"
        )

        response = self._call_gpt(system_prompt, user_message, temperature=0.6)
        return self._parse_json(
            response,
            {
                "grammar_points": [{
                    "name": "Basic Grammar",
                    "explanation": "Grammar explanation based on the reading.",
                    "rule": "See examples below.",
                    "examples": [{f"sentence_{lang_lower}": "Exemple.", "sentence_english": "Example."}],
                }],
                "grammar_exercises": [{"instruction": "Rewrite using the grammar point.", "exercise": "Practice sentence."}],
                "grammar_tips": f"Focus on understanding the grammar pattern in context at {language_level} level.",
            },
        )

    # ──────────────────────────────────────────
    # Agent 6 – Role Play Creator
    # ──────────────────────────────────────────

    def agent_roleplay_creator(self, verse_data: dict, reading_data: dict, language_level: str) -> dict:
        lang = self.target_language
        lang_lower = lang.lower()
        theme = verse_data.get("verse_reference", "today's reading")

        system_prompt = f"""You are a creative {lang} conversation coach for {language_level} learners.
Design an engaging role-play scenario inspired by the spiritual theme.
The scenario must involve a realistic everyday situation (cafe, work, with a neighbour).

Return ONLY valid JSON with:
- "scenario_title": Short catchy title
- "scenario_description": Description in English (3-5 sentences)
- "characters": Array of 2 objects with "name" and "role" fields
- "dialogue": Array of objects with "speaker", "line_{lang_lower}", "line_english"
- "useful_phrases": Array of objects with "phrase_{lang_lower}", "phrase_english", "notes"
- "conversation_challenges": Array of objects with "challenge" (in English)"""

        user_message = (
            f"Lesson theme / verse: {theme}\n"
            f"Reading topic: {reading_data.get('reading_text_english', '')[:200]}\n"
            f"Learner level: {language_level}\n"
            f"Target language: {lang}"
        )

        response = self._call_gpt(system_prompt, user_message, temperature=0.85)
        return self._parse_json(
            response,
            {
                "scenario_title": "Daily Conversation Practice",
                "scenario_description": "Practice everyday conversation inspired by today's lesson.",
                "characters": [{"name": "Person A", "role": "Learner"}, {"name": "Person B", "role": "Native Speaker"}],
                "dialogue": [{"speaker": "Person A", f"line_{lang_lower}": "Bonjour!", "line_english": "Hello!"}],
                "useful_phrases": [{f"phrase_{lang_lower}": "Comment allez-vous?", "phrase_english": "How are you?", "notes": "Formal greeting"}],
                "conversation_challenges": [{"challenge": "Try the dialogue without looking at translations."}],
            },
        )

    # ──────────────────────────────────────────
    # Agent 7 – TTS Generator
    # ──────────────────────────────────────────

    def agent_tts_generator(self, reading_text: str, language_level: str) -> str:
        try:
            audio_filename = (
                f"reading_audio_{self.target_language}_{language_level}_"
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
            )
            # Always use tempdir — writable on HF Spaces
            audio_path = os.path.join(tempfile.gettempdir(), audio_filename)
            print(f"Generating TTS audio: {audio_path}")

            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="alloy",
                input=reading_text,
                response_format="mp3",
            )
            with open(audio_path, "wb") as f:
                f.write(response.read())
            return audio_path
        except Exception as e:
            print(f"TTS Generation Error: {str(e)}")
            return None

    # ──────────────────────────────────────────
    # PDF generation
    # NOTE: Emojis removed from PDF text — ReportLab has no emoji font on HF Spaces
    # ──────────────────────────────────────────

    def generate_pdf(self, lesson_content: dict) -> str:
        filename = (
            f"bible_lesson_{self.target_language}_{lesson_content['level']}"
            f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        filepath = os.path.join(tempfile.gettempdir(), filename)
        print(f"PDF filepath: {filepath}")

        doc = SimpleDocTemplate(
            filepath, pagesize=letter,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=18,
        )

        elements = []
        styles = getSampleStyleSheet()
        lang_lower = self.target_language.lower()

        title_style = ParagraphStyle(
            "CustomTitle", parent=styles["Heading1"],
            fontSize=24, textColor="darkblue",
            spaceAfter=30, alignment=TA_CENTER,
        )

        # ── Title ──
        elements.append(Paragraph(
            f"Bible Language Learning Lesson<br/>{self.target_language}", title_style))
        elements.append(Spacer(1, 0.2 * inch))

        # ── Date / Level ──
        verse_data = lesson_content.get("verse_data", {})
        verse_date = verse_data.get("verse_date", datetime.now().strftime("%B %d, %Y"))
        elements.append(Paragraph(
            f"Date: {verse_date}<br/>Level: {lesson_content.get('level', 'B1')}",
            styles["BodyText"]))
        elements.append(Spacer(1, 0.3 * inch))

        # ── Verse ──
        elements.append(Paragraph("Verse of the Day", styles["Heading2"]))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(f"<b>{verse_data.get('verse_reference', 'N/A')}</b>", styles["BodyText"]))
        elements.append(Paragraph(f"<i>{verse_data.get(f'verse_text_{lang_lower}', 'N/A')}</i>", styles["BodyText"]))
        elements.append(Spacer(1, 0.2 * inch))

        source_url = verse_data.get("verse_source_url", "")
        if source_url:
            elements.append(Paragraph(f"Source: {source_url}", styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        meditation = verse_data.get(f"meditation_{lang_lower}", "")
        if meditation:
            elements.append(Paragraph(f"<b>Meditation:</b> {meditation}", styles["BodyText"]))
            elements.append(Spacer(1, 0.3 * inch))

        # ── Reading ──
        reading_data = lesson_content.get("reading_data", {})
        elements.append(Paragraph("Reading Comprehension", styles["Heading2"]))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(reading_data.get(f"reading_text_{lang_lower}", "N/A"), styles["BodyText"]))
        elements.append(Spacer(1, 0.3 * inch))

        if lesson_content.get("audio_path"):
            elements.append(Paragraph("<b>Audio available for listening exercise</b>", styles["BodyText"]))
            elements.append(Spacer(1, 0.2 * inch))

        # ── Key Vocabulary (simple list) ──
        vocab_list = reading_data.get("key_vocabulary", [])
        if vocab_list:
            elements.append(Paragraph("<b>Key Vocabulary:</b>", styles["BodyText"]))
            vocab_text = ", ".join(vocab_list) if isinstance(vocab_list, list) else str(vocab_list)
            elements.append(Paragraph(vocab_text, styles["BodyText"]))
            elements.append(Spacer(1, 0.2 * inch))

        # ── Vocabulary Meanings (dict: word -> definition) ──
        vocab_meaning = reading_data.get("vocabulary_meaning", {})
        if vocab_meaning:
            elements.append(Paragraph("<b>Key Vocabulary &amp; Meanings:</b>", styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))
            if isinstance(vocab_meaning, dict):
                for word, definition in vocab_meaning.items():
                    elements.append(Paragraph(f"<b>- {word}:</b> {definition}", styles["BodyText"]))
                    elements.append(Spacer(1, 0.05 * inch))
            elif isinstance(vocab_meaning, list):
                for item in vocab_meaning:
                    elements.append(Paragraph(f"- {item}", styles["BodyText"]))
                    elements.append(Spacer(1, 0.05 * inch))
            elements.append(Spacer(1, 0.3 * inch))

        elements.append(PageBreak())

        # ── Exercises ──
        lesson_data = lesson_content.get("lesson_data", {})
        self._add_exercises(elements, "Reading Exercises",          lesson_data.get("reading_exercises", []),  styles)
        self._add_exercises(elements, "Writing Exercises",          lesson_data.get("writing_exercises", []),  styles)
        self._add_exercises(elements, "Listening Exercises",        lesson_data.get("listening_exercises", []),styles)
        self._add_exercises(elements, "Speaking Exercises",         lesson_data.get("speaking_exercises", []), styles)
        self._add_exercises(elements, "Fill-in-the-Blank Exercises",lesson_data.get("filling_exercises", []),  styles)

        elements.append(PageBreak())

        # ── Grammar Lesson ──
        grammar_data = lesson_content.get("grammar_data", {})
        elements.append(Paragraph("Grammar Lesson", styles["Heading2"]))
        elements.append(Spacer(1, 0.1 * inch))

        for gp in grammar_data.get("grammar_points", []):
            elements.append(Paragraph(f"<b>{gp.get('name', '')}</b>", styles["Heading3"]))
            elements.append(Paragraph(gp.get("explanation", ""), styles["BodyText"]))
            elements.append(Paragraph(f"<i>Rule: {gp.get('rule', '')}</i>", styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))
            for ex in gp.get("examples", []):
                tl = ex.get(f"sentence_{lang_lower}", "")
                en = ex.get("sentence_english", "")
                elements.append(Paragraph(f"- {tl} <i>({en})</i>", styles["BodyText"]))
            elements.append(Spacer(1, 0.2 * inch))

        tips = grammar_data.get("grammar_tips", "")
        if tips:
            elements.append(Paragraph(f"<b>Tip:</b> {tips}", styles["BodyText"]))
            elements.append(Spacer(1, 0.2 * inch))

        elements.append(Paragraph("<b>Grammar Exercises</b>", styles["Heading3"]))
        for i, ex in enumerate(grammar_data.get("grammar_exercises", []), 1):
            elements.append(Paragraph(
                f"{i}. {ex.get('instruction', '')} - {ex.get('exercise', '')}",
                styles["BodyText"]))
            elements.append(Spacer(1, 0.15 * inch))

        elements.append(PageBreak())

        # ── Role Play ──
        rp = lesson_content.get("roleplay_data", {})
        elements.append(Paragraph("Role Play", styles["Heading2"]))
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(f"<b>{rp.get('scenario_title', '')}</b>", styles["Heading3"]))
        elements.append(Paragraph(rp.get("scenario_description", ""), styles["BodyText"]))
        elements.append(Spacer(1, 0.2 * inch))

        characters = rp.get("characters", [])
        if characters:
            char_text = " | ".join([f"<b>{c['name']}</b>: {c['role']}" for c in characters])
            elements.append(Paragraph(char_text, styles["BodyText"]))
            elements.append(Spacer(1, 0.15 * inch))

        elements.append(Paragraph("<b>Sample Dialogue</b>", styles["Heading3"]))
        for line in rp.get("dialogue", []):
            speaker  = line.get("speaker", "")
            tl_line  = line.get(f"line_{lang_lower}", "")
            en_line  = line.get("line_english", "")
            elements.append(Paragraph(f"<b>{speaker}:</b> {tl_line} <i>({en_line})</i>", styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph("<b>Useful Phrases</b>", styles["Heading3"]))
        for phrase in rp.get("useful_phrases", []):
            tl_p  = phrase.get(f"phrase_{lang_lower}", "")
            en_p  = phrase.get("phrase_english", "")
            note  = phrase.get("notes", "")
            note_str = f" ({note})" if note else ""
            elements.append(Paragraph(f"- <b>{tl_p}</b> - <i>{en_p}</i>{note_str}", styles["BodyText"]))
            elements.append(Spacer(1, 0.1 * inch))

        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph("<b>Conversation Challenges</b>", styles["Heading3"]))
        for i, ch in enumerate(rp.get("conversation_challenges", []), 1):
            elements.append(Paragraph(f"{i}. {ch.get('challenge', '')}", styles["BodyText"]))
            elements.append(Spacer(1, 0.12 * inch))

        elements.append(PageBreak())

        # ── Answer Key ──
        elements.append(Paragraph("Answer Key", styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))
        answers = lesson_content.get("answers", {})
        self._add_answers(elements, "Reading Answers",            answers.get("reading_exercises", []),  styles)
        self._add_answers(elements, "Writing Answers",            answers.get("writing_exercises", []),  styles)
        self._add_answers(elements, "Listening Answers",          answers.get("listening_exercises", []),styles)
        self._add_answers(elements, "Speaking Answers",           answers.get("speaking_exercises", []), styles)
        self._add_answers(elements, "Fill-in-the-Blank Answers",  answers.get("filling_exercises", []),  styles)

        doc.build(elements)
        return filepath

    def _add_exercises(self, elements, title, exercises, styles):
        elements.append(Paragraph(title, styles["Heading2"]))
        elements.append(Spacer(1, 0.1 * inch))
        if isinstance(exercises, list):
            for i, ex in enumerate(exercises, 1):
                question = ex.get("question", str(ex)) if isinstance(ex, dict) else str(ex)
                elements.append(Paragraph(f"{i}. {question}", styles["BodyText"]))
                elements.append(Spacer(1, 0.15 * inch))
        elements.append(Spacer(1, 0.3 * inch))

    def _add_answers(self, elements, title, answers, styles):
        elements.append(Paragraph(f"<b>{title}</b>", styles["Heading3"]))
        elements.append(Spacer(1, 0.1 * inch))
        if isinstance(answers, list):
            for i, ans in enumerate(answers, 1):
                if isinstance(ans, dict):
                    answer = ans.get("answer", "")
                    explanation = ans.get("explanation", "")
                    text = f"{i}. <b>{answer}</b>"
                    if explanation:
                        text += f" <i>({explanation})</i>"
                else:
                    text = f"{i}. {str(ans)}"
                elements.append(Paragraph(text, styles["BodyText"]))
                elements.append(Spacer(1, 0.1 * inch))
        elements.append(Spacer(1, 0.2 * inch))

    # ──────────────────────────────────────────
    # Orchestrator
    # ──────────────────────────────────────────

    def run_full_lesson_generation(self, language_level: str = "B1"):
        print("0.00  Starting lesson generation...")

        print("0.10  Fetching verse of the day...")
        verse_data = self.agent_verse_retriever(language_level)

        print("0.25  Creating reading comprehension...")
        reading_data = self.agent_content_creator(verse_data, language_level)

        print("0.38  Designing lesson exercises...")
        lesson_data = self.agent_lesson_designer(verse_data, reading_data, language_level)

        print("0.50  Generating answer key...")
        answers = self.agent_answer_key_generator(lesson_data, verse_data, reading_data)

        print("0.62  Building grammar lesson...")
        grammar_data = self.agent_grammar_lesson(reading_data, language_level)

        print("0.74  Creating role-play scenario...")
        roleplay_data = self.agent_roleplay_creator(verse_data, reading_data, language_level)

        print("0.84  Generating audio...")
        audio_path = None
        reading_text = reading_data.get(f"reading_text_{self.target_language.lower()}", "")
        if reading_text:
            audio_path = self.agent_tts_generator(reading_text, language_level)

        print("0.93  Creating PDF...")
        lesson_content = {
            "level":        language_level,
            "verse_data":   verse_data,
            "reading_data": reading_data,
            "lesson_data":  lesson_data,
            "answers":      answers,
            "grammar_data": grammar_data,
            "roleplay_data":roleplay_data,
            "audio_path":   audio_path,
        }
        pdf_path = self.generate_pdf(lesson_content)

        print("1.00  Complete!")
        return lesson_content, pdf_path, audio_path


# ─────────────────────────────────────────────
# Display helper
# ─────────────────────────────────────────────

def format_lesson_display(lesson_content):
    verse_data   = lesson_content.get("verse_data", {})
    reading_data = lesson_content.get("reading_data", {})
    lesson_data  = lesson_content.get("lesson_data", {})
    grammar_data = lesson_content.get("grammar_data", {})
    roleplay_data= lesson_content.get("roleplay_data", {})

    lang_keys = [k for k in verse_data.keys() if k.startswith("verse_text_") and k != "verse_text_english"]
    verse_lang_key    = lang_keys[0] if lang_keys else "verse_text_english"
    meditation_key    = verse_lang_key.replace("verse_text_", "meditation_")
    reading_lang_key  = verse_lang_key.replace("verse_text_", "reading_text_")
    lang_lower        = verse_lang_key.replace("verse_text_", "")

    source_url  = verse_data.get("verse_source_url", "")
    source_line = f"\n[Read online]({source_url})" if source_url else ""

    # ── Vocabulary Meaning block (dict-safe) ──
    vocab_meaning = reading_data.get("vocabulary_meaning", {})
    if isinstance(vocab_meaning, dict) and vocab_meaning:
        vocab_md = "\n".join([f"- **{w}**: {d}" for w, d in vocab_meaning.items()])
    elif isinstance(vocab_meaning, list) and vocab_meaning:
        vocab_md = "\n".join([f"- {item}" for item in vocab_meaning])
    else:
        vocab_md = ""

    output = f"""
# Verse of the Day — {verse_data.get('verse_date', '')}

**{verse_data.get('verse_reference', 'N/A')}**

*{verse_data.get(verse_lang_key, verse_data.get('verse_text_english', 'N/A'))}*{source_line}

**Meditation:**
{verse_data.get(meditation_key, verse_data.get('meditation_english', 'N/A'))}

---

# Reading Comprehension

{reading_data.get(reading_lang_key, reading_data.get('reading_text_english', 'N/A'))}

**Key Vocabulary:** {', '.join(reading_data.get('key_vocabulary', []))}

**Vocabulary & Meanings:**
{vocab_md}

---

# Grammar Lesson

"""
    for gp in grammar_data.get("grammar_points", []):
        output += f"## {gp.get('name', '')}\n"
        output += f"{gp.get('explanation', '')}\n\n"
        output += f"**Rule:** {gp.get('rule', '')}\n\n"
        output += "**Examples:**\n"
        for ex in gp.get("examples", []):
            tl = ex.get(f"sentence_{lang_lower}", "")
            en = ex.get("sentence_english", "")
            output += f"- {tl} *({en})*\n"
        output += "\n"

    tips = grammar_data.get("grammar_tips", "")
    if tips:
        output += f"> **Tip:** {tips}\n\n"

    output += "**Grammar Exercises:**\n"
    for i, ex in enumerate(grammar_data.get("grammar_exercises", []), 1):
        output += f"{i}. {ex.get('instruction', '')} — *{ex.get('exercise', '')}*\n"

    output += f"""

---

# Role Play — {roleplay_data.get('scenario_title', '')}

{roleplay_data.get('scenario_description', '')}

**Characters:** {' | '.join([f"{c['name']} ({c['role']})" for c in roleplay_data.get('characters', [])])}

### Sample Dialogue
"""
    for line in roleplay_data.get("dialogue", []):
        speaker = line.get("speaker", "")
        tl_line = line.get(f"line_{lang_lower}", "")
        en_line = line.get("line_english", "")
        output += f"**{speaker}:** {tl_line} *({en_line})*\n\n"

    output += "\n### Useful Phrases\n"
    for phrase in roleplay_data.get("useful_phrases", []):
        tl_p = phrase.get(f"phrase_{lang_lower}", "")
        en_p = phrase.get("phrase_english", "")
        note = phrase.get("notes", "")
        output += f"- **{tl_p}** — {en_p}" + (f" *({note})*" if note else "") + "\n"

    output += "\n### Conversation Challenges\n"
    for i, ch in enumerate(roleplay_data.get("conversation_challenges", []), 1):
        output += f"{i}. {ch.get('challenge', '')}\n"

    output += """

---

# Exercises

## Reading Exercises
"""
    for i, ex in enumerate(lesson_data.get("reading_exercises", []), 1):
        output += f"{i}. {ex.get('question', str(ex))}\n"

    output += "\n## Writing Exercises\n"
    for i, ex in enumerate(lesson_data.get("writing_exercises", []), 1):
        output += f"{i}. {ex.get('question', str(ex))}\n"

    output += "\n## Listening Exercises\n"
    for i, ex in enumerate(lesson_data.get("listening_exercises", []), 1):
        output += f"{i}. {ex.get('question', str(ex))}\n"

    output += "\n## Speaking Exercises\n"
    for i, ex in enumerate(lesson_data.get("speaking_exercises", []), 1):
        output += f"{i}. {ex.get('question', str(ex))}\n"

    output += "\n## Fill-in-the-Blank Exercises\n"
    for i, ex in enumerate(lesson_data.get("filling_exercises", []), 1):
        output += f"{i}. {ex.get('question', str(ex))}\n"

    return output


# ─────────────────────────────────────────────
# Gradio entry point
# FIX: signature now matches the 4 inputs sent by Gradio (api_key, language, level, model)
# elevenlabs_key removed from UI since TTS uses OpenAI
# ─────────────────────────────────────────────

def generate_lesson(api_key: str, language: str, level: str, model: str):
    if not api_key:
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "Please enter your OpenAI API key", None, None

    try:
        system = BibleLanguageLearningSystem(
            api_key=api_key,
            target_language=language,
            model=model,
        )
        lesson_content, pdf_path, audio_path = system.run_full_lesson_generation(level)
        display_text = format_lesson_display(lesson_content)
        return display_text, pdf_path, audio_path
    except Exception as e:
        import traceback
        return f"Error: {str(e)}\n\n{traceback.format_exc()}", None, None


# ─────────────────────────────────────────────
# Gradio UI
# FIX: removed height= from gr.Markdown (not supported in current Gradio)
# FIX: removed elevenlabs_key input — it was passed to generate_lesson but not used
# ─────────────────────────────────────────────

with gr.Blocks(title="Bible Language Learning System", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # Bible Language Learning System
    ### Learn Languages Through Scripture with AI

    This agentic AI system creates personalised language lessons based on the daily Bible verse.
    Each lesson includes reading, grammar, role-play, listening, writing, speaking, and fill-in-the-blank exercises.
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Settings")

            api_key = gr.Textbox(
                label="OpenAI API Key",
                placeholder="sk-...",
                type="password",
                info="Get your key from platform.openai.com"
            )

            language = gr.Dropdown(
                choices=["Spanish", "French", "German", "Italian", "Portuguese",
                         "Chinese", "Japanese", "Korean", "Arabic", "Hebrew"],
                value="Spanish",
                label="Target Language"
            )

            level = gr.Dropdown(
                choices=["A1", "A2", "B1", "B2", "C1", "C2"],
                value="B1",
                label="Language Level (CEFR)",
                info="A1=Beginner  B1=Intermediate  C1=Advanced"
            )

            model = gr.Dropdown(
                choices=["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
                value="gpt-4o-mini",
                label="AI Model",
                info="gpt-4o-mini recommended for cost/quality balance"
            )

            generate_btn = gr.Button("Generate Lesson", variant="primary", size="lg")

            gr.Markdown("""
            ### How it works
            1. **Agent 1** — Fetches today's real Bible verse
            2. **Agent 2** — Creates reading comprehension + vocabulary
            3. **Agent 3** — Designs exercises
            4. **Agent 4** — Generates answer key
            5. **Agent 5** — Builds grammar mini-lesson
            6. **Agent 6** — Creates role-play scenario
            7. **Agent 7** — Generates audio (TTS)
            8. PDF created automatically

            ### Estimated cost per lesson
            - gpt-4o-mini: ~$0.01–0.02
            - gpt-4o: ~$0.10–0.20
            """)

        with gr.Column(scale=2):
            gr.Markdown("### Your Lesson")

            lesson_output = gr.Markdown(
                value="Click **Generate Lesson** to create your personalised Bible language lesson!"
            )

            with gr.Row():
                pdf_output = gr.File(
                    label="Download PDF Lesson",
                    file_types=[".pdf"]
                )
                audio_output = gr.Audio(
                    label="Listening Audio",
                    type="filepath"
                )

    # FIX: inputs list matches the 4 parameters of generate_lesson exactly
    generate_btn.click(
        fn=generate_lesson,
        inputs=[api_key, language, level, model],
        outputs=[lesson_output, pdf_output, audio_output]
    )

    gr.Markdown("""
    ---
    ### API Keys
    - **OpenAI** (required): [platform.openai.com](https://platform.openai.com/)

    ### About
    Bible verse sourced daily from [discoverybiblestudy.org](https://discoverybiblestudy.org).
    Audio generated with OpenAI TTS (no extra key needed).
    """)

if __name__ == "__main__":
    demo.launch()