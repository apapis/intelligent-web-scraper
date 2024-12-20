import requests
from bs4 import BeautifulSoup, Comment
from dotenv import load_dotenv
import os

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

if __name__ == "__main__":

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


