# ProgettoGestioneInfo

Nota: Eseguire tutti i file specificati dalla directory contenente questo file

Istruzioni per la creazione degli indici:
    1.  Eseguire il file "dataset.py": esso crea la cartella "dataset" contenente
          le recensioni organizzate per singoli file a partire dal file "Book_ratings.csv"
    2.  Whoosh:
            ...
        PyLucene:
            Eseguire il file "pylucene/generate_indexes.py": esso crea quattro indici, uno per ogni
              modello implementato, nella cartella "pylucene/indexes" usando i dati contenuti in "dataset".
        PostgreSQL:
            ...
        
Istruzioni per la ricerca:
    Whoosh:
        ...
    PyLucene:
        Eseguire il file "pylucene/menu.py" e seguire le istruzioni.
    PostgreSQL:
        ...