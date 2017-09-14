import os
from datetime import datetime, timedelta, date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base


engine = create_engine(
    os.environ.get(
        'DB_URI',
        'sqlite:///test.db'
    ),
    convert_unicode=True
)

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    """
    Create the SQL database. Called from the shell
    """
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    from app.models import User, Diary  # noqa
    Base.metadata.create_all(bind=engine)


def destroy_db():
    """
    Destroy the SQL database. Called from the shell
    """
    from app.models import User, Diary  # noqa
    Base.metadata.drop_all(bind=engine)


def fixtures():
    from app.models import User, Diary  # noqa

    users = [
        User() for _ in range(10)
    ]

    db_session.add_all(users)

    for i in range(5):
        diary = Diary(
            id=i,
            user_id=i,
            date=date.today() + timedelta(days=i),
            time_into_bed=datetime.now(),
            time_out_of_bed=datetime.now() + timedelta(hours=1),
            sleep_quality=9,
        )

        db_session.add(diary)

    db_session.commit()
