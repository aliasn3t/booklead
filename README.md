# booklead
Утилита для загрузки книг из интернет-библиотек

## Поддерживаемые ресурсы:

* elib.shpl.ru - электронная библиотека ГПИБ
* docs.historyrussia.org - электронная библиотека исторических документов
* prlib.ru - президентская библиотека имени Б.Н. Ельцина
* elibrary.unatlib.ru - национальная электронная библиотека Удмуртской республики
* gwar.mil.ru - информационный портал о первой мировой войне 1914-1918

## Запуск

Для **Windows** доступны бинарные сборки в разделе [Releases](https://github.com/aliasn3t/booklead/releases)  
Для запуска кода потребуется Python с модулями **img2pdf**, **requests** и **beautifulsoup4**  
Установка модулей: `python3 -m pip install -r requirements.txt`  

## Использование

`--list` загрузка книг по ссылкам из файла  
Пример использования: `booklead --list books.txt`  
Пример содержимого **books.txt**:  
```
https://www.prlib.ru/item/420931
http://docs.historyrussia.org/ru/nodes/139435
...
http://elib.shpl.ru/ru/nodes/16533-vyp-1-zhilischnoe-stroitelstvo-v-gorodskih-poseleniyah-rsfsr-ukrainskoy-ssr-i-belorusskoy-ssr-1927
```
`--url` загрузка одной книги по ссылке  
Пример использования: `booklead --url https://www.prlib.ru/item/420931`  
`--pdf` создание PDF-версий загружаемых книг  
Пример использования: `booklead --list books.txt --pdf y`  
