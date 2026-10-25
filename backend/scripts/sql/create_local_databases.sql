-- One-time local setup (implementation plan §2.9). Run in pgAdmin 4's Query Tool while connected
-- as the `postgres` superuser. Replace the placeholder password locally; never commit it.
-- The application, tests, migrations and seeding all connect as `imibereho`, never as `postgres`.

CREATE ROLE imibereho LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '<choose locally; never commit>';

CREATE DATABASE imibereho            OWNER imibereho;
CREATE DATABASE imibereho_test       OWNER imibereho;
CREATE DATABASE imibereho_migrations OWNER imibereho;
