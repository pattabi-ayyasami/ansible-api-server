import logging
import os
import cgi

from pecan import request, response, expose
from webob.static import FileIter
from random import choice
from mimetypes import guess_type
from ansible_api_server.utils.utils import Util
from ansible_api_server.db.mysqldb import PlaybookDB

LOG = logging.getLogger(__name__)


playbook_db = PlaybookDB()
class PlaybookController(object):
    def __init__(self, id):
        self.id = id

    @expose(generic=True, template='json')
    def index(self):
        try:
            entry = playbook_db.get(self.id)
            if entry is None:
                message = "Ansible Playbook %s does not exist"
                LOG.debug(message, self.id)
                return Util.error_response(message=message, tokens=[self.id])
            else:
                del entry["content"]
                return Util.success_response({"playbook": entry})
        except Exception as e:
            return Util.handle_exception(e)

    @index.when(method='DELETE', template='json')
    def index_DELETE(self):
        try:
            entry = playbook_db.get(self.id)
            if entry is None:
                message = "Ansible Playbook %s does not exist"
                LOG.debug(message, self.id)
                return Util.error_response(message=message, tokens=[self.id])

            playbook_db.remove(self.id)
            return Util.success_response({"playbook": {"id": self.id}})
        except Exception as e:
            return Util.handle_exception(e)


class PlaybookListController(object):
    @expose()
    def _lookup(self, id, *remainder):
        return PlaybookController(id), remainder

    @expose(generic=True, template='json')
    def index(self):
        try:
            playbooks = playbook_db.get_all()
            # Do not show the content file path to the user
            for entry in playbooks:
                LOG.debug("Playbook: %s", entry)
            return Util.success_response({"playbooks": playbooks})
        except Exception as e:
            return Util.handle_exception(e)

    @index.when(method='POST', template='json')
    def index_POST(self, **kw):
        temp = None
        playbook_id = None
        try:
            content = request.POST["playbook"].file.read()
            data = {}
            data["name"] = request.POST["playbook"].filename
            data["content"] = content

            playbook_id = playbook_db.add(data)
        except Exception as e:
            return Util.handle_exception(e)

        return Util.success_response({"playbook": {"id": playbook_id}})
