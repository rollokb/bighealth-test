import pytest
import json

from flask import Response
from flask.testing import FlaskClient

from app.db import db_session, init_db, destroy_db, Base
from app.flask import create_app


class TestClient(FlaskClient):
    def open(self, *args, **kwargs):
        if 'content_type' not in kwargs:
            kwargs['content_type'] = 'application/json'

        if 'json' in kwargs:
            kwargs['data'] = json.dumps(kwargs.pop('json'))

        return super(TestClient, self).open(*args, **kwargs)


class TestResponse(Response):
    """
    Force response to be json
    """
    @property
    def json(self):
        return json.loads(self.data.decode('utf-8'))


@pytest.fixture(scope='session')
def tables():
    destroy_db()
    init_db()
    yield


@pytest.fixture
def session(tables):
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()

    yield db_session

    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
    db_session.remove()


@pytest.fixture
def app(tables):
    app = create_app()
    app.response_class = TestResponse
    app.test_client_class = TestClient
    app.testing = True
    return app


@pytest.fixture
def client(app, session):
    return app.test_client()
