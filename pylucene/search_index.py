import sys, lucene

from java.nio.file import Paths
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import NIOFSDirectory
from org.apache.lucene.search import IndexSearcher

def interactive_search(searcher, analyzer):
    while True:
        print()
        print("Hit enter with no input to quit.")
        command = input("Query: ")
        if command == '':
            return
        print()

        search(searcher, analyzer, command)

def search(searcher, analyzer, command):
    print("Searching for:", command)
    print()
    query = QueryParser("content", analyzer).parse(command)
    scoreDocs = searcher.search(query, 5).scoreDocs
    print("%s total matching documents." % len(scoreDocs))
    print()

    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc.doc)
        print("filename:", doc.get("filename"))
        print("reviewer_username:", doc.get("reviewer_username"), "rating:", doc.get("rating"), "summary:", doc.get("summary"))
        # for field in ["filename", "book_title", "reviewer_username", "rating", "summary"]:
        #     print(f'{field}:', doc.get(field))
        print()


if __name__ == '__main__':
    print()
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    print('lucene', lucene.VERSION)
    print()
    print()
    directory = NIOFSDirectory(Paths.get('pylucene/indexdir'))
    searcher = IndexSearcher(DirectoryReader.open(directory))
    analyzer = StandardAnalyzer()
    if len(sys.argv) == 1:
        interactive_search(searcher, analyzer)
    else:
        search(searcher, analyzer, ' '.join(sys.argv[1:]))
    del searcher