# web_fuzz_with_radamsa

Создать корпус из xml бурпа:
```
usage: burp_xml_to_corpus.py [-h] -x XML -c CORPUS

optional arguments:
  -h, --help  show this help message and exit
  -x XML      path to xml
  -c CORPUS   path to corpus dir
 ```
 
 Запуск фаззера:
 ```
 usage: fuzzer.py [-h] -u URL -c CORPUS [--proxy PROXY] [--mutates MUTATES] [--regexp REGEXP]

Black-box fuzzing with radamsa

optional arguments:
  -h, --help         show this help message and exit
  -u URL             destination ip fuzzing for
  -c CORPUS          path to directory to corpus, which include folders POST and GET
  --proxy PROXY      proxy like http://127.0.0.1:8080 if necessary
  --mutates MUTATES  mutate count
  --regexp REGEXP    path to file with regexp for sub
 ```
