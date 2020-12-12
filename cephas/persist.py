# Author:  Tim Alberts (timothy.alberts@snhu.edu)
# Class: CS-499-X2150 Computer Science Capstone 20EW2
# Instructor: Joe Conlan (j.conlan@snhu.edu)
# Due Date: 2020-11-29

import datetime
import logging
from bson import json_util
from pymongo import MongoClient
from . import domain


my_mongo_ctx = None

DEFAULT_PROJECT = {
    "_id": 0,
    "key": 1,
    "begin_timestamp": 1,
    "end_timestamp": 1,
    "location": 1,
    "description": 1,
}


class MongoConfig(object):
    """ Configuration wrapper for a basic MongoDB connection to a single 
    collection.
    """

    def __init__(self, db_name, host='localhost', port=27017, user=None, passwd=None):
        self.db_name = db_name
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
    
    def uses_auth(self):
        return self.user is not None and self.passwd is not None


class MongoContext(object):
    """ Thin wrapper for a basic MongoDB connection.  Handles the persistence
    logic for the SpaceTimeEvent domain and general mongo interactions
    handling.
    """
    
    def __init__(self, mongoconfig):
        self.mongoconfig = mongoconfig
        if self.mongoconfig.uses_auth():
            logging.info("Connecting with auth")
            self.connection = MongoClient('mongodb://%s:%s@%s:%s' % (
                self.mongoconfig.user,
                self.mongoconfig.passwd,
                self.mongoconfig.host,
                self.mongoconfig.port)
            )
        else:
            logging.info("Connecting without auth")
            self.connection = MongoClient(self.mongoconfig.host, self.mongoconfig.port)
        self.db = self.connection[self.mongoconfig.db_name]
        self.collection = None

    def getDbs(self):
        try:
            return self.connection.list_database_names()
        except Exception as e:
            logging.exception('Exception occurred accessing DB: %s', e)
            return None

    def checkDBExists(self, db_name):
        dbs = self.getDbs()
        if dbs is None:
            return False
        return db_name in dbs
    
    def getCollections(self):
        try:
            return self.db.list_collection_names()
        except Exception as e:
            logging.exception('Exception occurred accessing DB: %s', e)
            return None
    
    def checkCollectionExists(self, collection_name):
        collections = self.getCollections()
        if collections is None:
            return False
        return collection_name in collections

    def useCollection(self, collection_name):
        self.collection = self.db[collection_name]
    
    def insertRecord(self, event_record):
        if not event_record.valid:
            raise Exception("Invalid record")
        # Convert record to a dictionary and insert
        event_dict = {}
        event_dict['key'] = event_record.key
        event_dict['deleted'] = False
        event_dict['begin_timestamp'] = event_record.begin_timestamp
        event_dict['end_timestamp'] = event_record.end_timestamp
        event_dict['location'] = event_record.location_coords
        event_dict['description'] = event_record.description
        return self._insertOne(event_dict)

    def _insertOne(self, input_dict):
        try:
            self.collection.insert_one(input_dict)
            return True
        except Exception as e:
            logging.exception('Exception occurred at insert one: %s', e)
            return False

    def findRecord(self, query):
        global DEFAULT_PROJECT
        return self._findOne(query, DEFAULT_PROJECT)

    def _findOne(self, query = None, projection = None):
        if query is not None:
            query['deleted'] = False
        try:
            result = self.collection.find_one(query, projection)
            if result is None:
                return "No matching result"
            result['begin_timestamp'] = result['begin_timestamp'].isoformat()
            if 'end_timestamp' in result:
                result['end_timestamp'] = result['end_timestamp'].isoformat()
            return json_util.dumps(result)
        except Exception as e:
            logging.exception('Exception occurred at find one: %s', e)
            return "An error occurred during search"

    def findInTime(self, start_time, end_time):
        global DEFAULT_PROJECT

        my_query = {
            "begin_timestamp":{
                "$gte": datetime.datetime.fromisoformat(start_time),
                "$lt": datetime.datetime.fromisoformat(end_time) 
            }
        }
        
        return self._find(my_query, DEFAULT_PROJECT)

    def findInSpace(self, latituted, longitude, maxDistance):
        global DEFAULT_PROJECT

        my_query = {
            "location": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [
                            longitude,
                            latituted
                        ],
                        "$maxDistance": maxDistance
                    }
                }
            }
        }

        return self._find(my_query, DEFAULT_PROJECT)

    def findInSpaceTime(self, start_time, end_time, latituted, longitude, maxDistance):
        global DEFAULT_PROJECT

        my_query = {
            "begin_timestamp":{
                "$gte": datetime.datetime.fromisoformat(start_time),
                "$lt": datetime.datetime.fromisoformat(end_time) 
            },
            "location": {
                "$nearSphere": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [
                            longitude,
                            latituted
                        ],
                        "$maxDistance": maxDistance
                    }
                }
            }
        }
        
        return self._find(my_query, DEFAULT_PROJECT)

    def _find(self, query = None, projection = None):
        if query is not None:
            query['deleted'] = False
        try:
            cursor = self.collection.find(query, projection)
            if cursor is None:
                return "No matching result"

            result_list = list(cursor)
            print(type(result_list))
            for doc in result_list:
                doc['begin_timestamp'] = doc['begin_timestamp'].isoformat()
                if 'end_timestamp' in doc:
                    doc['end_timestamp'] = doc['end_timestamp'].isoformat()
            
            return json_util.dumps(result_list)
            # TODO ensure return type is dictionary?
            # return json.loads(json_util.dumps(list(cursor)))
        except Exception as e:
            logging.exception('Exception occurred at find: %s', e)
            return "An error occurred during search"
    
    def updateRecord(self, event_key, event_record):
        global DEFAULT_PROJECT

        if not event_record.valid:
            raise Exception("Invalid record")
        
        my_query = {"key": event_key}

        # Convert record to a dictionary and insert
        event_dict = {}
        event_dict['last_updated'] = datetime.datetime.utcnow()
        if event_record.begin_timestamp is not None:
            event_dict['begin_timestamp'] = event_record.begin_timestamp
        if event_record.end_timestamp is not None:
            event_dict['end_timestamp'] = event_record.end_timestamp
        if event_record.location_coords is not None:
            event_dict['location'] = event_record.location_coords
        if event_record.description is not None:
            event_dict['description'] = event_record.description
        my_update = {"$set": event_dict}

        return self._updateOne(my_query, my_update, DEFAULT_PROJECT)

    def _updateOne(self, query, values, projection = None):
        if query is not None:
            query['deleted'] = False
        try:
            self.collection.update_one(query, values)
            return self._findOne(query, projection)
        except Exception as e:
            logging.exception('Exception occurred at update one: %s', e)
            return "An error occurred during update"

    def deleteRecord(self, event_key):
        my_query = {"deleted": False, "key": event_key}

        my_update = {
            "$set": {
                "deleted": True,
                "last_updated": datetime.datetime.utcnow()
            }
        }
        
        try:
            self.collection.update_one(my_query, my_update)
            return True
        except Exception as e:
            logging.exception('Exception occurred at delete: %s', e)
            return "An error occurred during delete"
