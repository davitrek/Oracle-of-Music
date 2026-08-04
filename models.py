# I can have my own models here if I want, and they *should* work with the
#   MBDB tables because of lines 17-20 in db.py

# copy-pasted (with own additions)
from sqlalchemy import Column, Index, Integer, String, Text, ForeignKey, Boolean, DateTime, Time, Date, Enum, Interval, CHAR, CheckConstraint, sql, Table, create_engine
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, composite, backref, DeclarativeBase, Mapped, mapped_column
from mbdata.types import PartialDate, Point, Cube as _Cube, regexp, UUID, SMALLINT, BIGINT, JSONB
from typing import Any, Union, List

from db import db

#from mbdata.models import apply_schema

class ArtistAdjacents(db.Model):
    #__tablename__ = 'artist_adjacents'
    # Mapped[xyz] can be omitted        mapped_column can be omitted -> type and attributes will be inferred
    artist0_id: Mapped[int]              = mapped_column(primary_key = True)
    artist1_id: Mapped[int]              = mapped_column(primary_key = True)
    
    
# track_artists = Table(
#     #'track_artists',
#     db.Model.metadata,
#     Column('track_id', ForeignKey('tracks.id'), primary_key=True),  # will create compound (i.e., multi-column) key
#     Column('artist_id', ForeignKey('artists.id'), primary_key=True),# will create compound (i.e., multi-column) key
# )


# album_artists = Table(
#     'album_artists',
#     db.Model.metadata,
#     Column('album_id', ForeignKey('albums.id'), primary_key=True),  # will create compound (i.e., multi-column) key
#     Column('artist_id', ForeignKey('artists.id'), primary_key=True),# will create compound (i.e., multi-column) key
# )


# # See https://docs.sqlalchemy.org/en/20/core/types.html for a list of types and mappings to SQL
# class Artists(db.Model):
#     __tablename__ = 'artists'
#     # Mapped[xyz] can be omitted        mapped_column can be omitted -> type and attributes will be inferred
#     id: Mapped[int]                     = mapped_column(primary_key=True)
#     spotify_id: Mapped[str | None]      = mapped_column(Text, unique=True)
#     artist_name: Mapped[str]            = mapped_column(Text) #lack of Optional[str] implies nullable=False
    
#     # many-to-many
#     albums: Mapped[List['Albums']]      = relationship(secondary=album_artists, back_populates='artists')

#     # many-to-many
#     tracks: Mapped[List['Tracks']]      = relationship(secondary=track_artists, back_populates='artists')
    
#     # not necessary, but ensures nice printing of class details
#     #   otherwise, trying to print thisclass will result in <__main__.artists at 0x...>
#     def __repr__(self) -> str:
#         return f'Artists(id={self.id!r}, spotify_id={self.spotify_id!r}, artist_name={self.artist_name!r})'


# class Albums(db.model):
#     __tablename__ = 'albums'

#     id: Mapped[int]                     = mapped_column(primary_key=True)
#     spotify_id: Mapped[str | None]      = mapped_column(Text, unique=True)
#     album_name: Mapped[str]             = mapped_column(Text)
    
#     # one-to-many https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
#     # can use <objectname>.tracks.append(<objectname of type Tracks>) to relate them
#     tracks: Mapped[List["Tracks"]]      = relationship(back_populates='album')

#     # many-to-many
#     artists: Mapped[List[Artists]]      = relationship(secondary=album_artists, back_populates='albums')

#     def __repr__(self) -> str:
#         return f'Albums(id={self.id!r}, spotify_id={self.spotify_id!r}, album_name={self.album_name!r})'


# class Tracks(db.model):
#     __tablename__ = 'tracks'

#     id: Mapped[int]                     = mapped_column(primary_key=True)
#     spotify_id: Mapped[str | None]      = mapped_column(Text, unique=True)
#     track_name: Mapped[str]             = mapped_column(Text)
    
#     # many-to-one https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
#     # can use <objectname of type Tracks>.album = <objectname of type Albums> to relate them
#     album_id                            = mapped_column(ForeignKey('albums.id'))
#     album: Mapped['Albums']             = relationship(back_populates='tracks')

#     # many-to-many https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html
#     artists: Mapped[List[Artists]]      = relationship(secondary=track_artists, back_populates='tracks')

#     def __repr__(self) -> str:
#         return f'Tracks(id={self.id!r},spotify_id={self.spotify_id!r}, track_name={self.track_name!r}, album_id={self.album_id!r})'


# From mbdata module, modified
# TODO: replace 'apply_schema' below with 'musicbrainz.<first argument>'
#       this function just replaces the 'musicbrainz' in that string with another
#       schema name, based on a dictionary elsewhere
#       -> wholly unnecessary for my purposes

class Artist(db.Model):
    __tablename__ = 'artist'
    __table_args__ = (
        Index('artist_idx_gid', 'gid', unique=True),
        Index('artist_idx_name', 'name'),
        Index('artist_idx_sort_name', 'sort_name'),
        Index('artist_idx_area', 'area'),
        Index('artist_idx_begin_area', 'begin_area'),
        Index('artist_idx_end_area', 'end_area'),
        Index('artist_idx_null_comment', 'name', unique=True),
        Index('artist_idx_uniq_name_comment', 'name', 'comment', unique=True),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    gid = Column(UUID, nullable=False)
    name = Column(String, nullable=False)
    sort_name = Column(String, nullable=False)
    begin_date_year = Column(SMALLINT)
    begin_date_month = Column(SMALLINT)
    begin_date_day = Column(SMALLINT)
    end_date_year = Column(SMALLINT)
    end_date_month = Column(SMALLINT)
    end_date_day = Column(SMALLINT)
    #type_id = Column('type', Integer, ForeignKey(apply_schema('artist_type.id', 'musicbrainz'), name='artist_fk_type'))
    area_id = Column('area', Integer)
    #area_id = Column('area', Integer, ForeignKey(apply_schema('area.id', 'musicbrainz'), name='artist_fk_area'))
    #gender_id = Column('gender', Integer, ForeignKey(apply_schema('gender.id', 'musicbrainz'), name='artist_fk_gender'))
    comment = Column(String(255), nullable=False, default='', server_default=sql.text("''"))
    #edits_pending = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    #last_updated = Column(DateTime(timezone=True), server_default=sql.func.now())
    ended = Column(Boolean, nullable=False, default=False, server_default=sql.false())
    begin_area_id = Column('begin_area', Integer)
    #begin_area_id = Column('begin_area', Integer, ForeignKey(apply_schema('area.id', 'musicbrainz'), name='artist_fk_begin_area'))
    end_area_id = Column('end_area', Integer)
    #end_area_id = Column('end_area', Integer, ForeignKey(apply_schema('area.id', 'musicbrainz'), name='artist_fk_end_area'))

    #type = relationship('ArtistType', foreign_keys=[type_id])
    #area = relationship('Area', foreign_keys=[area_id])
    #gender = relationship('Gender', foreign_keys=[gender_id])
    #begin_area = relationship('Area', foreign_keys=[begin_area_id])
    #end_area = relationship('Area', foreign_keys=[end_area_id])

    begin_date = composite(PartialDate, begin_date_year, begin_date_month, begin_date_day)
    end_date = composite(PartialDate, end_date_year, end_date_month, end_date_day)

    # DT additions
    # innerjoin=True only works for many-to-one (child has many parents)
    #linked_records: Mapped[List['LinkArtistRecording']] = relationship(viewonly=True) # not that useful: only refers to prod credits, etc
    #aliases: Mapped[List['ArtistAlias']] = relationship()
    #                     local column name               what it's a foreign key to    name of constraint
    #link_type_id = Column('link_type', Integer, ForeignKey('musicbrainz.link_type.id', name='link_fk_link_type'), nullable=False)
    
    #                       Related class           foreign key that joins them   V- is faster but only works for one-to-one or many-to-one  
    #link_type = relationship('LinkType', foreign_keys=[link_type_id], innerjoin=True)

    
class ArtistAlias(db.Model):
    __tablename__ = 'artist_alias'
    __table_args__ = (
        Index('artist_alias_idx_artist', 'artist'),
        Index('artist_alias_idx_primary', 'artist', 'locale', unique=True),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    artist_id = Column('artist', Integer, ForeignKey('musicbrainz.artist.id', name='artist_alias_fk_artist'), nullable=False)
    #artist_id = Column('artist', Integer, ForeignKey(apply_schema('artist.id', 'musicbrainz'), name='artist_alias_fk_artist'), nullable=False)
    name = Column(String, nullable=False)
    locale = Column(String)
    #edits_pending = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    #last_updated = Column(DateTime(timezone=True), server_default=sql.func.now())
    #type_id = Column('type', Integer, ForeignKey(apply_schema('artist_alias_type.id', 'musicbrainz'), name='artist_alias_fk_type'))
    sort_name = Column(String, nullable=False)
    begin_date_year = Column(SMALLINT)
    begin_date_month = Column(SMALLINT)
    begin_date_day = Column(SMALLINT)
    end_date_year = Column(SMALLINT)
    end_date_month = Column(SMALLINT)
    end_date_day = Column(SMALLINT)
    primary_for_locale = Column(Boolean, nullable=False, default=False, server_default=sql.false())
    ended = Column(Boolean, nullable=False, default=False, server_default=sql.false())

    artist = relationship('Artist', foreign_keys=[artist_id], innerjoin=True)
    #type = relationship('ArtistAliasType', foreign_keys=[type_id])

    begin_date = composite(PartialDate, begin_date_year, begin_date_month, begin_date_day)
    end_date = composite(PartialDate, end_date_year, end_date_month, end_date_day)

    
class Recording(db.Model):
    __tablename__ = 'recording'
    __table_args__ = (
        Index('recording_idx_gid', 'gid', unique=True),
        Index('recording_idx_name', 'name'),
        Index('recording_idx_artist_credit', 'artist_credit'),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    gid = Column(UUID, nullable=False)
    name = Column(String, nullable=False)
    artist_credit_id = Column('artist_credit', Integer, ForeignKey('musicbrainz.artist_credit.id', name='recording_fk_artist_credit'), nullable=False)
    #artist_credit_id = Column('artist_credit', Integer, ForeignKey(apply_schema('artist_credit.id', 'musicbrainz'), name='recording_fk_artist_credit'), nullable=False)
    length = Column(Integer)
    comment = Column(String(255), nullable=False, default='', server_default=sql.text("''"))
    #edits_pending = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    #last_updated = Column(DateTime(timezone=True), server_default=sql.func.now())
    video = Column(Boolean, nullable=False, default=False, server_default=sql.false())

    artist_credit = relationship('ArtistCredit', foreign_keys=[artist_credit_id], innerjoin=True)
    
    # DT additions

    #                     local column name               what it's a foreign key to    name of constraint
    #link_type_id = Column('link_type', Integer, ForeignKey('musicbrainz.link_type.id', name='link_fk_link_type'), nullable=False)
    
    #                       Related class           foreign key that joins them   V- is faster but only works for one-to-one or many-to-one  
    #link_type = relationship('LinkType', foreign_keys=[link_type_id], innerjoin=True)
    
    
class LinkArtistRecording(db.Model):
    __tablename__ = 'l_artist_recording'
    __table_args__ = (
        Index('l_artist_recording_idx_uniq', 'entity0', 'entity1', 'link', 'link_order', unique=True),
        Index('l_artist_recording_idx_entity1', 'entity1'),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    link_id = Column('link', Integer, ForeignKey('musicbrainz.link.id', name='l_artist_recording_fk_link'), nullable=False)
    #link_id = Column('link', Integer, ForeignKey(apply_schema('link.id', 'musicbrainz'), name='l_artist_recording_fk_link'), nullable=False)
    entity0_id = Column('entity0', Integer, ForeignKey('musicbrainz.artist.id', name='l_artist_recording_fk_entity0'), nullable=False)
    #entity0_id = Column('entity0', Integer, ForeignKey(apply_schema('artist.id', 'musicbrainz'), name='l_artist_recording_fk_entity0'), nullable=False)
    entity1_id = Column('entity1', Integer, ForeignKey('musicbrainz.recording.id', name='l_artist_recording_fk_entity1'), nullable=False)
    #entity1_id = Column('entity1', Integer, ForeignKey(apply_schema('recording.id', 'musicbrainz'), name='l_artist_recording_fk_entity1'), nullable=False)
    #edits_pending = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    #last_updated = Column(DateTime(timezone=True), server_default=sql.func.now())
    link_order = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    entity0_credit = Column(String, nullable=False, default='', server_default=sql.text("''"))
    entity1_credit = Column(String, nullable=False, default='', server_default=sql.text("''"))

    link = relationship('Link', foreign_keys=[link_id], innerjoin=True)
    entity0 = relationship('Artist', foreign_keys=[entity0_id], innerjoin=True)
    entity1 = relationship('Recording', foreign_keys=[entity1_id], innerjoin=True)

    @hybrid_property
    def artist(self):
        return self.entity0

    @hybrid_property
    def artist_id(self):
        return self.entity0_id

    @hybrid_property
    def recording(self):
        return self.entity1

    @hybrid_property
    def recording_id(self):
        return self.entity1_id

    # DT additions:
    #recording: Mapped['Recording'] = relationship()


class LinkArtistArtist(db.Model):
    __tablename__ = 'l_artist_artist'
    __table_args__ = (
        Index('l_artist_artist_idx_uniq', 'entity0', 'entity1', 'link', 'link_order', unique=True),
        Index('l_artist_artist_idx_entity1', 'entity1'),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    link_id = Column('link', Integer, ForeignKey('musicbrainz.link.id', name='l_artist_artist_fk_link'), nullable=False)
    #link_id = Column('link', Integer, ForeignKey(apply_schema('link.id', 'musicbrainz'), name='l_artist_artist_fk_link'), nullable=False)
    entity0_id = Column('entity0', Integer, ForeignKey('musicbrainz.artist.id', name='l_artist_artist_fk_entity0'), nullable=False)
    #entity0_id = Column('entity0', Integer, ForeignKey(apply_schema('artist.id', 'musicbrainz'), name='l_artist_artist_fk_entity0'), nullable=False)
    entity1_id = Column('entity1', Integer, ForeignKey('musicbrainz.artist.id', name='l_artist_artist_fk_entity1'), nullable=False)
    #entity1_id = Column('entity1', Integer, ForeignKey(apply_schema('artist.id', 'musicbrainz'), name='l_artist_artist_fk_entity1'), nullable=False)
    #edits_pending = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    #last_updated = Column(DateTime(timezone=True), server_default=sql.func.now())
    link_order = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    entity0_credit = Column(String, nullable=False, default='', server_default=sql.text("''"))
    entity1_credit = Column(String, nullable=False, default='', server_default=sql.text("''"))

    link = relationship('Link', foreign_keys=[link_id], innerjoin=True)
    entity0 = relationship('Artist', foreign_keys=[entity0_id], innerjoin=True)
    entity1 = relationship('Artist', foreign_keys=[entity1_id], innerjoin=True)

    @hybrid_property
    def artist0(self):
        return self.entity0

    @hybrid_property
    def artist0_id(self):
        return self.entity0_id

    @hybrid_property
    def artist1(self):
        return self.entity1

    @hybrid_property
    def artist1_id(self):
        return self.entity1_id

    
class LinkType(db.Model):
    __tablename__ = 'link_type'
    __table_args__ = (
        Index('link_type_idx_gid', 'gid', unique=True),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    parent_id = Column('parent', Integer, ForeignKey('musicbrainz.link_type.id', name='link_type_fk_parent'))
    #parent_id = Column('parent', Integer, ForeignKey(apply_schema('link_type.id', 'musicbrainz'), name='link_type_fk_parent'))
    child_order = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    gid = Column(UUID, nullable=False)
    entity_type0 = Column(String(50), nullable=False)
    entity_type1 = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String)
    link_phrase = Column(String(255), nullable=False)
    reverse_link_phrase = Column(String(255), nullable=False)
    long_link_phrase = Column(String(255), nullable=False)
    #last_updated = Column(DateTime(timezone=True), server_default=sql.func.now())
    is_deprecated = Column(Boolean, nullable=False, default=False, server_default=sql.false())
    has_dates = Column(Boolean, nullable=False, default=True, server_default=sql.true())
    entity0_cardinality = Column(SMALLINT, nullable=False, default=0, server_default=sql.text('0'))
    entity1_cardinality = Column(SMALLINT, nullable=False, default=0, server_default=sql.text('0'))

    parent = relationship('LinkType', foreign_keys=[parent_id])


class Link(db.Model):
    __tablename__ = 'link'
    __table_args__ = (
        Index('link_idx_type_attr', 'link_type', 'attribute_count'),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    link_type_id = Column('link_type', Integer, ForeignKey('musicbrainz.link_type.id', name='link_fk_link_type'), nullable=False)
    #link_type_id = Column('link_type', Integer, ForeignKey(apply_schema('link_type.id', 'musicbrainz'), name='link_fk_link_type'), nullable=False)
    begin_date_year = Column(SMALLINT)
    begin_date_month = Column(SMALLINT)
    begin_date_day = Column(SMALLINT)
    end_date_year = Column(SMALLINT)
    end_date_month = Column(SMALLINT)
    end_date_day = Column(SMALLINT)
    attribute_count = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    created = Column(DateTime(timezone=True), server_default=sql.func.now())
    ended = Column(Boolean, nullable=False, default=False, server_default=sql.false())

    link_type = relationship('LinkType', foreign_keys=[link_type_id], innerjoin=True)

    begin_date = composite(PartialDate, begin_date_year, begin_date_month, begin_date_day)
    end_date = composite(PartialDate, end_date_year, end_date_month, end_date_day)


class ArtistCredit(db.Model):
    __tablename__ = 'artist_credit'
    __table_args__ = (
        Index('artist_credit_idx_gid', 'gid', unique=True),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    artist_count = Column(SMALLINT, nullable=False)
    ref_count = Column(Integer, default=0, server_default=sql.text('0'))
    created = Column(DateTime(timezone=True), server_default=sql.func.now())
    edits_pending = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    gid = Column(UUID, nullable=False)

    # DT additions
    #artist_credit_names: Mapped[List['ArtistCreditName']] = relationship(viewonly=True)


class ArtistCreditName(db.Model):
    __tablename__ = 'artist_credit_name'
    __table_args__ = (
        Index('artist_credit_name_idx_artist', 'artist'),
        {'schema': 'musicbrainz'}
    )

    artist_credit_id = Column('artist_credit', Integer, ForeignKey('musicbrainz.artist_credit.id', name='artist_credit_name_fk_artist_credit', ondelete='CASCADE'), nullable=False, primary_key=True)
    #artist_credit_id = Column('artist_credit', Integer, ForeignKey(apply_schema('artist_credit.id', 'musicbrainz'), name='artist_credit_name_fk_artist_credit', ondelete='CASCADE'), nullable=False, primary_key=True)
    position = Column(SMALLINT, nullable=False, primary_key=True)
    artist_id = Column('artist', Integer, ForeignKey('musicbrainz.artist.id', name='artist_credit_name_fk_artist', ondelete='CASCADE'), nullable=False)
    #artist_id = Column('artist', Integer, ForeignKey(apply_schema('artist.id', 'musicbrainz'), name='artist_credit_name_fk_artist', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    join_phrase = Column(String, nullable=False, default='', server_default=sql.text("''"))

    artist_credit = relationship('ArtistCredit', foreign_keys=[artist_credit_id], innerjoin=True, backref=backref('artists', order_by="ArtistCreditName.position"))
    artist = relationship('Artist', foreign_keys=[artist_id], innerjoin=True)


class Track(db.Model):
    __tablename__ = 'track'
    __table_args__ = (
        Index('track_idx_gid', 'gid', unique=True),
        Index('track_idx_recording', 'recording'),
        Index('track_idx_artist_credit', 'artist_credit'),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    gid = Column(UUID, nullable=False)
    recording_id = Column('recording', Integer, ForeignKey('musicbrainz.recording.id', name='track_fk_recording'), nullable=False)
    #recording_id = Column('recording', Integer, ForeignKey(apply_schema('recording.id', 'musicbrainz'), name='track_fk_recording'), nullable=False)
    medium_id = Column('medium', Integer, ForeignKey('musicbrainz.medium.id', name='track_fk_medium'), nullable=False)
    #medium_id = Column('medium', Integer, ForeignKey(apply_schema('medium.id', 'musicbrainz'), name='track_fk_medium'), nullable=False)
    position = Column(Integer, nullable=False)
    number = Column(String, nullable=False)
    name = Column(String, nullable=False)
    artist_credit_id = Column('artist_credit', Integer, ForeignKey('musicbrainz.artist_credit.id', name='track_fk_artist_credit'), nullable=False)
    #artist_credit_id = Column('artist_credit', Integer, ForeignKey(apply_schema('artist_credit.id', 'musicbrainz'), name='track_fk_artist_credit'), nullable=False)
    length = Column(Integer)
    #edits_pending = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    #last_updated = Column(DateTime(timezone=True), server_default=sql.func.now())
    is_data_track = Column(Boolean, nullable=False, default=False, server_default=sql.false())

    recording = relationship('Recording', foreign_keys=[recording_id], innerjoin=True, backref=backref('tracks'))
    medium = relationship('Medium', foreign_keys=[medium_id], innerjoin=True, backref=backref('tracks', order_by="Track.position"))
    artist_credit = relationship('ArtistCredit', foreign_keys=[artist_credit_id], innerjoin=True)

class Medium(db.Model):
    __tablename__ = 'medium'
    __table_args__ = (
        Index('medium_idx_gid', 'gid', unique=True),
        Index('medium_idx_track_count', 'track_count'),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    release_id = Column('release', Integer, ForeignKey('musicbrainz.release.id', name='medium_fk_release'), nullable=False)
    #release_id = Column('release', Integer, ForeignKey(apply_schema('release.id', 'musicbrainz'), name='medium_fk_release'), nullable=False)
    position = Column(Integer, nullable=False)
    #format_id = Column('format', Integer, ForeignKey('musicbrainz.medium_format.id', name='medium_fk_format'))
    #format_id = Column('format', Integer, ForeignKey(apply_schema('medium_format.id', 'musicbrainz'), name='medium_fk_format'))
    name = Column(String, nullable=False, default='', server_default=sql.text("''"))
    #edits_pending = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    #last_updated = Column(DateTime(timezone=True), server_default=sql.func.now())
    track_count = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    gid = Column(UUID, nullable=False)

    release = relationship('Release', foreign_keys=[release_id], innerjoin=True, backref=backref('mediums', order_by="Medium.position"))
    #format = relationship('MediumFormat', foreign_keys=[format_id])

class ReleaseGroup(db.Model):
    __tablename__ = 'release_group'
    __table_args__ = (
        Index('release_group_idx_gid', 'gid', unique=True),
        Index('release_group_idx_name', 'name'),
        Index('release_group_idx_artist_credit', 'artist_credit'),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    gid = Column(UUID, nullable=False)
    name = Column(String, nullable=False)
    artist_credit_id = Column('artist_credit', Integer, ForeignKey('musicbrainz.artist_credit.id', name='release_group_fk_artist_credit'), nullable=False)
    #artist_credit_id = Column('artist_credit', Integer, ForeignKey(apply_schema('artist_credit.id', 'musicbrainz'), name='release_group_fk_artist_credit'), nullable=False)
    type_id = Column('type', Integer, ForeignKey('musicbrainz.release_group_primary_type.id', name='release_group_fk_type'))
    #type_id = Column('type', Integer, ForeignKey(apply_schema('release_group_primary_type.id', 'musicbrainz'), name='release_group_fk_type'))
    comment = Column(String(255), nullable=False, default='', server_default=sql.text("''"))
    edits_pending = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    last_updated = Column(DateTime(timezone=True), server_default=sql.func.now())

    artist_credit = relationship('ArtistCredit', foreign_keys=[artist_credit_id], innerjoin=True)
    type = relationship('ReleaseGroupPrimaryType', foreign_keys=[type_id])


class ReleaseGroupPrimaryType(db.Model):
    __tablename__ = 'release_group_primary_type'
    __table_args__ = (
        Index('release_group_primary_type_idx_gid', 'gid', unique=True),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    parent_id = Column('parent', Integer, ForeignKey('musicbrainz.release_group_primary_type.id', name='release_group_primary_type_fk_parent'))
    #parent_id = Column('parent', Integer, ForeignKey(apply_schema('release_group_primary_type.id', 'musicbrainz'), name='release_group_primary_type_fk_parent'))
    child_order = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    description = Column(String)
    gid = Column(UUID, nullable=False)

    parent = relationship('ReleaseGroupPrimaryType', foreign_keys=[parent_id])


class ReleaseStatus(db.Model):
    __tablename__ = 'release_status'
    __table_args__ = (
        Index('release_status_idx_gid', 'gid', unique=True),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    parent_id = Column('parent', Integer, ForeignKey('musicbrainz.release_status.id', name='release_status_fk_parent'))
    #parent_id = Column('parent', Integer, ForeignKey(apply_schema('release_status.id', 'musicbrainz'), name='release_status_fk_parent'))
    child_order = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    description = Column(String)
    gid = Column(UUID, nullable=False)

    parent = relationship('ReleaseStatus', foreign_keys=[parent_id])


class Release(db.Model):
    __tablename__ = 'release'
    __table_args__ = (
        Index('release_idx_gid', 'gid', unique=True),
        Index('release_idx_name', 'name'),
        Index('release_idx_release_group', 'release_group'),
        Index('release_idx_artist_credit', 'artist_credit'),
        {'schema': 'musicbrainz'}
    )

    id = Column(Integer, primary_key=True)
    gid = Column(UUID, nullable=False)
    name = Column(String, nullable=False)
    artist_credit_id = Column('artist_credit', Integer, ForeignKey('musicbrainz.artist_credit.id', name='release_fk_artist_credit'), nullable=False)
    #artist_credit_id = Column('artist_credit', Integer, ForeignKey(apply_schema('artist_credit.id', 'musicbrainz'), name='release_fk_artist_credit'), nullable=False)
    release_group_id = Column('release_group', Integer, ForeignKey('musicbrainz.release_group.id', name='release_fk_release_group'), nullable=False)
    #release_group_id = Column('release_group', Integer, ForeignKey(apply_schema('release_group.id', 'musicbrainz'), name='release_fk_release_group'), nullable=False)
    status_id = Column('status', Integer, ForeignKey('musicbrainz.release_status.id', name='release_fk_status'))
    #status_id = Column('status', Integer, ForeignKey(apply_schema('release_status.id', 'musicbrainz'), name='release_fk_status'))
    packaging_id = Column('packaging', Integer, ForeignKey('musicbrainz.release_packaging.id', name='release_fk_packaging'))
    #packaging_id = Column('packaging', Integer, ForeignKey(apply_schema('release_packaging.id', 'musicbrainz'), name='release_fk_packaging'))
    language_id = Column('language', Integer, ForeignKey('musicbrainz.language.id', name='release_fk_language'))
    #language_id = Column('language', Integer, ForeignKey(apply_schema('language.id', 'musicbrainz'), name='release_fk_language'))
    script_id = Column('script', Integer, ForeignKey('musicbrainz.script.id', name='release_fk_script'))
    #script_id = Column('script', Integer, ForeignKey(apply_schema('script.id', 'musicbrainz'), name='release_fk_script'))
    barcode = Column(String(255))
    comment = Column(String(255), nullable=False, default='', server_default=sql.text("''"))
    edits_pending = Column(Integer, nullable=False, default=0, server_default=sql.text('0'))
    quality = Column(SMALLINT, nullable=False, default=-1, server_default=sql.text('-1'))
    last_updated = Column(DateTime(timezone=True), server_default=sql.func.now())

    artist_credit = relationship('ArtistCredit', foreign_keys=[artist_credit_id], innerjoin=True)
    release_group = relationship('ReleaseGroup', foreign_keys=[release_group_id], innerjoin=True)
    status = relationship('ReleaseStatus', foreign_keys=[status_id])
    #packaging = relationship('ReleasePackaging', foreign_keys=[packaging_id])
    #language = relationship('Language', foreign_keys=[language_id])
    #script = relationship('Script', foreign_keys=[script_id])
