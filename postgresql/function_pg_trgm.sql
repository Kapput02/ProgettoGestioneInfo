CREATE OR REPLACE FUNCTION search_documents_trgm(query TEXT, limit_num INT)
RETURNS TABLE(file_name TEXT, title TEXT, summary TEXT, content TEXT, rating FLOAT, rank REAL) AS $$
DECLARE
    field_query TEXT := NULL;
    processed_query TEXT;
    phrase_search BOOLEAN := FALSE;
BEGIN
    IF query ~* '^(title|summary|content|rating):' THEN
        field_query := split_part(query, ':', 1);
        query := split_part(query, ':', 2);
    END IF;
    processed_query := replace(query, ' AND ', ' & ');
    processed_query := replace(processed_query, ' OR ', ' | ');
    processed_query := replace(processed_query, ' NOT ', ' ! ');
	
    IF query LIKE '%"%"%' THEN
        phrase_search := TRUE;
        query := replace(query, '"', '');
    END IF;
    processed_query := regexp_replace(processed_query, '(\w+)~', '\1', 'g');
    RETURN QUERY 
    SELECT 
        d.file_name, d.title, d.summary, d.content, d.rating,
        CAST(
            (2 * similarity(d.title, processed_query) +
            1.5 * similarity(d.summary, processed_query) +
            1 * similarity(d.content, processed_query) +
            1 * similarity(CAST(d.rating AS TEXT), processed_query))
        AS REAL) AS rank
    FROM documents d
    WHERE 
        (phrase_search = TRUE AND (
            (field_query = 'title' AND d.title ILIKE '%' || query || '%') OR
            (field_query = 'summary' AND d.summary ILIKE '%' || query || '%') OR
            (field_query = 'content' AND d.content ILIKE '%' || query || '%') OR
            (field_query = 'rating' AND CAST(d.rating AS TEXT) ILIKE '%' || query || '%') OR
            (field_query IS NULL AND (
                d.title ILIKE '%' || query || '%' OR
                d.summary ILIKE '%' || query || '%' OR
                d.content ILIKE '%' || query || '%' OR
                CAST(d.rating AS TEXT) ILIKE '%' || query || '%'
            ))
        ))
        OR (phrase_search = FALSE AND (
            (field_query = 'title' AND similarity(d.title, processed_query) > 0.01)
            OR (field_query = 'summary' AND similarity(d.summary, processed_query) > 0.01)
            OR (field_query = 'content' AND similarity(d.content, processed_query) > 0.01)
            OR (field_query = 'rating' AND similarity(CAST(d.rating AS TEXT), processed_query) > 0.01)
            OR (field_query IS NULL AND (
                similarity(d.title, processed_query) > 0.01 OR
                similarity(d.summary, processed_query) > 0.01 OR
                similarity(d.content, processed_query) > 0.01 OR
                similarity(CAST(d.rating AS TEXT), processed_query) > 0.01
            ))
        ))
    ORDER BY rank DESC
    LIMIT limit_num;
END;
$$ LANGUAGE plpgsql;