# imports
from flask import Flask, render_template, request, redirect, url_for, jsonify, session as login_session, make_response, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Items as Item, Users as User

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
session_keys = ["user_id", "access_token", "name", "gplus_id", "username", "email", "picture"]

# routes
@app.route('/')
def home():
	if 'hash_key' not in login_session:
		hash_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
			for x in xrange(32))
		login_session['hash_key'] = hash_key
	return render_template('login.html', data = { "login_session" : login_session })


@app.route('/login')
def login():
    hash_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['hash_key'] = hash_key
    return render_template('login.html', data = { "login_session" : login_session })


@app.route('/logout')
def logout():
	return redirect(url_for('gdisconnect'))

@app.route('/user/email')
def user_email():
	data = login_session['email']
	return data

@app.route('/connect-googleplus/', methods=['POST'])
def connect_googleplus():
	if request.args.get('hash_key') != login_session['hash_key']:
		response = make_response(json.dumps('Not Permitted'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	code = request.data
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
	http = httplib2.Http()
	result = json.loads(http.request(url, 'GET')[1])
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
	login_session['access_token'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)

	data = answer.json()
	login_session['name'] = data['name']
	login_session['image'] = data['picture']
	login_session['email'] = data['email']

	# test delete user first
	# deleted_user = delete_user({'email' : login_session['email']})

	# Create user only if we do not already have the same email
	user = db.query(User).filter_by(email=login_session['email']).first()
	if user is None:
		user_created = create_user({'login_session' : login_session})
		login_session['user_id'] = user_created.id
		print "user created " + user_created.email
		if user_created is False:
			response = make_response(json.dumps('Failed to create User.'), 
				500)
			response.headers['Content-Type'] = 'application/json'
			return response
	else:
		print "user already exists " + user.email

	# Prepares the function response given nothing above failed
	final_response = make_response(json.dumps("success"), 200)
	return final_response


@app.route('/gdisconnect')
def gdisconnect():
	if 'access_token' not in login_session:
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	http = httplib2.Http()
	result = http.request('https://accounts.google.com/o/oauth2/revoke?token=%s' 
    	% login_session['access_token'], 'GET')[0]
	if result['status'] == '200':
		session_cleared = revoke_session()
		if(session_cleared):
			response = make_response(json.dumps('Successfully disconnected.'), 200)
			response.headers['Content-Type'] = 'application/json'
			return response
		else:
			response = make_response(json.dumps('Something went wrong. User name not found', 400))
			response.headers['Content-Type'] = 'application/json'
			return response
	else:
		response = make_response(json.dumps('Failed to revoke token for given user.', 400))
		response.headers['Content-Type'] = 'application/json'
		return response


@app.route('/update-item/<name>')
def Update(name):
	item = db.query(Item).filter_by(name=name).first()
	if item:
		# do some alterations to data here
		db.add(item)
		db.commit()
		return "updated " + item.name
	else: 
		return "item not found"

@app.route('/revoke')
def revoke():
	revoke_session()
	return redirect(url_for('home'))

@app.route('/User/delete')
def user_delete():
	user = db.query(User).filter_by(email=login_session['email']).first()
	db.delete(user)
	db.commit()
	revoke_session()
	return redirect(url_for('home'))


@app.route('/delete-item/<name>')
def Delete(name):
	item = db.query(Item).filter_by(name=name).first()
	db.delete(item)
	db.commit()
	return "deleted"


@app.route('/create-item/<name>')
def Create(name):
	if login_session['access_token'] is None:
		response = make_response(json.dumps('Not Authorized.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	if(name):
		# validate data first
		item = Item(name=name,user_id=login_session['user_id'])
		db.add(item)
		db.commit()
		response = make_response(json.dumps('Success.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:
		return "nothing added"


@app.route('/read-item/<name>')
def Read(name):
	item = db.query(Item).filter_by(name=name).first()
	if item:
		return "Item is " + item.name
	else:
		return "Nothing to show here"
 	# items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)


# functions

def revoke_session():
	for key in session_keys:
		if key in login_session:
			del login_session[key]
	if 'name' in login_session:
		return False
	else:
		return True


def create_user(args):
	if 'login_session' not in args:
		return False
	user_session = args['login_session']
	user = User(name=user_session['name'], image=user_session['image'], 
		email=user_session['email'])
	db.add(user)
	db.commit()
	added_user = db.query(User).filter_by(email=user_session['email']).one()
	return added_user


def delete_user(args):
	if 'email' in args:
		key = 'email'
		value = args['email']
	elif 'user_id' in args:
		key = 'user_id'
		value = args['user_id']
	if key and value:
		# user = db.query(User).filter(User['email'] == value)
		user = db.query(User).filter_by(email=value).first()
		db.delete(user)
		db.commit()
	return user

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)