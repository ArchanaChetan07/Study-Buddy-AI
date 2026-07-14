"""
templates.py — LangChain prompt templates for question generation.
"""
from langchain_core.prompts import PromptTemplate

mcq_prompt_template = PromptTemplate(
    template=(
        "You are an expert educator creating a quiz.\n\n"
        "Generate a {difficulty} multiple-choice question about: {topic}\n\n"
        "Rules:\n"
        "- The question must be clear and factually accurate.\n"
        "- Provide EXACTLY 4 options — no more, no fewer.\n"
        "- The correct_answer must be copied EXACTLY from the options array.\n"
        "- Distractors should be plausible but clearly wrong to a knowledgeable reader.\n\n"
        "Return ONLY a valid JSON object — no markdown fences, no preamble:\n"
        "{{\n"
        '    "question": "<the question text>",\n'
        '    "options": ["<option A>", "<option B>", "<option C>", "<option D>"],\n'
        '    "correct_answer": "<one of the four options>"\n'
        "}}"
    ),
    input_variables=["topic", "difficulty"],
)

fill_blank_prompt_template = PromptTemplate(
    template=(
        "You are an expert educator creating a quiz.\n\n"
        "Generate a {difficulty} fill-in-the-blank question about: {topic}\n\n"
        "Rules:\n"
        "- Use exactly three underscores '___' to mark the blank — no more, no fewer.\n"
        "- The sentence must make complete sense when the blank is filled.\n"
        "- The answer must be a specific word or short phrase (≤ 5 words).\n"
        "- The question should be factually accurate.\n\n"
        "Return ONLY a valid JSON object — no markdown fences, no preamble:\n"
        "{{\n"
        '    "question": "<sentence with ___ as the blank>",\n'
        '    "answer": "<correct word or phrase>"\n'
        "}}"
    ),
    input_variables=["topic", "difficulty"],
)
