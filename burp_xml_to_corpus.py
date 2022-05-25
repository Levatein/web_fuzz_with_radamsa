import xml.etree.ElementTree as ET
import argparse
import os

def parse_params():
    parser = argparse.ArgumentParser()
    parser.add_argument('-x', dest="xml", help='path to xml', required=True)
    parser.add_argument('-c', dest="corpus", help='path to corpus dir', required=True)
    return parser.parse_args()


def main():
    params = parse_params()
    elems = []
    corpus_path_POST = os.path.join(params.corpus, 'POST')
    corpus_path_GET = os.path.join(params.corpus, 'GET')
    if not os.path.isdir(corpus_path_POST):
        os.mkdir(corpus_path_POST)
    if not os.path.isdir(corpus_path_GET):
        os.mkdir(corpus_path_GET)

    for event, elem in ET.iterparse(params.xml, ):
        if elem.tag == "request":
            if 'POST /' in elem.text:
                e = elem.text
                prs = e.split('\n')[-1]
                req = e.split('\n')[0].split()[1]
                e = req + '\n' + prs
                if len(prs) > 0:
                    if e not in elems:
                        elems.append(e)

    for i in range(len(elems)):
        with open(os.path.join(corpus_path_POST, str(i)), 'wb') as f:
            f.write(elems[i].encode())

    print('create {} files in POST'.format(len(elems)))
    elems = []

    for event, elem in ET.iterparse(params.xml, ):
        if elem.tag == "request":
            if 'GET /' in elem.text:
                e = elem.text
                req = e.split('\n')[0].split()[1].split('?')
                prs = req[-1]
                req = req[0]
                e = req + '\n' + prs
                if len(prs) > 0:
                    if e not in elems:
                        elems.append(e)

    for i in range(len(elems)):
        with open(os.path.join(corpus_path_GET, str(i)), 'wb') as f:
            f.write(elems[i].encode())
    print('create {} files in GET'.format(len(elems)))

if __name__ == "__main__":
    main()

