:: Utility creating a Python SFX installer
:: 1) Download "Winpython32-3.9.1.0dot.exe" from https://winpython.github.io/ ~23 MB
:: 2) Extract it to get a file structure like ".\python-3.9.1\python.exe"
:: 3) Run this script
:: 4) Expect ".\python-3.9.1.exe" to appear
:: 5) Upload it
:: 6) The sfx can be extracted like: python-3.9.1.exe -y -oTARGET_DIR

set DIR=python-3.9.1
del /s *.pyc
"C:\Program Files\7-Zip\7z.exe" a "%DIR%.exe" -mmt -mx5 -sfx "%DIR%"
