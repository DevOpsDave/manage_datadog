#!/usr/bin/env python
"""
This script is kind of a 'cloud formation' for setting for managing datadog
objects.  The two main objects (ATM)  that the script can operate on are alerts
and dashboards.  See the following usage examples:


ALERTS
Get all alerts:
# manage_datadog.py alerts get > /tmp/all_alerts.json

Get alert id 5663:
# manage_datadog.py alerts get -i 5663 > /tmp/alert_5663.json

Update alert id 5663:
# manage_datadog.py alerts get -i 5663 > /tmp/alert_5663.json
edit /tmp/alert_5663.json. Change data how you like it. DO NOT MODIFY the id.
# manage_datadog.py alerts put /tmp/alert_5663.json

Delete alert id 5663:
# manage_datadog.py alerts get -i 5663 > /tmp/alert_5663.json
edit /tmp/alert_5663.json. Change the id to -5663.
# manage_datadog.py alerts put /tmp/alert_5663.json
OR
# manage_datadog.py alerts delete 5663

Create a alert like 5663
# manage_datadog.py alerts get -i 5663 > /tmp/alert_5663.json
edit /tmp/alert_5663.json. Modify the data to reflect your new alert.  Change id to 0.
# manage_datadog.py alerts put /tmp/alert_5663.json
Note: In this example your new alert will not be id 5663 but will actually be 
randomly generated.  Use 'getalerts' to check your work. 

DASHBOARDS (Dashboards work just like alerts.)
To get all dahsboards:
manage_datadog.py dashboards get > /tmp/all_dashes.json

Get dashboard id 5663:
manage_datadog.py dashboards get -i 5663 > /tmp/dash_5663.json

Update dashboard id 5663:
edit /tmp/dash_5663.json. Change data how you like it. DO NOT MODIFY the id.
manage_datadog.py dashboards put /tmp/dash_5663.json

Delete dashboard id 5663:
edit /tmp/dash_5663.json. Change the id to -5663.
manage_datadog.py dashboards put /tmp/dash_5663.json

Create a dashboard like 5663
edit /tmp/dash_5663.json. Change id to 0.
manage_datadog.py dashboards put /tmp/dash_5663.json
"""

import re
import argparse
import sys
import os
import yaml
import json
import ConfigParser

from dogapi import dog_http_api as api

class DataDogObject(object):
    def __repr__(self):
        return json.dumps(self.__dict__, indent=4)

    def is_live(self):
        """
        Determines if a specific object is already in datadog.
        """
        if (self.id != 0):
            return True
        else:
            return False


class DataDogObjectCollection(object):
    def __init__(self, api_key=None, app_key=None, config_file=None, team_section=None):
        """
        Get credentials and setup api.
        """
        api.api_key, api.application_key = self._return_credentials_(api_key,
            app_key, config_file, team_section)
        self.dapi = api

        """
        Holds data.
        """
        self.data = []

    def _return_credentials_(self, api_key, app_key, config_file, team_section):
        """
        Determines datadog credentials.
        Api credentials are held here.  They are needed for the
        load_alerts_from_api() and update_datadog() methods.
        1.  Use the values supplied at instantiation.
        2.  If None, see the config file.
        self.config_file =  <input values> || '/etc/dd-agent/datadog.conf'
        """

        """
        If both api_key and app_key are not None then return their values.
        """
        if ((api_key and app_key) is not None):
            return api_key, app_key

        """
        Fail if config_file is None or if the path is not legit.
        """
        # This will resolve a ~ if used.
        config_file = os.path.expanduser(config_file)
        # Make sure config file is valid.
        if (config_file is None) or (os.path.isfile(config_file) is False):
            raise Exception('Do not have a valid config file!!!!!!')

        """
        At this point the value of config_file is valid.  So parse it.  First get the api key from the connection
        section.
        """
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        api_key = config.get('Connection', 'apikey')

        """
        Next get the appkey.  If team team_section does not equal None then get the appkey from there.  Otherwise look
        in the Connection section.  Raise an exception if there is no app key to be found.
        """
        if team_section is None:
            app_key = config.get('Connection', 'appkey')
        else:
            app_key = config.get(team_section, 'appkey')

        """
        Make sure we got good values.
        """
        if (api_key == '') or (app_key == ''):
            raise Exception('Bad values!!!!')

        """
        Everything looks good!
        """
        return api_key, app_key

        return "%s" % (self.__dict__)

        return "%s(%r)" % (self.__class__, self.__dict__)

    def __repr__(self):
        return json.dumps(self.__dict__, indent=4)
        return self.__dict__

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, int_key):
        return self.data[int_key]

    def get_obj(self, int_id):
        for obj in self.data:
            if obj.id == int_id:
                return obj
        return None


        for obj in self.data:
            if obj.id == int_id:
                return obj
        return None

    def do(self, args):
        switch = {'get': self.get,
                  'put': self.put,
                  'delete': self.delete}
        switch[args.sub_subparser_name](args)

    def get(self, args):
        self.load_data_from_api(args.regex)

        if args.get_id != 0:
            data = []
            data.append(self.get_obj(args.get_id))
        else:
            data = self.data
        print data

    def put(self, args):
        self.load_data_from_file(args.from_file)
        self.update_datadog()

    def delete(self, args):
        self.delete_obj(args.alert_id)

class Alert(DataDogObject):
    """
    Alert data type.  Holds data for specific alerts.
    """
    def __init__(self, alert_dict):
        """
        alert_dict must have the following:
            alert_dict['id']:  Integer.  The id of the alert.  This is None
            on new alert creation.

            alert_dict['message']:  String.  Describes how alert will inform
            of problem (ie. pagerduty)

            alert_dict['name']:  String.  The name description of the alert.

            alert_dict['query']:  String.  The guts of the alert.  See the
            docs on the datadog alert api for more info.

            alert_dict['silenced']: Boolean.  Mute or not.
        """
        self.id = alert_dict['id']
        self.message = alert_dict['message']
        self.name = alert_dict['name']
        self.query = alert_dict['query']
        self.silenced = alert_dict['silenced']

class Alerts(DataDogObjectCollection):
    """
    Collection of alerts.
    """
    def load_data_from_api(self, regex_str):
        """
        Usese datadog method get_all_alerts to get all alerts.
        If regex_str is specified then regex is applied to 'name' field for
        each alert.  Otherwise regex_str = '' and will match every alert.
        """

        # Get all the alerts from datadog.
        all_alerts = self.dapi.get_all_alerts()

        # compile regex object if regex specified.
        if regex_str is None:
            regex_str = ''
        alerts_regex = re.compile(regex_str, re.I)

        # get list of alerts I want.
        for alert in all_alerts:
            if alerts_regex.search(alert['name']):
                alert_obj = Alert(alert)
                self.data.append(alert_obj)

    def load_data_from_file(self, file_path):
        """
        Loads all alerts listed in file 'file_path'.
        The format of the file should be as follows:
            [
             {id: <int>,
             message: <string>,
             name: <string>,
             query: <string>,
             silenced: <boolean>},
             ...
            ]
        """
        fp = open(file_path, 'r')
        alerts_python_obj = yaml.load(fp)

        for alert_dict in alerts_python_obj:
            self.data.append(Alert(alert_dict))

    def update_datadog(self):
        """
        Update datadog with data in self.data.
        To create a new alert:  Leave the id attribute None.  This will create
        a new alert.

        To update the alert:  id must have a valid positive integer that maps
        to a current event.

        To delet an event: make the id a negative number.  This will delete the
        alert.
        """
        for alert in self.data:
            if alert.is_live():
                if alert.id < 0:
                    self.dapi.delete_alert(abs(alert.id))
                else:
                    self.dapi.update_alert(alert.id, alert.query, alert.name,
                        alert.message, alert.silenced)
            else:
                self.dapi.alert(alert.query, alert.name, alert.message,
                    alert.silenced)

    def delete_obj(self, object_id):
        """
        Deletes alert by id
        """
        self.dapi.delete_alert(object_id)

class Dashbrd(DataDogObject):
    """
    Holds dashboard data.
    """
    def __init__(self, dash_dict):
        self.id = dash_dict['id']
        self.title = dash_dict['title']
        self.description = dash_dict['description']
        self.graphs = dash_dict['graphs']

class Dashbrds(DataDogObjectCollection):
    def load_data_from_api(self, regex_str):
        """
        Uses datadog method dashboards to get all dashboards.
        If regex_str is specified then regex is applied to 'title' field for
        each dashboard.  Otherwise regex_str = '' and will match every
        dashboard.
        """

        # Get all the alerts from datadog.
        all_dashboards = self.dapi.dashboards()

        # compile regex object if regex specified.
        if regex_str is None:
            regex_str = ''
        dash_regex = re.compile(regex_str, re.I)

        # get list of alerts I want.
        for dash in all_dashboards:
            if dash_regex.search(dash['title']):
                obj = self.dapi.dashboard(dash['id'])
                dash_obj = Dashbrd(obj)
                self.data.append(dash_obj)

    def load_data_from_file(self, file_path):
        fp = open(file_path, 'r')
        data_python_obj = json.load(fp)

        for data_dict in data_python_obj:
            self.data.append(Dashbrd(data_dict))

    def update_datadog(self):
        """
        Update datadog with data in self.data.
        To create a new dashboard:  Leave the id attribute 0.  This will create
        a new dashboard.

        To update a dashboard:  id must have a valid positive integer that maps
        to a current event.

        To delet an event: make the id a negative number.  This will delete the
        dashboard.
        """
        for obj in self.data:
            if obj.is_live():
                if obj.id < 0:
                    self.dapi.delete_dashboard(abs(obj.id))
                else:
                    self.dapi.update_dashboard(obj.id, obj.title,
                        obj.description, obj.graphs)
            else:
                self.dapi.create_dashboard(obj.title, obj.description,
                    obj.graphs)

        return self.data

def cmd_line(argv):
    """
    Get the command line arguments and options.
    Global options.
    """
    parser = argparse.ArgumentParser(description="Manage datadog alerts")
    parser.add_argument('-c', '--config-file',
        default='~/.dogrc',
        help='Specify datadog config file to get api key info.')
    parser.add_argument('-t', '--team-section', default=None,
                        help='Specify a team section in the config file to retrieve config values.')
    parser.add_argument('--api-key', default=None, help='Specify API key.')
    parser.add_argument('--app-key', default=None, help='Specify APP key.')
    subparsers = parser.add_subparsers(dest='subparser_name')

    """ Alerts. """
    alerts = subparsers.add_parser('alerts',
            description='Manage DataDog alerts.',
            help='Manage DataDog alerts.')
    alert_sub = alerts.add_subparsers(dest='sub_subparser_name')
    # Get Alerts.
    get_parent_parser = argparse.ArgumentParser(add_help=False)
    get_parent_parser.add_argument('-i', '--get-id', type=int, default=0,
                               help='Specify an id of an object to retrieve.  [INTEGER]')
    get_parent_parser.add_argument('-r', '--regex',
                               help='Regex string to use when selecting events.')
    alert_get = alert_sub.add_parser('get',
            description='Gets the alerts from datadog.',
            help='get alerts from datadog', parents=[get_parent_parser])
    # Put Alerts.
    alert_put = alert_sub.add_parser('put',
            description='Takes alerts from file argument and puts them in datadog.',
            help='put alerts to datadog')
    alert_put.add_argument('from_file',
            help='Use given file to create alerts. REQUIRED')
    # Delete Alerts.
    alert_delete = alert_sub.add_parser('delete',
            description='Takes alert id as argument and deletes alert.',
            help='Delete alert from datadog.')
    alert_delete.add_argument('alert_id',
            help='Use given id to delete alert. REQUIRED')

    # dashboards
    dash = subparsers.add_parser('dashboards',
            description='Manage dadadog dashboards.', help='Manage datadog dashboards.')
    dash_sub = dash.add_subparsers(dest='sub_subparser_name')
    dash_get = dash_sub.add_parser('get',
            description='Get dashboards from datadog.', help='Get dashboards from datadog.',
            parents=[get_parent_parser])
    dash_put = dash_sub.add_parser('put',
            description='Put dashboards to datadog.', help='Put dashboards to datadog.')
    dash_put.add_argument('from_file', help='Use given file to create alerts. REQUIRED')

    args = parser.parse_args()
    return args


def main():
    """
    Main function where it all comes together.
    """
    # Get the cmd line.
    args = cmd_line(sys.argv)

    # case/switch dictionary.
    switch = {'alerts': Alerts,
              'dashboards': Dashbrds}
    DDogObjColl = switch[args.subparser_name](args.api_key,args.app_key,args.config_file,args.team_section)
    DDogObjColl.do(args)

    exit(0)

if __name__ == "__main__":
    main()
