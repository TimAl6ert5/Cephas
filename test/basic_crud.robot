*** Settings ***
Library     REST         http://localhost:8080


*** Test cases ***

Get Health Check
    GET         /cephas/healthcheck
    Output      response
    Integer     response status             200
    String      response body status        ok


Happy Path CRUD Event
    POST        /cephas/api/v1.0/create-event           ${CURDIR}/happy_path_create_event.json
    Output      response
    Integer     response status             200
    Boolean     response body create        true
    ${event_key} =      Output      $.key

    GET         /cephas/api/v1.0/get-event/${event_key}
    Output      response
    Integer     response status             200
    String      response body key           ${event_key}

    PUT         /cephas/api/v1.0/update-event/${event_key}          ${CURDIR}/happy_path_update_event.json
    Output      response
    Integer     response status             200
    String      response body key           ${event_key}

    GET         /cephas/api/v1.0/get-event/${event_key}
    Output      response
    Integer     response status             200
    String      response body key           ${event_key}

    Delete      /cephas/api/v1.0/delete-event/${event_key}
    Output      response
    Integer     response status             200
    String      response body status        ok
