import argparse
import requests
import pyradamsa
import re
import os

from urllib.parse import quote_plus

hashes = []
METHODS = ['GET', 'POST']

header_form = {"Content-type": "application/x-www-form-urlencoded", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}
header_json = {"Content-type": "application/json-rpc", "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0",
"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"}
header_get = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"}
n = 100


class bcolors:
    # TODO: просто для красоты
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Fuzz_request(object):
    # TODO: класс запроса. Хранит в себе сам запрос, параметры, умеет мутировать, слать уникальное на прокси и выводить на кончоль
    
    def __init__(self, url, method, file, iteration, proxy=None, rules=None):
        """Constructor"""
        self.iteration = iteration
        self.rad = pyradamsa.Radamsa()
        self.method = method
        self.header = header_get
        self.proxy = proxy
        self.rules = rules
        self.response = None
        with open(file, 'rb') as f:
            pr = f.read()
            self.url = url + pr.split()[0].decode()
            self.param = pr[len(self.url) + 1:]
        self.request = requests.Request(self.method, self.url, data=self.param, headers=self.header)


    def make_it_color(self, color, text):
        # TODO: просто расскрашивает текст
        return color + text + bcolors.ENDC


    def update_hashes(self, text):
        self.print_uniq_answ()
        hashes.append(hash(text))


    def sub_matches(self):
        text = self.response.text
        for i in self.rules:
            text = i.sub('', text)
        return text

    
    def print_uniq_answ(self):
        color = bcolors.HEADER
        resp_code = str(self.response.status_code)
        if resp_code[0] == '2':
            color = bcolors.OKGREEN
        elif resp_code[0] == '3':
            color = bcolors.OKCYAN
        elif resp_code[0] == '4':
            color = bcolors.WARNING
        elif resp_code[0] == '5':
            color = bcolors.FAIL
        self.print_iter(self.make_it_color(color, ' NEW'))
        st = "answer length: {}".format(len(self.response.content))
        print(st)
        print('-'*n)
        print( ' ' + self.make_it_color(color, self.method + '  ' + resp_code + '  ' + self.url), '\n')
        print(self.param)
        print('='*n)


    def print_iter(self, text = ' PULSE'):
        st = "{}\titeration: {}".format(text, self.iteration)
        print(st)
        print('='*n)


    def send_request(self):
        s = requests.Session()
        self.mutate()
        self.iteration += 1

        if self.method == 'GET':
            self.request.data = None
            self.request.url = self.url + '?' + quote_plus(self.param)
        if self.method == 'POST':
            self.request.data = self.param

        prepped = self.request.prepare()
        self.response = s.send(prepped, verify=False)
        if hash(self.sub_matches()) not in hashes:
            s.send(prepped, verify=False, proxies=self.proxy)
            self.update_hashes(self.sub_matches())
        if self.iteration % 1000 == 0:
            self.print_iter()
     

    def mutate(self):
        self.param = self.rad.fuzz(self.param)
        if self.method == 'POST':
            if b'{' in self.param and b'}' in self.param:
                self.header = header_json
            else:
                self.header = header_form


def get_mutate_count(corpus_path, mutates):
    # TODO: считает кол-во мутаций исходя из необходимости получить 100_000 уникальных запросов
    corpus_path_POST = os.path.join(corpus_path, 'POST')
    corpus_path_GET = os.path.join(corpus_path, 'GET')

    POST_reqs = [name for name in os.listdir(corpus_path_POST) if os.path.isfile(os.path.join(corpus_path_POST, name))]
    GET_reqs = [name for name in os.listdir(corpus_path_GET) if os.path.isfile(os.path.join(corpus_path_GET, name))]
    if mutates is None:
        mutate_count = 100_000 // (len(POST_reqs) + len(GET_reqs))
        mutate_count = round(mutate_count * 2, -2) // 2 + 50
        return (mutate_count, POST_reqs, GET_reqs)
    return (mutates, POST_reqs, GET_reqs)


def parse_params():
    parser = argparse.ArgumentParser(description='Black-box fuzzing via radamsa')
    parser.add_argument('-u', dest="url", help='destination ip fuzzing for', required=True)
    parser.add_argument('-c', dest="corpus", help='path to directory to corpus, which include folders POST and GET', required=True)
    parser.add_argument('--proxy', dest="proxy", default=None, help='proxy like http://127.0.0.1:8080 if necessary')
    parser.add_argument('--mutates', type=int, dest="mutates", default=None, help='mutate count')
    parser.add_argument('--regexp', dest="regexp", default=None, help='path to file with regexp for sub')
    return parser.parse_args()


def prep_rules(rules_path):
    # TODO: обрабатывает регулярки в файле и готовит их для дальнейшего использования
    ready_rules = []
    with open(rules_path) as f:
        rules = f.read().split()
        for i in rules:
            ready_rules.append(re.compile(i))
    return ready_rules


def fuzz_it(params, mutate_count, proxies):
    # TODO: собсна процесс фаззинга
    corpus_path_POST = mutate_count[1]
    corpus_path_GET = mutate_count[2]
    regexps = prep_rules(params.regexp)
    iteration = 0
    for name in corpus_path_POST:
        req = Fuzz_request(params.url, 'POST', os.path.join(params.corpus, 'POST', name), iteration, proxy=proxies, rules=regexps)
        for i in range(mutate_count[0]):
            req.send_request()
    iteration = req.iteration
    for name in corpus_path_GET:
        req = Fuzz_request(params.url, 'GET', os.path.join(params.corpus, 'GET', name), iteration, proxy=proxies, rules=regexps)
        for i in range(mutate_count[0]):
            req.send_request()


def main():
    count = 0
    params = parse_params()
    if params.proxy != None:
        proxies = {
              "http": params.proxy,
              "https": params.proxy
            }
    else:
        proxies = None
    mutate_count = get_mutate_count(params.corpus, params.mutates)
    fuzz_it(params, mutate_count, proxies)


if __name__ == "__main__":
    print('='*n)
    main()

