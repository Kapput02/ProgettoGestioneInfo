import os
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh.scoring import BM25F

def search_index(query_str, model="bm25"):
    ix = open_dir("indexdir")
    if model == "bm25":
        searcher = ix.searcher(weighting=BM25F())
    else:
        searcher = ix.searcher()
    
    with searcher:
        query_parser = QueryParser("content", ix.schema)
        query = query_parser.parse(query_str)
        results = searcher.search(query, limit=10)
        
        for hit in results:
            print(f"Titolo: {hit['title']}, Voto: {hit['rating']}, Recensione: {hit['content']}, Punteggio: {hit.score:.4f}")
        
if __name__ == "__main__":
    user_query = input("Inserisci la query di ricerca: ")
    model_type = input("Scegli il modello (bm25/boolean): ").strip().lower()
    search_index(user_query, model_type)