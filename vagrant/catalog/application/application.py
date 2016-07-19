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
    """ Auth Route: logout - GET /logout

        Performs the necessary steps to end users session. If additional
        authentication services are used that logic will be contained here.
    """

    return redirect(url_for('gdisconnect'))


@app.route('/connect-googleplus/', methods=['POST'])
def connect_googleplus():
    """ Auth Route: connect_googleplus - POST /connect-googleplus

        Route to handle authentication using google's oauth2 api.
        This accepts POST http method. Returns 200 on completed
        authentication. Returns another appropriate error code on
        for any errors encountered.

        Post Parameters:
        code: Response code from google oauth2 api
    """

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
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
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
    # user is valid at this point, grab and store data in session

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    user_info = requests.get(userinfo_url, params=params).json()
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id
    login_session['name'] = user_info['name']
    login_session['image'] = user_info['picture']
    login_session['email'] = user_info['email']
    # Create user with our login session only if not present

    user_created = create_user({'login_session': login_session})
    login_session['user_id'] = user_created.id
    return make_response(json.dumps("success"), 200)


@app.route('/gdisconnect')
def gdisconnect():
    """ Auth Route: gdisconnect - GET /gdisconnect

        Logs out a user who is logged in using google oauth2
        authentication.
    """

    if 'access_token' not in login_session:
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # user connected perform disconnect or return error

    session_cleared = revoke_session()
    if(session_cleared):
        response = make_response(json.dumps('Successfully disconnected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Something went wrong.\
                                 User name not found', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# API Routes
#   most of these are not used in this app but will allow for
#   additional platform layouts.

@app.route('/Item/delete/<id>')
def Delete(id):
    """ API Route: Delete - GET /Item/delete/<id>

        Enpoint to perform delete on a given item. Note: user
        must be authorized to delete for this to succeed. Returns
        appropriate response on failure or success.

        Args:
        id: integer that represents the item to delete
    """

    json_data = {'success': False, 'data': []}
    # get item and check for authorization

    item = db.query(Item).filter_by(id=id).first()
    if not item or 'user_id' not in login_session \
       or not item.user_id or login_session['user_id'] != item.user_id:
        # item not found or user not authorized to delete

        response = make_response(json.dumps({'success': False}), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # item found, user authorized, delete it

        db.delete(item)
        db.commit()
        response = make_response(json.dumps({'success': True}), 200)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/Item/', methods=['GET'])
def read_item():
    """ API Route: read_item - GET /Item/

        Enpoint to perform general read on Items. This will return
        all available items.
    """

    json_data = {'success': False, 'data': []}
    # get data or return empty

    data = db.query(Item, Categories).join(Categories).all()
    if not data or not data[0].Items:
        response = make_response(json.dumps(json_data), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # data found

    json_data['success'] = True
    for result in data:
        # map the data of each item and add to our data array

        db_item = result.Items
        item = {
            'name': db_item.name,
            'id': db_item.id,
            'text': db_item.text,
            'categories': []
            }
        if result.Categories:
            cat = result.Categories
            item['categories'].append({'name': cat.name, 'id': cat.id})
        if item:
            json_data['data'].append(item)
    response = make_response(json.dumps(json_data), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/Item/', methods=['POST'])
def create_item():
    """ API Route: create_item - POST /Item/delete/<id>

        Enpoint to create a new Item entry in the database. This accepts
        POST http method.

        Post Parameters:
        title: name/title of item
        text: description and/or text copy about the item
        category: integer representing id of selected category
        hash_key: form hash must match sessions hash
    """

    form_data = request.values
    if form_data['hash_key'] != login_session['hash_key']:
        # form csrf didnt match session or isnt there

        response = make_response(json.dumps('Not Permitted'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if form_data['title']:
        # if we have required fields create Item object with our data

        item = Item(
            name=form_data['title'],
            user_id=login_session['user_id'],
            text=form_data['text'].rstrip() or "",
            category_id=form_data['category'] or None
        )
        # save Item to db

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
    """ API Route: update_item - UPDATE /Item/

        Enpoint to update an existing Item in our
        database. This requires that id matches an existing
        record. This will not create a new record.

        Post Parameters:
        id: integer of the item thats being updated
        title: name/title of item
        text: description and/or text copy about the item
        category: integer representing id of selected category
        hash_key: form hash must match sessions hash
    """

    form_data = request.values
    if form_data['hash_key'] != login_session['hash_key']:
        # form csrf didnt match session or isnt there

        response = make_response(json.dumps('Not Permitted'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    if 'id' not in form_data:
        # id of item to update wasnt found

        response = make_response(json.dumps('Something went wrong'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response
    item = db.query(Item).filter(Item.id == form_data['id']).first()
    if item.user_id != login_session['user_id']:
        # user is not authorized to edit this item

        response = make_response(json.dumps('Not Permitted'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # user authorized, csrf valid

    name = form_data.get('title') or item.name
    text = form_data.get('text') or item.text
    category_id = form_data.get('category') or item.category_id
    # create item object with our id and merged form data

    item_obj = Item(
        id=item.id,
        name=name,
        category_id=category_id,
        text=text.rstrip(),
        user_id=login_session['user_id']
        )

    # update item (merge)

    newItem = db.merge(item_obj)
    db.commit()
    response = make_response(json.dumps('Success.'), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/Item/<int:id>', methods=['GET'])
def Read(id):
    """ API Route: Read - GET /Item/<int:id>

        Enpoint to read a specific item from the database.

        Args:
        id: integer of the record to read
    """

    json_data = {'success': False, 'data': []}
    data = db.query(Item, Categories)\
        .join(Categories).filter(Item.id == id).first()
    if data:
        # data was found for this id, prep then return it

        json_data['id'] = data.Items.id
        json_data['name'] = data.Items.name
        json_data['cats'] = []
        if(data.Categories):
            json_data['cats'].append({
                'id': data.Categories.id,
                'name': data.Categories.name
            })
    response = make_response(json.dumps(json_data), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/Category/')
def Categories_read():
    """ API Route: Categories_read - GET /Category/

        Enpoint to read all categories from the database.
    """

    json_data = {'success': False, 'data': []}
    data = db.query(Categories).all()
    if data:
        # catgegory data was found, prep then return it

        json_data['success'] = True
        for result in data:
            json_data['data'].append({
                'name': result.name,
                'id': result.id
            })
    response = make_response(json.dumps(json_data), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/Category/Item/')
def Categories_with_items():
    """ API Route: Categories_with_items - GET /Category/Item/

        Enpoint to read all categories and the items contained in
        that category.
    """

    json_data = {'success': False, 'data': []}
    data = db.query(Categories).all()
    if not data:
        response = make_response(json.dumps(json_data), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    # data was found

    json_data['success'] = True
    for result in data:
        # query items for each category

        cat = {'name': result.name, 'id': result.id, 'items': []}
        cats_items = db.query(Item).filter(Item.category_id == result.id).all()
        for item in cats_items:
            # add data to our response

            cat['items'].append({
                'id': item.id,
                'name': item.name,
                'text': item.text
            })
            json_data['data'].append(cat)
    response = make_response(json.dumps(json_data), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/User/delete')
def user_delete():
    """ API Route: user_delete - GET /User/delete'

        Deletes the current user logged in. We use
        delete_user function to run the removal from the DB.
        See documention for that function for more info. We
        also revoke active tokens here.
    """

    deleted_user = delete_user({"email": login_session['email']})
    result = revoke_googleplus(2)   # how many attempts to revoke
    revoke_session()
    return redirect(url_for('layout_home'))


# layout routes

@app.route('/')
def layout_home():
    """ Layout Route: layout_home

        Renders homepage with the post necessary data

        Uses Template: home.html
    """

    items = []
    if 'hash_key' not in login_session:
        # generate a hash if we dont already have one

        hash_key = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['hash_key'] = hash_key
    data = db.query(Item, Categories).join(Categories).all()
    cats = db.query(Categories).all()
    if not data or not data[0].Items:
        return render_template('home.html', data={
                    "login_session": login_session
                })
    # data was found, prepare it for template use

    for result in data:
        # map the data of each item and add to our data array

        db_item = result.Items
        item = {
            'name': db_item.name,
            'id': db_item.id,
            'text': db_item.text,
            'categories': []
            }
        if result.Categories:
            cat = result.Categories
            item['categories'].append(
                    {'name': cat.name, 'id': cat.id})
        items.append(item)
    return render_template('home.html', data={
                "login_session": login_session,
                "list": items,
                "cats": cats
            })


@app.route('/category/<int:id>')
def layout_category(id):
    """ Layout Route: layout_category

        Renders posts all posts for the given category id.

        Args:
          id: category id for the posts we want to see

        Uses Template: home.html
    """

    items = []
    cat_name = ""
    # get our data

    data = db.query(Item, Categories).filter(Item.category_id == id)\
        .join(Categories).all()
    cats = db.query(Categories).all()
    selected_cat = db.query(Categories).filter_by(id=id).first()
    # render empty if none

    if not data or not data[0].Items:
        return render_template('home.html', data={
                    "login_session": login_session,
                    "cats": cats,
                    "selected_cat": selected_cat
                })
    # has data, prepare it for template use

    for result in data:
        # map the data of each item and add to our data array

        db_item = result.Items
        item = {
            "name": db_item.name,
            "id": db_item.id,
            "text": db_item.text,
            "categories": []
            }
        if result.Categories:
            cat = result.Categories
            item['categories'].append({
                'name': cat.name, 'id': cat.id})
            cat_name = item['categories'][0]['name']
        items.append(item)
    return render_template('home.html', data={
                "login_session": login_session,
                "list": items,
                "cats": cats,
                "selected_cat": selected_cat
            })


@app.route('/user/<int:id>')
def layout_user_items(id):
    """ Layout Route: layout_user_items

        Renders posts for a specific user using
        our homepage template.

        Args:
          id: user id for the posts we want to see

        Uses Template: home.html
    """

    items = []
    name = ""
    cats = db.query(Categories).all()
    user = db.query(User).filter(User.id == id).first()
    if not user:
        return redirect(url_for('layout_home'))
    # user was found for the given id, grab their data or render empty

    name = user.email
    data = db.query(Item, Categories).join(Categories)\
        .filter(Item.user_id == id).all()
    if not data or not data[0].Items:
        return render_template('home.html', data={
                "login_session": login_session,
                "list": items,
                "cats": cats,
                "username": name
            })
    # data found for user

    for result in data:
        # map the data of each item and add to our data array

        db_item = result.Items
        item = {
            "name": db_item.name,
            "id": db_item.id,
            "text": db_item.text,
            "categories": []
            }
        if result.Categories:
            cat = result.Categories
            item["categories"].append({"name": cat.name, "id": cat.id})
        items.append(item)
    return render_template('home.html', data={
                "login_session": login_session,
                "list": items,
                "cats": cats,
                "username": name
            })


@app.route('/new-item')
def layout_new_item():
    """ Layout Route: layout_new_item

        Renders form to create a new item in the
        database. Note: user must be logged in to
        reach this route.

        Uses Template: add_item.html
    """

    if 'user_id' not in login_session:
        return redirect(url_for('layout_home'))
    # fill template with cats

    cats = db.query(Categories).all()
    return render_template('add_item.html', data={
                "login_session": login_session,
                "categories": cats
            })


@app.route('/item/<int:id>')
def layout_item(id):
    """ Layout Route: layout_item

        Renders single post for the given item id.

        Args:
          id: item id for the post we want to see

        Uses Template: item.html
    """

    item = {}
    # get data from db or render empty

    db_data = db.query(Item, Categories).join(Categories)\
        .filter(Item.id == id).first()
    cats = db.query(Categories).all()
    if not db_data:
        return render_template('item.html', data={
                "login_session": login_session,
                "item": item,
                "cats": cats
            })
    # has data, map data for our reponse and return it

    item['id'] = db_data.Items.id
    item['name'] = db_data.Items.name
    item['text'] = db_data.Items.text
    item['user_id'] = db_data.Items.user_id
    item['cats'] = []
    if(db_data.Categories):
        item['cats'].append({
            'id': db_data.Categories.id,
            'name': db_data.Categories.name
        })
    return render_template('item.html', data={
                "login_session": login_session,
                "item": item,
                "cats": cats
            })


@app.route('/update-item/<int:ids>')
def layout_update_item(ids):
    """ Layout Route: layout_update_item

        Renders update item form for the selected item
        given the user is authorized to edit. Only content
        owners can edit.

        Args:
          id: item id for the post we want to update

        Uses Template: add_item.html
    """

    item = False
    # get data and authorize user otherwise redirect

    data = db.query(Item, Categories).join(Categories)\
        .filter(Item.id == ids).first()
    if data:
        item = data.Items
    if not item or 'user_id' not in login_session \
            or item.user_id != login_session['user_id']:
        return redirect(url_for('layout_home'))
    # item found and user authorized return template

    item_cats = data.Categories
    cats = db.query(Categories).all()
    return render_template('add_item.html', data={
        "update": 1,
        "login_session": login_session,
        "categories": cats,
        "item": item,
        "item_cats": item_cats
    })


# functions

def revoke_session():
    """ Called to clear any current sessions stored in the application.

        Takes 0 arguments however this requires value session_keys to
        be set to the keys that represent your session.

        session_keys : ["user_id", ...]
    """

    for key in session_keys:
        if key in login_session:
            del login_session[key]
    if 'name' in login_session:
        return False
    else:
        return True


def revoke_googleplus(max_attempts=3):
    """ Revokes Oauth2 token from google apis

        Attempts to ping google's api to revoke the token
        stored in login_session. This will try "max_attempts"
        number of times before returning result. Typically
        "max_attempts" will be set at 1. In some cases you may
        need to increase this. User can revoke their own
        permissions through their google back end.

        Args:
        max_attempts: integer value that indicates the maximum
            number of requests made to the api.
    """

    i = 0
    # ping api for until success or limit reached

    while i < max_attempts:
        http = httplib2.Http()
        result = http.request('https://accounts.google.com/o/oauth2\
            /revoke?token=%s' % login_session['access_token'], 'GET')[0]
        if result['status'] == '200':
            # success we can just reurn response now

            return 1
        i += 1
    return 0


def create_user(args):
    """ Creates a user using the given parameters.

        Converts a login_session value into a new user.
        Note: this function assumes that we do not want
        to overwrite an existing user.

        Args:
        email: validated email of user
        name: validated username of user
        image: validated image url of user. Note: this
            simply points to the image. Upload handled
            elsewhere. (if applicable)

        Return Types:
        Success: Indicates user added or found, returns tuple
            of the added/found user
        Fail: returns False.
    """

    if 'login_session' not in args:
        return False
    # check for existing user, if found return it

    user_session = args['login_session']
    user_found = db.query(User).filter_by(email=user_session['email']).first()
    if user_found:
        return user_found
    # user not found so so create new one and return it

    user = User(name=user_session['name'], image=user_session['image'],
                email=user_session['email'], active=1)
    db.add(user)
    db.commit()
    added_user = db.query(User).filter_by(email=user_session['email']).one()
    return added_user


def delete_user(args):
    """ Deletes user based on the given parameters.

        Deletes the user with the specified email. Note:
        application never deletes user records, instead
        we flag user as inactive so that accounts can be
        re opened.

        Args:
        email: email of user to delete

        Return Types:
        Success: Returns deleted user
        Fail: returns False if something goes wrong.
    """

    if 'email' in args:
        user = db.query(User).filter_by(email=args['email']).first()
        # we dont want to delete our record entirely just set to inactive

        user.active = 0
        new_user = db.merge(user)
        db.commit()
    if user:
        return user
    else:
        return False


# flask start

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
