# src/brain2/ollama_summarizer.py
import re
import json
import subprocess
from pathlib import Path
import ollama

def clean_reasoning_output(text: str) -> str:
    """
    Удаляет все блоки, начинающиеся с 'Thinking...' и заканчивающиеся на '...done thinking.'
    Оставляет только финальный ответ модели.
    """
    # Регулярное выражение, которое учитывает:
    # - 'Thinking' в любом регистре
    # - возможные точки и пробелы после 'Thinking'
    # - любой текст между (включая переносы строк)
    # - 'done thinking' в любом регистре с возможными точками в конце
    pattern = r'Thinking[.]*\s*[\s\S]*?done[ ]+thinking[.]*'
    
    # Удаляем все совпадения
    cleaned = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Убираем возможные лишние пробелы/пустые строки
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned).strip()
    
    # Если после очистки текст пустой, возвращаем оригинальный текст
    if not cleaned:
        return text
    
    return cleaned

def ollama_chat(system_prompt, user_prompt, model="qwen3.5:9b"):
    try:
    # Библиотека ollama сама управляет ожиданием и работает быстрее
        response = ollama.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt},
            ],
            options={
                'temperature': 0.2, # Снижаем фантазию
                'num_ctx': 4096     # Увеличиваем окно контекста для длинных списков
            }
        )
        return response['message']['content']
    except Exception as e:
        return f"Ошибка при обращении к Ollama: {str(e)}"

# def ollama_chat(
    # system_prompt: str,
    # user_prompt: str,
    # model: str = "qwen3.5:9b",
    # temperature: float = 0.3,
# ) -> str:
    # payload = {
        # "model": model,
        # "prompt": user_prompt,
        # "system": system_prompt,
        # "stream": False,
        # "options": {
            # "temperature": temperature,
            # "num_predict": 1200,  # увеличиваем для более длинных ответов
        # },
    # }
    
    # try:
        # proc = subprocess.run(
            # ["ollama", "run", model],
            # input=json.dumps(payload).encode(),
            # capture_output=True,
            # check=True,
            # timeout=600,
        # )
        # raw_output = proc.stdout.decode(errors="ignore").strip()
        # return clean_reasoning_output(raw_output)
    # except subprocess.CalledProcessError as exc:
        # err_msg = exc.stderr.decode(errors="ignore").strip()
        # raise RuntimeError(f"Ollama error: {err_msg}") from exc
    # except subprocess.TimeoutExpired:
        # raise RuntimeError("Ollama timeout - модель слишком долго генерировала ответ")

def summarize_text(text: str, max_len: int = 5000) -> str:
    """
    Генерирует подробное изложение научной статьи (15-20 предложений).
    
    system = (
    //    "Ты — научный журналист. Твоя задача: пересказать научную статью простым языком, "
     //   "как если бы объяснял другу. Не добавляй рассуждений — только факты из статьи.\n\n"
    //    "ТРЕБОВАНИЯ:\n"
    //    "- Объём: 15-20 предложений\n"
    //    "- Структура: проблема → методы → результаты → значение\n"
    //    "- Язык: живой, разговорный, без терминов\n"
    //    "- Объясняй сложные понятия в скобках\n"
    //    "- Начинай сразу с сути, без вступлений\n"
    //    "- Никаких 'статья показывает', 'авторы считают'\n\n"
    //    "ПРИМЕР ХОРОШЕГО ОТВЕТА:\n"
    //    "'Учёные обнаружили, что кофе улучшает память (способность запоминать информацию). "
    //    "Они дали 100 людям по чашке кофе и проверили их память. "
    //    "Результаты показали, что память улучшилась на 20%. "
    //    "Это может помочь при лечении возрастных проблем с памятью.'"
    //)
    """
    
    system = ("Ты популяризатор науки. Изложи суть и идеи этой статьи в научно-популярном стиле на русском языке")
    
    user = (
        f"Ты популяризатор науки. Изложи суть и идеи этой статьи в научно-популярном стиле на русском языке:\n\n"
        f"{text[:max_len]}\n\n"
    )
    
    return ollama_chat(system, user)
