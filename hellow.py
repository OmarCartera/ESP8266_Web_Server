#!/usr/bin/python
# coding: utf-8
from flask import Flask, render_template
import MySQLdb
from sys import exit


app = Flask(__name__)

@app.route('/result')

def result():
  results=[]
  db = MySQLdb.connect("localhost","cartera","Password1!","task0" )
  cursor = db.cursor()
  sql = "SELECT * FROM sensors "
  try:
    # Execute the SQL command
    cursor.execute(sql)
    # Fetch all the rows in a list of lists.
    results = cursor.fetchall()
		
  except:
    print "Error: unable to fecth data"
   
  return render_template('result.html',results=results)


if __name__ == '__main__':
  app.run(debug = True)