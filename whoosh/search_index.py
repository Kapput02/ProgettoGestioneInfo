from whoosh.index import open_dir
from whoosh.qparser import QueryParser

ix = open_dir("whoosh/indexdir")
searcher = ix.searcher()
parser = QueryParser("content", ix.schema)
parser_titolo = QueryParser("title", ix.schema)
query = parser.parse("")
results = searcher.search(query)
print(results[0:1])
