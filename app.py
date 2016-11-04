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
from flask_restful import Resource, Api
import apic
import sqlite3
import os
import requests
import json



app = Flask(__name__)
api = Api(app)

app.config.from_object(__name__)

app.config.update(dict(
    EDQOS_DATA_SERVER='localhost:5002'
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

class GetApps(Resource):
    def get(self):
        pol = request.args.get('policy')
        # get the app list from the data server
        req_url = get_dataserv() + "/_get_apps_db/?policy=" + pol
        entries = requests.get(req_url)
        return entries.json()


# These API calls retrieve information from the APIC-EM.

class CheckIsRelevant(Resource):
    def get(self):
        app = request.args.get('app')
        policy_tag = request.args.get('policy')
        ticket = apic.get_ticket()
        app_id = apic.get_app_id(ticket, app)
        policy = apic.get_policy(ticket, policy_tag)
        return apic.get_app_state(policy, app_id, app)



class GetPolicyScope(Resource):
    def get(self):
        return apic.get_policy_scope(apic.get_ticket())


class GetApplications(Resource):
    def get(self):
        policy_tag = request.args.get('policy')
        result = apic.get_applications(apic.get_ticket(), policy_tag)
        return result


# These API calls are used by the config/status UI to manipulate
# app state and the configuration.

class SaveConfig(Resource):
    def post(self):
        applist = request.form.getlist('selections')
        policy_tag = request.form.getlist('policy_tag')[0]
        apps = applist[0].split(",")
        # map this to the data server
        req_url = get_dataserv() + "/_save_config_db/"
        payload = { "selections": applist,
                    "policy_tag": policy_tag }
        response = requests.post(req_url, data=payload)
        return



class EventOn(Resource):
    def get(self):
        policy_scope = request.args.get('policy')
        event_status = True
        req_url = get_dataserv() + "/_get_apps_db/?policy=" + policy_scope
        saved_apps = requests.get(req_url, verify=False)
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


class EventOff(Resource):
    def get(self):
        policy_scope = request.args.get('policy')
        event_status = False
        req_url = get_dataserv() + "/_get_apps_db/?policy=" + policy_scope
        saved_apps = requests.get(req_url, verify=False)
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


api.add_resource(GetApplications, '/_get_applications/')
api.add_resource(GetPolicyScope, '/_get_policy_scope/')
api.add_resource(CheckIsRelevant, '/_is_relevant/')
api.add_resource(GetApps, '/_get_apps/')
api.add_resource(SaveConfig, '/_save_config_db/')
api.add_resource(EventOn,'/event/on/')
api.add_resource(EventOff, '/event/off')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
