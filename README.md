# ProgettoGestioneInfo

Nota: Eseguire tutti i file specificati dalla directory contenente questo file

Istruzioni per la creazione degli indici:
    1.  Eseguire il file "dataset.py": esso crea la cartella "dataset" contenente
          le recensioni organizzate per singoli file a partire dal file "Book_ratings.csv"
    2.  Whoosh:
            Eseguire il file "whoosh/generate_indexes.py": gli indici saranno creati basandosi sui dati di "dataset" e saranno contenuti nella cartella indexdir
        PyLucene:
            Eseguire il file "pylucene/generate_indexes.py": esso crea quattro indici, uno per ogni
              modello implementato, nella cartella "pylucene/indexes" usando i dati contenuti in "dataset".
        PostgreSQL:
            Creare il database Progetto_libri da postgresql, poi eseguire al suo interno la query postgresql/crea_doc.sql. Eseguire poi postgresql/crea_db.py e di nuovo all'interno del database eseguire le query index.sql, postgresql/funcion_pg_tgrm.sql,postgresql/funcion_ts_rank_cd.sql rispettivamente per creare l'index e le funzioni di searching dei modelli.
        
Istruzioni per la ricerca:
    Whoosh:
        Eseguire il file menu.py e seguire le istruzioni.
    PyLucene:
        Eseguire il file "pylucene/menu.py" e seguire le istruzioni.
    PostgreSQL:
        Eseguire il file postgresql/postg.py e seguire le istruzioni.