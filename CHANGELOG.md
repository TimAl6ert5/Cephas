# Change Log


## [0.0.2] - Not yet released

### Tasks

- [] Implement full text search
- [] Errors during persist operations should return dictionary with error message, not just error string
- [] Search with no match should return dictionary with error message, not just error string
- [] Externalize configuration (i.e. database name, collection name, db host/port)
- [] Update documentation

**Additional Testing**

- [] Invalid methods
- [] Missing content-type
- [] Get deleted data
- [] Error response format
- [] Empty results format
- [] Check UUID searches case insensitive


### Added

- Input data validation and filtering to only allow validated data to be persisted.
- Added example Postman collection for testing and documentation purposes.
- Implemented delete 'tombstoning' pattern so documents aren't actually deleted, they are flagged and filtered as deleted.
- Implemented acceptance test cases using [Robot Framework](https://robotframework.org/)

### Changed

- Refactored database schema from stock data to 'when/where/what' data
- Refactored code into modules
- Modified MongoContext so 'internal' low level methods start with _. (Example: findOne became _findOne)

### Removed

- Removed extraneous persistence methods in MongoContext (such as distinct, deleteMany...)

### Fixed

- Security Bug: Can no longer save 'anything' in the document

## [0.0.1] - 2020-06-21
Initial implementation.
