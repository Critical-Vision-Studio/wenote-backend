from flask import jsonify

from app.exceptions import LogicalError

def exception_handler_middleware(app):
    def middleware(environ, start_response):
        try:
            return app(environ, start_response)
        except LogicalError as e:
            # TODO: Add proper logging
            print(f"LogicalError: {e}")
            response = jsonify({"error": "Logical error occurred"})
            response.status_code = 500
            return response(environ, start_response)
        except (FileNotFoundError, IOError) as e:
            print(f"File error: {e}")
            response = jsonify({"error": "File not found or IO error occurred"})
            response.status_code = 500
            return response(environ, start_response)
    return middleware

