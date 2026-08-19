# Adapted from [1] to work with MusicBrainz Postgres database

# [1]: https://github.com/metabrainz/mbdata/tree/main

from db import db
from mbdata.types import (
    SMALLINT,
    UUID,
    PartialDate,
)
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    sql,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    Mapped,
    backref,
    composite,
    mapped_column,
    relationship,
)


class ArtistAdjacents(db.Model):
    __tablename__ = "artist_adjacents"
    artist0_id: Mapped[int] = mapped_column(primary_key=True)
    artist1_id: Mapped[int] = mapped_column(primary_key=True)


class Artist(db.Model):
    __tablename__ = "artist"
    __table_args__ = (
        Index("artist_idx_gid", "gid", unique=True),
        Index("artist_idx_name", "name"),
        Index("artist_idx_sort_name", "sort_name"),
        Index("artist_idx_area", "area"),
        Index("artist_idx_begin_area", "begin_area"),
        Index("artist_idx_end_area", "end_area"),
        Index("artist_idx_null_comment", "name", unique=True),
        Index("artist_idx_uniq_name_comment", "name", "comment", unique=True),
        {"schema": "musicbrainz"},
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
    area_id = Column("area", Integer)
    comment = Column(
        String(255), nullable=False, default="", server_default=sql.text("''")
    )
    ended = Column(
        Boolean, nullable=False, default=False, server_default=sql.false()
    )
    begin_area_id = Column("begin_area", Integer)
    end_area_id = Column("end_area", Integer)

    begin_date = composite(
        PartialDate, begin_date_year, begin_date_month, begin_date_day
    )
    end_date = composite(
        PartialDate, end_date_year, end_date_month, end_date_day
    )


class ArtistAlias(db.Model):
    __tablename__ = "artist_alias"
    __table_args__ = (
        Index("artist_alias_idx_artist", "artist"),
        Index("artist_alias_idx_primary", "artist", "locale", unique=True),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    artist_id = Column(
        "artist",
        Integer,
        ForeignKey("musicbrainz.artist.id", name="artist_alias_fk_artist"),
        nullable=False,
    )
    name = Column(String, nullable=False)
    locale = Column(String)
    sort_name = Column(String, nullable=False)
    begin_date_year = Column(SMALLINT)
    begin_date_month = Column(SMALLINT)
    begin_date_day = Column(SMALLINT)
    end_date_year = Column(SMALLINT)
    end_date_month = Column(SMALLINT)
    end_date_day = Column(SMALLINT)
    primary_for_locale = Column(
        Boolean, nullable=False, default=False, server_default=sql.false()
    )
    ended = Column(
        Boolean, nullable=False, default=False, server_default=sql.false()
    )

    artist = relationship("Artist", foreign_keys=[artist_id], innerjoin=True)

    begin_date = composite(
        PartialDate, begin_date_year, begin_date_month, begin_date_day
    )
    end_date = composite(
        PartialDate, end_date_year, end_date_month, end_date_day
    )


class Recording(db.Model):
    __tablename__ = "recording"
    __table_args__ = (
        Index("recording_idx_gid", "gid", unique=True),
        Index("recording_idx_name", "name"),
        Index("recording_idx_artist_credit", "artist_credit"),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    gid = Column(UUID, nullable=False)
    name = Column(String, nullable=False)
    artist_credit_id = Column(
        "artist_credit",
        Integer,
        ForeignKey(
            "musicbrainz.artist_credit.id", name="recording_fk_artist_credit"
        ),
        nullable=False,
    )
    length = Column(Integer)
    comment = Column(
        String(255), nullable=False, default="", server_default=sql.text("''")
    )
    video = Column(
        Boolean, nullable=False, default=False, server_default=sql.false()
    )

    artist_credit = relationship(
        "ArtistCredit", foreign_keys=[artist_credit_id], innerjoin=True
    )


class LinkArtistRecording(db.Model):
    __tablename__ = "l_artist_recording"
    __table_args__ = (
        Index(
            "l_artist_recording_idx_uniq",
            "entity0",
            "entity1",
            "link",
            "link_order",
            unique=True,
        ),
        Index("l_artist_recording_idx_entity1", "entity1"),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    link_id = Column(
        "link",
        Integer,
        ForeignKey("musicbrainz.link.id", name="l_artist_recording_fk_link"),
        nullable=False,
    )
    entity0_id = Column(
        "entity0",
        Integer,
        ForeignKey(
            "musicbrainz.artist.id", name="l_artist_recording_fk_entity0"
        ),
        nullable=False,
    )
    entity1_id = Column(
        "entity1",
        Integer,
        ForeignKey(
            "musicbrainz.recording.id", name="l_artist_recording_fk_entity1"
        ),
        nullable=False,
    )
    link_order = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    entity0_credit = Column(
        String, nullable=False, default="", server_default=sql.text("''")
    )
    entity1_credit = Column(
        String, nullable=False, default="", server_default=sql.text("''")
    )

    link = relationship("Link", foreign_keys=[link_id], innerjoin=True)
    entity0 = relationship("Artist", foreign_keys=[entity0_id], innerjoin=True)
    entity1 = relationship(
        "Recording", foreign_keys=[entity1_id], innerjoin=True
    )

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


class LinkArtistArtist(db.Model):
    __tablename__ = "l_artist_artist"
    __table_args__ = (
        Index(
            "l_artist_artist_idx_uniq",
            "entity0",
            "entity1",
            "link",
            "link_order",
            unique=True,
        ),
        Index("l_artist_artist_idx_entity1", "entity1"),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    link_id = Column(
        "link",
        Integer,
        ForeignKey("musicbrainz.link.id", name="l_artist_artist_fk_link"),
        nullable=False,
    )
    entity0_id = Column(
        "entity0",
        Integer,
        ForeignKey("musicbrainz.artist.id", name="l_artist_artist_fk_entity0"),
        nullable=False,
    )
    entity1_id = Column(
        "entity1",
        Integer,
        ForeignKey("musicbrainz.artist.id", name="l_artist_artist_fk_entity1"),
        nullable=False,
    )
    link_order = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    entity0_credit = Column(
        String, nullable=False, default="", server_default=sql.text("''")
    )
    entity1_credit = Column(
        String, nullable=False, default="", server_default=sql.text("''")
    )

    link = relationship("Link", foreign_keys=[link_id], innerjoin=True)
    entity0 = relationship("Artist", foreign_keys=[entity0_id], innerjoin=True)
    entity1 = relationship("Artist", foreign_keys=[entity1_id], innerjoin=True)

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
    __tablename__ = "link_type"
    __table_args__ = (
        Index("link_type_idx_gid", "gid", unique=True),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    parent_id = Column(
        "parent",
        Integer,
        ForeignKey("musicbrainz.link_type.id", name="link_type_fk_parent"),
    )
    child_order = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    gid = Column(UUID, nullable=False)
    entity_type0 = Column(String(50), nullable=False)
    entity_type1 = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String)
    link_phrase = Column(String(255), nullable=False)
    reverse_link_phrase = Column(String(255), nullable=False)
    long_link_phrase = Column(String(255), nullable=False)
    is_deprecated = Column(
        Boolean, nullable=False, default=False, server_default=sql.false()
    )
    has_dates = Column(
        Boolean, nullable=False, default=True, server_default=sql.true()
    )
    entity0_cardinality = Column(
        SMALLINT, nullable=False, default=0, server_default=sql.text("0")
    )
    entity1_cardinality = Column(
        SMALLINT, nullable=False, default=0, server_default=sql.text("0")
    )

    parent = relationship("LinkType", foreign_keys=[parent_id])


class Link(db.Model):
    __tablename__ = "link"
    __table_args__ = (
        Index("link_idx_type_attr", "link_type", "attribute_count"),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    link_type_id = Column(
        "link_type",
        Integer,
        ForeignKey("musicbrainz.link_type.id", name="link_fk_link_type"),
        nullable=False,
    )
    begin_date_year = Column(SMALLINT)
    begin_date_month = Column(SMALLINT)
    begin_date_day = Column(SMALLINT)
    end_date_year = Column(SMALLINT)
    end_date_month = Column(SMALLINT)
    end_date_day = Column(SMALLINT)
    attribute_count = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    created = Column(DateTime(timezone=True), server_default=sql.func.now())
    ended = Column(
        Boolean, nullable=False, default=False, server_default=sql.false()
    )

    link_type = relationship(
        "LinkType", foreign_keys=[link_type_id], innerjoin=True
    )

    begin_date = composite(
        PartialDate, begin_date_year, begin_date_month, begin_date_day
    )
    end_date = composite(
        PartialDate, end_date_year, end_date_month, end_date_day
    )


class ArtistCredit(db.Model):
    __tablename__ = "artist_credit"
    __table_args__ = (
        Index("artist_credit_idx_gid", "gid", unique=True),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    artist_count = Column(SMALLINT, nullable=False)
    ref_count = Column(Integer, default=0, server_default=sql.text("0"))
    created = Column(DateTime(timezone=True), server_default=sql.func.now())
    edits_pending = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    gid = Column(UUID, nullable=False)


class ArtistCreditName(db.Model):
    __tablename__ = "artist_credit_name"
    __table_args__ = (
        Index("artist_credit_name_idx_artist", "artist"),
        {"schema": "musicbrainz"},
    )

    artist_credit_id = Column(
        "artist_credit",
        Integer,
        ForeignKey(
            "musicbrainz.artist_credit.id",
            name="artist_credit_name_fk_artist_credit",
            ondelete="CASCADE",
        ),
        nullable=False,
        primary_key=True,
    )
    position = Column(SMALLINT, nullable=False, primary_key=True)
    artist_id = Column(
        "artist",
        Integer,
        ForeignKey(
            "musicbrainz.artist.id",
            name="artist_credit_name_fk_artist",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    name = Column(String, nullable=False)
    join_phrase = Column(
        String, nullable=False, default="", server_default=sql.text("''")
    )

    artist_credit = relationship(
        "ArtistCredit",
        foreign_keys=[artist_credit_id],
        innerjoin=True,
        backref=backref("artists", order_by="ArtistCreditName.position"),
    )
    artist = relationship("Artist", foreign_keys=[artist_id], innerjoin=True)


class Track(db.Model):
    __tablename__ = "track"
    __table_args__ = (
        Index("track_idx_gid", "gid", unique=True),
        Index("track_idx_recording", "recording"),
        Index("track_idx_artist_credit", "artist_credit"),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    gid = Column(UUID, nullable=False)
    recording_id = Column(
        "recording",
        Integer,
        ForeignKey("musicbrainz.recording.id", name="track_fk_recording"),
        nullable=False,
    )
    medium_id = Column(
        "medium",
        Integer,
        ForeignKey("musicbrainz.medium.id", name="track_fk_medium"),
        nullable=False,
    )
    position = Column(Integer, nullable=False)
    number = Column(String, nullable=False)
    name = Column(String, nullable=False)
    artist_credit_id = Column(
        "artist_credit",
        Integer,
        ForeignKey(
            "musicbrainz.artist_credit.id", name="track_fk_artist_credit"
        ),
        nullable=False,
    )
    length = Column(Integer)
    is_data_track = Column(
        Boolean, nullable=False, default=False, server_default=sql.false()
    )

    recording = relationship(
        "Recording",
        foreign_keys=[recording_id],
        innerjoin=True,
        backref=backref("tracks"),
    )
    medium = relationship(
        "Medium",
        foreign_keys=[medium_id],
        innerjoin=True,
        backref=backref("tracks", order_by="Track.position"),
    )
    artist_credit = relationship(
        "ArtistCredit", foreign_keys=[artist_credit_id], innerjoin=True
    )


class Medium(db.Model):
    __tablename__ = "medium"
    __table_args__ = (
        Index("medium_idx_gid", "gid", unique=True),
        Index("medium_idx_track_count", "track_count"),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    release_id = Column(
        "release",
        Integer,
        ForeignKey("musicbrainz.release.id", name="medium_fk_release"),
        nullable=False,
    )
    position = Column(Integer, nullable=False)
    name = Column(
        String, nullable=False, default="", server_default=sql.text("''")
    )
    track_count = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    gid = Column(UUID, nullable=False)

    release = relationship(
        "Release",
        foreign_keys=[release_id],
        innerjoin=True,
        backref=backref("mediums", order_by="Medium.position"),
    )


class ReleaseGroup(db.Model):
    __tablename__ = "release_group"
    __table_args__ = (
        Index("release_group_idx_gid", "gid", unique=True),
        Index("release_group_idx_name", "name"),
        Index("release_group_idx_artist_credit", "artist_credit"),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    gid = Column(UUID, nullable=False)
    name = Column(String, nullable=False)
    artist_credit_id = Column(
        "artist_credit",
        Integer,
        ForeignKey(
            "musicbrainz.artist_credit.id",
            name="release_group_fk_artist_credit",
        ),
        nullable=False,
    )
    type_id = Column(
        "type",
        Integer,
        ForeignKey(
            "musicbrainz.release_group_primary_type.id",
            name="release_group_fk_type",
        ),
    )
    comment = Column(
        String(255), nullable=False, default="", server_default=sql.text("''")
    )
    edits_pending = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    last_updated = Column(
        DateTime(timezone=True), server_default=sql.func.now()
    )

    artist_credit = relationship(
        "ArtistCredit", foreign_keys=[artist_credit_id], innerjoin=True
    )
    type = relationship("ReleaseGroupPrimaryType", foreign_keys=[type_id])


class ReleaseGroupPrimaryType(db.Model):
    __tablename__ = "release_group_primary_type"
    __table_args__ = (
        Index("release_group_primary_type_idx_gid", "gid", unique=True),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(
        "parent",
        Integer,
        ForeignKey(
            "musicbrainz.release_group_primary_type.id",
            name="release_group_primary_type_fk_parent",
        ),
    )
    child_order = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    description = Column(String)
    gid = Column(UUID, nullable=False)

    parent = relationship("ReleaseGroupPrimaryType", foreign_keys=[parent_id])


class ReleaseStatus(db.Model):
    __tablename__ = "release_status"
    __table_args__ = (
        Index("release_status_idx_gid", "gid", unique=True),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    parent_id = Column(
        "parent",
        Integer,
        ForeignKey(
            "musicbrainz.release_status.id", name="release_status_fk_parent"
        ),
    )
    child_order = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    description = Column(String)
    gid = Column(UUID, nullable=False)

    parent = relationship("ReleaseStatus", foreign_keys=[parent_id])


class Release(db.Model):
    __tablename__ = "release"
    __table_args__ = (
        Index("release_idx_gid", "gid", unique=True),
        Index("release_idx_name", "name"),
        Index("release_idx_release_group", "release_group"),
        Index("release_idx_artist_credit", "artist_credit"),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    gid = Column(UUID, nullable=False)
    name = Column(String, nullable=False)
    artist_credit_id = Column(
        "artist_credit",
        Integer,
        ForeignKey(
            "musicbrainz.artist_credit.id", name="release_fk_artist_credit"
        ),
        nullable=False,
    )
    release_group_id = Column(
        "release_group",
        Integer,
        ForeignKey(
            "musicbrainz.release_group.id", name="release_fk_release_group"
        ),
        nullable=False,
    )
    status_id = Column(
        "status",
        Integer,
        ForeignKey("musicbrainz.release_status.id", name="release_fk_status"),
    )
    packaging_id = Column(
        "packaging",
        Integer,
        ForeignKey(
            "musicbrainz.release_packaging.id", name="release_fk_packaging"
        ),
    )
    language_id = Column(
        "language",
        Integer,
        ForeignKey("musicbrainz.language.id", name="release_fk_language"),
    )
    script_id = Column(
        "script",
        Integer,
        ForeignKey("musicbrainz.script.id", name="release_fk_script"),
    )
    barcode = Column(String(255))
    comment = Column(
        String(255), nullable=False, default="", server_default=sql.text("''")
    )
    edits_pending = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    quality = Column(
        SMALLINT, nullable=False, default=-1, server_default=sql.text("-1")
    )
    last_updated = Column(
        DateTime(timezone=True), server_default=sql.func.now()
    )

    artist_credit = relationship(
        "ArtistCredit", foreign_keys=[artist_credit_id], innerjoin=True
    )
    release_group = relationship(
        "ReleaseGroup", foreign_keys=[release_group_id], innerjoin=True
    )
    status = relationship("ReleaseStatus", foreign_keys=[status_id])


class ReleaseGroupSecondaryType(db.Model):
    __tablename__ = "release_group_secondary_type"
    __table_args__ = (
        Index("release_group_secondary_type_idx_gid", "gid", unique=True),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, nullable=False, primary_key=True)
    name = Column(String, nullable=False)
    parent_id = Column(
        "parent",
        Integer,
        ForeignKey(
            "musicbrainz.release_group_secondary_type.id",
            name="release_group_secondary_type_fk_parent",
        ),
    )
    child_order = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    description = Column(String)
    gid = Column(UUID, nullable=False)

    parent = relationship("ReleaseGroupSecondaryType", foreign_keys=[parent_id])


class ReleaseGroupSecondaryTypeJoin(db.Model):
    __tablename__ = "release_group_secondary_type_join"
    __table_args__ = {"schema": "musicbrainz"}  # noqa: RUF012

    release_group_id = Column(
        "release_group",
        Integer,
        ForeignKey(
            "musicbrainz.release_group.id",
            name="release_group_secondary_type_join_fk_release_group",
        ),
        nullable=False,
        primary_key=True,
    )
    secondary_type_id = Column(
        "secondary_type",
        Integer,
        ForeignKey(
            "musicbrainz.release_group_secondary_type.id",
            "musicbrainz",
            name="release_group_secondary_type_join_fk_secondary_type",
        ),
        nullable=False,
        primary_key=True,
    )
    created = Column(
        DateTime(timezone=True), nullable=False, server_default=sql.func.now()
    )

    release_group = relationship(
        "ReleaseGroup",
        foreign_keys=[release_group_id],
        innerjoin=True,
        backref=backref("secondary_types"),
    )
    secondary_type = relationship(
        "ReleaseGroupSecondaryType",
        foreign_keys=[secondary_type_id],
        innerjoin=True,
    )


class URL(db.Model):
    __tablename__ = "url"
    __table_args__ = (
        Index("url_idx_gid", "gid", unique=True),
        Index("url_idx_url", "url", unique=True),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    gid = Column(UUID, nullable=False)
    url = Column(String, nullable=False)


class LinkArtistURL(db.Model):
    __tablename__ = "l_artist_url"
    __table_args__ = (
        Index(
            "l_artist_url_idx_uniq",
            "entity0",
            "entity1",
            "link",
            "link_order",
            unique=True,
        ),
        Index("l_artist_url_idx_entity1", "entity1"),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    link_id = Column(
        "link",
        Integer,
        ForeignKey("musicbrainz.link.id", name="l_artist_url_fk_link"),
        nullable=False,
    )
    entity0_id = Column(
        "entity0",
        Integer,
        ForeignKey("musicbrainz.artist.id", name="l_artist_url_fk_entity0"),
        nullable=False,
    )
    entity1_id = Column(
        "entity1",
        Integer,
        ForeignKey("musicbrainz.url.id", name="l_artist_url_fk_entity1"),
        nullable=False,
    )
    link_order = Column(
        Integer, nullable=False, default=0, server_default=sql.text("0")
    )
    entity0_credit = Column(
        String, nullable=False, default="", server_default=sql.text("''")
    )
    entity1_credit = Column(
        String, nullable=False, default="", server_default=sql.text("''")
    )

    link = relationship("Link", foreign_keys=[link_id], innerjoin=True)
    entity0 = relationship("Artist", foreign_keys=[entity0_id], innerjoin=True)
    entity1 = relationship("URL", foreign_keys=[entity1_id], innerjoin=True)

    @hybrid_property
    def artist(self):
        return self.entity0

    @hybrid_property
    def artist_id(self):
        return self.entity0_id

    @hybrid_property
    def url(self):
        return self.entity1

    @hybrid_property
    def url_id(self):
        return self.entity1_id


class ReleaseLabel(db.Model):
    __tablename__ = "release_label"
    __table_args__ = (
        Index("release_label_idx_release", "release"),
        Index("release_label_idx_label", "label"),
        {"schema": "musicbrainz"},
    )

    id = Column(Integer, primary_key=True)
    release_id = Column(
        "release",
        Integer,
        ForeignKey(
            "musicbrainz.release.id",
            name="release_label_fk_release",
        ),
        nullable=False,
    )
    label_id = Column(
        "label",
        Integer,
        ForeignKey(
            "musicbrainz.label.id",
            name="release_label_fk_label",
        ),
    )
    catalog_number = Column(String(255))
    last_updated = Column(
        DateTime(timezone=True), server_default=sql.func.now()
    )

    release = relationship(
        "Release",
        foreign_keys=[release_id],
        innerjoin=True,
        backref=backref("labels"),
    )
