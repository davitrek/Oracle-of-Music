from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
#from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# initialise connection to database
#engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, echo=True)


# -- For SQLite only --

# # ensure SQLite DB connection enforces foreign keys
# def _fk_pragma_on_connect(dbapi_con, con_record):
#     dbapi_con.execute('pragma foreign_keys=ON')

# from sqlalchemy import event
# event.listen(engine, 'connect', _fk_pragma_on_connect)


# -- --------------- --
#from config import Base
# create tables if they don't exist
#Base.metadata.create_all(engine)

# "this should be the first place where you import anything from mbdata" - from docs
# -> but this is assuming I'm using the mbdata.models directly
# --->because I'm self-defining models in my models.py based on my own Base class,
#     providing my Base class to mbdata.models isn't actually a concern
#import mbdata.config
#mbdata.config.configure(base_class=Base)
