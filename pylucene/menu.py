import os
import lucene

from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.analysis.standard import StandardAnalyzer
from java.nio.file import Paths
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.store import NIOFSDirectory
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity

from sklearn.metrics import ndcg_score
import numpy as np
import time
import matplotlib.pyplot as plt
import pandas as pd

#Scelta del modello da utilizzare
# DONE
def modelUI():
    print("\n")
    print("Choose the model you want to use: ")
    print("1. BM25 with default values")
    print("2. BM25 with k1=1 and b=1")
    print("3. BM25 with k1=2 and b=0")
    print("4. Lucene ClassicSimilarity")
    print("5. Compare different models using benchmark")
    model_choice = input("Model: ")
    return model_choice

#Carica query dal file di benchmark
# DONE
def load_queries_from_file(filename):
    queries = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            query_text = parts[0].strip()
            relevant_docs = [doc.strip() for doc in parts[1].split(',')]
            queries[query_text] = relevant_docs
    return queries

#Calcola precisione ai livelli standard
# DONE
def calculate_interpolated_precision(retrieved, relevant):
    recall_levels = np.linspace(0,1,11)
    precision_at_recall = {r:0 for r in recall_levels}
    relevant_found = 0
    total_relevant = len(relevant)
    if total_relevant == 0:
        return precision_at_recall
    for i, doc in enumerate(retrieved):
        if doc in relevant:
            relevant_found += 1
            recall = relevant_found / total_relevant
            precision = relevant_found / (i + 1)
            
            for r in recall_levels:
                if recall >= r:
                    precision_at_recall[r] = max(precision_at_recall[r], precision)

    return precision_at_recall

#Calcola average precision
# DONE
def calculate_ap(retrieved, relevant):
    ap = 0
    relevant_found = 0

    for i, doc in enumerate(retrieved):
        if doc in relevant:
            relevant_found += 1
            ap += relevant_found / (i + 1)

    return ap / len(relevant) if relevant else 0

# DONE
def execute_queries(searcher, queries):
    interpolated_precisions = {}  # Salva precisioni interpolate per ogni query
    results_table = []

    query_parser = QueryParser("content", StandardAnalyzer())

    for query_text, relevant_docs in queries.items():
        query = query_parser.parse(query_text)
        scoreDocs = searcher.search(query, 10).scoreDocs

        retrieved_docs = [searcher.doc(scoreDoc.doc).get('filename') for scoreDoc in scoreDocs]

        precision_at_recall = calculate_interpolated_precision(retrieved_docs, relevant_docs)
        interpolated_precisions[query_text] = precision_at_recall

        results_table.append([query_text] + [precision_at_recall[r] for r in sorted(precision_at_recall.keys())])

        print(f"\nQuery: {query_text}")
        for r in sorted(precision_at_recall.keys()):
            print(f"Recall {r:.1f} → Precision: {precision_at_recall[r]:.3f}")
    
    return interpolated_precisions

# DONE
def plot_interpolated_precision_recall_curves(interpolated_precisions):
    plt.figure(figsize=(10, 7))

    for query_text, precision_at_recall in interpolated_precisions.items():
        recall_levels = sorted(precision_at_recall.keys())
        precision_values = [precision_at_recall[r] for r in recall_levels]

        plt.plot(recall_levels, precision_values, marker='o', linestyle='-', label=query_text)

    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curves for Each Query')
    plt.legend()
    plt.grid()
    plt.show()

# DONE
def show_results_table(results_table):
    recall_levels = [f"Recall {r:.1f}" for r in np.linspace(0, 1, 11)]
    df = pd.DataFrame(results_table, columns=["Query"] + recall_levels)

    df.iloc[:, 1:] = df.iloc[:, 1:].applymap(lambda x: round(x, 3))

    print("\n🔹 Tabella della Precision Interpolata:")
    print(df.to_string(index=False))

# DONE
def printResults(result):
    # Print query results
    for doc in result:
        print(f"Filename: {doc.get('filemane')}")
        print(f"Book title: {doc.get('book_title')}")
        print(f"Reviewer username: {doc.get('reviewer_username')}")
        print(f"Rating: {doc.get('rating')}")
        print(f"Summary: {doc.get('summary')}")
        print(f"Content: {doc.get('content')}")
        print("---------------\n")

# DONE
def do_benchmark(searcher, benchmark_file):
    queries = load_queries_from_file(benchmark_file)
    interpolated_precisions= execute_queries(searcher, queries)
    plot_interpolated_precision_recall_curves(interpolated_precisions)

# DONE
def calculate_ndcg(retrieved, relevant, k=10):
    relevance_scores = [1 if doc in relevant else 0 for doc in retrieved[:k]]
    ideal_scores = sorted(relevance_scores, reverse=True)
    
    if sum(ideal_scores) == 0:
        return 0  # Se non ci sono documenti rilevanti, NDCG è 0

    return ndcg_score([ideal_scores], [relevance_scores])

# DONE
def compare_models(indexes_dir, benchmark_file):
    models = {
        "BM25 (default values)": (BM25Similarity(), 'BM25_default'),
        "BM25 (k1=1, B=1)": (BM25Similarity(k1=1, B=1), 'BM25_k1_1_b_1'),
        "BM25 (k1=2, B=0)": (BM25Similarity(k1=2, B=0), 'BM25_k1_2_b_0'),
        "Lucene ClassicSimilarity": (ClassicSimilarity(), 'ClassicSimilarity')
    }

    queries = load_queries_from_file(benchmark_file)
    model_results = {}

    for model_name, model, index_sub_dir in models.items():
        print(f"\n🔹 Evaluating {model_name}...")
        # Calcola MAP e NDCG@10 per il modello
        total_ap = 0
        total_ndcg = 0
        num_queries = len(queries)

        directory = NIOFSDirectory(Paths.get(os.path.join(indexes_dir, index_sub_dir)))
        searcher = IndexSearcher(DirectoryReader.open(directory))
        searcher.setSimilarity(model)
        query_parser = QueryParser("content", StandardAnalyzer())
        for query_text, relevant_docs in queries.items():
            query = query_parser.parse(query_text)
            scoreDocs = searcher.search(query, 10).scoreDocs
            retrieved_docs = [searcher.doc(scoreDoc.doc).get('filename') for scoreDoc in scoreDocs]

            total_ap += calculate_ap(retrieved_docs, relevant_docs)
            total_ndcg += calculate_ndcg(retrieved_docs, relevant_docs, k=10)

        map_score = total_ap / num_queries
        avg_ndcg = total_ndcg / num_queries

        model_results[model_name] = {
            "MAP": round(map_score, 4),
            "NDCG@10": round(avg_ndcg, 4)
        }

    df = pd.DataFrame.from_dict(model_results, orient='index')
    print("\n🔹 Tabella di confronto tra i modelli:")
    print(df.to_string())


def main():
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])

    indexes_dir = 'pylucene/indexes'
    benchmark_file = "benchmark.txt"
    corpus_dir = '../dataset'
    
    model_choice = modelUI()
    if model_choice == '1':
        model = BM25Similarity()
        index_sub_dir = 'BM25_default'
    elif model_choice == '2':
        model = BM25Similarity(k1=1, b=1)
        index_sub_dir = 'BM25_k1_1_b_1'
    elif model_choice == '3':
        model = BM25Similarity(k1=2, b=0)
        index_sub_dir = 'BM25_k1_2_b_0'
    elif model_choice == '4':
        model = ClassicSimilarity()
        index_sub_dir = 'ClassicSimilarity'
    elif model_choice == '5':
        compare_models(indexes_dir, benchmark_file)
        exit(0)
    else:
        print("Invalid Model")
        exit(1)

    directory = NIOFSDirectory(Paths.get(os.path.join(indexes_dir, index_sub_dir)))
    searcher = IndexSearcher(DirectoryReader.open(directory))
    searcher.setSimilarity(model)
    query_parser = QueryParser("content", StandardAnalyzer())
    while True:
        # print("\nQUERY SYNTAX")
        # print("Phrasal search: \"word1 word2\"")
        # print("Proximity search: \"word1 word2\"~N")
        # print("Wildcard search: word*")
        # print("Range search: [word1 TO word2]")
        # print("Boolean search: word1 OR word2")
        # print("Fuzzy search: word~")
        # print("Field search: field:word ---> fields are title, rating, summary and content")
        print("B to evaluate the model with the benchmark")
        print("q to quit")
        query_text = input("\nInsert the query: ")
        if query_text == 'q':
            break
        if query_text == 'B':
            do_benchmark(searcher, benchmark_file)
            continue
        query = query_parser.parse(query_text)

        start = time.perf_counter()
        results = [searcher.doc(scoreDoc.doc) for scoreDoc in searcher.search(query, 10).scoreDocs]
        end = time.perf_counter()

        elapsed_time = end - start
        
        print(f"\n\nElapsed time query: " + str(round(elapsed_time, 4)))
        
        print('\nRESULTS:' + str(len(results)))
        printResults(results)


if __name__ == "__main__":
    main()