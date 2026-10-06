-- Everything to be published goes in a database of its own, `publish`,
-- kept apart from the private tables in the main one: the privacy checks
-- (90_checks.sql) look at every table in it, and only its tables are
-- exported (95_export.sql). It lives in memory; DuckDB moves to its temp
-- folder whatever does not fit.
ATTACH IF NOT EXISTS ':memory:' AS publish;
