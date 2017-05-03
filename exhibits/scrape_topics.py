from builtins import input
from builtins import str
from bs4 import BeautifulSoup
from exhibits.models import Exhibit, NotesItem, ExhibitItem
from django.utils.text import slugify
import re

# GET CONTEXTUAL ESSAY
def getEssay(soup, topic):
    topic_content = soup.find('h2')
    user_input = ''
    essay_text = ''

    while user_input != 'stop':
        user_input = eval(input(topic_content))
        if user_input == 's':
            topic_content = topic_content.find_next('h2')
        elif user_input == 'n':
            topic_content = topic_content.find_next()
        elif user_input == 'y':
            if topic_content.name == 'h2':
                topic_content.name = 'h3'
            elif topic_content.name == 'h3':
                topic_content.name = 'h4'
            elif topic_content.name == 'h5':
                topic.content.name = 'h6'
            elif topic_content.name == 'h6':
                topic_content.name = 'b'
            essay_text = essay_text + str(topic_content)
            topic_content = topic_content.find_next()
        else: 
            user_input = eval(input('whoops, try again'))

    e = Exhibit(title=soup.h1.string, slug=slugify(soup.h1.string), essay=essay_text, scraped_from=topic)
    e.save()
    return e

# GET SIDEBAR ITEMS
def getSidebar(soup, e):
    topic_sidebar = soup.find_all('div', class_='secondary-text')
    for s in topic_sidebar:
       sidebar_content = ""
       for c in s.contents:
         if c.name != 'h1':
           sidebar_content = sidebar_content + str(c.string)
       note = NotesItem(title=s.h1.text, essay=sidebar_content, exhibit_id=e.id)
       note.save()

# GET EXHIBIT ITEMS
def getItems(soup, e):
    topic_items = soup.find_all('a', href=re.compile('ark'))

    for item in topic_items:
        if item.get('href')[-1] == '/':
            item_id = item.get('href')[1:-1]
        else:
            item_id = item.get('href')[1::]
        exhibit_item = ExhibitItem(item_id = item_id, exhibit=e)
        exhibit_item.save()

def scrapeTopic(filename):
    topic = "calisphere1/jarda/browse/" + filename
    # topic = "calisphere1/calcultures/ethnic_groups/" + filename
    # topic = "calisphere1/themed_collections/" + filename
    soup = BeautifulSoup(open(topic))
    exhibit = getEssay(soup, topic)
    getSidebar(soup, exhibit)
    getItems(soup, exhibit)