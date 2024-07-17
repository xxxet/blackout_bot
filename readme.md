Run last alembic migration:
alembic upgrade head

go to first version:
alembic downgrade rev#

generate initial migration:
alembic revision --autogenerate -m 'initial'
create revision:
alembic revision -m "seed"

run in docker 
sudo ./run_migrations.sh "bot_id"
sudo ./run_in_docker.sh "bot_id"