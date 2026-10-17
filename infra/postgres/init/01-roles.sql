-- Runs once when a Postgres container starts with an empty data directory.
-- as_owner (POSTGRES_USER) owns the tables and runs migrations. as_app is the role
-- the app connects as: data access only, granted by the accounts grants migration.
-- Local and test only; real environments create roles with their own secrets.
CREATE ROLE as_app LOGIN PASSWORD 'as_app' NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
