import psycopg2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import ndcg_score
import time

# Connessione al database PostgreSQL
conn = psycopg2.connect(
    dbname="Progetto_libri",
    user="postgres",
    password=input("Inserisci passwd postgres\n"),
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Funzioni per eseguire query con i due modelli
def execute_query_ts(query_text):
    cursor.execute("""
        SELECT file_name, title, summary, content, rating, rank
        FROM search_documents_ts(%s, 20);
    """, (query_text,))
    return cursor.fetchall()

def execute_query_trgm(query_text):
    cursor.execute("""
        SELECT file_name, title, summary, content, rating, rank
        FROM search_documents_trgm(%s, 20);
    """, (query_text,))
    return cursor.fetchall()
def execute_query_hybrid(query_text):
    cursor.execute("""
        SELECT file_name, title, summary, content, rating, rank
        FROM search_documents_hybrid(%s, 20);
    """, (query_text,))
    return cursor.fetchall()
    
def print_results(results):
    for hit in results:
        print(f"File: {hit[0]}")
        print(f"Title: {hit[1]}")
        print(f"Summary: {hit[2]}")
        print(f"Content: {hit[3]}...")
        print(f"Rating: {hit[4]}")
        print(f"Score: {round(hit[5], 3)}")
        print("---------------\n")

# Menu della query syntax in base al modello
def print_query_syntax(model_choice):
    print("\nQUERY SYNTAX DISPONIBILE:")

    if model_choice == "1":
        print("  - TS_RANK_CD (Full-Text Search) supporta:")
        print("  - Phrasal search: \"word1 word2\"")
        print("  - Wildcard search: word*")
        print("  - Boolean search: word1 AND word2 / word1 OR word2 / NOT word1")
        print("  - Field search: title:word, summary:word, content:word, rating:word")
        

    elif model_choice == "2":
        print("  - pg_trgm (Fuzzy Matching) supporta:")
        print("  - Phrasal search: \"word1 word2\" (Simile con `ILIKE`)")
        print("  - Boolean search: word1 AND word2 / word1 OR word2 / NOT word1")
        print("  - Fuzzy search: word~ (Trigram similarity)")
        print("  - Field search: title:word, summary:word, content:word, rating:word")
        
    elif model_choice == "2":
        print("  - hybrid (Fuzzy Matching) supporta:")
        print("  - Phrasal search: \"word1 word2\" (Simile con `ILIKE`)")
        print("  - Boolean search: word1 AND word2 / word1 OR word2 / NOT word1")
        print("  - Fuzzy search: word~ (Trigram similarity)")
        print("  - Field search: title:word, summary:word, content:word, rating:word")
    print("  - B to evaluate the model with the benchmark")
    print("  - q to quit")
# Carica query dal file di benchmark
def load_queries_from_file(filename):
    queries = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            query_text = parts[0].strip()
            relevant_docs = [doc.strip() for doc in parts[1].split(',')]
            queries[query_text] = relevant_docs
    return queries

# Precision interpolata ai livelli standard di recall
def calculate_interpolated_precision(retrieved, relevant):
    recall_levels = np.linspace(0, 1, 11)
    precision_at_recall = {r: 0 for r in recall_levels}
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

def calculate_ap(retrieved, relevant):
    ap = 0
    relevant_found = 0
    for i, doc in enumerate(retrieved):
        if doc in relevant:
            relevant_found += 1
            ap += relevant_found / (i + 1)
    return ap / len(relevant) if relevant else 0

def calculate_ndcg(retrieved, relevant):
    relevance_scores = [1 if doc in relevant else 0 for doc in retrieved[:20]]
    ideal_relevance = sorted(relevance_scores, reverse=True)
    if len(relevance_scores) < 2:
        return 0
    return ndcg_score([ideal_relevance], [relevance_scores]) if relevance_scores else 0

def evaluate_queries(queries, search_function):
    results_table = []
    map_scores = []
    ndcg_scores = []

    for query_text, relevant_docs in queries.items():
        results = search_function(query_text)
        retrieved_docs = [row[0] for row in results]

        precision_at_recall = calculate_interpolated_precision(retrieved_docs, relevant_docs)
        ap = calculate_ap(retrieved_docs, relevant_docs)
        ndcg = calculate_ndcg(retrieved_docs, relevant_docs)

        map_scores.append(ap)
        ndcg_scores.append(ndcg)

        results_table.append([query_text] + [precision_at_recall[r] for r in sorted(precision_at_recall.keys())])

    return results_table, np.mean(map_scores), np.mean(ndcg_scores)
def compare_postgres_models():
    queries = load_queries_from_file("benchmark.txt")
    models = {
        "TS_RANK_CD": execute_query_ts,
        "pg_trgm": execute_query_trgm,
        "hybrid TS-pg": execute_query_hybrid
    }
    model_results = {}

    for model_name, search_function in models.items():
        print(f"\n🔹 Evaluating {model_name}...")
        results_table, map_score, ndcg_score = evaluate_queries(queries, search_function)
        model_results[model_name] = {
            "MAP": round(map_score, 4),
            "NDCG@10": round(ndcg_score, 4)
        }

    df = pd.DataFrame.from_dict(model_results, orient='index')
    print("\n🔹 Tabella di confronto tra i modelli:")
    print(df.to_string())
def execute_queries(queries, model):
    
    interpolated_precisions = {}  # Salva precisioni interpolate per ogni query
    results_table = []

    for query_text, relevant_docs in queries.items():
        if model == 'ts':
            results = execute_query_ts(query_text)
        elif model == 'pg':
            results = execute_query_trgm(query_text)
        else:
            results = execute_query_hybrid(query_text)
        retrieved_docs = [hit[0] for hit in results]

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
def do_benchmark(model):
    queries = load_queries_from_file(benchmark_file)
    interpolated_precisions= execute_queries(queries, model)
    plot_interpolated_precision_recall_curves(interpolated_precisions)
if __name__ == "__main__":
    benchmark_file = "benchmark.txt"
    print("\nScegli l'operazione:")
    print("1. Esegui una query manuale")
    print("2. Esegui il benchmark e confronta i modelli")
    choice = input("Scelta: ")

    if choice == "1":
        print("\nScegli il modello di ricerca:")
        print("1. TS_RANK_CD (Full-Text Search)")
        print("2. pg_trgm (Fuzzy Matching)")
        print("3. hybrid (Fuzzy + Full-text)")
        model_choice = input("Scelta: ")

        while True:
            print_query_syntax(model_choice)
            query_text = input("\nInserisci la query: ")
            start = time.perf_counter()
            if query_text.lower() == 'q':
                break
            if model_choice == "1":
                if query_text == 'B':
                    do_benchmark('ts')
                else:
                    results = execute_query_ts(query_text)
                    print(f"\nRisultati per '{query_text}':\n")
                    print_results(results)
                end = time.perf_counter()
                elapsed_time = end - start
                print(f"\n\nElapsed time query: " + str(round(elapsed_time, 4)))
            elif model_choice == "2":
                if query_text == 'B':
                    do_benchmark('pg')
                else:
                    results = execute_query_trgm(query_text)
                    print(f"\nRisultati per '{query_text}':\n")
                    print_results(results)
                end = time.perf_counter()
                elapsed_time = end - start
                print(f"\n\nElapsed time query: " + str(round(elapsed_time, 4)))
            elif model_choice == "3":
                if query_text == 'B':
                    do_benchmark('hy')
                else:
                    results = execute_query_hybrid(query_text)
                    print(f"\nRisultati per '{query_text}':\n")
                    print_results(results)
                end = time.perf_counter()
                elapsed_time = end - start
                print(f"\n\nElapsed time query: " + str(round(elapsed_time, 4)))
            else:
                print("Scelta non valida.")
                continue

            

    elif choice == "2":
        compare_postgres_models()

    else:
        print("Scelta non valida. Riprova.")
