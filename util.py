# -*- coding: utf-8 -*-
import codecs
import datetime
import errno
import functools
import hashlib
import logging
import os
import random
import shutil
import sys
import time

import requests
from bs4 import Tag
from requests import Response
from typing import Dict, Optional, Pattern, Union

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


LOG_FILE = 'booklead.log'
logging_set_up = False


def _setup_logging():
    time_format = '%Y-%m-%d %H:%M:%S'
    log_formatter = logging.Formatter("%(asctime)s %(levelname)-5.5s %(message)s", time_format)
    log_level = os.getenv('LOGLEVEL', 'INFO')
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    if root_logger.hasHandlers():
        # https://stackoverflow.com/questions/7173033/duplicate-log-output-when-using-python-logging-module
        root_logger.handlers.clear()

    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    if os.getenv('LOGTOCONSOLE', '0') == '1':
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)


def get_logger(name=None):
    if not logging_set_up:
        _setup_logging()
    return logging.getLogger(name)


log = get_logger(__name__)


def perror(msg):
    """печать ошибки на экран, не может быть стёрто"""
    log.error(f'Ошибка отображена пользователю: {msg}')
    sys.stdout.write(f'\rОшибка: {msg}\n')


def ptext(msg):
    """печать обычного сообщения на экран, не может быть стёрто"""
    log.info(f'Сообщение отображено пользователю: {msg}')
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


def to_float(s: str, fallback=0.0):
    try:
        return float(s)
    except ValueError:
        return fallback


def md5_hex(s: str) -> str:
    md5 = hashlib.md5()
    md5.update(s.encode('utf-8'))
    return md5.hexdigest()


def random_pause(target_pause: float):
    return random.uniform(
        target_pause - target_pause * 0.5,
        target_pause + target_pause * 0.5)


def select_one_required(root: Tag, selector: str) -> Tag:
    tag = root.select_one(selector)
    if not tag:
        raise Exception(f'Не найден элемент по пути {selector}')
    return tag


def select_one_text_required(root: Tag, selector: str):
    tag = root.select_one(selector)
    if not tag:
        raise Exception(f'Не найден элемент по пути {selector}')
    text = tag.text.strip()
    if not text:
        raise Exception(f'Не найден text у элемента по пути {selector}')
    return text


def select_one_text_optional(root: Tag, selector: str):
    tag = root.select_one(selector)
    if not tag:
        raise Exception(f'Не найден элемент по пути {selector}')
    text = tag.text if tag else ''
    return text.strip()


def select_one_attr_required(root: Tag, selector: str, attr_name: str):
    tag = root.select_one(selector)
    if not tag:
        raise Exception(f'Не найден элемент по пути {selector}')
    val: str = tag.get(attr_name)
    val = val.strip() if val else val
    if not val:
        raise Exception(f'Не найден аттрибут {attr_name} у элемента по пути {selector}')
    return val


def safe_file_name(title: str, url: str = None):
    # todo implement
    return title


last_time_connected: Optional[datetime.datetime] = None


def pausable(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global last_time_connected
        bro: Browser = args[0]
        if last_time_connected and bro.pause:
            pause = random_pause(bro.pause) - (datetime.datetime.now() - last_time_connected).total_seconds()
        else:
            pause = 0
        if pause > 0:
            log.info(f'Sleeping for {pause} s')
            time.sleep(pause)
        last_time_connected = datetime.datetime.now()
        return func(*args, **kwargs)
    return wrapper


class Browser:

    def __init__(self, pause: float):
        self.pause = pause

    @pausable
    def get_text(self, url: str, headers: Dict = None, content_type: str = None):
        headers = self._prepare_headers(headers)
        log.info(f'Requesting GET {url}, headers: {headers}')
        response = requests.get(url, headers=headers)
        log.info(f'Response: {response.status_code} {response.reason}')
        log.info(f'Headers: {response.headers}')
        self._validate_response(response, url, content_type)
        return response.text

    @pausable
    def download(self, url: str,
                 fpath: str,
                 headers: Dict = None,
                 content_type: Union[str, Pattern] = None,
                 skip_if_file_exists=False):
        global last_time_connected
        progress(f' - Скачиваю {url}')
        if skip_if_file_exists and os.path.exists(fpath) and os.stat(fpath).st_size > 0:
            log.info(f'Пропускаем уже скачанный файл: {fpath}')
            last_time_connected = None
            return
        headers = self._prepare_headers(headers)
        log.info(f'Requesting GET {url}, headers: {headers}')
        response = requests.get(url, stream=True, headers=headers)
        log.info(f'Response: {response.status_code} {response.reason}')
        log.info(f'Headers: {response.headers}')
        self._validate_response(response, url, content_type)
        mkdirs_for_regular_file(fpath)
        with open(fpath, 'wb') as fd:
            shutil.copyfileobj(response.raw, fd)
        length = os.stat(fpath).st_size
        ptext(f' - Сохранено в файл {fpath} ({length} байт)')

    def _prepare_headers(self, additional_headers: Dict):
        headers = additional_headers if additional_headers else {}
        headers.update({'User-Agent': random.choice(user_agents)})
        return headers

    def _validate_response(self, response: Response, url, expected_ct: Union[str, Pattern]):
        if not response.ok:
            raise Exception(f'Не удалось скачать файл {url} - {response.status_code} {response.reason}')
        if expected_ct:
            actual_ct: str = response.headers.get('content-type')
            if actual_ct:
                if isinstance(expected_ct, Pattern):
                    if not expected_ct.match(actual_ct):
                        perror(f'Некорректный content-type {actual_ct} по адресу {url}')
                else:
                    if actual_ct != expected_ct:
                        perror(f'Некорректный content-type {actual_ct} по адресу {url}')
