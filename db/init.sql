CREATE USER repl_user WITH REPLICATION ENCRYPTED  PASSWORD 'repl_password';
SELECT pg_create_physical_replication_slot('replications');

CREATE DATABASE pt;

\c pt;

CREATE TABLE IF NOT EXISTS phones (
    id SERIAL PRIMARY KEY,
    номер VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    почта VARCHAR(100) NOT NULL
);

INSERT INTO emails (почта) VALUES ('pt@start.ru'), ('superfet01@gmail.com');
INSERT INTO phones (номер) VALUES ('8-987-654-32-10'), ('+7 (987) 654 32 10');
