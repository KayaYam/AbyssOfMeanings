import sys
import io
import codecs
from .. import semantic_downloader as s2

# Это заставит консоль Windows понимать UTF-8
sys.stdout.reconfigure(encoding='utf-8')
from .. import arxiv_downloader as arxiv

# Принудительный UTF-8 для Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
STOP_WORDS = [
        "deep learning", "neural network", "transformer", "large language model", 
        "robot", "computer vision", "algorithmic", "architecture", "benchmark",
        "training", "optimization", "gradient", "backpropagation", "implementation"
    ]

exclude_query = " OR ".join([f'all:"{word}"' for word in STOP_WORDS])

def main():
    # Настройки глубины (сколько статей на одну тему мы хотим в базе)
    DEPTH_PER_TOPIC = 1000  # Например, возьмем по 150 последних по каждой теме
    BATCH_SIZE = 50        # arXiv отдает порциями по 50

    queries = [
        ("мышление", "human reasoning", "q-bio.NC ANDNOT cat:cs.*"),
        ("психология", "cognitive psychology", "q-bio.NC ANDNOT cat:cs.*"),
        ("Талеб", "fat tails probability", "stat.TH ANDNOT cat:cs.*"),
        ("Талеб", "Nassim Taleb", "econ.TH"),
        ("когнитивистика", "human cognition", "q-bio.NC ANDNOT cat:cs.*"),
        ("Сапольски", "Robert Sapolsky neurobiology of behavior stress free will"),
        ("Сапольски", "Robert Sapolsky determinism and moral responsibility"),
        ("Брене Браун", "Brené Brown vulnerability and shame resilience"),
        ("Брене Браун", "Brené Brown courageous leadership and empathy"),
        ("Брене Браун", "Brené Brown qualitative research grounded theory"),
        ("Сапольски", "Robert Sapolsky Why Zebras Don't Get Ulcers")
    ]
    
    cognitive_queries = [
        ("мышление", "human mental models and heuristics"),
        ("мышление", "epistemology of decision making uncertainty"),
        ("мышление", "cognitive biases in human reasoning"),
        ("мышление", "dual process theory psychology"),
        ("мышление", "bounded rationality and intuitive judgment"),
        ("мышление", "metacognition and critical thinking")
    ]

# И запускаем их так же через s2.search_and_download
    for label, query in cognitive_queries:
        s2.search_and_download(query, label, limit=100)

    thinkers = [
    # Фундамент: Талеб и Далио
    ("Талеб", "Nassim Nicholas Taleb antifragility incerto"),
    ("Далио", "Ray Dalio economic machine principles"),
    
    # Когнитивистика и ошибки
    ("Каннеман", "Daniel Kahneman judgment heuristics bias"),
    ("Саймон", "Herbert Simon bounded rationality decision making"),
    
    # Прогнозирование и системы
    ("Тетлок", "Philip Tetlock superforecasting expert judgment"),
    ("Мангер", "Charlie Munger mental models lattices"),
    
    # Причинность и реальность
    ("Перл", "Judea Pearl causality calculus do-calculus"),
    ("Хоффман", "Donald Hoffman interface theory of perception"),
]
    
    print("\n=== ЗАПУСК СБОРА МЫСЛИТЕЛЕЙ (Semantic Scholar) ===")
    for label, query in thinkers:
        s2.search_and_download(query, label, limit=100)
    
    # Фильтр дат: от 2015 года до сегодня (чтобы не брать совсем старье)
    date_filter = "submittedDate:[201001010000 TO 202612312359]"

    for label, kw, cat in queries:
        print(f"\n[ARCHIVE] Копаем тему: {label} ({kw})")
        
        # Цикл по страницам (оффсетам)
        for start_index in range(0, DEPTH_PER_TOPIC, BATCH_SIZE):
            print(f"  > Запрашиваем статьи с {start_index} по {start_index + BATCH_SIZE}...")
            
            # Добавляем фильтр даты к категории
            full_cat = f"{cat} AND {date_filter}"
            
            results = arxiv.run(
                keywords=kw,
                categories=cat,
                #categories=full_cat,
                exclude="robot OR drone OR 'neural network'",
                max_total=BATCH_SIZE,
                start=start_index # Передаем оффсет
            )
            
            if not results: # Если arXiv больше ничего не отдает по этому запросу
                break

if __name__ == "__main__":
    main()