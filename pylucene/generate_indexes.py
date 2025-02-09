import os, lucene
from datetime import datetime

from java.nio.file import Paths
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, FieldType
from org.apache.lucene.index import IndexWriter, IndexWriterConfig, IndexOptions
from org.apache.lucene.store import NIOFSDirectory
from org.apache.lucene.search.similarities import BM25Similarity, ClassicSimilarity


def generate_index(inputDir, storeDir, analyzer, similarity):

    if not os.path.exists(storeDir):
        os.mkdir(storeDir)

    store = NIOFSDirectory(Paths.get(storeDir))
    analyzer = LimitTokenCountAnalyzer(analyzer, 1048576)
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    config.setSimilarity(similarity)
    writer = IndexWriter(store, config)

    t1 = FieldType()
    t1.setStored(True)
    t1.setTokenized(False)
    t1.setIndexOptions(IndexOptions.DOCS_AND_FREQS)

    t2 = FieldType()
    t2.setStored(False)
    t2.setTokenized(False)
    t2.setIndexOptions(IndexOptions.DOCS_AND_FREQS)

    t3 = FieldType()
    t3.setStored(False)
    t3.setTokenized(True)
    t3.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    total_numer_of_reviews = len(os.listdir(inputDir))
    for i, filename in enumerate(os.listdir(inputDir)):
        with open(os.path.join(inputDir, filename)) as f:
            book_id, book_title, reviewer_user_id, reviewer_username, rating, summary, content = f.read().strip().split('\n')
        
        doc = Document()
        doc.add(Field("filename", filename, t1))
        doc.add(Field("book_id", book_id, t2))
        doc.add(Field("book_title", book_title, t3))
        doc.add(Field("reviewer_user_id", reviewer_user_id, t2))
        doc.add(Field("reviewer_username", reviewer_username, t3))
        doc.add(Field("rating", rating, t2))
        doc.add(Field("summary", summary, t3))
        doc.add(Field("content", content, t3))

        writer.addDocument(doc)

        if i % 100 == 99 or i == total_numer_of_reviews - 1:
            print(f'  {i+1} / {total_numer_of_reviews} done', end=('\n' if i == total_numer_of_reviews - 1 else '\r'))
    
    writer.commit()
    writer.close()


def generate_all_indexes(inputDir, outputDir):
    if not os.path.exists(outputDir):
        os.mkdir(outputDir)
    
    for name, similarity, dir in [
        ('BM25 with default values', BM25Similarity(), 'BM25_default'),
        ('BM25 with k1=1 and b=1', BM25Similarity(k1=1, b=1), 'BM25_k1_1_b_1'),
        ('BM25 with k1=2 and b=0', BM25Similarity(k1=2, b=0), 'BM25_k1_2_b_0'),
        ('Lucene ClassicSimilarity', ClassicSimilarity(), 'ClassicSimilarity')
    ]:
        print('Generating index for model:', name, '...')
        generate_index(inputDir, os.path.join(outputDir, dir), StandardAnalyzer(), similarity)
        print()








if __name__ == '__main__':
    print()
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    print('lucene', lucene.VERSION)
    print()
    print()
    start = datetime.now()
    generate_all_indexes("dataset", "pylucene/indexes2")
    end = datetime.now()
    print()
    print(end - start)