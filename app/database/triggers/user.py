from sqlalchemy import text

USER_SEARCH_TRIGGER_FUNCTION = text(
    """
CREATE OR REPLACE FUNCTION update_user_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', coalesce(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(NEW.email, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(NEW.preferences::text, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
)


USER_SEARCH_TRIGGER = text(
    """
DROP TRIGGER IF EXISTS user_search_update ON users;
CREATE TRIGGER user_search_update
    BEFORE INSERT OR UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_user_search_vector();
"""
)
