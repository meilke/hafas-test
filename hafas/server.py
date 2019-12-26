import datetime

from flask import Flask, escape, request

from .cli import Trips

app = Flask(__name__)

@app.route('/')
def get_next_train():
    trips = Trips('XXX', 'http://demo.hafas.de/openapi/vbb-proxy',
                  '900210010', '900023201')
    result = trips.query_trips(datetime.timedelta(minutes=60))
    next_trip = result[list(result.keys())[0]]
    t = next_trip['start'].strftime('%H:%M')
    return t
