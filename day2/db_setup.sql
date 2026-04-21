-- create new database
CREATE DATABASE IF NOT EXISTS day1_db;

-- create new user
CREATE USER IF NOT EXISTS user@localhost IDENTIFIED BY 'password';

-- grant create
GRANT CREATE, SELECT, INSERT, UPDATE, DELETE
ON day1_db.*
TO 'user'@'localhost';