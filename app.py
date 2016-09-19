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



app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'edqos.db'),
    SECRET_KEY='devel key'
))

if os.environ.get("SECRET_KEY"):
    app.config.update(dict(
        SECRET_KEY=os.environ.get("SECRET_KEY")
    ))

def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def connect_db():
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = dict_factory
    return rv


def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    init_db()
    print 'Database initialized'


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def home():
    policy_tag = request.args.get('selected')
    policies = apic.get_policy_scope(apic.get_ticket())
    return render_template('index.html', policies=policies, policy_tag=policy_tag,
                               title='Event Driven QoS')


@app.route('/_get_apps/')
def get_apps():
    pol = request.args.get('policy')
    db = get_db()
    cur = db.execute('select id, policy, app from edqos where policy = ?', tuple([pol]))
    entries = cur.fetchall()
    return jsonify(map(dict, entries))

@app.route('/_is_relevant/')
def check_relevant():
    app = request.args.get('app')
    policy_tag = request.args.get('policy')
    ticket = apic.get_ticket()
    app_id = apic.get_app_id(ticket, app)
    policy = apic.get_policy(ticket, policy_tag)
    return apic.get_app_state(policy, app_id, app)

@app.route('/configure/')
def configure():
    policy = request.args.get('policy')
    app_list = apic.get_applications(apic.get_ticket(),policy)
    db = get_db()
    cur = db.execute('select id, policy, app from edqos where policy = ?', tuple([policy]))
    entries = cur.fetchall()
    selected_apps = []
    for item in entries:
        selected_apps.append(item['app'])
    return render_template('configure.html', apps=app_list, policy=policy,
                           selected_apps=selected_apps,
                           title='Event Driven QoS Configuration')

@app.route('/_save_config/', methods=["POST"])
def save_config():
    applist = request.form.getlist('selections')
    policy_tag = request.form.getlist('policy_tag')[0]
    apps = applist[0].split(",")
    db = get_db()
    cur = db.execute('delete from edqos')
    for item in apps:
        cur = db.execute('insert into edqos (policy, app) values (?,?)',
            [policy_tag, item])
    db.commit()
    return jsonify(applist)


@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', title='Oops.'), 404


@app.route('/event/on/')
def event_on():
    policy_scope = request.args.get('policy')
    event_status = True
    db = get_db()
    cur = db.execute('select app from edqos where policy = ?', tuple([policy_scope]))
    saved_apps = cur.fetchall()
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
    db = get_db()
    cur = db.execute('select app from edqos where policy = ?', tuple([policy_scope]))
    saved_apps = cur.fetchall()
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
