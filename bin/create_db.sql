CREATE DATABASE access4all;
CREATE USER access4all WITH PASSWORD 'access4all';
ALTER ROLE access4all SET client_encoding TO 'utf8';
ALTER ROLE access4all SET default_transaction_isolation TO 'read committed';
ALTER ROLE access4all SET timezone TO 'UTC';
ALTER DATABASE access4all OWNER TO access4all;
GRANT ALL PRIVILEGES ON DATABASE access4all TO access4all;
GRANT ALL PRIVILEGES IN SCHEMA public GRANT
\c access4all;
CREATE EXTENSION postgis;
CREATE EXTENSION pg_trgm;
CREATE EXTENSION unaccent;
CREATE TEXT SEARCH CONFIGURATION french_unaccent( COPY = french );
ALTER TEXT SEARCH CONFIGURATION french_unaccent
ALTER MAPPING FOR hword, hword_part, word
WITH unaccent, french_stem;

-- On localhost, duplicate it to create a test database named test_access4all
