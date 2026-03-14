from .ollama_summarizer import ollama_chat
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def ask_llm(question, context):
    system_prompt = (
        "Ты — аналитик и эксперт в области когнитивных наук и психологии. "
        "Используй предоставленный контекст из научных статей, чтобы ответить на вопрос. "
        "Если в контексте нет ответа, честно скажи об этом. "
        "Твой ответ должен быть структурированным и на русском языке."
    )
    
    user_prompt = f"КОНТЕКСТ ИЗ СТАТЕЙ:\n{context}\n\nВОПРОС ПОЛЬЗОВАТЕЛЯ: {question}"
    
    # Используем твою проверенную модель
    return ollama_chat(system_prompt, user_prompt, model="qwen3.5:9b")