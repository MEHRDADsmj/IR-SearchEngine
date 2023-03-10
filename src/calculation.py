import itertools
import math
import time
import pandas as pd
from src.indexer import Indexer
from src.indexer_v2 import IndexerV2


class Calculation:

    def __init__(self):
        self.indexer = IndexerV2()
        self.docs, self.total_doc_count = self.indexer.get_documents_list()

    def get_ranked_documents(self, query: list[str]):
        data_frame = pd.read_excel('../tfidf.xlsx', skiprows=0)
        query_vector = self.make_vector_from_query(query)
        # docs, total_doc_count = self.indexer.get_documents_list()[0]  # is is now in __init__, remove this!
        cosines = dict()

        for index in range(5):  # todo : replace 5 with 'self.total_doc_count'
            cosines[self.docs[index][0]] = (self.get_cos_vector(self.get_doc_as_vector(index, data_frame), query_vector))

        return dict(sorted(cosines.items(), key=lambda item: item[1], reverse=True))

    def make_tables(self) -> None:
        # making index table
        try:
            data_frame = pd.read_excel('../index.xlsx')
            if data_frame.empty:
                print("Indexing documents...")
                self.indexer.main()
        except Exception:
            print("Indexing documents...")
            self.indexer.main()

        try:
            data_frame = pd.read_excel('../tf_table.xlsx')
            if data_frame.empty:
                print("Extracting tf table...")
                self.extract_tf_table()
        except Exception:
            print("Extracting tf table...")
            self.extract_tf_table()

        try:
            data_frame = pd.read_excel('../idf_table.xlsx')
            if data_frame.empty:
                print("Calculating idf...")
                self.extract_idf_table(5)  # todo : replace 5 with 'self.total_doc_count'
        except Exception:
            print("Calculating idf...")
            self.extract_idf_table(5)  # todo : replace 5 with 'self.total_doc_count'

        try:
            data_frame = pd.read_excel('../tfidf.xlsx')
            if data_frame.empty:
                print("Calculating tf-idf...")
                self.extract_tfidf_table()
        except Exception:
            print("Calculating tf-idf...")
            self.extract_tfidf_table()

    def dot_product(self, vector1: list[int | float], vector2: list[int | float]) -> float:
        new_vector = []
        total_sum = 0

        if len(vector1) == len(vector2):
            for index in range(len(vector1)):
                new_vector.append(vector1[index] * vector2[index])
            for index in range(len(new_vector)):
                total_sum += new_vector[index]
            return total_sum
        else:
            print("Vectors are not the same size")

    def calculate_normal_idf(self, df: int, total_doc_count: int) -> float:
        return math.log(total_doc_count / df, 10)

    def calculate_normal_idf_for_all(self, dfs: list[int], total_doc_count: int) -> list[float]:
        idfs = [math.log(total_doc_count / df, 10) for df in dfs]
        return idfs

    def calculate_normal_tfidf(self, tf: int, idf: float) -> float:
        return float(math.log(1 + float(tf), 10)) * idf

    # Calculates tf-idf for a complete row (for a term in each document)
    def calculate_normal_tfidf_for_row(self, tfs: list[int], idf: float) -> list[float]:
        tfidf = [math.log(1 + tf, 10) * idf for tf in tfs]
        return tfidf

    # Calculates tf-idf for a complete column
    def calculate_normal_tfidf_for_col(self, tfs: list[int], idfs: list[float]) -> list[float]:
        tfidf = [math.log(1 + tf, 10) * idf for tf, idf in zip(tfs, idfs)]
        return tfidf

    def get_vector_size(self, vector: list[int | float]) -> float:
        total_sum = 0
        for index in range(len(vector)):
            total_sum += math.pow(vector[index], 2)
        return math.sqrt(total_sum)

    def get_cos_vector(self, vector1: list[int | float], vector2: list[int | float]) -> float:
        dot_result = self.dot_product(vector1, vector2)
        vector1_size = self.get_vector_size(vector1)
        vector2_size = self.get_vector_size(vector2)
        return dot_result / (vector1_size * vector2_size)

    def make_vector_from_query(self, query_list: list[str]) -> list[int]:
        vector = [0] * self.indexer.get_term_count()
        for word in query_list:
            try:
                vector[self.indexer.get_term_index_from_list(word)] += 1
            except Exception:
                pass
        return vector

    # TODO: Further optimization
    def extract_tf_table(self) -> None:
        data_frame = pd.read_excel('../index.xlsx', skiprows=0, usecols='A, D')

        start = time.time()

        terms = []
        docs = set()
        datas = []

        column = data_frame.iloc[:, 0]
        terms.append(list(column))
        terms = list(itertools.chain(*terms))

        for index in range(len(data_frame.values)):
            pair = dict(eval(data_frame.values[index][1]))
            docs.update(pair.keys())

        docs_list = list(docs)
        docs_list = sorted(docs_list, key=str.casefold)

        for index in range(len(data_frame.values)):
            doc_tf_dict = dict(eval(data_frame.values[index][1]))
            data = [0] * len(docs)
            for index2 in range(len(doc_tf_dict)):
                data[docs_list.index(list(doc_tf_dict.keys())[index2])] = list(doc_tf_dict.values())[index2]
            datas.append(data)

        print(time.time() - start)
        new_df = pd.DataFrame(datas, index=terms, columns=docs_list)
        new_df.to_excel('../tf_table.xlsx')

    def extract_idf_table(self, total_doc_count: int) -> None:
        data_frame = pd.read_excel('../index.xlsx', skiprows=0, usecols='A, C')
        terms = []
        dfs = []

        column = data_frame.iloc[:, 0]
        terms.append(list(column))
        terms = list(itertools.chain(*terms))

        column = data_frame.iloc[:, 1]
        dfs.append(list(column))
        dfs = list(itertools.chain(*dfs))

        new_df = pd.DataFrame(self.calculate_normal_idf_for_all(dfs, total_doc_count), index=terms)
        new_df.to_excel('../idf_table.xlsx')

    def extract_tfidf_table(self):
        data_frame_idf = pd.read_excel('../idf_table.xlsx', skiprows=0, usecols='B')
        data_frame = pd.read_excel('../tf_table.xlsx', skiprows=0)

        idfs = data_frame_idf.values.tolist()
        idfs = list(itertools.chain(*idfs))
        cols = data_frame[data_frame.columns[1:]]

        tfidf = []
        for index in range(5):
            tfidf.append(self.calculate_normal_tfidf_for_col(list(cols.iloc[:, index]), idfs))

        new_data_frame = pd.DataFrame(tfidf)
        new_data_frame = new_data_frame.transpose()
        new_data_frame.to_excel('../tfidf.xlsx')

    def get_doc_as_vector(self, doc_num: int, data_frame: pd.DataFrame) -> list[float]:
        all_cols = data_frame[data_frame.columns[1:]]
        mylist = [i[doc_num] for i in all_cols.values]
        return mylist
