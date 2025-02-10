CREATE OR REPLACE FUNCTION search_documents_trgm(query TEXT, limit_num INT)
RETURNS TABLE(file_name TEXT, title TEXT, summary TEXT, content TEXT, rating FLOAT, rank REAL) AS $$
DECLARE
    field_query TEXT := NULL;
    processed_query TEXT;
    phrase_search BOOLEAN := FALSE;
    query_terms TEXT[];
BEGIN
    -- Gestione del campo specifico nella query
    IF query ~* '^(title|summary|content|rating):' THEN
        field_query := split_part(query, ':', 1);
        query := split_part(query, ':', 2);
    END IF;

    -- Elaborazione della query per supportare la ricerca fuzzy
    processed_query := replace(query, ' AND ', ' & ');
    processed_query := replace(processed_query, ' OR ', ' | ');
    processed_query := replace(processed_query, ' NOT ', ' ! ');

    -- Gestione delle virgolette per la ricerca per frase
    IF query LIKE '%"%"%' THEN
        phrase_search := TRUE;
        query := replace(query, '"', '');
    END IF;

    processed_query := regexp_replace(processed_query, '(\w+)~', '\1', 'g');

    -- Se la query contiene AND, separiamo i termini
    IF processed_query LIKE '% & %' THEN
        query_terms := string_to_array(processed_query, ' & ');
    ELSE
        query_terms := string_to_array(processed_query, ' ');
    END IF;

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
        (
            -- Caso per ricerca per frase
            phrase_search = TRUE AND (
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
            )
        )
        OR (
            -- Caso per ricerca con AND (tutti i termini devono essere presenti)
            phrase_search = FALSE AND (
                (field_query = 'title' AND array_length(array(SELECT term FROM unnest(query_terms) AS term WHERE similarity(d.title, term) > 0.1), 1) = array_length(query_terms, 1)) OR
                (field_query = 'summary' AND array_length(array(SELECT term FROM unnest(query_terms) AS term WHERE similarity(d.summary, term) > 0.1), 1) = array_length(query_terms, 1)) OR
                (field_query = 'content' AND array_length(array(SELECT term FROM unnest(query_terms) AS term WHERE similarity(d.content, term) > 0.1), 1) = array_length(query_terms, 1)) OR
                (field_query = 'rating' AND array_length(array(SELECT term FROM unnest(query_terms) AS term WHERE similarity(CAST(d.rating AS TEXT), term) > 0.1), 1) = array_length(query_terms, 1)) OR
                (field_query IS NULL AND (
                    array_length(array(SELECT term FROM unnest(query_terms) AS term WHERE similarity(d.title, term) > 0.1), 1) = array_length(query_terms, 1) OR
                    array_length(array(SELECT term FROM unnest(query_terms) AS term WHERE similarity(d.summary, term) > 0.1), 1) = array_length(query_terms, 1) OR
                    array_length(array(SELECT term FROM unnest(query_terms) AS term WHERE similarity(d.content, term) > 0.1), 1) = array_length(query_terms, 1) OR
                    array_length(array(SELECT term FROM unnest(query_terms) AS term WHERE similarity(CAST(d.rating AS TEXT), term) > 0.1), 1) = array_length(query_terms, 1)
                ))
            )
        )
    ORDER BY rank DESC
    LIMIT limit_num;
END;
$$ LANGUAGE plpgsql;
