from flask_app.ext.app import app


def run_app():
    app.run(debug=False)


if __name__ == "__main__":
    run_app()
