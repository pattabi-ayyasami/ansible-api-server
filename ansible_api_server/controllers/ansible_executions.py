from pecan import expose, redirect, request
from webob.exc import status_map
import logging
import json
import pecan
from ansible_api_server.db import mysqldb as db

from ansible_api_server.utils.utils import Util

LOG = logging.getLogger(__name__)

class PlaybookExecutionController(object):
    def __init__(self, id):
        self.id = id

    @expose(generic=True, template='json')
    def index(self):
        try:
            entry = db.ExecutionLogsDB().get(self.id)
            if entry is None:
                message = "Execution Id  %s does not exist"
                LOG.debug(message, self.id)
                return Util.error_response(message=message, tokens=[self.id])
            else:
                execution = {}
                execution["execution_id"] = entry.get("execution_id") 
                request = json.loads(entry.get("request"))
                execution["request"] = request
                execution["status"] = entry.get("status")
                execution["result"] = entry.get("result")
                execution["duration"] = entry.get("duration")
                execution["logs"] = entry.get("logs")
                data = entry.get("execution_summary")
                summary = None
                if data is not None:
                    summary = json.loads(data)
                execution["execution_summary"] = summary
                return Util.success_response({"playbook_execution_details": execution})
        except Exception as e:
            return Util.handle_exception(e)


class AnsibleExecutionsController(object):
    @expose(generic=True, template='json')
    def index(self):
        print "Inside AnsibleServicesController index method"
        res_data = {"result": "index Success" }


    @expose()
    def _lookup(self, id, *remainder):
        return PlaybookExecutionController(id), remainder
        
    @expose(generic=True, template='json')
    def index(self):
        try:
            result = db.ExecutionLogsDB().get_all()
            executions = []
            for entry in result:
                execution = {}
                execution["execution_id"] = entry.get("execution_id") 
                request = json.loads(entry.get("request"))
                execution["request"] = request
                execution["status"] = entry.get("status")
                execution["result"] = entry.get("result")
                execution["duration"] = entry.get("duration")
                executions.append(execution)
            return Util.success_response({"executions": executions})
        except Exception as e:
            return Util.handle_exception(e)

