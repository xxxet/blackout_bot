from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello() -> str:
    return "Hello!"


def run_server(port: int) -> None:
    app.run(host="0.0.0.0", port=port)
