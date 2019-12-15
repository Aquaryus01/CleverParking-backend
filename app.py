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
    closest = []

    for p1, p in parking.iterrows():
        if p1 == len(parking):
            break

        d = calc_dist(data, p)
        if [d, {'name': p['garagecode'], 'lat': p['lat'], 'long': p['long'], 'distance': d}] not in closest:
            closest.append([d, {'name': p['garagecode'], 'lat': p['lat'], 'long': p['long'], 'distance': d}])

    for idx, (j, i) in enumerate(closest):
        cur.execute('SELECT AVG(vehiclecount*100/totalspaces) FROM parking_history WHERE TIME(updatetime) < TIME(?) AND TIME(updatetime) > TIME(?) AND garagecode = ?;', (f'{data["hour"]+1}:00:00', f'{data["hour"]}:00:00', i['name']))
        closest[idx][1]['full'] = cur.fetchall()[0][0]

        cur.execute('SELECT totalspaces FROM parking_history WHERE garagecode = ? LIMIT 1;', (i['name'],))
        closest[idx][1]['max_cars'] = cur.fetchall()[0][0]

        cur.execute('SELECT COUNT(*) FROM parked_cars WHERE parking_id = (SELECT _id FROM parking_history WHERE garagecode = ? LIMIT 1)', (i['name'],))
        closest[idx][1]['now_cars'] = cur.fetchall()[0][0]

        closest[idx][1]['address'] = gmaps.geocode(i['name'])[0]['formatted_address']

    return {'response': [i[1] for i in closest]}

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
