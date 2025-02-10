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


Ricerche benchmark:

    1.  Ricerca delle recensioni contenenti le parole "harry" e "potter" una dopo l'altra in questo ordine.
            Query: "harry potter"
    
    2.  Ricerca delle recensioni contenenti le parole "bad", "dorian" e "gray" in qualsiasi posizione e ordine.
            Query: bad AND dorian AND gray
    
    3.  Ricerca delle recensioni che contengono o la parola "ephemeral" o
        entrambe le parole "childhood" e "devoted", in qualsiasi posizione e ordine.
            Query: ephemeral OR (childhood AND devoted)

    4.  Ricerca delle recensioni che contengono la parola "panegiry".
            Query: panegiry
    
    5.  Ricerca delle recensioni contenenti le parole "romance", "plot" e "twist" in qualsiasi posizione e ordine.
            Query: romance AND plot AND twist

    6.  Ricerca delle recensioni che contengono la parola "great" nel campo "summary".
            Query: summary:great
    
    7.  Ricerca delle recensioni di libri che contengono la parola "parigi" nel titolo.
            Query: title:parigi

    8.  Ricerca delle recensioni che contengono la parola "terrible" nel campo "summary".
            Query: summary:terrible
    
    9.  Ricerca fuzzy delle recensioni che contengono le parole "dog" e "cat".
            Query: "dog cat"~1

    10. Ricerca delle recensioni contenenti le parole "fantasy" e "world" in qualsiasi posizione e ordine.
            Query: fantasy AND world



