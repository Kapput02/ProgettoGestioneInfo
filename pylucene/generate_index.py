import os, lucene
from datetime import datetime

from java.nio.file import Paths
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, IndexOptions
from org.apache.lucene.store import NIOFSDirectory


def generate_index(inputDir, storeDir, analyzer):

    if not os.path.exists(storeDir):
        os.mkdir(storeDir)

    store = NIOFSDirectory(Paths.get(storeDir))
    analyzer = LimitTokenCountAnalyzer(analyzer, 1048576)
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    writer = IndexWriter(store, config)

    t1 = FieldType()
    t1.setStored(True)
    t1.setTokenized(False)
    t1.setIndexOptions(IndexOptions.DOCS_AND_FREQS)

    t2 = FieldType()
    t2.setStored(True)
    t2.setTokenized(True)
    t2.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    t3 = FieldType()
    t3.setStored(False)
    t3.setTokenized(True)
    t3.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    for i, filename in enumerate(os.listdir(inputDir)):
        if i % 1000 == 0:
            print(i)
        
        with open(os.path.join(inputDir, filename)) as f:
            book_id, book_title, reviewer_user_id, reviewer_username, rating, summary, content = f.read().strip().split('\n')
        
        doc = Document()
        doc.add(Field("filename", filename, t1))
        doc.add(Field("book_id", book_id, t1))
        doc.add(Field("book_title", book_title, t2))
        doc.add(Field("reviewer_user_id", reviewer_user_id, t1))
        doc.add(Field("reviewer_username", reviewer_username, t2))
        doc.add(Field("rating", rating, t1))
        doc.add(Field("summary", summary, t2))
        doc.add(Field("content", content, t3))

        writer.addDocument(doc)
    
    writer.commit()
    writer.close()











if __name__ == '__main__':
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    print('lucene', lucene.VERSION)
    start = datetime.now()
    generate_index("dataset", "pylucene/indexdir", StandardAnalyzer())
    end = datetime.now()
    print(end - start)