# Cephas

A Python Mongo REST Service based on a schema to manage 'where, when, and what' information.

The idea is to be able to track events in time, where they happen(ed) and what the details were.
For example:
- Used to manage historical data
- Used to manage future events

# Development

Example running locally (Windows):
```
python3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r .\requirements.txt
python3 main.py
```

# Testing

A [Robot Framework](https://robotframework.org/) acceptance test can be run as follows (from the virtual env):
```
pip install -r .\test-requirements.txt
cd tests
robot .\basic_crud.robot
```

# Containerization

Build the image `docker build -t cephas:latest .`

Run the image `docker run -p 8080:8080 cephas:latest`

Run with compose `docker-compose up`

## Container Environment

- **CEPHAS_SERVER_LOGLEVEL**: Server logging output level (default DEBUG)
- **CEPHAS_SERVER_LISTEN_HOST**: Hostname or IP where the service will bind too
- **CEPHAS_SERVER_LISTEN_PORT**: Port number where the service will listen for requests
- **CEPHAS_DB_NAME**: Name of the MongoDB database
- **CEPHAS_DB_COLLECTION_NAME**: Name of the MongoDB collection
- **CEPHAS_DB_HOST**: Hostname where the MongoDB service is running
- **CEPHAS_DB_PORT**: Port number where the MongoDB is listening for connections
- **CEPHAS_DB_USER**: Mongo client username
- **CEPHAS_DB_PASS**: Mongo client password
- **CEPHAS_DB_SOCKET_TIMEOUT_MS**: Mongo client socketTimeoutMS
- **CEPHAS_DB_CONNECT_TIMEOUT_MS**: Mongo client connectTimeoutMS


# When Where What
There are nuances to managing data with respect to time and space.
Following are some notes to be converted into documentation details.

## Time
https://docs.mongodb.com/manual/tutorial/model-time-data/

Stored in UTC...local time can be computed by also storing the event timezone.
A strategy must be developed for managing time relative to location.
There are three possible perspectives of time:
- UTC for standardized records and comparison
- Local time for user presentation
- Time relative to the location where the event is

## Space
The application currently supports point locatoin data.
This should be expanded to fully support the geoJson specification.

https://docs.mongodb.com/manual/tutorial/geospatial-tutorial/
http://tugdualgrall.blogspot.com/2014/08/introduction-to-mongodb-geospatial.html

Note: coordinates are  [longitude, latitude]  ... google maps is  [latitude, longitude] apparently
https://stackoverflow.com/questions/41513112/cant-extract-geo-keys-longitude-latitude-is-out-of-bounds


# Example in Mongo

A day at Disneyland

## Create

```
db.www.insert(
    {
        "key": "abc123",
        "deleted": false,
        "begin_timestamp": ISODate("2020-11-10T09:00:00.000Z"),
        "end_timestamp": ISODate("2020-11-10T09:30:00.000Z"),
        "location": {
            "type": "Point",
            "coordinates": [-117.923667, 33.809173]
        },
        "description": "Family vacation to Disneyland. Started the morning in the Downtown Disney District."
    }
)

db.www.insert(
    {
        "key": "def234",
        "deleted": false,
        "begin_timestamp": ISODate("2020-11-10T09:30:00.000Z"),
        "end_timestamp": ISODate("2020-11-10T10:00:00.000Z"),
        "location": {
            "type": "Point",
            "coordinates": [-117.920500, 33.811265]
        },
        "description": "Family vacation to Disneyland. Went to Tarzan's Treehouse."
    }
)

db.www.insert(
    {
        "key": "ghi345",
        "deleted": false,
        "begin_timestamp": ISODate("2020-11-10T10:00:00.000Z"),
        "end_timestamp": ISODate("2020-11-10T10:30:00.000Z"),
        "location": {
            "type": "Point",
            "coordinates": [-117.920814, 33.811299]
        },
        "description": "Family vacation to Disneyland. Time for Pirates of the Caribbean. Arrr!"
    }
)

db.www.insert(
    {
        "key": "jkl456",
        "deleted": false,
        "begin_timestamp": ISODate("2020-11-10T10:30:00.000Z"),
        "end_timestamp": ISODate("2020-11-10T11:00:00.000Z"),
        "location": {
            "type": "Point",
            "coordinates": [-117.920814, 33.811299]
        },
        "description": "Family vacation to Disneyland. Isla and I went on Pirates of the Caribbean again."
    }
)

db.www.insert(
    {
        "key": "mno567",
        "deleted": false,
        "begin_timestamp": ISODate("2020-11-10T10:30:00.000Z"),
        "end_timestamp": ISODate("2020-11-10T11:00:00.000Z"),
        "location": {
            "type": "Point",
            "coordinates": [-117.921460, 33.811210]
        },
        "description": "Family vacation to Disneyland. Ellen and Josie went to New Orleans Square to wait for us."
    }
)
```

## Read

`db.www.find({"key": "abc123"}).pretty();`

## Update
The application supports updating of where, when and what data.
A record of 'last_updated' is managed in the persistence layer.

```
db.www.update(
    {"key": "abc123"},
    {
        "$set": {
            "last_updated": new Date(),
            "description": "Family vacation to Disneyland. Started the morning in the Downtown Disney District to get coffee."
        }
    }
)
```

## Delete
No actual deletes, just using tombstoning protocal in the persistence layer.

```
db.www.update(
    {"key": "abc123"},
    {
        "$set": {
            "last_updated": new Date(),
            "deleted": true
        }
    }
)
```


# Indexes

Indexing here is used for record uniqueness, location operations, and full text searching.

`db.www.getIndexes()`

## Unique
The application generates a unique key for each record using UUID.
This hides the actual persistence ID (i.e. Mongo Object ID) from the client.
To guarantee uniquness the key is indexed.

`db.www.ensureIndex({"key" : 1}, {"unique" : true})`

## Time
Time searches will be a critical part of the application.
Research is needed to determine the benefit and trade-off for indexing chronological data.

## Geo
The application currently supports Point data using geoJSON feature of MongoDB.

`db.www.ensureIndex({ "location":  "2dsphere" })`

## Full text

`db.www.ensureIndex({"description" : "text"})`


# Queries

Given: A time
Then: What was happening everywhere?

```
db.www.find({
    "begin_timestamp":{
        $gte: ISODate("2020-11-10T10:00"),
        $lt: ISODate("2020-11-10T11:00") 
    }
}).pretty();
```

Given: A location
Then: What happened in time?

```
db.www.find({ 
    "location": { 
        $nearSphere: { 
            $geometry: {
                type: "Point",
                coordinates: [-117.920814, 33.811299]
            },
            $maxDistance: 10
        } 
    } 
}).pretty();
```

Given: A time and location
Then: What is happening within a given distance?

```
db.www.find({ 
    "begin_timestamp":{
        $gte: ISODate("2020-11-10T10:00"),
        $lt: ISODate("2020-11-10T11:00") 
    },
    "location": { 
        $nearSphere: { 
            $geometry: {
                type: "Point",
                coordinates: [-117.920814, 33.811299]
            },
            $maxDistance: 10
        } 
    } 
}).pretty();
```
