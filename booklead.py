# -*- coding: utf-8 -*-

import sys
import requests
import random
import argparse
import urllib.parse
from bs4 import BeautifulSoup
import json
import shutil
from pathlib import Path
import os
import img2pdf
import uuid 

domains = {
    'elib.shpl.ru': 'eshplDl',
    'docs.historyrussia.org': 'eshplDl',
    'prlib.ru': 'prlDl',
    'www.prlib.ru': 'prlDl'
    }

eshplDl_params = {
    'quality': 8,
    'ext': 'jpg'
    }

prlDl_params = {
    'ext': 'jpg'
}

user_agents = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.78 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',
    'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0'
    ]

def initLoader(url):
    host = urllib.parse.urlsplit(url)
    try:
        return eval(domains[host.hostname]+'(url)')
    except Exception:
        return False

def makePdf(folder, ext):
    pdf_path = '{}.pdf'.format(folder)
    with open(pdf_path, "wb") as pdf_file:
        img_list = []
        for r, _, f in os.walk(folder):
            for fname in f:
                if not fname.endswith(ext):
                    continue
                img_list.append(os.path.join(r, fname))
        pdf = img2pdf.convert(img_list)
        pdf_file.write(pdf)

def makeFolder(folder):
    Path(folder).mkdir(exist_ok=True)

def saveImage(url, img_id, folder, ext):
    makeFolder(folder)

    headers = {
        'User-Agent': random.choice(user_agents)
        }

    response = requests.get(url, stream=True, headers=headers)
    image_path = '{}/{}.{}'.format(folder, str(img_id), ext)

    if response.ok:
        with open(image_path, 'wb') as page_file:
            shutil.copyfileobj(response.raw, page_file)

def main(args):
    urls = []
    
    try:
        if args.url:
            urls.append(args.url)
        if args.list:
            with open(args.list) as fp:
                line = fp.readline()
                while line:
                    urls.append(line.strip())
                    line = fp.readline()

        sys.stdout.write('Ссылок для загрузки - {}'.format(len(urls)))

        for url in urls:
            load = initLoader(url)
            if not load:
                sys.stdout.write('\nСсылка: {}\n - Ошибка загрузки!'.format(url))
            elif args.pdf.lower() == 'y': 
                sys.stdout.write('\n ─ Создание PDF...')
                imgs_folder, imgs_ext = load
                makePdf(imgs_folder, imgs_ext)
    except KeyboardInterrupt:
        sys.stdout.write('\nЗагрузка прервана!')

def eshplDl(url):
    ext = eshplDl_params['ext']
    book_id = str(uuid.uuid4()).upper()
    domain = urllib.parse.urlsplit(url).netloc
    quality = eshplDl_params['quality']

    # Обход 429 Too Many Requests 
    headers = {
        'User-Agent': random.choice(user_agents)
        }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    for script in soup.findAll('script'):
        if 'initDocview' in str(script):
            st = str(script)
            book_json = json.loads(st[st.find('{"') : st.find(')')])
    try:
        sys.stdout.write('\nCсылка: {}\n'.format(url))
        sys.stdout.write(' ─ Каталог для загрузки: {}\n'.format(book_id))
        for idx, page in enumerate(book_json['pages']):
            page_url = 'http://{}/pages/{}/zooms/{}'.format(domain, page['id'], quality)
            saveImage(page_url, idx + 1, book_id, ext)
            sys.stdout.write('\r ─ Прогресс: {} из {} стр.'.format(idx + 1, len(book_json['pages'])))
        return (book_id, ext)
    except Exception as e:
        sys.stdout.write(e)

def prlDl(url):
    ext = prlDl_params['ext']

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for script in soup.findAll('script'):
        if 'jQuery.extend' in str(script):
            st = str(script)
            book_json = json.loads(st[st.find('{"') : st.find(');')])
            book = book_json['diva']['1']['options']
    response = requests.get(book['objectData'])
    try:
        book_data = json.loads(response.text)
        sys.stdout.write('\nCсылка: {}\n'.format(url))
        sys.stdout.write(' ─ Каталог для загрузки: {}\n'.format(book_data['item_title']))
        for idx, page in enumerate(book_data['pgs']):
            page_url = 'https://content.prlib.ru/fcgi-bin/iipsrv.fcgi?FIF={}/{}&WID={}&CVT=jpeg'.format(book['imageDir'], page['f'], page['d'][len(page['d'])-1]['w'])
            saveImage(page_url, idx + 1, book_data['item_title'], ext)
            sys.stdout.write('\r ─ Прогресс: {} из {} стр.'.format(idx + 1, len(book_data['pgs'])))
        return (book_data['item_title'], ext)
    except Exception as e:
        sys.stdout.write(e)
        


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='booklead - Загрузчик книг из интернет-библиотек')
    parser.add_argument('--pdf', dest='pdf', default='', metavar='"Y"', help='Создавать PDF-версии книг')
    parser.add_argument('--list', dest='list', default='', metavar='"list.txt"', help='Файл со списком книг')
    parser.add_argument('--url', dest='url', default='', metavar='"http://..."', help='Ссылка на книгу')
    args = parser.parse_args()
    main(args)
