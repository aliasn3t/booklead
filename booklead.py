# -*- coding: utf-8 -*-
import argparse
import json
import os
import random
import shutil
import time
import urllib.parse

import img2pdf
import requests
from bs4 import BeautifulSoup

from util import select_one_text_required, select_one_attr_required, random_pause, \
    mkdirs_for_regular_file, md5_hex, to_float, cut_bom, perror, progress, ptext, safe_file_name, Browser, user_agents

DOWNLOADS_DIR = 'books'

timeout_btw_requests = 0
downloaded_last_time = False

eshplDl_params = {
    'quality': 8,
    'ext': 'jpg'
}

prlDl_params = {
    'ext': 'jpg'
}

bro = Browser()


def makePdf(pdf_path, img_folder, img_ext):
    img_list = []
    for r, _, ff in os.walk(img_folder):
        for fname in ff:
            if fname.endswith(f'.{img_ext}'):
                img_list.append(os.path.join(r, fname))
    img_list.sort()
    pdf = img2pdf.convert(img_list)
    with open(pdf_path, "wb") as fd:
        fd.write(pdf)


def saveImage(url, img_id, folder, ext):
    global downloaded_last_time, timeout_btw_requests

    image_short = '%05d.%s' % (img_id, ext)
    image_path = os.path.join(DOWNLOADS_DIR, folder, image_short)

    if os.path.exists(image_path) and os.stat(image_path).st_size > 0:
        downloaded_last_time = False
        return False

    if downloaded_last_time and timeout_btw_requests:
        time.sleep(random_pause(timeout_btw_requests))

    downloaded_last_time = True  # перед попыткой скачивания чтобы не нафлудить в случае массовых ошибок
    headers = {
        'User-Agent': random.choice(user_agents),
        'Referer': url,
    }
    response = requests.get(url, stream=True, headers=headers)
    if response.ok:
        content_type: str = response.headers.get('content-type')
        if content_type and not content_type.lower().startswith('image/'):
            perror(f'кажется, то что скачалось с адреса {url} не является изображением: {content_type}')
        mkdirs_for_regular_file(image_path)
        with open(image_path, 'wb') as page_file:
            shutil.copyfileobj(response.raw, page_file)
    else:
        perror(f'не удалось скачать файл {url} - ошибка {response.status_code} {response.reason}')
    return True


def eshplDl(url):
    ext = eshplDl_params['ext']
    book_id = md5_hex(url).upper()
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
            book_json = json.loads(st[st.find('{"'): st.find(')')])
    ptext(f' ─ Каталог для загрузки: {book_id}')
    for idx, page in enumerate(book_json['pages']):
        page_url = 'http://{}/pages/{}/zooms/{}'.format(domain, page['id'], quality)
        saveImage(page_url, idx + 1, book_id, ext)
        progress(' ─ Прогресс: {} из {} стр.'.format(idx + 1, len(book_json['pages'])))
    return book_id, ext


def prlDl(url):
    ext = prlDl_params['ext']

    headers = {
        'User-Agent': random.choice(user_agents)
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    for script in soup.findAll('script'):
        if 'jQuery.extend' in str(script):
            st = str(script)
            book_json = json.loads(st[st.find('{"'): st.find(');')])
            book = book_json['diva']['1']['options']
    response = requests.get(book['objectData'], headers=headers)
    book_data = json.loads(response.text)
    ptext(' ─ Каталог для загрузки: {book_data["item_title"]}')
    book_title = safe_file_name(book_data['item_title'], url)
    for idx, page in enumerate(book_data['pgs']):
        page_url = 'https://content.prlib.ru/fcgi-bin/iipsrv.fcgi?FIF={}/{}&WID={}&CVT=jpeg'.format(
            book['imageDir'], page['f'], page['d'][len(page['d']) - 1]['w'])
        saveImage(page_url, idx + 1, book_title, ext)
        progress(' ─ Прогресс: {} из {} стр.'.format(idx + 1, len(book_data['pgs'])))
    return book_title, ext


def unatlib_download(url):
    """
    Национальная электронная библиотека Удмуртской республики
    Формат - PDF
    Пример урла книги (HTML) - https://elibrary.unatlib.ru/handle/123456789/18116
    Пример урла книги (PDF) - https://elibrary.unatlib.ru/bitstream/handle/123456789/18116/uiiyl_book_075.pdf
    Реферером должен быть https://elibrary.unatlib.ru/build/pdf.worker.js
    """
    html_text = bro.get_text(url)
    soup = BeautifulSoup(html_text, 'html.parser')
    title = select_one_text_required(soup, 'title')
    title = safe_file_name(title, url)
    pdf_href = select_one_attr_required(soup, '#dsview', 'href')
    pdf_url = f'https://elibrary.unatlib.ru{pdf_href}'
    headers = {'Referer': 'https://elibrary.unatlib.ru/build/pdf.worker.js'}
    pdf_file = os.path.join(DOWNLOADS_DIR, f'{title}.pdf')
    bro.download(pdf_url, pdf_file, headers)
    return None  # all done, no further action needed


domains = {
    'elib.shpl.ru': eshplDl,
    'docs.historyrussia.org': eshplDl,
    'prlib.ru': prlDl,
    'www.prlib.ru': prlDl,
    'elibrary.unatlib.ru': unatlib_download,
}


def download_book(url):
    try:
        host = urllib.parse.urlsplit(url)
        if not host.hostname:
            perror(f'Некорректный урл: {url}')
            return None
        site_downloader = domains.get(host.hostname)
        if not site_downloader:
            perror(f'Домен {host.hostname} не поддерживается')
            return None
        ptext(f'Cсылка: {url}')
        return site_downloader(url)
    except Exception as e:
        perror(e)
        return None


def collect_urls():
    urls = []
    if args.url:
        urls.append(args.url)
    if args.list:
        with open(args.list) as fp:
            urls.extend([line.strip() for line in fp])
    return list(filter(bool, map(lambda x: cut_bom(x).strip(), urls)))


def main():
    try:
        urls = collect_urls()
        ptext(f'Ссылок для загрузки: {len(urls)}')
        if args.timeout:
            global timeout_btw_requests
            timeout_btw_requests = to_float(args.timeout)
        for url in urls:
            load = download_book(url)
            if load and args.pdf.lower() in ['y', 'yes']:
                progress(' ─ Создание PDF...')
                title, img_ext = load
                img_folder_full = os.path.join(DOWNLOADS_DIR, title)
                pdf_path = os.path.join(DOWNLOADS_DIR, f'{title}.pdf')
                makePdf(pdf_path, img_folder_full, img_ext)
                ptext(f' - Файл сохранён: {pdf_path}')
    except KeyboardInterrupt:
        perror('Загрузка прервана')
    except Exception as e:
        perror(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='booklead - Загрузчик книг из интернет-библиотек')
    parser.add_argument('--pdf', dest='pdf', default='', metavar='y', help='Создавать PDF-версии книг')
    parser.add_argument('--list', dest='list', default='', metavar='"list.txt"', help='Файл со списком книг')
    parser.add_argument('--url', dest='url', default='', metavar='"http://..."', help='Ссылка на книгу')
    parser.add_argument('--timeout', dest='timeout', default='0', metavar='1.0',
                        help='Пауза между HTTP-запросами в секундах')
    args = parser.parse_args()
    if args.url or args.list:
        main()
    else:
        parser.print_help()
