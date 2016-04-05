# imports
from flask import Flask, render_template, request, redirect, url_for, jsonify, session as login_session, make_response
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Items

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests
import random
import string

# setup
app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = '\x11\xa4W[\xfc\xba\x1df-\xe5OrW\xc1\xc3\xd8>r\xc1\xbciV\xfbp'
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db = DBSession()


# routes
@app.route('/')
def home():
	return render_template('login.html', data = { "login_session" : login_session })


@app.route('/login')
def login():
    hash_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['hash_key'] = hash_key
    return render_template('login.html', data = { "login_session" : login_session })

@app.route('/logout')
def logout():
	login_session['name'] = ''
	return redirect(url_for('home'))

@app.route('/connect-googleplus/', methods=['POST'])
def connect_googleplus():
	# if request.args.get('hash_key') != login_session['hash_key']:
	# 	response = make_response(json.dumps('Not Permitted.'), 401)
	# 	login_session = ''
	# 	response.headers['Content-Type'] = 'application/json'
	# 	return response
	# Obtain authorization code
	# code = request.data
	login_session['name'] = "heraldo"
	return "connecting google plus"


@app.route('/update-item/<name>')
def Update(name):
	item = db.query(Items).filter_by(name=name).first()
	if item:
		# do some alterations to data here
		db.add(item)
		db.commit()
		return "updated " + item.name
	else: 
		return "item not found"


@app.route('/delete-item/<name>')
def Delete(name):
	item = db.query(Items).filter_by(name=name).first()
	db.delete(item)
	db.commit()
	return "deleted"


@app.route('/create-item/<name>')
def Create(name):
	if(name):
		# validate data first
		item = Items(name=name)
		db.add(item)
		db.commit()
		return "added item named = " + item.name
	else:
		return "nothing added"


@app.route('/read-item/<name>')
def Read(name):
	item = db.query(Items).filter_by(name=name).first()
	if item:
		return "Item is " + item.name
	else:
		return "Nothing to show here"
 	# items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)