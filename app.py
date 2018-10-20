# Initial setup
from flask import Flask, request, redirect, url_for

import json
import requests
import time
import re
import pyrebase
import random
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
    

# Flask object creation
app = Flask(__name__)


# Index page
@app.route("/")
def index():
    return_value = {"message": "Welcome to the Notify-IPL API!"}
    json_string = json.dumps(return_value)
    return json_string


# Notification page
@app.route("/offer")
def noti():
    # Firebase configuration
    config = {
        "apiKey": "AIzaSyDDVJIFHI-xXAb2CNgjHWU5VTbTwTCcLMs",
        "authDomain": "flyingpanda-41a88.firebaseapp.com",
        "databaseURL": "https://flyingpanda-41a88.firebaseio.com",
        "projectId": "flyingpanda-41a88",
        "storageBucket": "flyingpanda-41a88.appspot.com"
    }
    firebase = pyrebase.initialize_app(config)
    db = firebase.database()
    all_users = db.child("data").get()
    lines = []
    for user in all_users.each():
        #print(user.key()) 
        for item in user.val():
            old_timestamp = 0
            #print(item)  
            line = []
            for timestmp in user.val()[item]:
                if(int(timestmp)-old_timestamp > 200000):
                    #print(timestmp)
                    if(len(line)>2):
                        lines.append(list(line))
                    line = [item]
                    line.append(user.val()[item][timestmp]["Flight"])
                    line.append(user.val()[item][timestmp]["vendor"])
                else:
                    line.append(user.val()[item][timestmp]["vendor"])
                old_timestamp = int(timestmp)
            if(len(line)>2):
                lines.append(list(line))     
            line = [item]
    te = TransactionEncoder()
    te_ary = te.fit(lines).transform(lines)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    frequent_itemsets = apriori(df, min_support=0.035, use_colnames=True)
    frequent_itemsets['length'] = frequent_itemsets['itemsets'].apply(lambda x: len(x))
    for item in (frequent_itemsets[ (frequent_itemsets['length'] > 2) &
                   (frequent_itemsets['support'] >= 0.035) ]['itemsets']):
        print(list(item))
    return json.dumps(item)


# Help page
@app.route("/help")
def help():
    return_value = {"message": "The available commands for this API will be visible here :)"}

    json_string = json.dumps(return_value)

    return json_string


# Error page
@app.errorhandler(404)
def page_not_found(e):
    return json.dumps("error"), 404


if __name__ == "__main__":
    app.debug = True
    app.run()
