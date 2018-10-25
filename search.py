import sys
import json
import re
import os
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


HOST = 'http://localhost:9200/'
FOLDER = "json/hep-th-2002/"
FIELDS = [("author", re.compile(" +author *= *")),
          ("date", re.compile(" +date *= *"))]


def anti_stupidity_function(folder):
    print(len(os.listdir(folder)))
    for filename in os.listdir(folder):
        print('.', end="", flush=True)
        txt = ""
        with open(folder + filename, 'r') as f:
            txt = f.read()
        txt = txt.replace("'", '"')
        txt = txt.replace(' "": "",', "")

        with open(folder + filename, 'w') as f:
            f.write(txt)
    print()


def json_to_bulk(folder, index, doc_type="document"):
    print("Building a new one with", len(os.listdir(folder)), "documents.")

    for filename in os.listdir(folder):
        print('.', end="")
        with open(folder + filename) as f:

            f_json = ""
            try :
                f_json = json.load(f)
            except json.decoder.JSONDecodeError:
                continue

            f_json["_index"] = index
            f_json["_type"] = doc_type

            yield f_json


def text_to_query(txt, fields=FIELDS):
    query = { "query" : { "match" : {} } }
    apostrophs = re.compile("'.*'")

    for field, pattern in fields:
        for i in re.finditer(pattern, txt):

            value = re.search(apostrophs, txt[i.end():])
            if value:
                query['query']['match'][field] = value.group()
                txt = txt[:i.start()] + txt[i.end() + value.end():]

    if txt.strip():
        query["query"]["match"]["content"] = txt

    return query


if __name__ == "__main__":
    es = Elasticsearch(hosts=[HOST])
    # es.indices.delete("test")
    if not es.indices.exists("test"):
        print("No test index found, ", end="", flush=True)
        es.indices.create("test")
        bulk(es, json_to_bulk(FOLDER, 'test'), stats_only=True)
        print("\nTest index is build.")

    query = text_to_query("theory author = 'Gibson' date = '2002'")

    print(query, end='\n\n')
    print(es.search(index="test", body=query)["hits"])