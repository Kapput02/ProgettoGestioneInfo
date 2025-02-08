ALTER TABLE documents ADD COLUMN tsv_title TSVECTOR;
ALTER TABLE documents ADD COLUMN tsv_summary TSVECTOR;
ALTER TABLE documents ADD COLUMN tsv_content TSVECTOR;
ALTER TABLE documents ADD COLUMN tsv_rating TSVECTOR;

UPDATE documents 
SET tsv_title = to_tsvector('english', title),
    tsv_summary = to_tsvector('english', summary),
    tsv_content = to_tsvector('english', content),
	tsv_rating = to_tsvector('english', CAST(rating as TEXT));

CREATE INDEX idx_title ON documents USING GIN(tsv_title);
CREATE INDEX idx_summary ON documents USING GIN(tsv_summary);
CREATE INDEX idx_content ON documents USING GIN(tsv_content);
CREATE INDEX idx_rating ON documents USING GIN(tsv_rating);
