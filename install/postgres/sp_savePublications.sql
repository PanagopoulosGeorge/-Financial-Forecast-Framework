CREATE OR REPLACE FUNCTION save_publications()
RETURNS VOID AS $$
BEGIN
    -- Step 1: Drop the target table if it exists
    DROP TABLE IF EXISTS publishes_save;

    -- Step 2: Create the target table and insert all data from the source table
    CREATE TABLE publishes_save AS
    SELECT * FROM publishes;
END;
$$ LANGUAGE plpgsql;
