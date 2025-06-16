CREATE OR REPLACE FUNCTION search_documents_hybrid(query TEXT, limit_num INT)
RETURNS TABLE(file_name TEXT, title TEXT, summary TEXT, content TEXT, rating FLOAT, rank REAL) AS $$
DECLARE
    field_query TEXT := NULL;
    query_tsquery TSQUERY;
    fuzzy_terms TEXT[];
    cleaned_query TEXT;
    fulltext_count INT;
BEGIN
    -- Estrai campo se specificato
    IF query ~* '^(title|summary|content|rating):' THEN
        field_query := split_part(query, ':', 1);
        query := ltrim(split_part(query, ':', 2));
    END IF;

    -- Prepara tsquery
    cleaned_query := replace(query, ' AND ', ' & ');
    cleaned_query := replace(cleaned_query, ' OR ', ' | ');
    cleaned_query := replace(cleaned_query, ' NOT ', ' ! ');
    cleaned_query := regexp_replace(cleaned_query, '(\w+)\*', '\1:*', 'g');

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

    -- Conta i risultati full-text
    SELECT COUNT(*) INTO fulltext_count
    FROM documents d
    WHERE
        (field_query = 'title' AND d.tsv_title @@ query_tsquery)
     OR (field_query = 'summary' AND d.tsv_summary @@ query_tsquery)
     OR (field_query = 'content' AND d.tsv_content @@ query_tsquery)
     OR (field_query = 'rating' AND to_tsvector('english', CAST(d.rating AS TEXT)) @@ query_tsquery)
     OR (field_query IS NULL AND (
            d.tsv_title @@ query_tsquery OR d.tsv_summary @@ query_tsquery OR d.tsv_content @@ query_tsquery
        )
     );

    -- Esegui query finale con fuzzy attivo se count < 5
    RETURN QUERY
    SELECT 
		d.file_name, d.title, d.summary, d.content, d.rating,
		CAST(
			0.8 * (
				ts_rank_cd(setweight(d.tsv_title, 'A'), query_tsquery) +
				ts_rank_cd(setweight(d.tsv_summary, 'B'), query_tsquery) +
				ts_rank_cd(setweight(d.tsv_content, 'D'), query_tsquery)
			)
			+
			CASE
				WHEN fulltext_count < 5 THEN
				  0.2 * GREATEST(
					  similarity(d.title, query),
					  similarity(d.summary, query),
					  similarity(d.content, query)
				  )
				ELSE 0
	        END
	    AS REAL) AS rank

    FROM documents d
    WHERE
      (field_query = 'title' AND (
          d.tsv_title @@ query_tsquery
          OR (fulltext_count < 5 AND EXISTS (
              SELECT 1 FROM unnest(fuzzy_terms) t 
              WHERE similarity(d.title, t) >= 0.2
          ))
      ))
   OR (field_query = 'summary' AND (
          d.tsv_summary @@ query_tsquery
          OR (fulltext_count < 5 AND EXISTS (
              SELECT 1 FROM unnest(fuzzy_terms) t 
              WHERE similarity(d.summary, t) >= 0.2
          ))
      ))
   OR (field_query = 'content' AND (
          d.tsv_content @@ query_tsquery
          OR (fulltext_count < 5 AND EXISTS (
              SELECT 1 FROM unnest(fuzzy_terms) t 
              WHERE similarity(d.content, t) >= 0.2
          ))
      ))
   OR (field_query = 'rating' AND (
          to_tsvector('english', CAST(d.rating AS TEXT)) @@ query_tsquery
          OR (fulltext_count < 5 AND EXISTS (
              SELECT 1 FROM unnest(fuzzy_terms) t 
              WHERE similarity(CAST(d.rating AS TEXT), t) >= 0.2
          ))
      ))
   OR (field_query IS NULL AND (
          d.tsv_title @@ query_tsquery
          OR d.tsv_summary @@ query_tsquery
          OR d.tsv_content @@ query_tsquery
          OR (fulltext_count < 5 AND EXISTS (
               SELECT 1 FROM unnest(fuzzy_terms) t
               WHERE similarity(d.title, t) >= 0.2
                  OR similarity(d.summary, t) >= 0.2
                  OR similarity(d.content, t) >= 0.2
            ))
      ))
    ORDER BY rank DESC
    LIMIT limit_num;
END;
$$ LANGUAGE plpgsql;
