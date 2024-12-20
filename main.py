import requests
from bs4 import BeautifulSoup, Comment
from dotenv import load_dotenv
import os
import json
from langfuse.decorators import observe, langfuse_context
from langfuse.openai import openai
import uuid

load_dotenv()
visited_urls = set()

def get_page_content(url):
    try:
        if url in visited_urls:
            print(f"Już byliśmy na: {url}")
            return None
        
        visited_urls.add(url)
        response = requests.get(url)
        return response.text
    except Exception as e:
        print(f"Błąd podczas pobierania strony {url}: {e}")
        return None
    
def clean_html(html_content):
    if html_content:
        soup= BeautifulSoup(html_content, 'html.parser')

        if soup.head:
            soup.head.decompose()

        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        for tag in soup.find_all():
            if tag.has_attr('class'):
                del tag['class']

        return str(soup.body) if soup.body else str(soup)
    return ""

def get_questions_from_user():
    questions = {}
    print("\nWprowadź pytania (aby zakończyć, naciśnij Enter bez wpisywania pytania):")

    question_num = 1
    while True:
        question = input(f"Pytanie {question_num}: ")
        if not question:
            break

        questions[f"{question_num:02d}"] = question
        question_num += 1

    return questions

@observe()
def analyze_with_ai(cleaned_html, questions, current_url, session_id):
    # Aktualizujemy kontekst Langfuse o ID sesji
    langfuse_context.update_current_trace(
        session_id=session_id
    )
    
    prompt = f"""
    Przeanalizuj poniższą stronę HTML i odpowiedz na pytania. Dla każdego pytania:
    1. Jeśli znajdziesz odpowiedź - zwróć ją w odpowiednim formacie:
       - tekst jeśli pytanie dotyczy informacji tekstowej
       - link jeśli pytanie prosi o odnośnik do konkretnej strony/zasobu
       - ścieżkę do pliku jeśli pytanie dotyczy konkretnego pliku
       (format odpowiedzi będzie sprecyzowany w treści pytania)
    2. Jeśli nie znajdziesz odpowiedzi - zastanów się dokładnie, który z dostępnych linków może prowadzić do odpowiedzi. Podczas analizy zastanów się nad:
       - tekstem linku (co znajduje się między tagami <a>)
       - atrybutem title jeśli jest dostępny
       - kontekstem w jakim link się pojawia (tekst wokół niego)
       - sekcją strony w której się znajduje
       - linki które mogą być pośrednio związane z odp
    3. Dodatkowo daj streszczenie zawartości strony

    Odpowiedź MUSI być w formacie JSON zgodnym z poniższą strukturą:

    {{
        "summary": "krótkie streszczenie zawartości strony",
        "current_url": "{current_url}",
        "questions": {{
            "01": {{
                "question": "treść pierwszego pytania",
                "answer": "znaleziona odpowiedź lub null jeśli nie znaleziono",
                "suggested_link": "link gdzie może być odpowiedź (jeśli nie znaleziono na obecnej stronie) lub null",
            }},
            // kolejne pytania w tej samej strukturze
        }}
    }}

    Strona do analizy: {cleaned_html}
    
    Pytania: {json.dumps(questions, ensure_ascii=False)}

    PAMIĘTAJ: Zwróć odpowiedź TYLKO w podanym formacie JSON, bez żadnego dodatkowego tekstu.
    """
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system", 
                "content": "Jesteś pomocnym asystentem, który analizuje strony HTML i odpowiada na pytania. ZAWSZE odpowiadasz tylko w formacie JSON, bez żadnego dodatkowego tekstu."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
    )
    
    return json.loads(response.choices[0].message.content)

def check_url_for_questions(url, questions_to_check, base_url, session_id, iteration_data, current_depth=0):
    if iteration_data['count'] >= iteration_data['max']:
        print(f"\nOsiągnięto maksymalną liczbę iteracji ({iteration_data['max']})")
        return {}

    iteration_data['count'] += 1
    print(f"\nIteracja {iteration_data['count']} z {iteration_data['max']}")
    print(f"Sprawdzam URL: {url}")

    html_content = get_page_content(url)
    if not html_content:
        return {}

    cleaned_html = clean_html(html_content)
    result = analyze_with_ai(cleaned_html, questions_to_check, url, session_id)
    print(f"\nWynik analizy:")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # Sprawdzamy każde pytanie, które wciąż nie ma odpowiedzi
    next_questions = {}
    for q_id, q_data in result['questions'].items():
        if q_data['answer'] is None and q_data['suggested_link']:
            next_questions[q_id] = questions_to_check[q_id]
            suggested_link = q_data['suggested_link']
            full_url = base_url.rstrip('/') + suggested_link if suggested_link.startswith('/') else suggested_link
            
            # Rekurencyjnie sprawdzamy sugerowany link
            sub_results = check_url_for_questions(
                full_url, 
                {q_id: questions_to_check[q_id]}, 
                base_url, 
                session_id, 
                iteration_data,
                current_depth + 1
            )
            
            # Aktualizujemy wynik o znalezione odpowiedzi
            if sub_results:
                result['questions'][q_id].update(sub_results.get('questions', {}).get(q_id, {}))

    return result
    
if __name__ == "__main__":
    MAX_ITERATIONS = 10
    iteration_data = {
        'count': 0,
        'max': MAX_ITERATIONS
    }
    
    session_id = str(uuid.uuid4())
    print(f"ID sesji: {session_id}")

    base_url = input("Proszę podać link do strony, którą chcesz przeanalizować: ")

    if not base_url:
        print("Błąd: Nie podano URL")
        exit()

    questions = get_questions_from_user()

    if not questions:
        print("Nie wprowadzono żadnych pytań")
        exit()

    print("\nPodsumowanie wprowadzonych pytań:")
    for num, question in questions.items():
        print(f"{num}: {question}")

    # Rozpoczynamy analizę od głównej strony
    final_results = check_url_for_questions(
        base_url, 
        questions, 
        base_url, 
        session_id, 
        iteration_data
    )
    
    print("\nKońcowe wyniki:")
    print(json.dumps(final_results, ensure_ascii=False, indent=2))