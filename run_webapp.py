#!/usr/bin/env python

import os

from app.flask import app
from app.db import init_db, fixtures

if __name__ == '__main__':

    if not os.path.exists('./test.db'):
        init_db()
        fixtures()

    app.run(port=5000, host='0.0.0.0')
