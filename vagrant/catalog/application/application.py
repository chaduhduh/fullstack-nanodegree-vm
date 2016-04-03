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
	item = Items(name="Item 1")
	session.add(item)
	session.commit()
	return "added items"

@app.route('/test')
def HelloWorld():
	item = session.query(Items).first()
	return "Item is " + item.name
 	# items = session.query(MenuItem).filter_by(restaurant_id=restaurant.id)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)