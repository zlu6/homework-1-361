import re
import csv
import sys
import os
import nltk
from nltk.stem import WordNetLemmatizer
nltk.download('wordnet')


class Processor:
    def __init__(self):
        if len(sys.argv) == 3:
            # check if the user inputs two command line arguments
            # 1. path to where the index files are and
            # 2. an arbitrary Boolean query
            self.index_path = sys.argv[1] + "/"
            # check if 1. path to index file exist
            if not os.path.exists(self.index_path):
                print("Path of the file is invalid")
                sys.exit(1)
            self.query = sys.argv[2]
            # the boolean query
        else:
            print('please input 2 args in command line')
            sys.exit(1)

    def find_posting_list(self, zone, token):
        """
        retrieve posting list from tsv files.
        :param zone: (str) zone
        :param token: (str) normalized term
        :return: None if the posting list do not exits
                (str) posting list by (zone: token) pair
        """
        posting_list = None
        try:
            file = self.index_path + zone + ".tsv"
            f = open(file, 'r')
            data = csv.reader(f, delimiter="\t")
            for info in data:
                if info[0] == token:
                    posting_list = info[2]
                    # the third column contains posting lists
                    break
            if not posting_list:
                # if a token appears in the query without a corresponding zone
                # let the user know
                print("Error: can not find posting list in %s:%s" % (zone, token))
                return None
        except IOError:
            print("Error:Can't open such file")
            sys.exit(1)
        else:
            f.close()
            return posting_list

    def find_posting_freq(self, zone, token):
        """
        find DF of (zone:token) query
        :param zone: (str) zone
        :param token: (str) normalized term
        :return: (int)  0 if such query does not exist
                    else return DF
        """
        freq = 0
        try:
            file = self.index_path + zone + ".tsv"
            f = open(file, 'r')
            data = csv.reader(f, delimiter="\t")
            for info in data:
                if info[0] == token:
                    freq = int(info[1])
                    break
            if not freq:
                print("Error: can not find posting list in %s:%s" % (zone, token))
                return 0
        except IOError:
            print("Error:Can't open such file")
            sys.exit(1)
        else:
            f.close()
            return freq

    def validate_query(self):
        """
        to validate if the query is valid
        """
        # check equal parenthesis
        if self.query.count("(") != self.query.count(")"):
            print("Error: incomplete query. Please check parenthesis")
            sys.exit(1)
        # check if bool. operation is missing
        if self.query.count(":") != 1:
            if self.query.find("AND") == -1 and self.query.find("OR") == -1 and self.query.find("NOT") == -1:
                print("Error: can not find boolean operation. Make sure the boolean operation words are upper cases")
                sys.exit(1)
        # check if : is missing
        if self.query.count(":") != (self.query.count("AND") + self.query.count("OR")) + 1:
            print("Error: incomplete query. missing : in query")
            sys.exit(1)

    def find_query(self):
        self.validate_query()
        qp = QueryProcessor()
        res = qp.parenthesis_query(self.query)
        print(*res, sep='\n')


class QueryProcessor:
    def __init__(self):
        self.bool_exp = ["AND", "OR", "NOT"]
        self.file_process = Processor()

    def parenthesis_query(self, my_query):
        """
        if query contains parenthesis, search inner parenthesis query first, replace query with posting lists
        then recursively search rest of the parenthesis until no parenthesis in query
        :param my_query: (str) query
        :return: (str) posting list
        """
        if "(" and ")" not in my_query:
            res = self.process_query(my_query)
            return res
        left = my_query.rfind("(")
        # find last "("
        right = left+my_query[left:].find(")")
        # find first ")" after left parenthesis
        sub_query = self.process_query(my_query[left+1: right])
        return self.parenthesis_query(my_query.replace(my_query[left: right+1], str(sub_query)))

    def process_query(self, my_query):
        """
        process simple query with no parenthesis
        some code used from https://stackoverflow.com/questions/46977923/python-query-processing-and-boolean-search
        answered by Gnudiff, Oct 27 '17 at 18:06.
        :param my_query: (str) query
        :return:
        """
        result_set = set()
        output = set()
        operation = None
        res_flag = True
        # if 2 or more "AND" in query,
        # optimizing by process in order of increasing frequency
        if my_query.count("AND") >= 2 and my_query.find("NOT") == -1:
            my_query = self.conjunctive_query_opt(my_query)

        for word in re.split(" +(AND|OR|) +", my_query):
            inverted = False # for "NOT word" operations
            if res_flag:
                # check if the first query is already got the posting list
                if word.find(':') == -1 and word not in self.bool_exp:
                    for char in word:
                        if char.isdigit():
                            result_set.add(char)
                res_flag = False
            if not result_set and word not in self.bool_exp:
                # if result set is empty
                zone_token = word.split(":")
                posting_list = self.file_process.find_posting_list(zone_token[0], self.normalize(zone_token[1]))
                # find posting list
                if not posting_list:
                    result_set = set()
                else:
                    for ele in posting_list.replace(",", ""):
                        result_set.add(ele)

            if word in ['AND', 'OR']:
                operation = word
                continue

            if word.find('NOT') == 0:

                inverted = True
                # the word is inverted!
                realword = word[4:]
            else:
                realword = word

            if operation:
                # do and/or/not operation
                current_set = set()
                if realword.find(':') == -1 and word not in self.bool_exp:
                    for char in word:
                        if char.isdigit():
                            current_set.add(char)
                    # res_flag = True
                else:
                    zone_token = realword.split(":")
                    posting_list = self.file_process.find_posting_list(zone_token[0], self.normalize(zone_token[1]))
                    if not posting_list:
                        current_set = set()
                    else:
                        for ele in posting_list.replace(",", ""):
                            current_set.add(ele)

                if operation == 'AND':
                    if inverted == True:
                        result_set -= current_set
                    else:
                        result_set &= current_set
                if operation == 'OR':
                    result_set |= current_set

            operation = None
        for i in result_set:
            output.add(int(i))
        return output

    def conjunctive_query_opt(self, my_query):
        """
        optimize conjunctive query
        :param my_query: query
        :return: sorted query according to its frequency
        """
        word_freq_dict = {}
        result_set = set()
        for word in re.split(" +(AND) +", my_query):
            if word == "AND":
                continue
            if word.find(':') == -1 and word not in self.bool_exp:
                for char in word:
                    if char.isdigit():
                        result_set.add(char)
                word_freq_dict[word] = len(result_set)
                result_set = set()
            else:
                zone_token = word.split(":")
                freq = self.file_process.find_posting_freq(zone_token[0], self.normalize(zone_token[1]))
                word_freq_dict[word] = freq
        # reorder the query
        d = [pair[0] for pair in sorted(word_freq_dict.items(), key=lambda item: item[1])]
        for i in range(len(d)+1):
            if i % 2 == 1:
                d.insert(i, " AND ")
        res = ''.join(d)
        return res

    def normalize(self, word):

        lemmatizer = WordNetLemmatizer()
        word_lower = word.lower()

        return lemmatizer.lemmatize(word_lower)


if __name__ == '__main__':
    processor = Processor()
    processor.find_query()

