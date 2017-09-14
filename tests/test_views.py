import pytest
import json
import pytz

from datetime import datetime, timedelta, date

from app.models import User, Diary


@pytest.fixture
def users(session):
    users = [
        User() for _ in range(10)
    ]

    session.add_all(users)
    session.commit()
    return users


def test_index_view_404(app, session):
    with app.test_request_context('/user/1/diaries'):
        response = app.dispatch_request()

    assert response.status_code == 404
    assert response.json.get('message'), 'No error message returned'


def test_index_view(app, session, users):
    with app.test_request_context('/user/1/diaries'):
        response = app.dispatch_request()

    assert response.status_code == 200
    assert response.json == []

    diary = Diary(
        user_id=1,
        date=date.today(),
        time_into_bed=datetime.now(pytz.utc),
        time_out_of_bed=datetime.now(pytz.utc) + timedelta(hours=1),
        sleep_quality=9,
    )

    session.add(diary)
    session.commit()

    with app.test_request_context('/user/1/diaries'):
        response = app.dispatch_request()

    assert response.status_code == 200
    assert len(response.json) == 1, 'Did not read diary'


def test_diary_post_404(app, session):
    with app.test_request_context(
        '/user/1/diary',
        method='POST', content_type='application/json',
        data=json.dumps({})
    ):
        response = app.dispatch_request()

    assert response.status_code == 404
    assert response.json.get('message'), 'No error message returned'


def test_diary_post_json_errors(app, session, users):
    with app.test_request_context(
        '/user/1/diary',
        method='POST', content_type='application/json',
        data='not json'
    ):
        response = app.dispatch_request()

    assert response.status_code == 400
    assert response.json.get('message'), 'No error message returned'

    post_data = {
        'date': 'Not a date',
        'timeIntoBed': datetime.now().isoformat(),
        'timeOutOfBed': (datetime.now() + timedelta(hours=1)).isoformat(),
        'sleepQuality': -1,
    }

    with app.test_request_context(
        '/user/1/diary',
        method='POST', content_type='application/json',
        data=json.dumps(post_data)
    ):
        response = app.dispatch_request()

    assert response.status_code == 400
    assert response.json == {
        'date': ['Not a valid date.'], 'sleepQuality': ['Invalid value.']
    }


def test_diary_post_json(app, session, users):
    post_data = {
        'date': date.today().isoformat(),
        'timeIntoBed': datetime.now().isoformat(),
        'timeOutOfBed': (datetime.now() + timedelta(hours=1)).isoformat(),
        'sleepQuality': 9,
    }

    with app.test_request_context(
        '/user/1/diary',
        method='POST', content_type='application/json',
        data=json.dumps(post_data)
    ):
        response = app.dispatch_request()

    assert response.status_code == 201
    assert response.json['date'] == post_data['date']
    assert response.json['timeIntoBed'].startswith(post_data['timeIntoBed'])
    assert response.json['timeOutOfBed'].startswith(post_data['timeOutOfBed'])
    assert response.json['sleepQuality'] == post_data['sleepQuality']

    with app.test_request_context(
        '/user/1/diary',
        method='POST', content_type='application/json',
        data=json.dumps(post_data)
    ):
        response = app.dispatch_request()

    assert response.status_code == 400, 'Only one diary per day'
    assert response.json == {
        'date': ['No More Than One Diary For a User Per Day']
    }


def test_tz_handling(app, session, users):
    # test tz handling
    dt = datetime(2016, 1, 1, 6, tzinfo=pytz.utc)

    post_data = {
        'date': date.today().isoformat(),
        'timeIntoBed': dt.astimezone(pytz.timezone('Asia/Shanghai')).isoformat(),
        'timeOutOfBed': (dt.astimezone(pytz.utc) + timedelta(hours=1)).isoformat(),
        'sleepQuality': 9,
    }

    with app.test_request_context(
        '/user/1/diary',
        method='POST', content_type='application/json',
        data=json.dumps(post_data)
    ):
        response = app.dispatch_request()

    assert response.json['timeIntoBed'] == '2016-01-01T06:00:00+00:00'


def test_put(app, session, users):
    post_data = {
        'date': date.today().isoformat(),
        'timeIntoBed': datetime.now().isoformat(),
        'timeOutOfBed': (datetime.now() + timedelta(hours=1)).isoformat(),
        'sleepQuality': 9,
    }

    with app.test_request_context(
        '/user/1/diary',
        method='POST', content_type='application/json',
        data=json.dumps(post_data)
    ):
        app.dispatch_request()

    diary = session.query(Diary).first()
    put_data = {
        'sleepQuality': 5,
    }

    with app.test_request_context(
        '/user/1/diary/{}'.format(diary.id),
        method='PUT', content_type='application/json',
        data=json.dumps(put_data)
    ):
        response = app.dispatch_request()

    assert response.status_code == 200
    assert response.json['sleepQuality'] == 5


def test_unique_date_put(app, session, users):
    for i in range(2):
        diary = Diary(
            user_id=1,
            date=date.today() + timedelta(days=i),
            time_into_bed=datetime.now(),
            time_out_of_bed=datetime.now() + timedelta(hours=1),
            sleep_quality=9,
        )

        session.add(diary)

    session.commit()

    put_data = {
        'sleepQuality': 5,
        'date': date.today().isoformat()
    }

    with app.test_request_context(
        '/user/1/diary/{}'.format(diary.id),
        method='PUT', content_type='application/json',
        data=json.dumps(put_data)
    ):
        response = app.dispatch_request()

    assert response.status_code == 400
    assert response.json == {
        'date': ['No More Than One Diary For a User Per Day']
    }


def test_only_edit_own_diaries(app, session, users):
    for i in range(2):
        diary = Diary(
            id=i,
            user_id=i,
            date=date.today() + timedelta(days=i),
            time_into_bed=datetime.now(),
            time_out_of_bed=datetime.now() + timedelta(hours=1),
            sleep_quality=9,
        )

        session.add(diary)

    session.commit()

    put_data = {
        'sleepQuality': 5,
        'date': date.today().isoformat()
    }

    with app.test_request_context(
        '/user/1/diary/2',
        method='PUT', content_type='application/json',
        data=json.dumps(put_data)
    ):
        response = app.dispatch_request()

    assert response.status_code == 404

    with app.test_request_context(
        '/user/1/diary/1',
        method='PUT', content_type='application/json',
        data=json.dumps(put_data)
    ):
        response = app.dispatch_request()

    assert response.status_code == 200


def test_delete(app, session, users):
    for i in range(2):
        diary = Diary(
            id=i,
            user_id=i,
            date=date.today() + timedelta(days=i),
            time_into_bed=datetime.now(),
            time_out_of_bed=datetime.now() + timedelta(hours=1),
            sleep_quality=9,
        )

        session.add(diary)

    session.commit()

    with app.test_request_context(
        '/user/1/diary/20',
        method='DELETE',
    ):
        response = app.dispatch_request()

    assert response.status_code == 404

    with app.test_request_context(
        '/user/1/diary/1',
        method='DELETE',
    ):
        response = app.dispatch_request()

    assert response.status_code == 204
