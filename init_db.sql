-- Script de inicialización para PostgreSQL (EVA-2)
-- Base de datos: edtech_db

CREATE DATABASE edtech_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Spanish_Spain.1252'
    LC_CTYPE = 'Spanish_Spain.1252'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

\c edtech_db;

-- Una vez creada la base de datos, ejecutar en PowerShell:
-- py manage.py migrate
-- py manage.py poblar_datos
