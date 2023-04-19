from flask_app.ext.app import app



def run_app():
    app.run(debug=True, host="0.0.0.0")


if __name__ == "__main__":
    run_app()
