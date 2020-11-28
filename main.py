# Author:  Tim Alberts (timothy.alberts@snhu.edu)
# Class: CS-499-X2150 Computer Science Capstone 20EW2
# Instructor: Joe Conlan (j.conlan@snhu.edu)
# Due Date: 2020-11-29

import sys
import logging
import json
import datetime
from bson import json_util
import bottle
from bottle import route, run, request, response, abort, error
from cephas.persist import MongoConfig, MongoContext
from cephas.domain import SpaceTimeEvent


ERROR_MSG_INVALID_DATA = "Invalid data"

my_mongo_ctx = None


def error_view(err, msg, code):
    err.set_header('content-type', "application/json")
    response = {"error": {"message": msg, "code": code}}
    return json.dumps(response)


@error(405)
def error405(error):
    return error_view(error, "Method Not Allowed", 405)


@error(404)
def error404(error):
    return error_view(error, "Not Found", 404)


@error(400)
def error400(error):
    return error_view(error, "Invalid Request", 400)


@error(500)
def error500(error):
    logging.error("Internal Server Error: %s", error)
    return error_view(error, "Internal Server Error", 500)


def check_keys(required, data):
    for r in required:
        if r not in data:
            return False
    return True


def check_request(req):
    if req.headers.get('content-type') != "application/json":
        abort(400, "Invalid content-type")


# Server healthcheck endpoint
@route('/cephas/healthcheck', method='GET')
def handle_hello():
    check_request(request)
    # Health check endpoint
    # TODO check DB connection
    response = {"status": "ok"}
    return response


# Create a new entry.
@route('/cephas/api/v1.0/create-event', method='POST')
def handle_create_event():
    check_request(request)

    userEventData = request.json
    if userEventData is None:
        logging.warning("Invalid create request: missing data")
        abort(400, ERROR_MSG_INVALID_DATA)

    create_record = SpaceTimeEvent()
    create_record.parseCreateJson(userEventData)

    if not create_record.valid:
        logging.warning("Invalid create data: %s", create_record.errorsDict)
        # TODO pass validation errors back to the client
        abort(400, ERROR_MSG_INVALID_DATA)

    global my_mongo_ctx
    try:
        success = my_mongo_ctx.insertRecord(create_record)
        response = {"create": success, "key": create_record.key}
        return response
    except Exception as e:
        logging.exception("Persist Exception")
        abort(500, e)


# Get an event record by key
@route('/cephas/api/v1.0/get-event/<event_key>', method='GET')
def handle_get_event(event_key):
    check_request(request)

    if event_key is None:
        abort(400, "Invalid request")

    my_query = {"key": event_key}

    global my_mongo_ctx
    try:
        result = my_mongo_ctx.findRecord(my_query)
        response.content_type = 'application/json' # TODO search result is a list...
        return result
    except Exception as e:
        abort(500, e)


# Update an event record by key
@route('/cephas/api/v1.0/update-event/<event_key>', method='PUT')
def handle_update_event(event_key):
    check_request(request)

    if event_key is None:
        abort(400, "Invalid request")
        
    userUpdateData = request.json
    if userUpdateData is None:
        abort(400, ERROR_MSG_INVALID_DATA)
    
    update_record = SpaceTimeEvent()
    update_record.parseUpdateJson(userUpdateData)
    if not update_record.valid:
        logging.warning("Invalid update data: %s", update_record.errorsDict)
        abort(400, ERROR_MSG_INVALID_DATA)

    global my_mongo_ctx
    try:
        result = my_mongo_ctx.updateRecord(event_key, update_record)
        response.content_type = 'application/json' # TODO search result is a list...
        return result
    except Exception as e:
        abort(500, e)


# Delete an event record by key
@route('/cephas/api/v1.0/delete-event/<event_key>', method='DELETE')
def handle_delete_event(event_key):
    check_request(request)

    if event_key is None:
        abort(400, "Invalid request")
    
    global my_mongo_ctx
    try:
        # result = my_mongo_ctx.updateOne(my_query, my_update)
        result = my_mongo_ctx.deleteRecord(event_key)
        response.content_type = 'application/json'
        safe_delete_response = {'status': 'ok'} # don't return the record of a 'deleted' event
        return safe_delete_response
    except Exception as e:
        abort(500, e)


# Find events that happened within a time period
@route('/cephas/api/v1.0/find/in-time', method='POST')
def handle_find_event_in_time():
    check_request(request)

    user_in_time_query = request.json
    if user_in_time_query is None:
        abort(400, "Invalid Request")
    
    key_check_result = check_keys(["start_time", "end_time"], user_in_time_query)
    if not key_check_result:
        abort(400, ERROR_MSG_INVALID_DATA)
    
    # TODO make sure datatime is getting properly constructed from the request
    
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.findInTime(user_in_time_query['start_time'], user_in_time_query['end_time'])
        response.content_type = 'application/json' # TODO search result is a list...
        return result
    except Exception as e:
        abort(500, e)


# Find events that happened near a location
@route('/cephas/api/v1.0/find/in-space', method='POST')
def handle_find_event_in_space():
    check_request(request)
    
    user_in_space_query = request.json
    if user_in_space_query is None:
        abort(400, "Invalid Request")
    
    key_check_result = check_keys(["latituted", "longitude", "maxDistance"], user_in_space_query)
    if not key_check_result:
        abort(400, ERROR_MSG_INVALID_DATA)
    
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.findInSpace(
            user_in_space_query['latituted'],
            user_in_space_query['longitude'],
            user_in_space_query['maxDistance']
        )
        response.content_type = 'application/json' # TODO search result is a list...
        return result
    except Exception as e:
        abort(500, e)


# Find events that happened within a time period, near a location
@route('/cephas/api/v1.0/find/in-space-time', method='POST')
def handle_find_event_in_space_time():
    check_request(request)
    
    user_in_space_time_query = request.json
    if user_in_space_time_query is None:
        abort(400, "Invalid Request")
    
    key_check_result = check_keys(["start_time", "end_time", "latituted", "longitude", "maxDistance"], user_in_space_time_query)
    if not key_check_result:
        abort(400, ERROR_MSG_INVALID_DATA)
    
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.findInSpaceTime(
            user_in_space_time_query['start_time'],
            user_in_space_time_query['end_time'],
            user_in_space_time_query['latituted'],
            user_in_space_time_query['longitude'],
            user_in_space_time_query['maxDistance']
        )
        response.content_type = 'application/json' # TODO search result is a list...
        return result
    except Exception as e:
        abort(500, e)


def connect_mongo(db, collection):
    global my_mongo_ctx
    my_mongo_cfg = MongoConfig(db)
    my_mongo_ctx = MongoContext(my_mongo_cfg)
    my_mongo_ctx.useCollection(collection)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG)
    connect_mongo('space-time', 'www')
    run(host='localhost', port=8080, debug=True, reloader=True)
