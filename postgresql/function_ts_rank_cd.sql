CREATE OR REPLACE FUNCTION search_documents_ts(query TEXT, limit_num INT)
RETURNS TABLE(file_name TEXT, title TEXT, summary TEXT, content TEXT, rating FLOAT, rank REAL) AS $$
DECLARE
    field_query TEXT := NULL;
    processed_query TEXT;
    query_tsquery TSQUERY;
BEGIN
    IF query ~* '^(title|summary|content|rating):' THEN
        field_query := split_part(query, ':', 1);
        query := split_part(query, ':', 2);
    END IF;

    query := replace(query, ' AND ', ' & ');
    query := replace(query, ' OR ', ' | ');
    query := replace(query, ' NOT ', ' ! ');

    IF query LIKE '%"%"%' THEN
        query_tsquery := phraseto_tsquery('english', query);
    ELSE
        query := regexp_replace(query, '(\w+)\*', '\1:*', 'g');
        query_tsquery := to_tsquery('english', query);
    END IF;

    RETURN QUERY 
    SELECT 
        d.file_name, d.title, d.summary, d.content, d.rating,
        ts_rank_cd(
            setweight(d.tsv_title, 'A') ||
            setweight(d.tsv_summary, 'B') ||
            setweight(d.tsv_content, 'D') ||
            setweight(to_tsvector('english', CAST(d.rating AS TEXT)), 'D'),
            query_tsquery  -- Qui abbiamo già scelto il tipo di query
        ) AS rank
    FROM documents d
    WHERE 
        (field_query = 'title' AND d.tsv_title @@ query_tsquery)
        OR (field_query = 'summary' AND d.tsv_summary @@ query_tsquery)
        OR (field_query = 'content' AND d.tsv_content @@ query_tsquery)
        OR (field_query = 'rating' AND to_tsvector('english', CAST(d.rating AS TEXT)) @@ query_tsquery)
        OR (field_query IS NULL AND (
            d.tsv_title @@ query_tsquery OR
            d.tsv_summary @@ query_tsquery OR
            d.tsv_content @@ query_tsquery OR
            to_tsvector('english', CAST(d.rating AS TEXT)) @@ query_tsquery
        ))
    ORDER BY rank DESC
    LIMIT limit_num;
END;
$$ LANGUAGE plpgsql;
