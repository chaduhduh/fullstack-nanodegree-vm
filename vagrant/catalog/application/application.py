from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Items


# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

app = Flask(__name__)
app.config.from_object(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# functions
def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


# routes
@app.route('/')
def Home():
	return "Welcome"

@app.route('/update-item/<name>')
def Update(name):
	item = session.query(Items).filter_by(name=name).first()
	if item:
		# do some alterations to data here
		session.add(item)
		session.commit()
		return "updated " + item.name
	else: 
		return "item not found"

@app.route('/delete-item/<name>')
def Delete(name):
	item = session.query(Items).filter_by(name=name).first()
	session.delete(item)
	session.commit()
	return "deleted"

@app.route('/create-item/<name>')
def Create(name):
	if(name):
		# validate data first
		item = Items(name=name)
		session.add(item)
		session.commit()
		return "added item named = " + item.name
	else:
		return "nothing added"

@app.route('/read-item/<name>')
def Read(name):
	item = session.query(Items).filter_by(name=name).first()
	if item:
		return "Item is " + item.name
	else:
		return "Nothing to show here"
 	# items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)