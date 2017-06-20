# Event Driven QoS

# Description

Event Driven QoS is a simple demo application illustrating programmatic control of APIC-EM to change
QoS parameters in an attached network. This is driven by an external event. In the initial implementation,
the application will promote facebook traffic when an event is detected; the inspiration came from
Facebook's ability to "check in" as "safe" in the event of a catastrophic event. In the initial implementation,
the event trigger is a static URL call. The application could potentially allow for the trigger to be an
external event, such as breaking news events, trending social media keywords, etc.


# Installation

## Environment

Prerequisites

* Python 3
* `pip install -r requirements.txt`


## Downloading

Option A:

If you have git installed, clone the repository

    git clone https://github.com/imapex/edqos_app

Option B:

If you don't have git, [download a zip copy of the repository](https://github.com/imapex/edqos_app/archive/master.zip)
and extract.


## Installing

### DevNet Mantl Sandbox
To install the application to the DevNet Mantl Sandbox using the DevNet APIC EM Sandbox:
1. Set your docker username
    ```
    export $DOCKERUSER=<your_username>
    ```
2. Execute the following commands
    ```    
    cp edqos_sample.json edqos_$DOCKERUSER.json
    sed -i "" -e "s/DOCKERUSER/$DOCKERUSER/g" edqos_$DOCKERUSER.json
    curl -k -X POST -u admin:1vtG@lw@y https://mantlsandbox.cisco.com:8080/v2/apps \
    -H "Content-type: application/json" \
    -d @edqos_$DOCKERUSER.json \
    | python -m json.tool
    ```

### BYOMantl
You can modify the sample app definition and commands above to deploy to your own Mantl instance.
  
### Local Container
You can run docker container 

### Local Deployment
You can also run the application locally rather than in a container environment by the following:

```
python app.py
```

# Usage

The application provides an API interface for getting QOS information out of APIC EM.

The supported APIs are:
* /api/policy_tags/ - (GET) Responds with list of policy tags available in APIC EM
* /api/applications/ - (GET) Responds with list of applications known to APIC EM
    * Optional argument: `search=<string>` Responds with list of applications matching search string
* /api/relevance/ - (GET) Responds with current relevance level for an application within a given scope
    * Required argument: `app=<string>` needs exact application name as known by APIC EM
    * Required argument: `policy=<string>` needs exact policy tag as known by APIC EM
* /api/relevance/ - (POST) Sets the given application to the given relevance level; takes application/x-www-form-urlencoded data
    * Required data: `app=<string>` needs exact application name as known by APIC EM 
    * Required data: `policy=<string>` needs exact policy tag as known by APIC EM
    * Required data: `relevance=<string>` needs exact relevance level as known by APIC EM
    ("Business-Relevant", "Default", "Business-Irrelevant")
    
    

# Development

Development requires access to Cisco's DevNet sandbox APIC-EM server, or a suitable
on-site installation. 