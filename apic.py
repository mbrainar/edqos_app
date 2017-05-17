#!/usr/bin/python
'''
    APIC-EM interface module for Event Driven QoS
    This module pulls needed APIC-EM APIs into python functions.

    The application is a simple demonstration of using APIC-EM
    dynamic QoS to modify QoS policies based on external factors
    such as weather events, power excursions, etc.
'''

# To Do's:
    # todo convert policy into class
    # todo add method to modify policy
    # todo convert REST API calls to use uniq? https://pypi.python.org/pypi/uniq/1.4.0.36
    


__author__ = 'sluzynsk'

import requests
import os
import json

# Define global variables
if os.environ.get("APIC_SERVER"):
    apic=os.environ.get("APIC_SERVER")
else:
    apic='sandboxapic.cisco.com'

if os.environ.get("APIC_USERNAME"):
    username=os.environ.get("APIC_USERNAME")
else:
    username='devnetuser'

if os.environ.get("APIC_PASSWORD"):
    password=os.environ.get("APIC_PASSWORD")
else:
    password='Cisco123!'



# Get the service ticket to be used in API calls
def get_ticket():

    reqUrl = "https://{0}/api/v1/ticket".format(apic)
    payload = {'username': username, 'password': password}

    r = requests.post(reqUrl, json=payload, verify=False)

    if (r.status_code == 200):
        return r.json()[u'response'][u'serviceTicket']
    else:
        r.raise_for_status()

# Get the application ID
def get_app_id(service_ticket, app_name):
    reqUrl = "https://{0}/api/v1/application?name={1}".format(apic, app_name)
    header = {"X-Auth-Token": service_ticket}

    r = requests.get(reqUrl, headers=header, verify=False)

    if (r.status_code == 200):
        return r.json()['response'][0]['id']
    else:
        r.raise_for_status()

# Get the current policy
def get_policy(service_ticket, policy_scope):
    reqUrl = "https://{0}/api/v1/policy?policyScope={1}".format(apic, policy_scope)
    header = {"X-Auth-Token": service_ticket}

    r = requests.get(reqUrl, headers=header, verify=False)

    if r.status_code == 200:
        return r.json()
    else:
        r.raise_for_status()

# Check whether the application is business relevant, irrelevant or default
def get_app_state(policy, app_id, app_name):
    for item in policy['response']:
        for apps in item['resource']['applications']:
            if app_name in apps.values():
                return item['actionProperty']['relevanceLevel']
            else:
                continue

# Rewrites the policy based on the external event status; if no change is needed, returns false
def update_app_state(service_ticket, event_status, policy, app_list):
    if event_status == True:
        print "Event trigger ON"
        # Loop through each of the applications in the list of specified apps
        for app_name in app_list:
            i = 0
            app_id = get_app_id(service_ticket, app_name)
            print "Looping in app list, appName={0}".format(app_name)
            if get_app_state(policy, app_id, app_name) != "Business-Relevant":
                print "Only performing update if {0} is not already part of business-relevant".format(app_name)
                # Loop through each of the 3 policy entries from the policy scope
                for i in range(len(policy['response'])):
                    a = 0
                    # If we are looking at the business-relevant policy, add the specified application
                    if policy['response'][i]['actionProperty']['relevanceLevel'] == "Business-Relevant":
                        policy['response'][i]['resource']['applications'].append({"id": app_id, "appName": app_name})
                        print "Appended {0} to business-relevant".format(app_name)
                    # If we are looking at the business-irrelevant (or default) policy, remove the specified application
                    else:
                        # Loop through each of the applications in the business-irrelevant policy
                        for app in policy['response'][i]['resource']['applications']:
                            # If app matches, delete from business-irrelevant, else continue looping applications
                            if app["appName"] == app_name:
                                policy['response'][i]['resource']['applications'].remove(app)
                                print "Removed {0} from business-irrelevant".format(app_name)
                            else:
                                continue
            else:
                continue
        return policy
    else:
        print "Event trigger is OFF"
        # Loop through each of the applications in the list of specified apps
        for app_name in app_list:
            i = 0
            app_id = get_app_id(service_ticket, app_name)
            print "looping in app list, appName={0}".format(app_name)
            if get_app_state(policy, app_id, app_name) != "Business-Irrelevant":
                print "Only performing update if {0} is not already part of business-irrelevant".format(app_name)
                # Loop through each of the 3 policy entries in the policy scope
                for i in range(len(policy['response'])):
                    a = 0
                    # If we are looking at the business-irrelevant policy, add the specified application
                    if policy['response'][i]['actionProperty']['relevanceLevel'] == "Business-Irrelevant":
                        policy['response'][i]['resource']['applications'].append({"id": app_id, "appName": app_name})
                        print "Appended {0} to business-irrelevant".format(app_name)
                    # If we are looking at the business-relevant (or default) policy, remove the specified application
                    else:
                        # Loop through each of the applications in the business-relevant (and default)
                        for app in policy['response'][i]['resource']['applications']:
                            #if app matches, delete from business-relevant, else continue looping applications
                            if app["appName"] == app_name:
                                policy['response'][i]['resource']['applications'].remove(app)
                                print "Removed {0} from business-relevant".format(app_name)
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

# Call API to get list of policy scopes
# This is used to populate the UI
def get_policy_scope(service_ticket):
    reqUrl = "https://{0}/api/v1/policy/tag".format(apic)
    header = {"X-Auth-Token": service_ticket}

    r = requests.get(reqUrl, headers=header, verify=False)

    if r.status_code == 200:
        list = []
        for scope in r.json()['response']:
            list.append(scope['policyTag'])
        list.sort(key=lambda y: y.lower())
        return list
    else:
        r.raise_for_status()

# Get list of all currently business irrelevant applications
# This is used to populate the UI
def get_applications(service_ticket, policy_scope):
    reqUrl = "https://{0}/api/v1/policy?policyScope={1}".format(apic, policy_scope)
    header = {"X-Auth-Token": service_ticket}

    r = requests.get(reqUrl, headers=header, verify=False)

    if r.status_code == 200:
        list = []
        for policy in r.json()['response']:
            if policy['actionProperty']['relevanceLevel'] == "Business-Irrelevant":
                for app in policy['resource']['applications']:
                    list.append(app['appName'])
            else:
                continue
            list.sort(key=lambda y: y.lower())
            break
        return list
    else:
        r.raise_for_status()

# standard guard to make sure the application is only run if called as a script
# as opposed to being imported i.e. for unit testing or linting.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

'''
#Code test block
apic="10.10.10.111"
username="admin"
password="1vtG@lw@y"

policy_scope = "ed-qos"
app_list = ["facebook"]
service_ticket = get_ticket(username,password)

#print get_app_state(get_policy(get_ticket(),policy_scope),get_app_id(get_ticket(),app_name),app_name)

old = open("old.json", "w")
new = open("new.json", "w")

old.write(json.dumps(get_policy(service_ticket,policy_scope), indent=4))
new.write(json.dumps(update_app_state(service_ticket,True,get_policy(service_ticket,policy_scope),app_list), indent=4))

old.close()
new.close()

#print put_policy_update(service_ticket,update_app_state(service_ticket,False,get_policy(service_ticket,policy_scope),app_list),policy_scope)
'''
