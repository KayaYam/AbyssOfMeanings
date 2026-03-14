import sys
import argparse
from ..query_engine import get_context
from ..llm_client import ask_llm  # Убедись, что этот файл существует

def run_ask(question, mode="ask"):
    context_text, sources = get_context(question, mode=mode)
    
    # Формируем промпт для LLM
    answer = ask_llm(question, context_text)
    
    # Формируем красивый текстовый блок
    output = []
    output.append("="*50)
    output.append(f"ВОПРОС: {question}")
    output.append("-"*50)
    output.append(answer)
    output.append("-"*50)
    
    if sources:
        output.append("\nИСТОЧНИКИ:")
        unique_sources = { (s['id'], s['title']) for s in sources }
        for i, (doc_id, title) in enumerate(unique_sources, 1):
            output.append(f"[{i}] {title}")
    output.append("="*50)
    
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--mode", default="ask")
    args = parser.parse_args()
    
    print(run_ask(args.question, args.mode))

if __name__ == "__main__":
    main()