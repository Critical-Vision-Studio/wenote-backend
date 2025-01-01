from app import create_app

app = create_app()

@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "* Authorization"
    response.headers["Access-Control-Max-Age"] = "300"
    return response

