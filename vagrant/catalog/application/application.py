# imports

from flask import Flask, \
	render_template, request, redirect, \
	url_for, jsonify, session as login_session, \
	make_response, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, \
 	Items as Item, \
 	Users as User, \
 	Categories as Categories
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
session_keys = ["user_id", "access_token", "name", 
					"gplus_id", "username", "email", "picture"]


# Auth routes

@app.route('/logout')
def logout():
	return redirect(url_for('gdisconnect'))

@app.route('/login')
def login():
    hash_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                	for x in xrange(32))
    login_session['hash_key'] = hash_key
    return render_template('home.html', data = { "login_session" : login_session })

@app.route('/connect-googleplus/', methods=['POST'])
def connect_googleplus():
	if request.args.get('hash_key') != login_session['hash_key']:
		response = make_response(json.dumps('Not Permitted'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	# authorization code to credentials object

	try:
	    oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
	    oauth_flow.redirect_uri = 'postmessage'
	    credentials = oauth_flow.step2_exchange(request.data)
	except FlowExchangeError:
	    response = make_response(
	        json.dumps('Failed to upgrade the authorization code.'), 401)
	    response.headers['Content-Type'] = 'application/json'
	    return response
	# validate token with google from credentials object
	
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'% access_token)
	http = httplib2.Http()
	result = json.loads(http.request(url, 'GET')[1])
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'
	# validate token for this user

	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
    # validate token for this specific app

	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response
	# check to see if this user is already logged in

	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	user_info = requests.get(userinfo_url, params=params).json()
	login_session['access_token'] = credentials.access_token
	login_session['gplus_id'] = gplus_id
	login_session['name'] = user_info['name']
	login_session['image'] = user_info['picture']
	login_session['email'] = user_info['email']
	# Create user only if we do not already have the same email

	user = db.query(User).filter_by(email=login_session['email']).first()
	if user is None:
		user_created = create_user({'login_session' : login_session})
		login_session['user_id'] = user_created.id
		if user_created is False:
			response = make_response(json.dumps('Failed to create User.'), 
				500)
			response.headers['Content-Type'] = 'application/json'
			return response
	else:
		login_session['user_id'] = user.id
	final_response = make_response(json.dumps("success"), 200)
	return final_response


@app.route('/gdisconnect')
def gdisconnect():
	if 'access_token' not in login_session:
		response = make_response(json.dumps('Current user not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	session_cleared = revoke_session()
	if(session_cleared):
		response = make_response(json.dumps('Successfully disconnected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:
		response = make_response(json.dumps('Something went wrong. User name not found', 400))
		response.headers['Content-Type'] = 'application/json'
		return response


# API Routes  ( these are not used in this app but will allow for additional platform layouts )

@app.route('/Item/delete/<id>')
def Delete(id):
	json_data = { 'success' : False, 'data' : []}
	item = db.query(Item).filter_by(id=id).first()
	if not item or 'user_id' not in login_session \
	   		or not item.user_id or login_session['user_id'] != item.user_id:
		response = make_response(json.dumps({ 'success' : False }), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:
		db.delete(item)
		db.commit()
		response = make_response(json.dumps({ 'success' : True }), 200)
		response.headers['Content-Type'] = 'application/json'
		return response


@app.route('/Item/', methods=['GET'])
def read_item():
	json_data = { 'success' : False, 'data' : []}
	data = db.query(Item, Categories).join(Categories).all()
	if data:
		json_data['success'] = True
		for result in data:
			if result.Items:
				db_item = result.Items
				item = { 
					'name' : db_item.name, 
					'id' : db_item.id, 
					'text' : db_item.text, 
					'categories' : [] 
				}
			if result.Categories:
				cat = result.Categories
				item['categories'].append({ 'name' : cat.name, 'id' : cat.id })
			if item:
				json_data['data'].append(item)
	response = make_response(json.dumps(json_data), 200)
	response.headers['Content-Type'] = 'application/json'
	return response


@app.route('/Item/', methods=['POST'])
def create_item():
	form_data = request.values
	if form_data['hash_key'] != login_session['hash_key']:
		response = make_response(json.dumps('Not Permitted'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	if form_data['title']:
		item = Item( 
				name = form_data['title'],
			 	user_id = login_session['user_id'],
			 	text = form_data['text'].rstrip() or "", 
			 	category_id = form_data['category'] or None
			)
		db.add(item)
		db.commit()
		response = make_response(json.dumps('Success.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:
		response = make_response(json.dumps('Something went wrong'), 400)
		response.headers['Content-Type'] = 'application/json'
		return response


@app.route('/Item/', methods=['UPDATE'])
def update_item():
	form_data = request.values
	if 'id' not in form_data:
		response = make_response(json.dumps('Something went wrong'), 400)
		response.headers['Content-Type'] = 'application/json'
		return response
	if form_data['hash_key'] != login_session['hash_key']:
			response = make_response(json.dumps('Not Permitted'), 401)
			response.headers['Content-Type'] = 'application/json'
			return response
	else:
		item = db.query(Item).filter(Item.id==form_data['id']).first()
		if item.user_id == login_session['user_id']:
			name = form_data.get('title') or item.name
			text = form_data.get('text') or item.text
			category_id = form_data.get('category') or item.category_id
			item_obj = Item(
					id=item.id, 
					name=name, 
					category_id=category_id, 
					text=text.rstrip(), 
					user_id=login_session['user_id']
				)
			newItem = db.merge(item_obj)
			db.commit()
			response = make_response(json.dumps('Success.'), 200)
			response.headers['Content-Type'] = 'application/json'
			return response
		else:
			response = make_response(json.dumps('Not Permitted'), 401)
			response.headers['Content-Type'] = 'application/json'
			return response


@app.route('/Item/<int:id>', methods=['GET'])
def Read(id):
	json_data = { 'success' : False, 'data' : []}
	data = db.query(Item, Categories).join(Categories).filter(Item.id==id).first()
	if data:
		json_data['id'] = data.Items.id
		json_data['name'] = data.Items.name
		json_data['cats'] = []
		if(data.Categories):
			json_data['cats'].append({
				'id' : data.Categories.id,
				'name' : data.Categories.name
				})
	response = make_response(json.dumps(json_data), 200)
	response.headers['Content-Type'] = 'application/json'
	return response


@app.route('/Category/')
def Categories_read():
	json_data = { 'success' : False, 'data' : []}
	data = db.query(Categories).all()
	if data:
		json_data['success'] = True
		for result in data:
			json_data['data'].append({ 
				'name' : result.name, 
				'id' : result.id 
				}) 
	response = make_response(json.dumps(json_data), 200)
	response.headers['Content-Type'] = 'application/json'
	return response


@app.route('/Category/Item/')
def Categories_with_items():
	json_data = { 'success' : False, 'data' : []}
	data = db.query(Categories).all()
	if data:
		json_data['success'] = True
		for result in data:
			cat = {'name' : result.name, 'id' : result.id, 'items' : [] } 
			cats_items = db.query(Item).filter(Item.category_id==result.id).all()
			for item in cats_items:
				cat['items'].append({ 
					'id' : item.id,
					'name' : item.name,
					'text' : item.text
				})
			json_data['data'].append(cat)
	response = make_response(json.dumps(json_data), 200)
	response.headers['Content-Type'] = 'application/json'
	return response


@app.route('/User/delete')
def user_delete():
	user = db.query(User).filter_by(email=login_session['email']).first()
	user.active = 0;
	new_user = db.merge(user)
	db.commit()
	result = revoke_googleplus(2)
	revoke_session()
	return redirect(url_for('layout_home'))


# layout routes

@app.route('/')
def layout_home():
	items = []
	if 'hash_key' not in login_session:
		hash_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
			for x in xrange(32))
		login_session['hash_key'] = hash_key
	data = db.query(Item, Categories).join(Categories).all()
	cats = db.query(Categories).all()
	if data:
		for result in data:
			if result.Items:	
				db_item = result.Items
				item = { 
					'name' : db_item.name, 
					'id' : db_item.id, 
					'text' : db_item.text, 
					'categories' : [] 
				}
			if result.Categories:
				cat = result.Categories
				item['categories'].append({ 'name' : cat.name, 'id' : cat.id })
			if item:
				items.append(item)
	return render_template('home.html', data = { 
				"login_session" : login_session, 
				"list" : items, 
				"cats" : cats 
			})


@app.route('/category/<int:id>')
def layout_category(id):
	items = []
	cat_name = ""
	data = db.query(Item, Categories).filter(Item.category_id==id).join(Categories).all()
	cats = db.query(Categories).all()
	selected_cat = db.query(Categories).filter_by(id=id).first()
	if data:
		for result in data:
			if result.Items:
				db_item = result.Items
				item = { 
					'name' : db_item.name, 
					'id' : db_item.id, 
					'text' : db_item.text, 
					'categories' : [] 
				}
			if result.Categories:
				cat = result.Categories
				item['categories'].append({ 'name' : cat.name, 'id' : cat.id })
				cat_name = item['categories'][0]['name'];
			if item:
				items.append(item)
	return render_template('home.html', data = { 
				"login_session" : login_session, 
				"list" : items, 
				"cats" : cats, 
				"selected_cat" : selected_cat 
			})


@app.route('/user/<int:id>')
def layout_user_items(id):
	items = []
	name = ""
	cats = db.query(Categories).all()
	user = db.query(User).filter(User.id==id).first()
	if user:
		name = user.email;
		data = db.query(Item, Categories).join(Categories).filter(Item.user_id==id).all()
		if data:
			for result in data:
				if result.Items:
					db_item = result.Items
					item = { 
						'name' : db_item.name, 
						'id' : db_item.id, 
						'text' : db_item.text, 
						'categories' : [] 
					}
				if result.Categories:
					cat = result.Categories
					item['categories'].append({ 'name' : cat.name, 'id' : cat.id })
				if item:
					items.append(item)
	return render_template('home.html', data = { 
				"login_session" : login_session, 
				"list" : items, 
				"cats" : cats, 
				"username" : name 
			})


@app.route('/new-item')
def layout_new_item():
	if 'user_id' not in login_session:
		return redirect(url_for('layout_home'))
	cats = db.query(Categories).all()
	return render_template('add_item.html', data = { 
				"login_session" : login_session, 
				"categories" : cats
			})


@app.route('/item/<int:id>')
def layout_item(id):
	item = {}
	db_data = db.query(Item, Categories).join(Categories).filter(Item.id==id).first()
	cats = db.query(Categories).all()
	if db_data:
		item['id'] = db_data.Items.id
		item['name'] = db_data.Items.name
		item['text'] = db_data.Items.text
		item['user_id'] = db_data.Items.user_id
		item['cats'] = []
		if(db_data.Categories):
			item['cats'].append({
				'id' : db_data.Categories.id,
				'name' : db_data.Categories.name
			})
	return render_template('item.html', data = { 
				"login_session" : login_session, 
				"item" : item, 
				"cats" : cats 
			})


@app.route('/update-item/<int:ids>')
def layout_update_item(ids):
	item = False
	data = db.query(Item, Categories).join(Categories).filter(Item.id==ids).first()
	if data:
		item = data.Items
	if not item or 'user_id' not in login_session \
				or item.user_id != login_session['user_id']:
		return redirect(url_for('layout_home'))
	else:
		item_cats = data.Categories
		cats = db.query(Categories).all()
		return render_template('add_item.html', data = { 
			"update" : 1, 
			"login_session" : login_session, 
			"categories" : cats, 
			"item" : item,
			"item_cats" : item_cats
		})


# functions

def revoke_session():
	for key in session_keys:
		if key in login_session:
			del login_session[key]
	if 'name' in login_session:
		return False
	else:
		return True


def revoke_googleplus(max_attempts=3):
	i = 0
	while i < max_attempts:
		http = httplib2.Http()
		result = http.request('https://accounts.google.com/o/oauth2/revoke?token=%s' 
		   	% login_session['access_token'], 'GET')[0]
		if result['status'] == '200':
			return 1
	return 0


def create_user(args):
	if 'login_session' not in args:
		return False
	user_session = args['login_session']
	user = User(name=user_session['name'], image=user_session['image'], 
		email=user_session['email'], active=1)
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
		user = db.query(User).filter_by(email=value).first()
		user.active = 0;
		new_user = db.merge(user)
		db.commit()
	return user


# flask start

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)