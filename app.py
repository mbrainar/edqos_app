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
import os
import requests
from login import login
from apic import Policy
from apic import get_policy_scope
from apic import Applications




app = Flask(__name__)
api = Api(app)

app.config.from_object(__name__)

# default the data server to localhost to ease debugging
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


# These API calls retrieve information from the data/configuration service.

class GetApps(Resource):
    """
    This will get the list of applications that have been selected and saved in the database
    """
    def get(self):
        pol = request.args.get('policy')
        # get the app list from the data server
        req_url = get_dataserv() + "/_get_apps_db/?policy=" + pol
        entries = requests.get(req_url)
        return entries.json()


# These API calls retrieve information from the APIC-EM.


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
        saved_apps = requests.get(req_url, verify=False).json()
        app_list = []
        for item in saved_apps:
            app_list.append(item['app'])
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
        saved_apps = requests.get(req_url, verify=False).json()
        app_list = []
        for item in saved_apps:
            app_list.append(item['app'])
        service_ticket = apic.get_ticket()
        return apic.put_policy_update(service_ticket,
                                      apic.update_app_state(service_ticket,
                                                            event_status,
                                                            apic.get_policy(service_ticket, policy_scope),
                                                            app_list),
                                      policy_scope)

client = login()

# Applications API class
class GetApplications(Resource):
    """
    Get applications and returns as list
    """
    def get(self):
        applications_object = Applications(client).applications
        applications_list = [app.name for app in applications_object.response]
        return applications_list

# Policy Tags API class
class GetPolicyTags(Resource):
    """
    Gets policy tags and returns as list
    """
    def get(self):
        policy_tags_object = Policy(client).policy_tags
        policy_tags_list = [tag.policyTag for tag in policy_tags_object.response]
        return policy_tags_list

# Application relevance API class
class GetRelevance(Resource):
    """
    Checks current relevanceLevel of an app within a given policy scope
    <url>/api/relevance/?policy=<policy scope>&app=<app name>
    """
    def get(self):
        app_name = request.args.get('app')
        policy_tag = request.args.get('policy')
        return Policy(client).app_relevance(policy_tag, app_name)



# Create API resources
api.add_resource(GetApplications, '/api/applications/')
api.add_resource(GetPolicyTags, '/api/policy_tags/')
api.add_resource(GetRelevance, '/api/relevance/')


api.add_resource(GetApps, '/_get_apps/')
api.add_resource(SaveConfig, '/_save_config_db/')
api.add_resource(EventOn,'/event/on/')
api.add_resource(EventOff, '/event/off/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
