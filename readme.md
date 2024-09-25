Run last alembic migration:
`alembic upgrade head`

go to previous version:
`alembic downgrade rev#`

generate initial migration:
```
alembic revision --autogenerate -m 'initial'
create revision:
alembic revision -m "text"
alembic revision --autogenerate
```


Run tests:
```
cp blackout.db blackout-test.db
BLACKOUT_DB=blackout-test.db pytest

with coverage report 
BLACKOUT_DB=blackout-test.db pytest --cov --cov-report=html:coverage_re
```
run in docker using venv on host:

`
sudo TOKEN="token" ./hostvenv_run_in_docker.sh
`

build docker container with bot and run:
```
docker build . -t blackout
docker run -e TOKEN="token" -e AWS_ACCESS_KEY_ID="key" -e AWS_SECRET_ACCESS_KEY="secret" --rm blackout  
```

install precommit hooks:
`
pre-commit install
pre-commit run --all-files
`

deploy on fly.io without autoscaling:
`
fly deploy --ha=false   
`

scale app:
`
fly scale show
fly scale count 1
`

storage dashboard:
`
fly storage dashboard
`