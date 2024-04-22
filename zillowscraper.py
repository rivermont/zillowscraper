#!/usr/bin/env python3

from time import gmtime, strftime, sleep
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import requests
import json


def get_urls(text):
    """
    Returns a list of valid URLs found in text.
    Uses BeautifulSoup to find all links in html <a> tags.
    """
    return [i['href'] for i in BeautifulSoup(text, 'lxml').find_all('a', href=True)]


def filter_urls(urls):
    """
    Returns two lists, one of individual listings and one of additional pages of listings.
    """
    return [i for i in urls if '/homedetails/' in i], ['https://www.zillow.com' + i for i in urls if i[-3:] == '_p/']


def crawl_result(url, user_agent):
    headers = {'user-agent': user_agent}

    response = requests.get(url, headers=headers)
    text = response.text

    out_urls = get_urls(text)

    return filter_urls(out_urls)


def crawl_listing(url, user_agent, referer=''):
    headers = {'user-agent': user_agent,
               'referer': referer}

    response = requests.get(url, headers=headers)
    text = response.text

    out_urls = get_urls(text)

    out_data = {'url': url,
                'crawl-time': strftime('%Y-%m-%d %H:%M:%S', gmtime()),
                'response-headers': dict(response.headers),
                'response-code': response.status_code,
                'urls': out_urls
                }

    soup = BeautifulSoup(text, 'lxml')

    # extract variables
    try:
        footage = soup.findAll('div', {'data-testid': 'bed-bath-sqft-fact-container'})[-1].text
    except AttributeError as e:
        print(e)
        footage = None
        # footage = soup.select('.summary-container > div > div > div > span > span')[-1].text

    try:
        addr = soup.find('div', {'data-testid': 'home-details-chip-container'}).find('h1').text
    except AttributeError as e:
        print(e)
        addr = None
        # addr = soup.select_one('.summary-container > div > div > div > h1').text

    out_data.update({'sq_footage': footage,
                     'address': addr
                     })

    return out_data


def main(url_list, user_agent):
    listings = set()
    done = set()

    while url_list:  # crawl listing results
        sleep(1)  # crawl delay

        url = url_list.pop()
        done.add(url)

        print(f'Crawling reults page: {url}')

        out_listings, out_results = crawl_result(url, user_agent)

        listings.update(out_listings)

        # TODO: add additional listing results pages to crawl list
        # for i in out_results:
        #     if i not in done:  # TODO: this does not work for some reason
        #         print(i)
        #         url_list.append(i)

    data = []

    while listings:
        sleep(1)  # crawl delay

        url = listings.pop()

        print(f'Crawling listing {url}')

        parsed_url = urlparse(url)

        if not parsed_url.netloc: continue  # ignore weird/relative URLs

        data.append(crawl_listing(url, user_agent, parsed_url.netloc))

    return data


if __name__ == '__main__':
    init_urls = ['https://www.zillow.com/watauga-county-nc']
    init_ua = 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0'

    results = main(init_urls, init_ua)

    with open('results.json', 'w+') as f:
        f.write(json.dumps(results))
