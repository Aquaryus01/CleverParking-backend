#!/usr/bin/python3
import pandas
import googlemaps
import sqlite3

c = sqlite3.connect('Datasets/Parking/parking.sqlite', check_same_thread=False)
cur = c.cursor()

google_api_key = 'AIzaSyBEgEtjNunnLyyIBVO0ZlCh3gReySJZhkQ'
