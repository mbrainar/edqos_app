# Event Driven QoS 1.0

# Description

Event Driven QoS is a simple demo application illustrating programmatic control of APIC-EM to change
QoS parameters in an attached network. This is driven by an external event.

There are three containers involved in the delivery of the application:
* edqos_app (this container) - responsible for presenting API calls for external events to
toggle the status of configured applications.
* edqos_data - implements an abstraction layer over the configuration database.
Currently implemented as SQLite and lacking in persistence between launches of
the container.
* edqos_web - front end application for configuration and status reporting. Includes
manual event triggers to confirm proper functioning of the application.

Additionally, an optional installation repository is available as edqos_installer.
This repository includes scripts for installation into an instance of [mantl](http://mantl.io)
as well as a [docker-compose](http://docker.com) script.

# Installation

## Environment

Prerequisites

* Python 2.7+
* [setuptools package](https://pypi.python.org/pypi/setuptools)
* [Flask](http://flask.pocoo.org)
* [Requests](http://docs.python-requests.org/en/master/)
* Hosting environment - any environment capable of hosting multiple containers
and implementing networking between them. Tested/supported environments are
currently [mantl](http://mantl.io) and [Docker](http://www.docker.com).

The front end application makes use of [JQuery](http://jquery.com) and [Chosen](https://harvesthq.github.io/chosen/);
separate installation of these libraries is not required as they are linked from
public CDN networks.

## Downloading

Option A:

If you have git installed, clone the repositories into the same directory.

    git clone https://github.com/imapex/edqos_app
    git clone https://github.com/imapex/edqos_data
    git clone https://github.com/imapex/edqos_web
    git clone https://github.com/imapex/edqos_installer (optional)

Option B:


The latest build of this project is also available as a Docker image from Docker Hub

    docker pull imapex/edqos_app:latest
    docker pull imapex/edqos_web:latest
    docker pull imapex/edqos_data:latest

Though in the case of docker installation, the docker-compose script is the simplest
choice as it correctly instantiates the dependencies between the containers
and builds networking between them.


## Installing

### Mantl installation

These instructions assume that you have cloned the installation repo as listed
above.

* Edit the sample-demoapp.json file (included) to reflect credentials for your
Cisco APIC-EM installation.
* Source edqos_setup. This will prompt for temporary environment variables
needed for the installation.
* Run the edqos-install.sh script to install the application to your
[mantl](http://mantl.io) server. This script will also create json files that can
be used to re-install the application if needed.

### Docker installation

To quickly bring the application up, type "docker-compose up". This will launch
the containers in the correct sequence and instantiate the web interface.

Installation into a swarm should work but has not yet been tested.

# Usage

It is required to create a policy in the APIC-EM interface directly and assign
that policy to network equipment as appropriate. This application cannot
build a policy from scratch.

The application provides a web interface for status reporting and configuration.
That interface will be available after the application is deployed
at http://0.0.0.0:5000.

The web front-end application presents a configuration interface as well as
manual toggles that can be clicked to test application functionality. Status
reporting is included as well.


# Development

Development requires access to Cisco's DevNet sandbox APIC-EM server, or a suitable
on-site installation. The application can be run locally rather than in a container
environment by the following:

    export FLASK_APP=app.py
    flask initdb (on first launch to initialize a local database)
    flask run


## Linting

We use flake 8 to lint our code. Please keep the repository clean by running:

    flake8

## Testing

Currently test coverage is lacking for this application.


# License

MIT license. See the included [LICENSE.TXT](LICENSE.TXT) file for details.
