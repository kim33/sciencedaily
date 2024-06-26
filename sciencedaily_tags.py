import requests as req
from bs4 import BeautifulSoup
import json
import certifi
import urllib3
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor, as_completed

#send request for each url
def get_soup(url):
    res = req.get(url, headers=headers)
    res.raise_for_status()
    return BeautifulSoup(res.text, 'html.parser')

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

#get metadata of each article
def get_article_data(article_url):
  final_article = {}
  full_article_url = f"{base_url}{article_url}"
  article_soup = get_soup(full_article_url)

  title_tag = article_soup.find('title').text
  final_article['title'] = title_tag

  summary_tag = article_soup.find('meta', attrs={'name':'description'}).get('content', ' ')
  final_article['summary'] = summary_tag

  keywords_tag = article_soup.find('meta', attrs={'name':'keywords'}).get('content', ' ')
  final_article['keywords'] = keywords_tag

  url_tag = article_soup.find('meta', attrs={'property':'og:url'}).get('content', ' ')
  final_article['url'] = url_tag

  ref = article_soup.find('div', {"id": "story_text"})
  if ref :
    paragraph = ref.find_all('p')
    final_article['fullstory'] = ' '.join([p.get_text(strip=True) for p in paragraph])
  else :
    final_article['fullstory'] = "None"

  return final_article

# iterate each categories and extract data for each article in a single category.
# append the new data from the article to the final_article array
def get_articles_in_category(single_cat):
  single_category_url = f"{base_url}{single_cat}"
  articles_in_single_category = req.get(single_category_url, headers = headers)
  single_soup = get_soup(single_category_url)

  #sets of articles under each category
  set_articles = single_soup.find_all('div', class_='latest-head')
  article_urls = [article.find('a')['href'] for article in set_articles]

  #to process concurrently to reduce process time for entire categories
  with ThreadPoolExecutor(max_workers=10) as executor:
    results = [executor.submit(get_article_data, url) for url in article_urls]
    for result in as_completed(results):
        article_data = result.result()
        if article_data:
            all_info.append(article_data)


#dictionary to save the final data
all_info = []

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6287.195 Safari/537.36",
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'application/json',
    'Referer': 'https://www.google.com/'
}

base_url = 'https://www.sciencedaily.com'
soup = get_soup(base_url)
#take all categories from the website
all_category = get_category_url()

#for each category, gather information
for category in all_category:
  get_articles_in_category(category)

#export final_article array into json format
with open('articles.json', 'w', encoding='utf-8') as f:
  json.dump(all_info, f, indent = 4, ensure_ascii=False)

