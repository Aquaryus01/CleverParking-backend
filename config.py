#!/usr/bin/python3
import pandas
import googlemaps
import sqlite3

def connection():
    c = sqlite3.connect('Datasets/Parking/parking.sqlite')
    return c.cursor()

google_api_key = 'AIzaSyBEgEtjNunnLyyIBVO0ZlCh3gReySJZhkQ'
parking = pandas.read_csv('Datasets/Parking/parking_locations.csv')
