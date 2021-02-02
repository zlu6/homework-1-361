import json
import nltk


class Application:
    def __init__(self):
        pass

    def load_corpus(self):
        try:
            f = open('../data/dr_seuss_lines.json')
            data = json.load(f)
        except IOError:
            print("Can't open such file")
        else:
            f.close()
            return data


class InvertedIndex:
    def __init__(self):
        self.app = Application()
        self.corpus = self.app.load_corpus()
        # print(self.corpus)

    def find_zones(self):
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
        zone_dict = self.find_zones()
        normalized_corpus = []

        for data in self.corpus:
            for zone in zone_dict[data['doc_id']]:
                data[zone] = self.normalize(data[zone])

            normalized_corpus.append(data)
        return normalized_corpus

    def normalize(self, sentence):
        tokens = nltk.word_tokenize(sentence)
        new_tokens = [word.lower() for word in tokens if word.isalnum()]
        return new_tokens


if __name__ == '__main__':
    inv = InvertedIndex()
    res = inv.collect_docs()
    print(res)