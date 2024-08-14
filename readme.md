Run last alembic migration:
`alembic upgrade head`

go to first version:
`alembic downgrade rev#`

generate initial migration:
`alembic revision --autogenerate -m 'initial'
create revision:
alembic revision -m "seed"
`
run in docker using venv on host:
`
sudo ./hostvenv_run_in_docker.sh

`

install precommit hooks 
`
pre-commit install
pre-commit run --all-files
`
deploy on fly.io without autoscaling
`
fly deploy --ha=false   
`
scale app
`
fly scale show
fly scale count 1
`

storage dashboard:
`
fly storage dashboard
`