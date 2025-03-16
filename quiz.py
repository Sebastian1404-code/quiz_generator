#!/usr/bin/env python
# coding: utf-8

# In[5]:


import gradio as gr
import openai
import json
import PyPDF2
from dotenv import load_dotenv
import os


# In[2]:


get_ipython().system('pip install pypdf2')


# In[6]:


load_dotenv(override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')


# In[53]:


def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def generate_quiz_from_pdf(pdf_file):
    text = extract_text_from_pdf(pdf_file)

    prompt = f"""
    Generate 10 multiple-choice quiz questions from the following text.
    Each question should have exactly 4 answer options, with only one correct answer.
    Return the result in JSON format like this:
    [
        {{"question": "What is AI?", "options": ["A technology", "A fruit", "A car", "A planet"], "correct": "A technology"}},
        {{"question": "What is Java?", "options": ["A type of coffee", "A fruit", "A car", "A programming language"], "correct": "A programming language"}},
        ...
    ]
    Don't add extra words besides the format that I provide meaning that the response is just a list of dictionaries.
    Here is the text:
    {text}
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a helpful assistant that generates multiple-choice quizzes."},
                  {"role": "user", "content": prompt}]
    )

    try:
        content = response.choices[0].message.content
        if content.startswith("```json") and content.endswith("```"):
            content = content[7:-3].strip() 
        questions = json.loads(content)
        if isinstance(questions, list):  # Ensure the parsed object is a list
                return questions
        else:
             return "Error: API did not return a valid list of questions."
    except json.JSONDecodeError:
        return "Error generating questions."


# In[58]:


quiz_questions = []
current_index = 0


# In[66]:


def show_question(index):
    global current_index
    if 0 <= index < len(quiz_questions):
        current_index = index
        question = quiz_questions[index]["question"]
        options = quiz_questions[index]["options"]
        return question, gr.update(choices=options), "" 
    return "No questions available", [], ""


# In[69]:


def check_answer(user_answer):
    global current_index
    if not quiz_questions:
        return "No quiz available. Please generate a quiz first."

    if user_answer is None:
        return "⚠️ You need to answer this question."
    
    correct_answer = quiz_questions[current_index]["correct"]
    if user_answer == correct_answer:
        return "✅ Correct!"
    else:
        return f"❌ Incorrect. The correct answer is: {correct_answer}"

def process_pdf(pdf_file):
    global quiz_questions, current_index
    quiz_questions = generate_quiz_from_pdf(pdf_file)  
    if isinstance(quiz_questions, str) and quiz_questions.startswith("Error"):
        return quiz_questions, gr.update(choices=[]), "" 
    current_index = 0
    return show_question(0)


# In[70]:


with gr.Blocks(theme=gr.themes.Soft()) as iface:
    gr.Markdown("# AI-Powered Multiple-Choice Quiz from PDF")

    pdf_input = gr.File(label="Upload a PDF", type="filepath")
    start_button = gr.Button("Generate Quiz")

    question_box = gr.Textbox(label="Question", interactive=False)
    choices = gr.Radio(label="Select an Answer", choices=[])
    check_button = gr.Button("Check Answer")
    feedback = gr.Textbox(label="Feedback", interactive=False)

    with gr.Row():
        prev_button = gr.Button("Previous")
        next_button = gr.Button("Next")

    # Event handlers
    start_button.click(process_pdf, inputs=pdf_input, outputs=[question_box, choices, feedback])
    check_button.click(check_answer, inputs=choices, outputs=[feedback])

    prev_button.click(lambda: show_question(current_index - 1), outputs=[question_box, choices, feedback])
    next_button.click(lambda: show_question(current_index + 1), outputs=[question_box, choices, feedback])

iface.launch()





