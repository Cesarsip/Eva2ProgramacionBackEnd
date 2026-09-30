-- Script de inicialización para PostgreSQL (EVA-2)
-- Base de datos: edtech_db
-- Crea la base vacía antes de ejecutar Django; al quitar el bloque CREATE
-- DATABASE, la aplicación necesitaría que alguien la cree manualmente.

CREATE DATABASE edtech_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Spanish_Spain.1252'
    LC_CTYPE = 'Spanish_Spain.1252'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

\c edtech_db;

-- Cambia la sesión de psql a la base creada; si se omite, los comandos
-- posteriores se aplicarían a la base que estuviera seleccionada.
-- Después de crearla, ejecutar en PowerShell estos pasos para construir el
-- esquema de Django y cargar los datos de demostración; sin ellos la base queda vacía:
-- py manage.py migrate
-- py manage.py poblar_datos
