#!/usr/bin/python
'''
    This application is a simple demonstration of using APIC-EM
    dynamic QoS to modify QoS policies based on external factors
    such as weather events, power excursions, etc.
'''

__author__ = 'mbrainar'

from flask import Flask
from flask import request
from flask_restful import Resource
from flask_restful import Api
from login import login
from apic import Policy
from apic import Applications
import json
import re



# Create flask app and flask_restful api
app = Flask(__name__)
api = Api(app)

app.config.from_object(__name__)

# Create "/" app route
@app.route("/")
def health_check():
    return "Healthy"

# Applications API class
class ApplicationsAPI(Resource):

    def get(self):
        """
            Get applications and returns as list

            Usage:
                http://<url>/api/applications/?search=<search string>

            Args:
                search: application name search query (string)

            Returns:
                list of applications, 200 status code, access-control header
        """
        # Create NbClientManager object for uniq library
        client = login()

        try:
            search = request.args.get('search')
        except:
            search = None

        applications_object = Applications(client).applications

        if search:
            rsearch = re.compile(search, re.IGNORECASE)
            applications_list = [app.name for app in applications_object.response if rsearch.search(app.name)]
        else:
            # Return only the list of application names
            applications_list = [app.name for app in applications_object.response]

        # Optionally return the entire ApplicationsListResult object in JSON
        # applications_list = [client.serialize(app) for app in applications_object.response]

        return applications_list, 200, {'Access-Control-Allow-Origin': '*'}


# Policy Tags API class
class PolicyTagsAPI(Resource):

    def get(self):
        """
            Gets policy tags and returns as list

            Usage:
                http://<url>/api/policy_tags/

            Returns:
                list of policy tags, 200 status code, access-control header
        """
        # Create NbClientManager object for uniq library
        client = login()

        policy_tags_object = Policy(client, None).policy_tags

        # Return only the list of policy tags
        policy_tags_list = [tag.policyTag for tag in policy_tags_object.response]

        # Optionally return the entire PolicyTagListResult object in JSON
        # policy_tags_list = [client.serialize(tag) for tag in policy_tags_object.response]

        return policy_tags_list, 200, {'Access-Control-Allow-Origin': '*'}


# Application relevance API class
class RelevanceAPI(Resource):

    def get(self):
        """
            Checks current relevanceLevel of an app within a given policy scope

            Usage:
                http://<url>/api/relevance/?policy=<policy scope>&app=<app name>

            Args:
                app_name: Application name (string)
                policy: Policy Scope

            Returns:
                String representation of relevance level, 200 status code, access-control header
        """
        # Create NbClientManager object for uniq library
        client = login()

        app_name = request.args.get('app')
        policy_tag = request.args.get('policy')
        if not app_name:
            return "Missing Argument: app", 400, {'Access-Control-Allow-Origin': '*'}
        elif not policy_tag:
            return "Missing Argument: policy", 400, {'Access-Control-Allow-Origin': '*'}
        else:
            relevance = Policy(client, policy_tag).app_relevance(app_name)
            if not relevance:
                return "Unable to get relevance level", 204, {'Access-Control-Allow-Origin': '*'}
            return relevance, 200, {'Access-Control-Allow-Origin': '*'}

    def post(self):
        """
            Sets the relevance level for the provided application name to the

            Usage:
                http://<url>/api/relevance/

            Payload params:
                app: application name that is being set
                policy: policy scope that is being modified
                relevance: target relevance level, to which the application is being set

            Returns:
                taskId object (from uniq)
        """
        # Create NbClientManager object for uniq library
        client = login()

        app_name = request.form['app']
        policy_tag = request.form['policy']
        target_relevance = request.form['relevance']

        if not app_name:
            return "Missing Form Parameter: app", 400, {'Access-Control-Allow-Origin': '*'}
        elif not policy_tag:
            return "Missing Form Parameter: policy", 400, {'Access-Control-Allow-Origin': '*'}
        elif not target_relevance:
            return "Missing Form Parameter: relevance", 400, {'Access-Control-Allow-Origin': '*'}

        # Create Policy object
        policy_object = Policy(client, policy_tag)

        if policy_object.app_relevance(app_name) == target_relevance:
            # If current relevance is target relevance print and return message
            message = "Application {} is already in {} policy".format(app_name, target_relevance)
            print(message)
            return message, 204, {'Access-Control-Allow-Origin': '*'}

        else:
            # Execute the change to the application's relevance level
            policy_object.reset_relevance(app_name, target_relevance)

            # DEBUG printing of output for troubleshooting
            # with open('file.txt', 'w') as p:
            #     p.write(json.dumps(client.serialize(policy_object.policy_list.response),indent=4))

            # Update the APIC EM policy via REST API PUT (using uniq wrapper), return taskId response
            task_id = policy_object.update_apic().response.taskId
            if task_id:
                message = "Success: {} set to relevance level {}".format(app_name, target_relevance)
                return message, 200, {'Access-Control-Allow-Origin': '*'}



# Create flask_restful API resources
api.add_resource(ApplicationsAPI, '/api/applications/')
api.add_resource(PolicyTagsAPI, '/api/policy_tags/')
api.add_resource(RelevanceAPI, '/api/relevance/')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
