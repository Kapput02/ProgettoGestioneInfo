import psycopg2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import ndcg_score

# Connessione al database PostgreSQL
conn = psycopg2.connect(
    dbname="Progetto_libri",
    user="postgres",
    password=input("Inserisci passwd postgres\n"),
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

def execute_query_trgm(query_text):
    cursor.execute("""
        SELECT file_name, title, summary, content, rating, rank
        FROM search_documents_trgm(%s, 10);
    """, (query_text,))
    
    results = cursor.fetchall()
    retrieved_docs = [row[0] for row in results]  # Lista dei file restituiti
    return retrieved_docs

# Funzione per eseguire query in PostgreSQL (Full-Text Search)
def execute_query_ts(query_text):
    cursor.execute("""
        SELECT file_name, title, summary, content, rating, rank
        FROM search_documents(%s, 10);
    """, (query_text,))
    
    results = cursor.fetchall()
    retrieved_docs = [str(row[0]) for row in results]  # Lista dei nome_file dei documenti retrieved
    return retrieved_docs

# unisci a menu
def load_queries_from_file(filename):
    queries = {}
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('|')
            query_text = parts[0].strip()
            relevant_docs = [doc.strip() for doc in parts[1].split(',')]
            queries[query_text] = relevant_docs
    return queries

#unisci a menu
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

# unisci menu
def calculate_ap(retrieved, relevant):
    ap = 0
    relevant_found = 0

    for i, doc in enumerate(retrieved):
        if doc in relevant:
            relevant_found += 1
            ap += relevant_found / (i + 1)

    return ap / len(relevant) if relevant else 0

#unisci menu
def calculate_ndcg(retrieved, relevant):
    relevance_scores = [1 if doc in relevant else 0 for doc in retrieved]
    ideal_relevance = sorted(relevance_scores, reverse=True)
    
    return ndcg_score([ideal_relevance], [relevance_scores])

# Valutazione delle query su un modello
def evaluate_queries(queries, search_function):
    results_table = []
    map_scores = []
    ndcg_scores = []

    for query_text, relevant_docs in queries.items():
        retrieved_docs = search_function(query_text)

        # Calcola metriche
        precision_at_recall = calculate_interpolated_precision(retrieved_docs, relevant_docs)
        ap = calculate_ap(retrieved_docs, relevant_docs)
        ndcg = calculate_ndcg(retrieved_docs, relevant_docs)

        map_scores.append(ap)
        ndcg_scores.append(ndcg)

        results_table.append([query_text] + [precision_at_recall[r] for r in sorted(precision_at_recall.keys())])

    mean_map = np.mean(map_scores)
    mean_ndcg = np.mean(ndcg_scores)

    return results_table, mean_map, mean_ndcg

# Confronto tra modelli
def compare_postgres_models():
    queries = load_queries_from_file("benchmark.txt")

    models = {
        "TS_RANK_CD": execute_query_ts,
        "BM25 (pg_trgm)": execute_query_trgm
    }

    model_results = {}

    for model_name, search_function in models.items():
        print(f"\n🔹 Evaluating {model_name}...")

        results_table, map_score, ndcg_score = evaluate_queries(queries, search_function)

        model_results[model_name] = {
            "MAP": round(map_score, 4),
            "NDCG@10": round(ndcg_score, 4)
        }

    # Disegna le Precision-Recall curves
    plt.figure(figsize=(10, 7))

    for model_name in models.keys():
        avg_precision_at_recall = {r: 0 for r in np.linspace(0, 1, 11)}
        
        for query_text in queries.keys():
            retrieved_docs = models[model_name](query_text)
            precision_at_recall = calculate_interpolated_precision(retrieved_docs, queries[query_text])

            for r in precision_at_recall:
                avg_precision_at_recall[r] += precision_at_recall[r]

        avg_precision_at_recall = {r: avg_precision_at_recall[r] / len(queries) for r in avg_precision_at_recall}
        recall_levels = sorted(avg_precision_at_recall.keys())
        precision_values = [avg_precision_at_recall[r] for r in recall_levels]

        plt.plot(recall_levels, precision_values, marker='o', linestyle='-', label=model_name)

    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Comparison for PostgreSQL Models')
    plt.legend()
    plt.grid()
    plt.show()

    # Tabella di confronto tra modelli
    df = pd.DataFrame.from_dict(model_results, orient='index')
    print("\n🔹 Tabella di confronto tra i modelli:")
    print(df.to_string())

# MAIN del programma
if __name__ == "__main__":
    print("\n🔹 Scegli l'operazione:")
    print("1. Esegui una query manuale")
    print("2. Esegui il benchmark e confronta i modelli")
    choice = input("Scelta: ")

    if choice == "1":
        query_text = input("Inserisci la query: ")
        retrieved_docs = execute_query_postgres(query_text)
        print(f"\n🔹 Documenti restituiti per '{query_text}':\n", retrieved_docs)

    elif choice == "2":
        compare_postgres_models()

    else:
        print("Scelta non valida. Riprova.")
