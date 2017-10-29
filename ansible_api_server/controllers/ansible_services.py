import logging
import json
import pecan
import uuid

from pecan import expose, redirect, request
from webob.exc import status_map

import  ansible_api_server.impl.run_playbook as run_playbook
import  ansible_executions

from ansible_api_server.db import mysqldb as db
from ansible_api_server.utils.utils import Util
from ansible_api_server.impl.run_playbook import PlaybookExecutor


LOG = logging.getLogger(__name__)

class AnsibleServicesController(object):
    executions = ansible_executions.AnsibleExecutionsController()

    @expose('json')
    def play(self, **body):
        try:
            print "inside AnsibleServicesController.play method"
            id = str(uuid.uuid1())

            execution_data = {}
            execution_data["execution_id"] = id
            execution_data["request"] = json.dumps(body, indent=4)
            execution_data["status"] = "pending"
            db.ExecutionLogsDB().add(execution_data)
     
            #run_playbook.run_ansible_playbook(id, body)
            PlaybookExecutor().run_ansible_playbook(id, body)
        
            response_data = {}
            response_data["execution_id"] = id

            response_body = {}

            status = {}
            status["reqStatus"] = "PENDING"
            response_body["status"] = status
            response_body["data"] = response_data

        except Exception as e:
            return Util.handle_exception(e)
        else:
            print("Success Response: %s", json.dumps(response_body, indent=4))      
            return response_body
