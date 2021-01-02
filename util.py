# -*- coding: utf-8 -*-
import codecs
import errno
import hashlib
import os
import random
import shutil
import sys

import requests
from bs4 import Tag
from requests import Response
from typing import Dict

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


def perror(msg):
    """печать ошибки на экран, не может быть стёрто"""
    sys.stdout.write(f'\rОшибка: {msg}\n')


def ptext(msg):
    """печать обычного сообщения на экран, не может быть стёрто"""
    sys.stdout.write(f'\r{msg}\n')


def progress(msg):
    """печать строки прогресса, стирает текущую строку"""
    sys.stdout.write(f'\r{msg}')


def mkdirs_for_regular_file(filename: str):
    """Создаёт все необходимые директории чтобы можно было записать указанный файл"""
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
        except OSError as e:  # Guard against race condition
            if e.errno != errno.EEXIST:
                raise


def cut_bom(s: str):
    bom = codecs.BOM_UTF8.decode("utf-8")
    return s[len(bom):] if s.startswith(bom) else s


def to_float(s: str, def_val=0.0):
    try:
        return float(s)
    except ValueError:
        return def_val


def md5_hex(s: str) -> str:
    md5 = hashlib.md5()
    md5.update(s.encode('utf-8'))
    return md5.hexdigest()


def random_pause(target_pause: float):
    return random.uniform(
        target_pause - target_pause * 0.5,
        target_pause + target_pause * 0.5
    )


def select_one_text_required(root: Tag, selector: str):
    tag = root.select_one(selector)
    if not tag:
        raise Exception(f'Не найден элемент по пути {selector}')
    text = tag.text.strip()
    if not text:
        raise Exception(f'Не найден text у элемента по пути {selector}')
    return text


def select_one_attr_required(root: Tag, selector: str, attr_name: str):
    tag = root.select_one(selector)
    if not tag:
        raise Exception(f'Не найден элемент по пути {selector}')
    val: str = tag.get(attr_name)
    val = val.strip() if val else val
    if not val:
        raise Exception(f'Не найден аттрибут {attr_name} у элемента по пути {selector}')
    return val


def safe_file_name(title: str, url: str):
    # todo implement
    return title


class Browser:
    def get_text(self, url: str, headers: Dict = None, content_type: str = None):
        headers = self._prepare_headers(headers)
        response = requests.get(url, headers=headers)
        self._validate_response(response, url, content_type)
        return response.text

    def download(self, url, fpath, headers: Dict = None, content_type: str = None):
        headers = self._prepare_headers(headers)
        progress(f'Скачиваю {url}')
        response = requests.get(url, stream=True, headers=headers)
        self._validate_response(response, url, None)
        mkdirs_for_regular_file(fpath)
        with open(fpath, 'wb') as fd:
            shutil.copyfileobj(response.raw, fd)
        length = os.stat(fpath).st_size
        ptext(f'Сохранено в файл {fpath} ({length} байт)')

    def _prepare_headers(self, additional_headers: Dict):
        headers = additional_headers if additional_headers else {}
        headers.update({'User-Agent': random.choice(user_agents)})
        return headers

    def _validate_response(self, response: Response, url, expected_ct):
        if not response.ok:
            raise Exception(f'Не удалось скачать файл {url} - {response.status_code} {response.reason}')
        if expected_ct:
            actual_ct: str = response.headers.get('content-type')
            if actual_ct:
                if actual_ct != expected_ct:
                    perror(f'Некорректный content-type {actual_ct} по адресу {url}')
