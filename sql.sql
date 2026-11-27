CREATE DATABASE pymes_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'pymes-user'@'localhost' IDENTIFIED BY 'cambia_esta_clave';

GRANT ALL PRIVILEGES ON pymes_db.* TO 'pymes-user'@'localhost';

FLUSH PRIVILEGES;
