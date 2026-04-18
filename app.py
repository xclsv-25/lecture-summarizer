def create_pdf(summary, flashcards, quiz):
    doc = SimpleDocTemplate("lecture_notes.pdf")
    styles = getSampleStyleSheet()

    content = []

    content.append(Paragraph("Lecture Summary", styles["Heading1"]))
    content.append(Paragraph(summary.replace("\n", "<br/>"), styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("Flashcards", styles["Heading1"]))
    content.append(Paragraph(flashcards.replace("\n", "<br/>"), styles["Normal"]))
    content.append(Spacer(1, 12))

    content.append(Paragraph("Quiz", styles["Heading1"]))
    content.append(Paragraph(quiz.replace("\n", "<br/>"), styles["Normal"]))

    doc.build(content)

    return "lecture_notes.pdf"

import streamlit as st
import whisper
from openai import OpenAI
client = OpenAI()
import tempfile

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

st.title("🎓 AI Lecture Assistant")
st.markdown("---")
st.caption("Turn lectures into summaries, flashcards, and quizzes instantly.")

@st.cache_resource
def load_model():
    return whisper.load_model("base")

model = load_model()

uploaded_file = st.file_uploader("Upload Audio", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    st.success(f"Uploaded: {uploaded_file.name}")
    st.divider()

    with open("temp_audio.mp3", "wb") as f:
        f.write(uploaded_file.read())

    temp_path = "temp_audio.mp3"

    if st.button("🚀 Generate Study Materials", use_container_width=True):

        # 🔹 TRANSCRIPTION
        with st.spinner("Transcribing..."):
            result = model.transcribe(temp_path)
            transcript = result["text"]

        st.subheader("Transcript")
        st.text_area("", transcript, height=200)
        st.divider()

        # 🔹 SUMMARY
        with st.spinner("Summarizing..."):
            prompt = f"""
You are an expert academic assistant.

Analyze this lecture and produce:
- Key Topics
- Explanation
- Definitions
- Notes
- Exam Questions

Lecture:
{transcript[:3000]}
"""
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            summary = response.choices[0].message.content

        # 🔹 FLASHCARDS
        with st.spinner("Generating flashcards..."):
            flashcard_prompt = f"""
Create 5-10 flashcards.

Format:
Q: question
A: answer

Lecture:
{transcript[:3000]}
"""
            flashcard_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": flashcard_prompt}]
            )
            flashcards = flashcard_response.choices[0].message.content

            st.divider()


        # 🔹 QUIZ
        with st.spinner("Generating quiz..."):
            quiz_prompt = f"""
You are a teacher.

Create 5 multiple choice questions.

Format:
Q1: Question
A. Option
B. Option
C. Option
D. Option
Answer: Letter
Explanation: Brief explanation

Lecture:
{transcript[:3000]}
"""
            quiz_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": quiz_prompt}]
            )
            quiz = quiz_response.choices[0].message.content
            questions = quiz.split("\n\n")
            
            st.divider()
        # 🔹 TABS
        tab1, tab2, tab3 = st.tabs(["📄 Summary", "🧠 Flashcards", "📝 Quiz"])

        with tab1:
            st.markdown(summary)
            pdf_file = create_pdf(summary, flashcards, quiz)
        
        with open(pdf_file, "rb") as f:
            st.download_button(
            label="📄 Download Full Notes as PDF",
            data=f,
            file_name="lecture_notes.pdf",
            mime="application/pdf"
        )

        with tab2:
            st.markdown(flashcards)

        with tab3:
            st.subheader("📝 Interactive Quiz")

        score = 0

        for i, q in enumerate(questions):
            lines = q.split("\n")

            if len(lines) < 6:
                continue 

            question = lines[0]
        options = lines[1:5]
        answer_line = lines[5]

        correct_answer = answer_line.split(":")[-1].strip()

        st.write(question)

        user_answer = st.radio(
            f"Select answer for Q{i+1}",
            options,
            key=f"q{i}"
        )

        if user_answer.startswith(correct_answer):
            score += 1

        if st.button("Submit Quiz"):
            st.success(f"Your Score: {score}/{len(questions)}")
