import os
import sys
from pathlib import Path

import pytest

# app modules import each other by bare name (e.g. `import globals`)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

# placeholder config so importing the app needs neither a .env nor a database;
# set before config.py runs load_dotenv(), which does not override existing vars
os.environ.setdefault("ARTISTS_TO_LOAD", "0")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SPOTIFY_CLIENT_ID", "test")
os.environ.setdefault("SPOTIFY_CLIENT_SECRET", "test")
os.environ.setdefault("ARTIST_NAMES_FILE_PATH", "/dev/null")


class _FakeTokenResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"access_token": "test", "expires_in": 3600}


def _import_app():
    # importing the app requests a Spotify access token and builds the
    # adjacency list from the database, so stub both for the import
    import requests

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(requests, "post", lambda *a, **kw: _FakeTokenResponse())

        from graph import adjacency_list

        mp.setattr(adjacency_list, "build_adjacency_list", lambda count: {})

        from app import app

    return app


flask_app = _import_app()


@pytest.fixture
def client():
    return flask_app.test_client()
