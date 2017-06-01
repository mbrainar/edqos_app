#!/usr/bin/python
'''
    APIC-EM interface module for Event Driven QoS
    This module pulls needed APIC-EM APIs into python functions.

    The application is a simple demonstration of using APIC-EM
    dynamic QoS to modify QoS policies based on external factors
    such as weather events, power excursions, etc.
'''


__author__ = 'mbrainar'

import json



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



# Create the Policy object
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


        # Create PolicyListResults (uniq model) object
        self.policy_list = self.client.policy.getFilterPolicies(policyScope=self.policy_scope)



    @property
    def policy_tags(self):
        """
            Creates policy tags list object using policy scope in self

            Returns:
                PolicyTagResult, uniq model
        """
        return self.client.policy.getPolicyTags()



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



    def find_app(self, app_name):
        """
            Finds the PolicyApplication object for the app name

            Args:
                app_name: name of application to find (string)

            Returns:
                 PolicyApplication (uniq model)
        """
        self._app = None
        for p in self.policy_list.response:
            apps = [app for app in p.resource.applications if app.appName == app_name]
            if len(apps) > 0:
                return apps[0]



    def reset_relevance(self, app_name, target_relevance):
        """
            Resets the relevance level for an application to the target level for the Policy object self

            Args:
                app_name: application name, string
                target_relevance: desired relevance level, string ["Business Relevant", "Default", "Business Irrelevant"]
        """
        # Check that target relevance is valid
        valid_relevance = ["Business-Relevant", "Default", "Business-Irrelevant"]
        if target_relevance not in valid_relevance:
            raise ValueError("Invalid relevance")

        # Find the PolicyApplication object (uniq model) for the app_name
        _app = self.find_app(app_name)
        # DEBUG prints PolicyApplication object matching app_name
        # print(self.client.serialize(_app))

        _relevance = self.app_relevance(app_name)

        # If current relevance is target relevance print message and return None
        if _relevance == target_relevance:
            print("Application {} is already in {} policy".format(app_name, target_relevance))
            return
        else:
            for p in self.policy_list.response:
                if p.actionProperty.relevanceLevel == target_relevance:
                    # If looping through target relevance, append ApplicationDTO
                    print("Adding application {} to {} policy".format(_app.appName, p.actionProperty.relevanceLevel))
                    p.resource.applications.append(_app)

                    # DEBUG prints newly modified applications list for target relevance level
                    # print(json.dumps(self.client.serialize(p.resource.applications),indent=4))
                elif p.actionProperty.relevanceLevel == _relevance:
                    # If looping through current relevance, remove ApplicationDTO
                    print("Removing application {} from {} policy".format(app_name, p.actionProperty.relevanceLevel))
                    p.resource.applications.remove(_app)

                    # DEBUG prints newly modified applications list for previous relevance level
                    # print(json.dumps(self.client.serialize(p.resource.applications),indent=4))
                else:
                    # Else, skip looping through policy
                    print("Skipping {} policy".format(p.actionProperty.relevanceLevel))



    def update_apic(self):
        """
            Updates the policy list in APIC EM through PUT request.
            Must execute reset_relevance to make changes to object first

            Returns:
                taskIdResult, uniq model
        """
        return self.client.policy.update(policyList=self.policy_list.response)