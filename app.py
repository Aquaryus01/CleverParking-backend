#!/usr/bin/python3
from flask import Flask, request
from flask_cors import CORS
from math import radians, sin, cos, acos
from config import *
from datetime import datetime
import uuid
import googlemaps

app = Flask(__name__)
CORS(app)
gmaps = googlemaps.Client(google_api_key)

def calc_dist(a, b):
    #print(a, b)
    slat = radians(float(a['lat']))
    slong = radians(float(a['long']))
    elat = radians(float(b['lat']))
    elong = radians(float(b['long']))

    return 6371.01 * acos(sin(slat)*sin(elat) + cos(slat)*cos(elat)*cos(slong - elong))

@app.route('/find_nearest', methods=['POST'])
def find_nearest():
    data = request.get_json(force=True)
    to_send = []

    cur.execute('SELECT name, lat, long FROM parkings')
    lines = cur.fetchall()

    for p in lines:
        d = calc_dist(data, {'lat': p[1], 'long': p[2]})

        temp = {'name': p[0], 'lat': p[1], 'long': p[2], 'distance': d}

        cur.execute('SELECT AVG(vehiclecount*100/totalspaces) FROM parking_history WHERE TIME(updatetime) < TIME(?) AND TIME(updatetime) > TIME(?) AND garagecode = ?;', (f'{str(int(data["hour"])+1).rjust(2, "0")}:00:00', f'{str(int(data["hour"])).rjust(2, "0")}:00:00', temp['name']))
        temp['full'] = cur.fetchall()[0][0]

        cur.execute('SELECT totalspaces FROM parking_history WHERE garagecode = ? LIMIT 1;', (p[0],))
        temp['max_cars'] = cur.fetchall()[0][0]

        cur.execute('SELECT COUNT(*) FROM parked_cars WHERE parking_id = (SELECT _id FROM parking_history WHERE garagecode = ? LIMIT 1)', (p[0],))
        temp['now_cars'] = cur.fetchall()[0][0]

        cur.execute('SELECT price FROM parkings WHERE name = ?', (temp['name'],))
        temp['price'] = cur.fetchall()[0][0]

        temp['address'] = gmaps.geocode(p[0])[0]['formatted_address']

        print(temp)
        to_send.append(temp)

    return {'response': to_send}

@app.route('/park_car/<name>', methods=['GET'])
def park_car(name):
    uid = uuid.uuid4().hex
    name = name.upper()
    t = datetime.now()
    print(name, uid, t)

    cur.execute('SELECT COUNT(*) FROM parking_history WHERE garagecode = ?', (name,))

    if cur.fetchall()[0][0] == 0:
        return '0'

    cur.execute('INSERT INTO parked_cars (parking_id, uuid, time) VALUES ((SELECT _id FROM parking_history WHERE garagecode = ?), ?, ?)', (name, uid, str(t)))
    c.commit()

    return {'uuid': uid, 'timestamp': t.timestamp()}

@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json(force=True)
    print(data)

    cur.execute('SELECT COUNT(*) FROM parked_cars WHERE uuid = ?', (data['uuid'],))

    if cur.fetchall()[0][0] != 0:
        cur.execute('DELETE FROM parked_cars WHERE uuid = ?', (data['uuid'],))
        c.commit()

        return '1'
    else:
        return '0'

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
