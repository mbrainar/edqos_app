#!/usr/bin/python
'''
    APIC-EM interface module for Event Driven QoS
    This module pulls needed APIC-EM APIs into python functions.

    The application is a simple demonstration of using APIC-EM
    dynamic QoS to modify QoS policies based on external factors
    such as weather events, power excursions, etc.
'''


__author__ = 'mbrainar'

import requests
from login import login



# Create APIC EM object
# client = login()



# Create Applications object
class Applications(object):

    def __init__(self, client):
        """
            Initializes the Applications object

            Args:
                 client: nbClientManager, uniq model
        """
        self.client = client



    @property
    def applications(self):
        """
            Create ApplicationsListResult object

            Returns:
                 ApplicationsListResult, uniq model
        """
        return self.client.application.getFilterApplication()



    def get_id(self, app_name):
        """
            Given an application name, returns the id of that application

            Args:
                app_name: name of application

            Returns:
                 applicationId, string
        """
        _id = []
        apps = [app for app in self.applications.response if app.name == app_name]
        if len(apps) > 0:
            return apps[0].id





class Policy(object):

    def __init__(self, client, policy_scope):
        """
            Initializes Policy object

            Args:
                client: nbClientManager, uniq model
                policy_scope: policy tag/scope, string
        """
        self.client = client
        self.policy_scope = policy_scope



    @property
    def policy_tags(self):
        """
            Creates policy tags list object using policy scope in self

            Returns:
                PolicyTagResult, uniq model
        """
        return self.client.policy.getPolicyTags()



    @property
    def policy_list(self):
        """
            Creates policy lists object using policy scope in self

            Returns:
                 PolicyListResults, uniq model
        """
        return self.client.policy.getFilterPolicies(policyScope=self.policy_scope)



    def app_relevance(self, app_name):
        """
            Given an application name, get that applications relevance level

            Args:
                app_name: application name, string

            Returns:
                relevanceLevel, string
        """
        for p in self.policy_list.response:
            apps = [app for app in p.resource.applications if app.appName == app_name]
            if len(apps) > 0:
                print("Found application {} in {} policy".format(app_name, p.actionProperty.relevanceLevel))
                return p.actionProperty.relevanceLevel



    def reset_relevance(self, app_name, target_relevance):
        """
            Resets the relevance level for an application to the target level for the Policy object self

            Args:
                app_name: application name, string
                target_relevance: desired relevance level, string ["Business Relevant", "Default", "Business Irrelevant"]
        """
        # Check that target relevance is valid
        valid_relevance = ["Business Relevant", "Default", "Business Irrelevant"]
        if target_relevance not in valid_relevance:
            raise valueError("Invalid relevance")

        # todo get applicationDTO object prior to making changes

        _app = []
        for p in self.policy_list.response:
            apps = [app for app in p.resource.applications if app.appName == app_name]
            if len(apps) > 0:
                if p.actionProperty.relevanceLevel == target_relevance:
                    print("Application {} already in {} policy".format(app_name, p.actionProperty.relevanceLevel))
                    return
                else:
                    print("Found application {} in {} policy".format(app_name, p.actionProperty.relevanceLevel))
                    _app = apps[0]
                    print("Removing application {}".format(app_name))
                    p.resource.applications.remove(_app)
            else:
                if p.actionProperty.relevanceLevel == target_relevance:
                    print("Found {} policy for policyScope {}".format(p.actionProperty.relevanceLevel, self.policy_scope))
                    print("Adding application {}".format(_app.appName))
                    p.resource.applications.append(_app)
                else:
                    print("Skipping {} policy".format(p.actionProperty.relevanceLevel))



    def update_apic(self):
        """
            Updates the policy list in APIC EM through PUT request.
            Must execute reset_relevance to make changes to object first

            Returns:
                taskIdResult, uniq model
        """
        return self.client.policy.update(policyList=self.policy_list.response)




# LEGACY Rewrites the policy based on the external event status; if no change is needed, returns false
"""
def update_app_state(service_ticket, event_status, policy, app_list):
    if event_status == True:
        print ("Event trigger ON")
        # Loop through each of the applications in the list of specified apps
        for app_name in app_list:
            i = 0
            app_id = get_app_id(service_ticket, app_name)
            print("Looping in app list, appName={0}".format(app_name))
            #if get_app_state(policy, app_id, app_name) != "Business-Relevant":
            if Policy(client, "ed-qos").app_relevance(app_name) != "Business-Relevant":
                print("Only performing update if {0} is not already part of business-relevant".format(app_name))
                # Loop through each of the 3 policy entries from the policy scope
                for i in range(len(policy['response'])):
                    a = 0
                    # If we are looking at the business-relevant policy, add the specified application
                    if policy['response'][i]['actionProperty']['relevanceLevel'] == "Business-Relevant":
                        policy['response'][i]['resource']['applications'].append({"id": app_id, "appName": app_name})
                        print("Appended {0} to business-relevant".format(app_name))
                    # If we are looking at the business-irrelevant (or default) policy, remove the specified application
                    else:
                        # Loop through each of the applications in the business-irrelevant policy
                        for app in policy['response'][i]['resource']['applications']:
                            # If app matches, delete from business-irrelevant, else continue looping applications
                            if app["appName"] == app_name:
                                policy['response'][i]['resource']['applications'].remove(app)
                                print ("Removed {0} from business-irrelevant".format(app_name))
                            else:
                                continue
            else:
                continue
        return policy
    else:
        print ("Event trigger is OFF")
        # Loop through each of the applications in the list of specified apps
        for app_name in app_list:
            i = 0
            app_id = get_app_id(service_ticket, app_name)
            print ("looping in app list, appName={0}".format(app_name))
            if get_app_state(policy, app_id, app_name) != "Business-Irrelevant":
                print ("Only performing update if {0} is not already part of business-irrelevant".format(app_name))
                # Loop through each of the 3 policy entries in the policy scope
                for i in range(len(policy['response'])):
                    a = 0
                    # If we are looking at the business-irrelevant policy, add the specified application
                    if policy['response'][i]['actionProperty']['relevanceLevel'] == "Business-Irrelevant":
                        policy['response'][i]['resource']['applications'].append({"id": app_id, "appName": app_name})
                        print ("Appended {0} to business-irrelevant".format(app_name))
                    # If we are looking at the business-relevant (or default) policy, remove the specified application
                    else:
                        # Loop through each of the applications in the business-relevant (and default)
                        for app in policy['response'][i]['resource']['applications']:
                            #if app matches, delete from business-relevant, else continue looping applications
                            if app["appName"] == app_name:
                                policy['response'][i]['resource']['applications'].remove(app)
                                print ("Removed {0} from business-relevant".format(app_name))
                            else:
                                continue

            else:
                continue
        return policy

# Call API to send the new policy to the APIC EM
def put_policy_update(service_ticket, policy, policy_scope):
    if policy != get_policy(service_ticket, policy_scope):
        reqUrl = "https://{0}/api/v1/policy".format(apic)
        header = {"X-Auth-Token": service_ticket, "Content-type":"application/json"}

        r = requests.put(reqUrl, headers=header, json=policy['response'], verify=False)

        if r.status_code == 202:
            task_id = r.json()['response']['taskId']
            if get_task(service_ticket, task_id)['response']['isError'] == False:
                return "taskId {0} completed without errors".format(task_id)
            else:
                return "taskId {0} failed with errors".format(task_id)
        else:
            r.raise_for_status()
    else:
        return "No changes made to policy"

# Call API to get the details of the taskId created by APIC EM when sending policy changes
def get_task(service_ticket, task_id):
    reqUrl = "https://{0}/api/v1/task/{1}".format(apic, task_id)
    header = {"X-Auth-Token": service_ticket, "Content-type": "application/json"}

    r = requests.get(reqUrl, headers=header, verify=False)

    if r.status_code == 200:
        return r.json()
    else:
        r.raise_for_status()
"""