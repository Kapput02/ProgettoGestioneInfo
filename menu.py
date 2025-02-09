from whoosh import index

from whoosh.qparser import MultifieldParser  # , QueryParser
from whoosh.qparser.plugins import FuzzyTermPlugin
from whoosh.scoring import BM25F, TF_IDF
from sklearn.metrics import ndcg_score
#from sklearn.metrics.pairwise import cosine_similarity

import numpy as np
import time
import matplotlib.pyplot as plt
import pandas as pd

#Scelta del model da utilizzare
def modelUI():
    print("\n")
    print("Choose the model you want to use: ")
    print("1. BM25F standard")
    print("2. BM25F with custom values (k = 1, B1 = 1)")
    print("3. BM25F with custom values (k = 2, B1 = 0)")
    print("4. Vector model TF-IDF")
    print("5. Compare different models using benchmark")
    model_choice = input("Model: ")
    return model_choice

#Carica query dal file di benchmark
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
def calculate_ap(retrieved, relevant):
    ap = 0
    relevant_found = 0

    for i, doc in enumerate(retrieved):
        if doc in relevant:
            relevant_found += 1
            ap += relevant_found / (i + 1)

    return ap / len(relevant) if relevant else 0
def execute_queries(ix, queries, weighting_model):
    
    interpolated_precisions = {}  # Salva precisioni interpolate per ogni query
    results_table = []

    with ix.searcher(weighting=weighting_model) as searcher:
        boost = {
            "title": 2,
            "summary": 1.5,
            "content": 1,
        }
        query_parser = MultifieldParser(["content", "title", "summary"], fieldboosts=boost,schema=ix.schema)
        query_parser.add_plugin(FuzzyTermPlugin)

        for query_text, relevant_docs in queries.items():
            query = query_parser.parse(query_text)
            results = searcher.search(query, limit=20)

            retrieved_docs = [hit['file'] for hit in results]

            precision_at_recall = calculate_interpolated_precision(retrieved_docs, relevant_docs)
            interpolated_precisions[query_text] = precision_at_recall

            results_table.append([query_text] + [precision_at_recall[r] for r in sorted(precision_at_recall.keys())])

            print(f"\nQuery: {query_text}")
            for r in sorted(precision_at_recall.keys()):
                print(f"Recall {r:.1f} → Precision: {precision_at_recall[r]:.3f}")
    return interpolated_precisions

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

def show_results_table(results_table):
    recall_levels = [f"Recall {r:.1f}" for r in np.linspace(0, 1, 11)]
    df = pd.DataFrame(results_table, columns=["Query"] + recall_levels)

    df.iloc[:, 1:] = df.iloc[:, 1:].applymap(lambda x: round(x, 3))

    print("\n🔹 Tabella della Precision Interpolata:")
    print(df.to_string(index=False))

def printResults(results):
    # Print query results
    for hit in results:
        print(f"File: {hit['file']}")
        print(f"Code book: {hit['cod_book']}")
        print(f"Title: {hit['title']}")
        print(f"Username reviewer: {hit['username_reviewer']}")
        print(f"Rating: {hit['rating']}")
        print(f"Summary: {hit['summary']}")
        print(f"Content: {hit['content'][:300]}...")
        print(f"Score: {round(hit.score, 3)}")
        print("---------------\n")
def do_benchmark(ix,weighting_model):
    queries = load_queries_from_file(benchmark_file)
    interpolated_precisions= execute_queries(ix, queries, weighting_model)
    plot_interpolated_precision_recall_curves(interpolated_precisions)


def calculate_ndcg(retrieved, relevant, k=10):
    relevance_scores = [1 if doc in relevant else 0 for doc in retrieved[:k]]
    ideal_scores = sorted(relevance_scores, reverse=True)
    
    if sum(ideal_scores) == 0:
        return 0

    return ndcg_score([ideal_scores], [relevance_scores])

def compare_models():
    models = {
        "BM25F (default)": BM25F,
        "BM25F (k=1, B=1)": BM25F(k1=1, B=1),
        "BM25F (k=2, B=0)": BM25F(k1=2, B=0),
        "TF-IDF": TF_IDF
    }

    queries = load_queries_from_file(benchmark_file)
    model_results = {}

    for model_name, weighting_model in models.items():
        print(f"\n🔹 Evaluating {model_name}...")
        total_ap = 0
        total_ndcg = 0
        num_queries = len(queries)

        with ix.searcher(weighting=weighting_model) as searcher:
            query_parser = MultifieldParser(["content", "title", "summary"], schema=ix.schema)
            for query_text, relevant_docs in queries.items():
                query = query_parser.parse(query_text)
                results = searcher.search(query, limit=10)
                retrieved_docs = [hit['file'] for hit in results]

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

if __name__ == "__main__":
    indexdir = input("Inserisci la directory dell'indice: ").strip()
    benchmark_file = "benchmark.txt"
    ix = index.open_dir(indexdir)
    
    model = modelUI()
    if model == '1':
        weighting_model = BM25F
    elif model == '2':
        weighting_model = BM25F(k1=1, B=1)
    elif model == '3':
        weighting_model = BM25F(k1=2, B=0)
    elif model == '4':
        weighting_model = TF_IDF
    elif model == '5':
        compare_models()
        exit(1)
    else:
        print("Invalid Model")
        exit(1)

    with ix.searcher(weighting=weighting_model) as searcher:
        boost = {
            "title": 2,
            "summary": 1.5,
            "content": 1,
        }

        query_parser = MultifieldParser(["content", "title", "summary"], fieldboosts=boost, schema=ix.schema)
        query_parser.add_plugin(FuzzyTermPlugin)
        while True:
            print("\nQUERY SYNTAX")
            print("Phrasal search: \"word1 word2\"")
            print("Proximity search: \"word1 word2\"~N")
            print("Wildcard search: word*")
            print("Range search: [word1 TO word2]")
            print("Boolean search: word1 OR word2")
            print("Fuzzy search: word~")
            print("Field search: field:word ---> fields are title, rating, summary and content")
            print("B to evaluate the model with the benchmark")
            print("q to quit")
            query_text = input("\nInsert the query: ")
            if query_text == 'q':
                break
            if query_text == 'B':
                do_benchmark(ix,weighting_model)
                continue
            query = query_parser.parse(query_text)
            start = time.perf_counter()
            
            results = searcher.search(query, limit=10, terms=True)
            if len(results) == 0:
                print("No results found with the original query")
                
                try:
                    new_query = searcher.correct_query(query, query_text)
                except (ValueError, TypeError, AttributeError) as e:
                    print("Impossible to correct query with this syntax!\n")
                    continue
                
                print(f"New query: {new_query.string}")

                # Check if the query is different from the original one
                if new_query.string == query_text:
                    print("Couldn't find a correct version of the query")
                    continue

                results = searcher.search(new_query.query, limit=10, terms=True)

                if len(results) == 0:
                    print("No results found with the new query")
                    continue

                # Allow did you mean results to get sorted
                query = new_query.query
            end = time.perf_counter()

            elapsed_time = end - start
            
            print(f"\n\nElapsed time query: " + str(round(elapsed_time, 4)))
            
            print('\nRESULTS:' + str(len(results)))
            printResults(results)