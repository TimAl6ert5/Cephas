# Author:  Tim Alberts (timothy.alberts@snhu.edu)
# Class: CS-340-Q1461 Client/Server Development 20EW1
# Instructor: Joe Conlan (j.conlan@snhu.edu)
# Due Date: 2020-10-18

import sys
import logging
import json
import datetime
from bson import json_util
import bottle
from bottle import route, run, request, response, abort, error
from pymongo import MongoClient


my_mongo_ctx = None


class MongoConfig(object):
    """ Configuration wrapper for a basic MongoDB connection """

    def __init__(self, db_name, host='localhost', port=27017):
        self.host = host
        self.port = port
        self.db_name = db_name


class MongoContext(object):
    """ Thin wrapper for a basic MongoDB connection """
    
    def __init__(self, mongoconfig):
        self.mongoconfig = mongoconfig
        self.connection = MongoClient(
            self.mongoconfig.host, self.mongoconfig.port)
        self.db = self.connection[self.mongoconfig.db_name]
        self.collection = None

    def getDbs(self):
        try:
            return self.connection.list_database_names()
        except Exception as e:
            logging.error('Exception occurred accessing DB: %s', e)
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
            logging.error('Exception occurred accessing DB: %s', e)
            return None
    
    def checkCollectionExists(self, collection_name):
        collections = self.getCollections()
        if collections is None:
            return False
        return collection_name in collections

    def useCollection(self, collection_name):
        self.collection = self.db[collection_name]
    
    def insertOne(self, input_dict):
        try:
            self.collection.insert_one(input_dict)
            return True
        except Exception as e:
            logging.warning('Exception occurred at insert one: %s', e)
            return False

    def findOne(self, query = None):
        try:
            result = self.collection.find_one(query)
            if result is None:
                return "No matching result"
            return result
        except Exception as e:
            logging.warning('Exception occurred at find one: %s', e)
            return "An error occurred during search"

    def find(self, query = None, projection = None):
        try:
            cursor = self.collection.find(query, projection)
            if cursor is None:
                return "No matching result"
            return json_util.dumps(list(cursor))
            # TODO ensure return type is dictionary?
            # return json.loads(json_util.dumps(list(cursor)))
        except Exception as e:
            logging.warning('Exception occurred at find: %s', e)
            return "An error occurred during search"
    
    def distinct(self, key, query=None):
        try:
            return self.collection.distinct(key, query)
        except Exception as e:
            logging.warning('Exception occurred at distinct: %s', e)
            return "An error occurred during search"
    
    def updateOne(self, query, values):
        try:
            self.collection.update_one(query, values)
            return self.find(query)
        except Exception as e:
            logging.warning('Exception occurred at update one: %s', e)
            return "An error occurred during update"

    def updateMany(self, query, values):
        try:
            self.collection.update_many(query, values)
            return self.find(query)
        except Exception as e:
            logging.warning('Exception occurred at update many: %s', e)
            return "An error occurred during update"

    def deleteOne(self, query):
        try:
            self.collection.delete_one(query)
            return self.find(query)
        except Exception as e:
            logging.warning('Exception occurred at delete one: %s', e)
            return "An error occurred during delete"

    def deleteMany(self, query):
        try:
            self.collection.delete_many(query)
            return self.find(query)
        except Exception as e:
            logging.warning('Exception occurred at delete many: %s', e)
            return "An error occurred during delete"
    
    def runAggregate(self, pipeline):
        try:
            cursor = self.collection.aggregate(pipeline)
            if cursor is None:
                return "No matching result"
            return json_util.dumps(list(cursor))
        except Exception as e:
            logging.warning('Exception occurred at aggregate: %s', e)
            return "An error occurred during search"


def error_view(err, msg, code):
    err.set_header('content-type', "application/json")
    response = {"error": {"message": msg, "code": code}}
    return json.dumps(response)


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
@route('/healthcheck', method='GET')
def handle_hello():
    check_request(request)
    # Health check endpoint
    # TODO check DB connection
    response = {"status": "ok"}
    return response


# Create new stock document for ticker symbol AA, from data provided with the request.
# Pattern: http://[hostname]/stocks/api/v1.0/createStock/[ticker_symbol] 
# Example: http://codio_server/stocks/api/v1.0/createStock/AA  
@route('/stocks/api/v1.0/createStock/<ticker_symbol>', method='POST')
def handle_create(ticker_symbol):
    check_request(request)

    if ticker_symbol is None:
        abort(400, "Invalid data")
    
    data = request.json
    if data is None:
        abort(400, "Invalid data")
    
    # TODO define required fields
    key_check_result = check_keys(["Ticker"], data)
    if not key_check_result:
        abort(400, "Invalid data")

    # TODO check the ticker symbol matches request and data
    # TODO other validation?

    # mongo
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.insertOne(data)
        response = {"create": result}
        return response
    except Exception as e:
        abort(500, e)


# Retrieve stock document for ticker symbol AA
# Pattern: http://[hostname]/stocks/api/v1.0/getStock/[ticker symbol] 
# Example: http://codio_server/stocks/api/v1.0/getStock/AA
@route('/stocks/api/v1.0/getStock/<ticker_symbol>', method='GET')
def handle_read(ticker_symbol):
    check_request(request)
    
    if ticker_symbol is None:
        abort(400, "Invalid data")
    
    my_qry = {"Ticker": ticker_symbol}

    # mongo
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.find(my_qry, None)
        response.content_type = 'application/json' # TODO search result is a list...
        return result
    except Exception as e:
        abort(500, e)


# Update stock document for ticker symbol AA, from data provided with the request.
# Pattern: http://[hostname]/stocks/api/v1.0/updateStock/[ticker symbol] 
# Example: http://codio_server/stocks/api/v1.0/updateStock/AA 
@route('/stocks/api/v1.0/updateStock/<ticker_symbol>', method='PUT')
def handle_update(ticker_symbol):
    check_request(request)
    
    if ticker_symbol is None:
        abort(400, "Invalid data")
    
    data = request.json
    if data is None:
        abort(400, "Invalid data")
    
    key_check_result = check_keys(["Volume"], data)
    if not key_check_result:
        abort(400, "Invalid data")
    
    # TODO check the ticker symbol matches request and data

    volume = data['Volume']
    if not (type(volume) is int and volume > 0):
        abort(400, "Invalid data")

    my_qry = {"Ticker": ticker_symbol}

    my_update = {
        "$set": {
            "Volume": volume
        }
    }

    # mongo
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.updateOne(my_qry, my_update)
        response.content_type = 'application/json' # TODO search result is a list...
        return result
    except Exception as e:
        abort(500, e)


# Delete stock document for ticker symbol AA.
# Pattern: http://[hostname]/stocks/api/v1.0/deleteStock/[ticker symbol] 
# Example: http://codio_server/stocks/api/v1.0/deleteStock/AA 
@route('/stocks/api/v1.0/deleteStock/<ticker_symbol>', method='DELETE')
def handle_delete(ticker_symbol):
    check_request(request)
    
    if ticker_symbol is None:
        abort(400, "Invalid data")
    
    my_qry = {"Ticker": ticker_symbol}

    # mongo
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.deleteOne(my_qry)
        response.content_type = 'application/json' # TODO search result is a list...
        return result
    except Exception as e:
        abort(500, e)


# Select and present specific stock summary information info by a user-derived list of ticker symbols.
# Retrieve stock report for list of ticker symbols from data provided with the request, e.g. { list=[AA,BA,T].
# Pattern: http://[hostname]/stocks/api/v1.0/stockReport
# Example: http://codio_server/stocks/api/v1.0/stockReport  
@route('/stocks/api/v1.0/stockReport', method='POST')
def handle_stock_report():
    check_request(request)
    
    data = request.json
    if data is None:
        abort(400, "Invalid data")
    
    key_check_result = check_keys(["list"], data)
    if not key_check_result:
        abort(400, "Invalid data")
    
    # TODO check the list is an array of string

    my_qry = { "Ticker" : { "$in" : data['list'] } }

    summary = {
        "Ticker" : 1,
        "Company" : 1,
        "Price" : 1,
        "EPS growth past 5 years" : 1,
        "EPS growth quarter over quarter" : 1,
        "EPS growth next 5 years" : 1,
        "EPS (ttm)" : 1,
        "EPS growth next year" : 1,
        "EPS growth this year" : 1,
        "P/E" : 1,
        "PEG" : 1,
        "P/B" : 1,
        "Performance (Week)" : 1,
        "Performance (Month)" : 1,
        "Performance (Quarter)" : 1,
        "Performance (Half Year)" : 1,
        "Performance (YTD)" : 1,
        "Volatility (Week)" : 1,
        "Volatility (Month)" : 1
    }

    # mongo
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.find(my_qry, summary)
        response.content_type = 'application/json' # TODO search result is a list...
        return result
    except Exception as e:
        abort(500, e)


# Get distinct values for select keys
# Pattern: http://[hostname]/stocks/api/v1.0/[Key] 
# Example: http://[hostname]/stocks/api/v1.0/Industry
@route('/stocks/api/v1.0/<distinct_key>/list', method='GET')
def handle_distinct(distinct_key):
    check_request(request)

    if distinct_key in ['Sector', 'Industry', 'Country']:
        # mongo
        global my_mongo_ctx
        try:
            values = my_mongo_ctx.distinct(distinct_key)
            result = {distinct_key: values}
            return result
        except Exception as e:
            abort(500, e)
    else:
        abort(404, "Invalid data")


# Find documents for which the "50-Day Simple Moving Average" is between the low and high values
# and return the count of the number of documents found
@route('/stocks/api/v1.0/sma50', method='GET')
def handle_simple_moving_avg_50day():
    check_request(request)

    try:
        qlo = float(request.query.low)
        qhi = float(request.query.high)
    except Exception as e:
        abort(400, "Invalid data")

    logging.debug("sma50 [low %f - high %f]", qlo, qhi)

    my_qry = [
        { "$match": { "50-Day Simple Moving Average" : { "$gte" : qlo, "$lte" : qhi } } },
        { "$group": { "_id": "null", "count": { "$sum": 1 } } }
    ]

    # mongo
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.runAggregate(my_qry)
        return {"count" : json.loads(result)[0]['count'] }
    except Exception as e:
        abort(500, e)


# Find symbols by industry
@route('/stocks/api/v1.0/symbols/byindustry', method='GET')
def handle_symbols_by_industry():
    check_request(request)

    industry = request.query.industry
    
    my_qry = { "Industry" : industry }

    # mongo
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.distinct("Ticker", my_qry)
        return {"symbols" : result}
    except Exception as e:
        abort(500, e)


# Report total outstanding shares grouped by Industry for a given Sector
@route('/stocks/api/v1.0/<sector>/sharesbyindustry', method='GET')
def handle_industry_shares(sector):
    check_request(request)

    my_qry = [
        { "$match": { "Sector" : sector } },
        { "$project" : { "Industry" : 1, "Shares Outstanding" : 1 } },
        { "$group": { 
            "_id": "$Industry",
            "shares total": { "$sum": "$Shares Outstanding" } 
        } },
        { "$sort" : {"_id" : 1}}
    ]

    # mongo
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.runAggregate(my_qry)
        response.content_type = 'application/json' # TODO search result is a list...
        return result
    except Exception as e:
        abort(500, e)


# Report a portfolio of five top stocks by a user-derived industry selection.
# Pattern: http://[hostname]/stocks/api/v1.0/industryReport/[Industry] 
# Example: http://codio_server/stocks/api/v1.0/industryReport/telecom  (Retrieve stock report for telecom industry.)
@route('/stocks/api/v1.0/industryReport/<industry>', method='GET')
def handle_industry_report(industry):
    check_request(request)
    
    my_qry = [
        { "$match": { "Industry" : industry } },
        { "$project" : {
            "Ticker" : 1,
            "Company" : 1,
            "Price" : 1,
            "EPS growth past 5 years" : 1,
            "EPS growth quarter over quarter" : 1,
            "EPS growth next 5 years" : 1,
            "EPS (ttm)" : 1,
            "EPS growth next year" : 1,
            "EPS growth this year" : 1,
            "P/E" : 1,
            "PEG" : 1,
            "P/B" : 1,
            "Performance (Week)" : 1,
            "Performance (Month)" : 1,
            "Performance (Quarter)" : 1,
            "Performance (Half Year)" : 1,
            "Performance (YTD)" : 1,
            "Volatility (Week)" : 1,
            "Volatility (Month)" : 1
        } },
        { "$sort" : {"Performance (YTD)" : -1}},
        { "$limit" : 5 }
    ]

    # mongo
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.runAggregate(my_qry)
        response.content_type = 'application/json' # TODO search result is a list...
        return result
    except Exception as e:
        abort(500, e)


# Report a portfolio of possible investments for a user derived company in the companies.json collection by like Industries. 
# Pattern: http://[hostname]/stocks/api/v1.0/portfolio/[company name] 
# Example: http://codio_server/stocks/api/v1.0/portfolio/AdventNet  (Retrieve stock portfolio report for company "AdventNet.")
@route('/stocks/api/v1.0/portfolio/<company_name>', method='GET')
def handle_portfolio(company_name):
    check_request(request)
    
    if company_name is None:
        abort(400, "Invalid data")
    
    my_qry = {"Company": company_name}

    # mongo
    global my_mongo_ctx
    try:
        result = my_mongo_ctx.find(my_qry, None)
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
    connect_mongo('market', 'stocks')
    run(host='localhost', port=8080, debug=True, reloader=True)

"""
curl Tests

curl -X POST -H 'Content-Type: application/json' -d '{"Ticker":"TIMA","Volume":0}' 'http://localhost:8080/stocks/api/v1.0/createStock/TIMA'

curl -X GET -H 'Content-Type: application/json' 'http://localhost:8080/stocks/api/v1.0/getStock/TIMA'

curl -X PUT -H 'Content-Type: application/json' -d '{"Volume":123}' 'http://localhost:8080/stocks/api/v1.0/updateStock/TIMA'

curl -X DELETE -H 'Content-Type: application/json' 'http://localhost:8080/stocks/api/v1.0/deleteStock/TIMA'


curl -X POST -H 'Content-Type: application/json' -d '{"list":["AAXJ","AA"]}' 'http://localhost:8080/stocks/api/v1.0/stockReport'

curl -X GET -H 'Content-Type: application/json' 'http://localhost:8080/stocks/api/v1.0/industryReport/Aluminum'

"""
