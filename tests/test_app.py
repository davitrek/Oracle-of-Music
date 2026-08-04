from db import db
from sqlalchemy.orm import Session
from sqlalchemy import event

import pytest

from models import ArtistCreditName, Track
from sqlalchemy import select
import random

from adjacency_list import create_adjacency_list

from flask import Flask

from config import Config

class TestApp():
    def setup_method(self, method):
        # create the app
        self.app = Flask(__name__)
        # configure the SQLite database, relative to the app instance folder
        self.app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI
        self.app.config["SQLALCHEMY_ECHO"] = True
        self.app.config["TESTING"] = True
        # initialize the app with Flask-SQLAlchemy extension
        db.init_app(self.app)

        # set app context for testing
        self.app_context = self.app.app_context()
        self.app_context.push()

        # # connect to the database
        self.connection = db.engine.connect()
        # # begin a non-ORM transaction
        self.trans = db.engine.begin()
        # bind an individual Session to the connection
        self.session = db.session(bind=self.connection)
        # self.session = Session(bind=self.connection)

        # starting a savepoint will allow tests to also
        # use rollback within tests
        self.nested = self.connection.begin_nested()

        @event.listens_for(self.session, "after_transaction_end")
        def end_savepoint(session, transaction):
            if not self.nested.is_active:
                self.nested = self.connection.begin_nested()

    # try 10 random entries in adjacency list and see if I can find record entries of them
    #   as a mini-test
    def test_adjacency_list(self):
        adj = create_adjacency_list(20)

        artists_to_check = set()
        while len(artists_to_check) < 10:
            artists_to_check.add(random.randrange(len(adj)))

        i = 0
        for artist, collaborators in adj.items():
            if i in artists_to_check:
                collabs_to_check = set()
                while len(collabs_to_check) < 10:
                    collabs_to_check.add(random.randrange(len(adj)))

                for j, collab in enumerate(adj[artist]):
                    if j in collabs_to_check:
                        sub_stmt_collab = (
                            select(ArtistCreditName.artist_credit_id)
                            .where(ArtistCreditName.artist_id == collab)
                        )
                        sub_stmt_main = (
                            select(ArtistCreditName.artist_credit_id)
                            .where(ArtistCreditName.artist_id == artist)
                        )
                        stmt = (
                            select(Track)
                            .where(Track.artist_credit_id.in_(sub_stmt_collab))
                            .where(Track.artist_credit_id.in_(sub_stmt_main))
                        )

                        t = self.session.execute(stmt).scalars().all()
                        assert len(t) > 0

            i = i + 1


    def teardown_method(self):
        # close app contex
        self.app_context.pop()
        # close session
        self.session.close()

        # rollback - everything that happened with the
        # Session above (including calls to commit())
        # is rolled back.
        self.trans.rollback()

        # return connection to the Engine
        self.connection.close()
