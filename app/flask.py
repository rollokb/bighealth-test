from flask import Flask

from app.views import diary
from app.db import db_session


class APIException(Exception):

    def __init__(self, message=None, status_code=400, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


def create_app():
    app = Flask(__name__)
    app.register_blueprint(diary)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        # Remove the session
        # Note the model I've chosen of using a scoped session
        # relies on implicitly creating a session per thread
        # this will not work if I was to use greenthreads.
        db_session.remove()

    return app

app = create_app()
