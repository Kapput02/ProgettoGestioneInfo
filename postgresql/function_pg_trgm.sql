CREATE OR REPLACE FUNCTION search_documents_trgm(query TEXT, limit_num INT)
RETURNS TABLE(file_name TEXT, title TEXT, summary TEXT, content TEXT, rating FLOAT, rank REAL) AS $$
DECLARE
    field_query TEXT := NULL;
    processed_query TEXT;
BEGIN
    IF query ~* '^(title|summary|content|rating):' THEN
        field_query := split_part(query, ':', 1);
        query := split_part(query, ':', 2);
    END IF;

    processed_query := replace(query, ' AND ', ' & ');
    processed_query := replace(processed_query, ' OR ', ' | ');
    processed_query := replace(processed_query, ' NOT ', ' ! ');

    processed_query := regexp_replace(processed_query, '(\w+)~', '\1', 'g');

    RETURN QUERY 
    SELECT 
        d.file_name, d.title, d.summary, d.content, d.rating,
        (
            2 * similarity(d.title, query) +
            1.5 * similarity(d.summary, query) +
            1 * similarity(d.content, query) +
            1 * similarity(CAST(d.rating AS TEXT), query)
        ) AS rank
    FROM documents d
    WHERE 
        (field_query = 'title' AND similarity(d.title, query) > 0.1)
        OR (field_query = 'summary' AND similarity(d.summary, query) > 0.1)
        OR (field_query = 'content' AND similarity(d.content, query) > 0.1)
        OR (field_query = 'rating' AND similarity(CAST(d.rating AS TEXT), query) > 0.1)
        OR (field_query IS NULL AND (
            similarity(d.title, query) > 0.1 OR
            similarity(d.summary, query) > 0.1 OR
            similarity(d.content, query) > 0.1 OR
            similarity(CAST(d.rating AS TEXT), query) > 0.1
        ))
    ORDER BY rank DESC
    LIMIT limit_num;
END;
$$ LANGUAGE plpgsql;
