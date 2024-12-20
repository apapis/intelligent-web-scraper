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
    
if __name__ == "__main__":

    session_id = str(uuid.uuid4())
    print(f"ID sesji: {session_id}")

    url = input("Proszę podać link do strony, którą chcesz przeanalizować: ")

    if not url:
        print("Błąd: Nie podano URL")
        exit()

    questions = get_questions_from_user()

    if not questions:
        print("Nie wprowadzono żadnych pytań")
        exit()

    print("\nPodsumowanie wprowadzonych pytań:")
    for num, question in questions.items():
        print(f"{num}: {question}")

    html_content = get_page_content(url)

    if html_content:
        cleaned_html = clean_html(html_content)
        print("Wyczyszczony HTML:")
        print(cleaned_html)

    result = analyze_with_ai(cleaned_html, questions, url, session_id)

    print(result)
