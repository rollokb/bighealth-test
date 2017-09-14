import pytz

from app.db import Base, db_session
from sqlalchemy import (
    Integer, Column, DateTime, ForeignKey, Date, CheckConstraint, UniqueConstraint
)

from marshmallow import Schema, fields, validates_schema, ValidationError


class Diary(Base):
    """
    Stub model of users.
    """
    __tablename__ = 'diary'
    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey('user.id'))
    date = Column(Date)

    time_into_bed = Column(DateTime(timezone=True))
    time_out_of_bed = Column(DateTime(timezone=True))
    sleep_quality = Column(Integer)

    __table_args__ = (
        CheckConstraint(sleep_quality.between(0, 10), name='sleep_quality_constraint'),
        CheckConstraint(time_out_of_bed >= time_into_bed, name='positive_time_slept_constraint'),
        UniqueConstraint(user_id, date, name='sleep_per_day_constraint')
    )


class User(Base):
    """
    Stub model of users.
    """
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)


class NormalizedDateTime(fields.DateTime):
    """
    Most DBAPIs have built in support for the datetime module,
    with the noted exception of SQLite. In the case of SQLite,
    date and time types are stored as strings which are then
    converted back to datetime objects when rows are returned.

    This class makes sure everything is Zulu time.
    """
    def _deserialize(self, value, attr, data):
        dt = super()._deserialize(value, attr, data)
        if dt.tzinfo:
            dt = dt.astimezone(pytz.utc)

        return dt


class DiarySchema(Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(
        dump_to='userId', dump_only=True
    )

    date = fields.Date(
        required=True,
    )

    time_into_bed = NormalizedDateTime(
        dump_to='timeIntoBed', load_from='timeIntoBed',
        required=True
    )
    time_out_of_bed = NormalizedDateTime(
        dump_to='timeOutOfBed', load_from='timeOutOfBed',
        required=True
    )

    sleep_quality = fields.Integer(
        validate=lambda n: 0 <= n <= 10,
        dump_to='sleepQuality', load_from='sleepQuality',
        required=True
    )

    @validates_schema
    def validate_date(self, data):
        if 'date' in data:
            diaries = db_session.query(Diary).filter(
                Diary.date == data['date'],
                Diary.user_id == self.context['user_id']
            )

            if self.context.get('id'):
                diaries = diaries.filter(Diary.id != self.context['id'])

            if diaries.count():
                raise ValidationError(
                    'No More Than One Diary For a User Per Day',
                    field_names=['date']
                )
