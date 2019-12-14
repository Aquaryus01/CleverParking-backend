#!/usr/bin/python3
from flask import Flask, request
from flask_cors import CORS
from math import radians, sin, cos, acos
import googlemaps
from config import *

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
    c = connection()

    for p1, p in parking.iterrows():
        if p1 == len(parking):
            break

        d = calc_dist(data, p)
        if [d, {'name': p['garagecode'], 'lat': p['lat'], 'long': p['long'], 'distance': d}] not in closest:
            closest.append([d, {'name': p['garagecode'], 'lat': p['lat'], 'long': p['long'], 'distance': d}])

        closest = sorted(closest)[:3]

    for idx, (j, i) in enumerate(closest):
        c.execute('SELECT AVG(vehiclecount*100/totalspaces) FROM parking_history WHERE TIME(updatetime) < TIME(?) AND TIME(updatetime) > TIME(?) AND garagecode = ?;', (f'{data["hour"]+1}:00:00', f'{data["hour"]}:00:00', i['name']))
        closest[idx][1]['full'] = c.fetchall()[0][0]

        c.execute('SELECT totalspaces FROM parking_history WHERE garagecode = ? LIMIT 1;', (i['name'],))
        closest[idx][1]['max_cars'] = c.fetchall()[0][0]
        closest[idx][1]['now_cars'] = 0

    return {'response': [i[1] for i in closest]}

if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
