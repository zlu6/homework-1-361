import json
import nltk
import csv,os
import sys
from nltk.stem import WordNetLemmatizer
nltk.download('wordnet')


class Application:
    def __init__(self):
        if len(sys.argv) == 3:

            self.json_path = sys.argv[1]
            # a path to the JSON file with the corpus

            self.index_path = sys.argv[2] + "/"
            # a path to the directory where the index files will be stored.
        else:
            print('please input 2 args in command line')
            sys.exit(1)

    def load_corpus(self):
        try:
            f = open(self.json_path)
            print("Successfully open the file %s " % self.json_path)
            data = json.load(f)
        except IOError:
            print("Invalid path. Can not open such file")
            sys.exit(1)
        else:
            f.close()
            return data

    def write_result(self):
        inv = InvertedIndex()
        inv.check_valid_doc()
        docs = inv.collect_docs()
        zone_list = inv.find_all_zones(docs)
        pair_token = inv.create_pairs(zone_list, docs)
        inv_index_dict = inv.create_index(pair_token)
        # path = 'movie_plots/'
        try:
            os.mkdir(self.index_path)
        except OSError:
            print("Creation of the directory %s failed" % self.index_path)
        else:
            print("Successfully created the directory %s " % self.index_path)

        for zone, values in inv_index_dict.items():
            with open(self.index_path + zone + ".tsv", 'w') as f:
                for key, id in values.items():
                    res = [key, str(len(id)), ",".join(str(item) for item in sorted(id))]
                    w = csv.writer(f, delimiter='\t')
                    w.writerow(res)


class InvertedIndex:
    def __init__(self):
        self.app = Application()
        self.corpus = self.app.load_corpus()
        # print(self.corpus)

    def check_valid_doc(self):
        """
        The program must check that every document in the corpus has an id and at least one zone.
        """
        key_list = []
        for data in self.corpus:
            for key in data.keys():
                key_list.append(key)
            if "doc_id" not in key_list:
                print("Error: no doc_id in the document")
                sys.exit(1)
            else:
                if len(key_list) == 1 and key_list[0] == "doc_id":
                    print("Error: no zone in the document ")
                    sys.exit(1)
                key_list = []

    def find_zones(self):
        """
        find zones in each document
        :return: (dict) key:doc_id val: zones of each document
        """
        zone_dict = {}
        zone_list = []
        index = 0
        for item in self.corpus:
            pairs = item.items()
            for key,val in pairs:
                if key == 'doc_id':
                    index = val
                else:
                    zone_list.append(key)
            zone_dict.update({str(index): zone_list})
            zone_list = []
        return zone_dict

    def collect_docs(self):
        """

        :return: (list) normalized corpus of loaded json file
        """
        zone_dict = self.find_zones()
        normalized_corpus = []

        for data in self.corpus:
            for zone in zone_dict[data['doc_id']]:
                data[zone] = self.normalize(data[zone])

            normalized_corpus.append(data)
        return normalized_corpus

    def normalize(self, sentence):
        """normalize the context by applying tokenization, lemmatization and lowercasing"""
        lemma_list = []
        lemmatizer = WordNetLemmatizer()
        tokens = nltk.word_tokenize(sentence)
        tokens_alnum = [word.lower() for word in tokens if word.isalnum()]
        for token in tokens_alnum:
            lemma_list.append(lemmatizer.lemmatize(token))

        return lemma_list

    def find_all_zones(self, corpus):
        """retrieve all zones in the corpus"""
        zone_list = []
        for ele in corpus:
            for key in ele.keys():
                if key != "doc_id":
                    zone_list.append(key)
        zone_set = set(zone_list)
        return zone_set

    def create_pairs(self, zone, corpus):
        """create pair of (doc_id, token)"""
        token_dict = {}
        token_pair = []
        token_id = 0
        for item in corpus:
            pairs = item.items()
            for key, val in pairs:
                if key == 'doc_id':
                    token_id = val
                    continue
                if key in zone:
                    index = key
                    for token in val:
                        token_pair.append((token, token_id))
                    token_dict.setdefault(index, [])
                    token_dict[index].extend(token_pair)
                    token_pair = []
        return token_dict

    def create_index(self, token_id_pair):
        """create inverted index"""
        token_dict = {}
        for zone, token_id in token_id_pair.items():
            token_id.sort(key=lambda x: x[0])
            token_dict[zone] = {}
            for token, id in token_id:
                token_dict[zone].setdefault(token, set()).add(id)
        return token_dict


if __name__ == '__main__':
    app = Application()
    app.write_result()



