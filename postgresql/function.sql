CREATE OR REPLACE FUNCTION search_documents(query TEXT, limit_num INT)
RETURNS TABLE(file_name TEXT, title TEXT, summary TEXT, content TEXT, rank REAL) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        d.file_name, d.title, d.summary, d.content,
        ts_rank_cd(d.tsv_content, plainto_tsquery('english', query)) AS rank
    FROM documents d
    WHERE d.tsv_content @@ plainto_tsquery('english', query)
    ORDER BY rank DESC
    LIMIT limit_num;
END;
$$ LANGUAGE plpgsql;
