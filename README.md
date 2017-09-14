# BigHealth Test

This is the short code test that I've done for BigHealth implementing a stub of
a sleep diary API. To run you can do the following:

    $ pip install -r requirements.txt
    $ python run_webapp.py

This should start the API on port 5000.

To test:
    
    $ pytest

If you want to run this in Docker, you can do the following.

    $ docker build -t bighealth_test .
    $ docker run -it bighealth_test /code/run_webapp.py

The database test.db will be created automatically if it doesn't already exist.

## Implementation

Implemented using SQLAlchemy as the data layer, Marshmallow for serialization,
and simple Flask powering the views.

## Notes

My interpretation of this requirement 'all dates/times in the API requests and
responses represent the local user dates and times.'. Was that the app should
accept localised datetime and normalize it to UTC.

It's not a good idea to store timezone information in databases. The server
should accept localised timezones, convert and store them as UTC. The client
should accept UTC and localize it when it needs to be displayed.
