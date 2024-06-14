import requests as req
from bs4 import BeautifulSoup
import json
import certifi
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed

final_article = []
#send request for each url
def get_soup(url):
    res = req.get(url, headers=headers)
    res.raise_for_status()
    return BeautifulSoup(res.text, 'html.parser')

def clean_text(text) :
	return text.strip()

#get the list of category url on sciencedaily.com
def get_category_url():
  url_list = []
  all_menu = soup.find_all('a', {"role" : "menuitem"})
  for menu in all_menu :
    cat_url = menu.get('href')
    if cat_url not in url_list:
      url_list.append(cat_url)
  return url_list


#function to retrieve doi reference for each article.
#if it does not have reference, return "None"
def find_doi(ref_soup):
  ref = ref_soup.find('div', {"id" : "journal_references"})
  if ref != None :
    return ref.find('a')['href']
  return "None"

def find_fullstory(ref_soup):
  full_text = ""
  ref = ref_soup.find('div',{"id":'story_text'})
  if ref :
    paragraph = ref.find_all('p')
    for p in paragraph :
      full_text += p.text
    return full_text
  return "None"

def get_article_data(article_url):
  full_article_url = f"{base_url}{article_url}"
  article_soup = get_soup(full_article_url)

  title = article_soup.find(class_= 'headline').get_text(strip=True)
  date =  article_soup.find('dd', {"id" :'date_posted'}).get_text(strip=True)
  source = article_soup.find('dd', {"id" : "source"}).get_text()
  abstract = article_soup.find('dd', {"id" : "abstract"}).get_text(strip=True)
  category = article_soup.find('ul', {"id" : "related_topics"}).find('a').get_text(strip=True)
  keywords = article_soup.find('ul', {"id" : "related_terms"}).get_text(strip=True, separator=', ')
  story_text = find_fullstory(article_soup)
  reference = find_doi(article_soup)

  return ({
      'url' : full_article_url,
      'title' : title,
      'date' : date,
      'source' : source,
      'summary' : abstract,
      'category' : category,
      'full story' : story_text,
      'reference' : reference
  })


# iterate each categories and extract data for each article in a single category.
# append the new data from the article to the final_article array
def get_articles_in_category(single_cat):
  single_category_url = f"{base_url}{single_cat}"
  articles_in_single_category = req.get(single_category_url, headers = headers)
  single_soup = BeautifulSoup(articles_in_single_category.text, 'html.parser')

  #sets of articles under each category
  set_articles = single_soup.find_all('div', class_='latest-head')
  article_urls = [article.find('a')['href'] for article in set_articles]

  with ThreadPoolExecutor(max_workers=10) as executor:
        results = [executor.submit(get_article_data, url) for url in article_urls]
        for result in as_completed(results):
            article_data = result.result()
            if article_data:
                final_article.append(article_data)

  #retrieve information of each article in the set and append it to final_article array


#meta_data = {}


headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6287.195 Safari/537.36",
           'Accept-Language': 'en-US,en;q=0.9',
           'Accept': 'application/json',
           'Referer': 'https://www.google.com/'}
base_url = 'https://www.sciencedaily.com'
soup = get_soup(base_url)

#get_articles_in_category("/news/health_medicine/")
#set of all categories
all_category = get_category_url()
for category in all_category:
  get_articles_in_category(category)

#export final_article array into json format
with open('articles.json', 'w', encoding='utf-8') as f:
  json.dump(final_article, f, indent = 4, ensure_ascii='False')

