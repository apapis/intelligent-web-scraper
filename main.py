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

if __name__ == "__main__":

    url = input("Proszę podać link do strony, którą chcesz przeanalizować: ")

    if not url:
        print("Błąd: Nie podano URL")
        exit()

    html_content = get_page_content(url)

    if html_content:
        cleaned_html = clean_html(html_content)
        print("Wyczyszczony HTML:")
        print(cleaned_html)


