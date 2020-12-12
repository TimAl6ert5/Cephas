# Change Log

## Planning

**Features and Improvements**

- Implement full text search
- Errors during persist operations should return dictionary with error message, not just error string
- Search with no match should return dictionary with error message, not just error string
- Add verification to ensure be begin_timestamp actually comes before the end_timestamp
- Update documentation
- Adjust mongo connection timeout

**Additional Testing**

- Invalid methods
- Missing content-type
- Get deleted data
- Error response format
- Empty results format
- Check UUID searches case insensitive


## [0.0.2] - Not yet released

### Added

- Input data validation and filtering to only allow validated data to be persisted.
- Added example Postman collection for testing and documentation purposes.
- Implemented delete 'tombstoning' pattern so documents aren't actually deleted, they are flagged and filtered as deleted.
- Implemented acceptance test cases using [Robot Framework](https://robotframework.org/)
- Containerization support
- Application environment configuration
- Support mongo client authentication

### Changed

- Refactored database schema from stock data to 'when/where/what' data
- Refactored code into modules
- Modified MongoContext so 'internal' low level methods start with _. (Example: findOne became _findOne)

### Removed

- Removed extraneous persistence methods in MongoContext (such as distinct, deleteMany...)

### Fixed

- Security Bug: Can no longer save 'anything' in the document

### Known Issues


## [0.0.1] - 2020-06-21
Initial implementation.
