ALTER TABLE documents ADD COLUMN tsv_content TSVECTOR;
UPDATE documents SET tsv_content = to_tsvector('english', title || ' ' || summary || ' ' || rating || ' ' || content);

CREATE INDEX idx_fts ON documents USING GIN(tsv_content);
