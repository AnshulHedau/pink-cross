# Initial setup

from flask import Flask, request, redirect, url_for

import json
import pyrebase
import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
import requests
import time
from datetime import datetime, timedelta
from autocorrect import spell
from bs4 import BeautifulSoup

# Flask object creation
app = Flask(__name__)

# Firebase configuration
config = {
    "apiKey": "AIzaSyDNio_QK2oYeytYQ_6H1I4yQYzgFEuSWPg",
    "authDomain": "edubuddy-b7f29.firebaseapp.com",
    "databaseURL": "https://edubuddy-b7f29.firebaseio.com",
    "storageBucket": "edubuddy-b7f29.appspot.com",
}

firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
db = firebase.database()

# Index page
@app.route("/")

def index():
	return_value = {"message":"Welcome to the Edu-Buddy API!"}
	json_string = json.dumps(return_value)
	return json_string

# Query page
@app.route("/query",methods = ["GET"])

def queryd():
	query_string = request.args.get('query').lower()
	token_words = nltk.word_tokenize(query_string)
	
	# Keeping only alphabetical words (removing punctuations)
	cleaned_words = [word for word in token_words if word.isalpha()]
	
	# Spell checking for the words
	cleaned_words = [spell(word) for word in cleaned_words]
	
	# Removing the stop-words
	stop_words = stopwords.words('english')
	stopped_words = [word for word in cleaned_words if not word in stop_words]
		
	porter = PorterStemmer()
	stemmed_words = [porter.stem(word) for word in stopped_words]
	stemmed_words.sort()
	data_repository = json.load(open('data_repository.json'))
	
	# Decision making for viewing the schedule
	if(("show" in stemmed_words or "what" in cleaned_words or "view" in cleaned_words or "enlist" in cleaned_words) and "schedul" in stemmed_words):
		# Checking if the 'after' keyword is present
		after_keyword = 0
		if ("after" in token_words):
			after_keyword = 1
		
		for key_parameter in stemmed_words:
			# The time needs to be adjusted for the UTC standard
			# Time to be sent in case of no specific day mentioned
			milliseconds = str(int(round(time.time() * 1000) + 5.5 * 3600 * 1000))
			
			try:
				# Get time for 'now' or 'today'
				if(key_parameter == "now" or key_parameter == "today"):
					milliseconds = str(int(round(time.time() * 1000) + 5.5 * 3600 * 1000))

					data_repository["show"]["schedul"][key_parameter]["data_2"] = milliseconds
					return json.dumps(data_repository["show"]["schedul"][key_parameter])
				
				# Get time for 'tomorrow'
				elif(key_parameter == "tomorrow"):
					# The time is adjusted to get the time for the next day's 12:00 AM
					epoch = datetime.utcfromtimestamp(0)
					
					# Add a time of one day to the calculation
					if (after_keyword == 1):
						now_time = datetime.now() + timedelta(days = 2) + timedelta(hours = 5) + timedelta(minutes = 30)
					else:
						now_time = datetime.now() + timedelta(days = 1) + timedelta(hours = 5) + timedelta(minutes = 30)
						
					tomorrow_time = now_time.replace(hour=0, minute=0, second=0, microsecond=0)
					milliseconds = str(int((tomorrow_time - epoch).total_seconds() * 1000))
					
					data_repository["show"]["schedul"][key_parameter]["data_2"] = milliseconds
					return json.dumps(data_repository["show"]["schedul"][key_parameter])
			except:
				fail = 1
		
		data_repository["show"]["schedul"]["today"]["data_2"] = milliseconds
		return json.dumps(data_repository["show"]["schedul"]["today"])
		
	elif("add" in stemmed_words and ("reminder" or "event" in stemmed_words)):
		return json.dumps(data_repository["add"])
		
	elif("interest" in stemmed_words or "news" in stemmed_words):
		url = ('https://newsapi.org/v2/top-headlines?country=in&apiKey=dfc5903247a14791b9db4a0dd940f0cf')
		response = requests.get(url)
		response = response.json()
		
		data_repository["news"]["data_1"] = response["articles"][0]["title"]
		data_repository["news"]["data_2"] = response["articles"][0]["description"]
		return json.dumps(data_repository["news"])
		
	else:
		return json.dumps(data_repository["error"])

# Courses Query page
@app.route("/courses",methods = ["GET"])

def courses():
	query_string = request.args.get('query')
	page = requests.get("https://www.coursera.org/courses?languages=en&query="+query_string)
	soup = BeautifulSoup(page.content, 'html.parser')
	
	data = soup.find_all('h2',class_="color-primary-text headline-1-text flex-1",limit=10)
	list_data = []
	
	for i in range(10):
		list_data.append(str(data[i])[73:-5])
	list_url = []
 
	for link in soup.findAll('a', class_="rc-OfferingCard nostyle",limit=10):
		list_url.append('https://www.coursera.org' + link.get('href'))
		
	courses = {"courses": {"names" : list_data, "url" : list_url}}
	return json.dumps(courses)

# Database page
@app.route("/data",methods = ["GET"])

def data():
	user_token = request.args.get('user_token')
	user_email = request.args.get('email')
	
	users = db.child("users").get(user_token)
	values  = users.val()
	json_string = json.dumps(values)
	
	return json_string

# Help page
@app.route("/help")

def help():
	return_value = {"message":"The available commands for this API will be visible here :)"}
	
	json_string = json.dumps(return_value)

	return json_string

# Authenticate user page
@app.route("/authenticate", methods = ["GET"])

def authenticate_user():
	try:
		email = request.args.get('email')
		password = request.args.get('password')
		
		user = auth.sign_in_with_email_and_password(email, password)
		return_value = {"data":user['idToken']}

		json_string = json.dumps(return_value)
		return json_string	

	except:
		return json.dumps(data_repository["error"])

# User details page
@app.route("/user_details", methods = ["GET"])

def user_details():
	try:
		user_token = request.args.get('user_token')
		account_information = auth.get_account_info(user_token)

		json_string = json.dumps(account_information)
		return json_string

	except:
		return json.dumps(data_repository["error"])

# Error page
@app.errorhandler(404)

def page_not_found(e):
	return json.dumps(data_repository["error"]), 404

if __name__ == "__main__":
	app.debug = True
	app.run()
