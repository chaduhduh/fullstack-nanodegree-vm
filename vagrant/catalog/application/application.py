# imports
from flask import Flask, render_template, request, redirect, url_for, jsonify, session as login_session, make_response, flash
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
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']


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
	if request.args.get('hash_key') != login_session['hash_key']:
		response = make_response(json.dumps('Not Permitted'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	code = request.data
	login_session['name'] = "heraldo"
	try:
	    # Upgrade the authorization code into a credentials object
	    oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
	    oauth_flow.redirect_uri = 'postmessage'
	    credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
	    response = make_response(
	        json.dumps('Failed to upgrade the authorization code.'), 401)
	    response.headers['Content-Type'] = 'application/json'
	    return response

	# make sure its a valid token
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'% access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

    # Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'), 
			200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	# login_session['credentials'] = credentials - TODO ERROR ?
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()
	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	output = ''
	output += '<h1>Welcome, '
	output += login_session['username']
	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
	flash("you are now logged in as %s" % login_session['username'])
	print "done!"
	return output


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