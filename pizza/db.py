import functools
import os
from contextlib import contextmanager
from typing import Iterator

import sqlalchemy.engine
import sqlalchemy.orm
from sqlalchemy import create_engine


@functools.cache
def get_engine(
    *, pool_size=None, max_overflow=None, **kwargs
) -> sqlalchemy.engine.Engine:
    return create_engine(
        os.environ["DATABASE_URL"],
        **kwargs,
    )


def create_session(**kwargs) -> sqlalchemy.orm.Session:
    return sqlalchemy.orm.Session(bind=get_engine(), **kwargs)


@contextmanager
def session(**kwargs) -> Iterator[sqlalchemy.orm.Session]:
    session = create_session()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
