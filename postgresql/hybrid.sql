CREATE OR REPLACE FUNCTION search_documents_hybrid(query TEXT, limit_num INT)
RETURNS TABLE(file_name TEXT, title TEXT, summary TEXT, content TEXT, rating FLOAT, rank REAL) AS $$
DECLARE
    field_query TEXT := NULL;
    processed_query TEXT;
    query_tsquery TSQUERY;
    fuzzy_terms TEXT[];
    cleaned_query TEXT;
    fulltext_count INT;
    avg_rank REAL;
BEGIN
    -- Estrai campo se presente
    IF query ~* '^(title|summary|content|rating):' THEN
        field_query := split_part(query, ':', 1);
        query := ltrim(split_part(query, ':', 2));
    END IF;

    -- Prepara la query ts
    cleaned_query := replace(query, ' AND ', ' & ');
    cleaned_query := replace(cleaned_query, ' OR ', ' | ');
    cleaned_query := replace(cleaned_query, ' NOT ', ' ! ');
    cleaned_query := regexp_replace(cleaned_query, '(\w+)\*', '\1:*', 'g');

    -- Usa phraseto_tsquery per virgolette
    IF query LIKE '%"%"%' THEN
        query_tsquery := phraseto_tsquery('english', query);
    ELSE
        query_tsquery := to_tsquery('english', cleaned_query);
    END IF;

    -- Estrai termini fuzzy
    fuzzy_terms := regexp_split_to_array(
        regexp_replace(lower(query), '[&|!()"*]', ' ', 'g'),
        '\s+'
    );

    -- Calcola numero di risultati e media del rank per decidere se attivare fuzzy
    SELECT COUNT(*) AS count, AVG(ft_rank) AS avg_rank INTO fulltext_count, avg_rank
    FROM (
        SELECT ts_rank_cd(
            setweight(d.tsv_title, 'A') ||
            setweight(d.tsv_summary, 'B') ||
            setweight(d.tsv_content, 'D') ||
            setweight(to_tsvector('english', CAST(d.rating AS TEXT)), 'D'),
            query_tsquery
        ) AS ft_rank
        FROM documents d
        WHERE (
            field_query = 'title' AND d.tsv_title @@ query_tsquery
        ) OR (
            field_query = 'summary' AND d.tsv_summary @@ query_tsquery
        ) OR (
            field_query = 'content' AND d.tsv_content @@ query_tsquery
        ) OR (
            field_query = 'rating' AND to_tsvector('english', CAST(d.rating AS TEXT)) @@ query_tsquery
        ) OR (
            field_query IS NULL AND (
                d.tsv_title @@ query_tsquery OR
                d.tsv_summary @@ query_tsquery OR
                d.tsv_content @@ query_tsquery
            )
        )
    ) AS sub;

    -- Esegui la query finale: se avg_rank < 0.2 allora usa fuzzy
    RETURN QUERY
    SELECT 
        d.file_name, d.title, d.summary, d.content, d.rating,
        (
            0.8 * (
                3.0 * ts_rank_cd(setweight(d.tsv_title, 'A'), query_tsquery) +
                1.5 * ts_rank_cd(setweight(d.tsv_summary, 'B'), query_tsquery) +
                1.0 * ts_rank_cd(setweight(d.tsv_content, 'D'), query_tsquery) +
                1.0 * ts_rank_cd(setweight(to_tsvector('english', CAST(d.rating AS TEXT)), 'D'), query_tsquery)
            )
            +
            CASE 
                WHEN avg_rank IS NULL OR avg_rank < 0.2 THEN
                    0.2 * GREATEST(
                        3.0 * similarity(d.title, query),
                        1.5 * similarity(d.summary, query),
                        1.0 * similarity(d.content, query)
                    )
                ELSE 0.0
            END
        )::REAL AS rank
    FROM documents d
    WHERE (
        field_query = 'title' AND (
            d.tsv_title @@ query_tsquery OR
            (avg_rank IS NULL OR avg_rank < 0.2 AND EXISTS (SELECT 1 FROM unnest(fuzzy_terms) t WHERE d.title % t))
        )
    ) OR (
        field_query = 'summary' AND (
            d.tsv_summary @@ query_tsquery OR
            (avg_rank IS NULL OR avg_rank < 0.2 AND EXISTS (SELECT 1 FROM unnest(fuzzy_terms) t WHERE d.summary % t))
        )
    ) OR (
        field_query = 'content' AND (
            d.tsv_content @@ query_tsquery OR
            (avg_rank IS NULL OR avg_rank < 0.2 AND EXISTS (SELECT 1 FROM unnest(fuzzy_terms) t WHERE d.content % t))
        )
    ) OR (
        field_query = 'rating' AND (
            to_tsvector('english', CAST(d.rating AS TEXT)) @@ query_tsquery OR
            (avg_rank IS NULL OR avg_rank < 0.2 AND EXISTS (SELECT 1 FROM unnest(fuzzy_terms) t WHERE CAST(d.rating AS TEXT) % t))
        )
    ) OR (
        field_query IS NULL AND (
            (d.tsv_title @@ query_tsquery OR d.tsv_summary @@ query_tsquery OR d.tsv_content @@ query_tsquery)
            OR (avg_rank IS NULL OR avg_rank < 0.2 AND EXISTS (
                SELECT 1 FROM unnest(fuzzy_terms) t 
                WHERE d.title % t OR d.summary % t OR d.content % t
            ))
        )
    )
    ORDER BY rank DESC
    LIMIT limit_num;
END;
$$ LANGUAGE plpgsql;
