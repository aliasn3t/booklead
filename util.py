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


def md5_hex(s: str):
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


def download_to_file(url: str, fpath: str, headers: dict):
    progress(f'Скачиваю {url}')
    response = requests.get(url, stream=True, headers=headers)
    if not response.ok:
        raise Exception(f'Ошибка: не удалось скачать файл {url} - {response.status_code} {response.reason}')
    mkdirs_for_regular_file(fpath)
    with open(fpath, 'wb') as fd:
        shutil.copyfileobj(response.raw, fd)
    length = os.stat(fpath).st_size
    ptext(f'Сохранено в файл {fpath} ({length} байт)')
