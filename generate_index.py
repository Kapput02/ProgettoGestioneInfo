import os
from whoosh.index import *
from whoosh.fields import *
from whoosh.analysis import StemmingAnalyzer
from whoosh.qparser import QueryParser

def index_files_in_directory(directory):
    schema = Schema(
        file=STORED,
        cod_book=STORED,
        title=TEXT(stored=True),
        #id_recensore=STORED,
        username_reviewer=STORED,
        rating=NUMERIC(numtype=float,stored=True),
        summary=TEXT(stored=True),
        content=TEXT(analyzer=StemmingAnalyzer(), stored=True)
    )

    if not os.path.exists("indexdir"):
        os.mkdir("indexdir")
    ix = create_in("indexdir", schema)
    batch_size = 10000
    all_files = os.listdir(directory)
    for i in range(0,len(all_files),batch_size):
        writer = ix.writer()
        batch = all_files[i:i+batch_size]
        for filename in batch:
                with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                    content = file.read()
                    #  Separate fields by newline
                    fields = content.split('\n')
                    
                    text = '\n'.join(fields[6:])
                    
                    writer.add_document(file=filename, cod_book=fields[0], title=fields[1], username_reviewer=fields[3],
                                                    rating=fields[4], summary=fields[5], content=text)
        writer.commit()
        print(i)
if __name__ == "__main__":
    
    input_directory = "dataset"
    index_files_in_directory(input_directory)