import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
VAR_DIR = os.path.join(BASE_DIR, 'var')
SESSION_DIR = os.path.join('/', 'var', 'data', 'session')
PLUGIN_DIR = os.path.join(BASE_DIR, 'plugins')
DIRECTORIES = [LOG_DIR, VAR_DIR]
#PSQL
#DB_ENGINE = "PMmJIadQN4ZuyKaajcyzT6ZjheoaVQWcchdDZgLixEO8t41L8vfg6QgEtaJn22E8"
#MYSQL
DB_ENGINE = "eyyHS9p6rhaIBay7ihE3TFGHXgsozMk4WVAKEFjGYbWYKvxVf0B5dBulSJh4FYxB"

