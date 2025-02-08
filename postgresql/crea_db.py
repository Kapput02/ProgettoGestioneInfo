import os
import psycopg2

# Connessione al database PostgreSQL
conn = psycopg2.connect(
    dbname="Progetto_libri", user="postgres", password=input("Inserisci passwd postgresql"), host="localhost", port="5432"
)
cur = conn.cursor()

# Percorso alla cartella che contiene i tuoi file
directory_path = "/Users/eliacapiluppi/Desktop/GestInfPratico/Dataset"
i=0
# Ciclo attraverso tutti i file nella directory
for filename in os.listdir(directory_path):
    if filename.endswith(".txt"):
        with open(os.path.join(directory_path, filename), 'r', encoding='utf-8') as f:
            # Leggi tutte le righe del file
            lines = f.readlines()
            if len(lines) >= 5:
                # Estrai i valori dai campi
                cod_book = lines[0].strip()
                title = lines[1].strip()
                username_reviewer = lines[3].strip()
                rating = float(lines[4].strip())
                summary = lines[5].strip()
                content = ''.join(line.strip() for line in lines[6:])

                # Inserisci i dati nel database
                insert_query = """
                INSERT INTO documents (file_name, cod_book, title, username_reviewer, rating, summary, content)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (filename, cod_book, title, username_reviewer, rating, summary, content))
            i = i+1
            if i % 1000 == 0:
                conn.commit()

# Esegui commit finale
conn.commit()

# Chiudi la connessione
cur.close()
conn.close()

print("Dati importati correttamente!")
