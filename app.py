#!/usr/bin/python
'''
    This application is a simple demonstration of using APIC-EM
    dynamic QoS to modify QoS policies based on external factors
    such as weather events, power excursions, etc.
'''

__author__ = 'sluzynsk'

from flask import Flask
from flask import render_template
from flask import redirect
from flask import url_for
from flask import jsonify
from flask import request
from flask import g
import apic
import sqlite3
import os
import requests



app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    EDQOS_DATA_SERVER='localhost'
))

if os.environ.get("EDQOS_DATA_SERVER"):
    app.config.update(dict(
        EDQOS_DATA_SERVER=os.environ.get("EDQOS_DATA_SERVER")
    ))

def get_dataserv():
    if not hasattr(g, 'data_server'):
        g.data_server = "http://" + app.config['EDQOS_DATA_SERVER']
    return g.data_server

# These API calls retrieve information from the data/configuration
# service.

@app.route('/_get_apps/')
def get_apps():
    pol = request.args.get('policy')
    # get the app list from the data server
    req_url = get_dataserv() + "/_get_apps_db?policy=" + pol
    entries = requests.get(req_url)
    if len(entries.text)>3:
        return jsonify(map(dict, entries))
    else:
        return ""


# These API calls retrieve information from the APIC-EM.

@app.route('/_is_relevant/')
def check_relevant():
    app = request.args.get('app')
    policy_tag = request.args.get('policy')
    ticket = apic.get_ticket()
    app_id = apic.get_app_id(ticket, app)
    policy = apic.get_policy(ticket, policy_tag)
    return jsonify(apic.get_app_state(policy, app_id, app))


@app.route('/_get_policy_scope/')
def get_policy_scope():
    result = apic.get_policy_scope(apic.get_ticket())
    print jsonify(result)
    return jsonify(result)


# These API calls are used by the config/status UI to manipulate
# app state and the configuration.

@app.route('/_save_config/', methods=["POST"])
def save_config():
    applist = request.form.getlist('selections')
    policy_tag = request.form.getlist('policy_tag')[0]
    apps = applist[0].split(",")
    # map this to the data server
    db = get_db()
    cur = db.execute('delete from edqos')
    for item in apps:
        cur = db.execute('insert into edqos (policy, app) values (?,?)',
            [policy_tag, item])
    db.commit()
    return jsonify(applist)



@app.route('/event/on/')
def event_on():
    policy_scope = request.args.get('policy')
    event_status = True
    req_url = get_dataserv() + "/_get_apps_db?policy=" + policy_scope
    saved_apps = requests.get(req_url)
    app_list = []
    for app in saved_apps:
        app_list.append(app['app'])
    #return str(app_list)
    service_ticket = apic.get_ticket()
    return apic.put_policy_update(service_ticket,
                                  apic.update_app_state(service_ticket,
                                                        event_status,
                                                        apic.get_policy(service_ticket, policy_scope),
                                                        app_list),
                                  policy_scope)


@app.route('/event/off/')
def event_off():
    policy_scope = request.args.get('policy')
    event_status = False
    req_url = get_dataserv() + "/_get_apps_db?policy=" + policy_scope
    saved_apps = requests.get(req_url)
    app_list = []
    for app in saved_apps:
        app_list.append(app['app'])
    # return str(app_list)
    service_ticket = apic.get_ticket()
    return apic.put_policy_update(service_ticket,
                                  apic.update_app_state(service_ticket,
                                                        event_status,
                                                        apic.get_policy(service_ticket, policy_scope),
                                                        app_list),
                                  policy_scope)


# Currently unused call to the weather plugin

@app.route('/weather/')
def check_weather():
    city = weather.getCity()
    state = weather.getState()
    temp = weather.getTemp(weather.getCurrentConditions())
    weather_description = weather.getWeather(weather.getCurrentConditions())
    weather_string = "The current weather in "+city+", "+state+" is "+str(temp)+" and "+weather_description
    return weather_string


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
