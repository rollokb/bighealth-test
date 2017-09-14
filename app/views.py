from werkzeug.exceptions import BadRequest
from flask import Blueprint, jsonify, request, make_response

from app.db import db_session
from app.models import Diary, DiarySchema, User

diary = Blueprint(__name__, 'diary')


@diary.route('/user/<int:user_id>/diaries')
def index(user_id):
    if not db_session.query(User).filter(User.id == user_id).count():
        return make_response(
            jsonify(message='No User Found'), 404
        )

    diaries = db_session.query(Diary).filter(Diary.user_id == user_id)
    schema = DiarySchema(many=True)
    result = schema.dump(diaries)
    return jsonify(result.data)


@diary.route('/user/<int:user_id>/diary', methods=['POST'])
def post(user_id):
    user = db_session.query(User).get(user_id)

    if not user:
        return make_response(
            jsonify(message='No User Found'), 404
        )

    try:
        request_json = request.get_json()
    except BadRequest:
        return make_response(
            jsonify(message='JSON POST data required'), 400
        )

    schema = DiarySchema(context={'user_id': user_id})
    result = schema.load(request_json)
    # Return the dict of marshmallow schema errors to the user
    if result.errors:
        return make_response(
            jsonify(result.errors), 400
        )

    diary = Diary(**result.data)
    diary.user_id = user_id
    db_session.add(diary)
    db_session.commit()

    result = schema.dump(diary)

    return make_response(
        jsonify(result.data),
        201,
    )


@diary.route('/user/<int:user_id>/diary/<int:diary_id>', methods=['PUT'])
def put(user_id, diary_id):
    diary = db_session.query(Diary).filter(
        Diary.id == diary_id, User.id == user_id
    ).first()

    if not diary:
        return make_response(
            jsonify(message='No Diary Found'), 404
        )

    try:
        request_json = request.get_json()
    except BadRequest:
        return make_response(
            jsonify(message='JSON POST data required'), 400
        )

    schema = DiarySchema(
        context={'user_id': user_id, 'id': diary_id},
        partial=True
    )
    result = schema.load(request_json)

    # Return the dict of marshmallow schema errors to the user
    if result.errors:
        return make_response(
            jsonify(result.errors), 400
        )

    update_result = db_session.query(Diary).filter(
        Diary.id == diary.id
    ).update(
        result.data
    )

    db_session.commit()

    if not update_result:
        # This could happen if the user or diary get's deleted
        # by another request during this request. It's unlikely
        # but if that's the case. The client should just try again.
        return make_response(
            jsonify(message='Server Error. Try again later.'), 500
        )

    db_session.refresh(diary)

    result = schema.dump(diary)

    return make_response(
        jsonify(result.data),
        200,
    )


@diary.route('/user/<int:user_id>/diary/<int:diary_id>', methods=['DELETE'])
def delete(user_id, diary_id):
    diary = db_session.query(Diary).filter(
        Diary.id == diary_id, User.id == user_id
    ).first()

    if not diary:
        return make_response(
            jsonify(message='No Diary Found'), 404
        )

    db_session.delete(diary)
    db_session.commit()

    return make_response('', 204)
