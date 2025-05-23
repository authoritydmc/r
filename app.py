from app import create_app

app = create_app()

if __name__ == '__main__':
    app.init_db()
    app.run(debug=True, port=app.config.get('port', 80))
