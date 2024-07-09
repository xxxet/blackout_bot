Run last alembic migration:
alembic upgrade head

go to first version:
alembic downgrade 8a7b8e7e4c3b

generate initial migration:
alembic revision --autogenerate -m 'initial'
create revision:
alembic revision -m "seed"

run in docker 
sudo ./run_in_docker.sh "path_to_group_file" "bot_id"