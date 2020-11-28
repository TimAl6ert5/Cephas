# Author:  Tim Alberts (timothy.alberts@snhu.edu)
# Class: CS-499-X2150 Computer Science Capstone 20EW2
# Instructor: Joe Conlan (j.conlan@snhu.edu)
# Due Date: 2020-11-29

import datetime
import geojson
import json
import re
import uuid
from dateutil.parser import *


ERROR_MSG_MISSING = "Missing"
ERROR_MSG_INVALID = "Invalid"
DESCRIPTION_MAX_LENGTH = 1024
DESCRIPTION_REGEX = "[A-Za-z0-9 ,.'!?]*"


def generateKey():
    return str(uuid.uuid4())


def validTime(time_string):
    """ Parse and validate an ISO datetime string
    returns a tuple of boolean flag indicating validity, and the datetime
    """
    try:
        datetime_object = isoparse(time_string)
        return True, datetime_object
    except ValueError:
        return False, None


def validPointCoordsList(coords_list):
    """ Parse and validate geoJson point coordinates from a list
    returns a tuple of boolean flag indicating validity, and the geojson Point
    """
    if type(coords_list) is not list:
        return False, None
    if len(coords_list) != 2:
        return False, None
    try:
        geo_point = geojson.Point((
            coords_list[0],
            coords_list[1]
        ))
        if geo_point.is_valid:
            return True, geo_point
        else:
            return False, None
    except:
        return False, None


def validDescription(description_string):
    """ Trim and validate the description content
    returns a tuple of boolean flag indicationg validity, and the description
    """
    stripped_description_string = description_string.strip()
    if len(stripped_description_string) > DESCRIPTION_MAX_LENGTH:
        return False, None
    if re.fullmatch(DESCRIPTION_REGEX, stripped_description_string):
        return True, stripped_description_string
    else:
        return False, None


class SpaceTimeEvent(object):
    def __init__(self):
        self.valid = False
        self.errorsDict = {}
        self.key = None
        self.deleted = False
        self.begin_timestamp = None
        self.end_timestamp = None
        self.location_type = None
        self.location_coords = None
        self.description = None

    def parseCreateJson(self, json_record):
        self.valid = True

        if 'begin_timestamp' not in json_record:
            self.errorsDict['begin_timestamp'] = ERROR_MSG_MISSING
            self.valid = False
        else:
            valid_begin, self.begin_timestamp = validTime(json_record['begin_timestamp'])
            if not valid_begin:
                self.errorsDict['begin_timestamp'] = ERROR_MSG_INVALID
                self.valid = False

        if 'end_timestamp' in json_record:
            valid_end, self.end_timestamp = validTime(json_record['end_timestamp'])
            if not valid_end:
                self.errorsDict['end_timestamp'] = ERROR_MSG_INVALID
                self.valid = False
        
        if 'location' not in json_record:
            self.errorsDict['location'] = ERROR_MSG_MISSING
            self.valid = False
        else:
            if 'type' not in json_record['location']:
                self.errorsDict['location.type'] = ERROR_MSG_MISSING
                self.valid = False
            else:
                if json_record['location']['type'].lower() != 'point':
                    self.errorsDict['location.type'] = ERROR_MSG_INVALID
                    self.valid = False
                else:
                    self.location_type = 'point'
            if 'coordinates' not in json_record['location']:
                self.errorsDict['location.coordinates'] = ERROR_MSG_MISSING
                self.valid = False
            else:
                valid_location, self.location_coords = validPointCoordsList(
                    json_record['location']['coordinates']
                )
                if not valid_location:
                    self.errorsDict['location.coordinates'] = ERROR_MSG_INVALID
                    self.valid = False

        if 'description' not in json_record:
            self.errorsDict['description'] = ERROR_MSG_MISSING
            self.valid = False
        else:
            valid_description, self.description = validDescription(json_record['description'])
            if not valid_description:
                self.errorsDict['description'] = ERROR_MSG_INVALID
                self.valid = False
        
        if self.valid:
            self.key = generateKey()
    

    def parseUpdateJson(self, json_record):
        self.valid = True
        update_field_count = 0

        if 'begin_timestamp' in json_record:
            update_field_count += 1
            valid_begin, self.begin_timestamp = validTime(json_record['begin_timestamp'])
            if not valid_begin:
                self.errorsDict['begin_timestamp'] = ERROR_MSG_INVALID
                self.valid = False
    
        if 'end_timestamp' in json_record:
            update_field_count += 1
            valid_end, self.end_timestamp = validTime(json_record['end_timestamp'])
            if not valid_end:
                self.errorsDict['end_timestamp'] = ERROR_MSG_INVALID
                self.valid = False
        
        if 'location' in json_record:
            update_field_count += 1
            if 'type' not in json_record['location']:
                self.errorsDict['location.type'] = ERROR_MSG_MISSING
                self.valid = False
            else:
                if json_record['location']['type'].lower() != 'point':
                    self.errorsDict['location.type'] = ERROR_MSG_INVALID
                    self.valid = False
                else:
                    self.location_type = 'point'
            if 'coordinates' not in json_record['location']:
                self.errorsDict['location.coordinates'] = ERROR_MSG_MISSING
                self.valid = False
            else:
                valid_location, self.location_coords = validPointCoordsList(
                    json_record['location']['coordinates']
                )
                if not valid_location:
                    self.errorsDict['location.coordinates'] = ERROR_MSG_INVALID
                    self.valid = False

        if 'description' in json_record:
            update_field_count += 1
            valid_description, self.description = validDescription(json_record['description'])
            if not valid_description:
                self.errorsDict['description'] = ERROR_MSG_INVALID
                self.valid = False
        
        # Must have at least one field to update
        if update_field_count == 0:
            self.errorsDict['update_fields'] = "None"
            self.valid = False
        

    def __repr__(self):
        return "SpaceTimeEvent({}, {}, {}, {}, {}, {}, {}, {})".format(
            self.key,
            self.begin_timestamp,
            self.end_timestamp,
            self.location_type,
            self.location_coords,
            self.description,
            self.valid,
            self.errorsDict
        )


if __name__ == '__main__':
    # A couple simple tests scenarios to play with during development.
    jsonString = """{
        "begin_timestamp": "2020-11-10T09:00:00.000Z",
        "end_timestamp": "2020-11-10T09:30:00.000Z",
        "location": {
            "type": "Point",
            "coordinates": [-117.923667, 33.809173]
        },
        "description": "Some thing happened."
    }"""

    create_record = SpaceTimeEvent()
    create_record.parseCreateJson(json.loads(jsonString))
    print(create_record)

    jsonString = """{
        "key": "abc123",
        "begin_timestamp": "2020-11-10T09:00:00.000Z",
        "end_timestamp": "2020-11-10T09:30:00.000Z",
        "location": {
            "type": "Point",
            "coordinates": [-117.923667, 33.809173]
        },
        "description": "Some thing happened."
    }"""

    update_record = SpaceTimeEvent()
    update_record.parseUpdateJson(json.loads(jsonString))
    print(update_record)
