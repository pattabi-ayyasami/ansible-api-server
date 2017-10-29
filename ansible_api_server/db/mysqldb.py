import sys
import MySQLdb
import uuid
import logging
import json
import magic
import os
import tempfile


LOG = logging.getLogger(__name__)

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            LOG.debug("instantiating the class: %s", cls)
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

mysql_host = "localhost"
user = "pattabi"
password = "pattabi"

class AnsibleDB(object):
    DB_NAME = "ansible"
    def __init__(self):
        LOG.debug("inside AnsibleDB.__init__()")

    def __del__(self):
        LOG.debug("inside destructor")

    def get_all(self, table, *columns):
        sql = "SELECT %s FROM %s" % (', '.join(columns), table)
        conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sql)
        result = list(cursor.fetchall())
        conn.close()
        return result

    def remove(self, table, id):
        try:
            sql = "DELETE FROM %s WHERE name='%s' OR id='%s'" %(table, id, id)
            conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
            cursor = conn.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            LOG.error(e)
            conn.rollback()
        else: 
            conn.close()
       

    def remove_all(self, table):
        try:
            sql = "DELETE FROM %s" %(table)
            conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
            cursor = conn.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            LOG.error(e)
            conn.rollback()
        else: 
            conn.close()



class PlaybookDB(AnsibleDB):
    __metaclass__ = Singleton
    TABLE_NAME = "playbook"
    def __init__(self):
        LOG.debug("inside PlaybookDB.__init__()")
        AnsibleDB.__init__(self)

    def create_schema(self):
        LOG.debug("PlaybookDB.create_schema")
        sql = "DROP TABLE IF EXISTS %s" %(PlaybookDB.TABLE_NAME)
        LOG.debug(sql)
        conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sql)

        sql = """
            CREATE TABLE %s (
                id           VARCHAR(64) NOT NULL,
                name         VARCHAR(64) NOT NULL,
                content      BLOB NOT NULL,
                content_type VARCHAR(32)
            )
        """ % (PlaybookDB.TABLE_NAME)
        LOG.debug(sql)
        cursor.execute(sql)

        cursor.execute("SHOW columns FROM %s" %(PlaybookDB.TABLE_NAME))
        result = cursor.fetchall() 
        LOG.info(result)
        conn.close()
    
    def content_type(self, content):
        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(content)
        temp.close()
        content_type  = magic.detect_from_filename(temp.name).mime_type
        os.remove(temp.name)
        return content_type


    def add(self, data):
        id = str(uuid.uuid1())
        name = data.get("name")
        content = data.get("content")
        content_type = self.content_type(content)
        sql = "INSERT INTO playbook(id, name, content, content_type) VALUES (%s, %s, %s, %s)" 
        try:
            conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
            cursor = conn.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(sql, (id, name, content, content_type))
            conn.commit()
            return id
        except Exception as e:
            LOG.error(e)
            conn.rollback()
            raise e
        else: 
            conn.close()

    def get_all(self):
        return super(PlaybookDB, self).get_all(PlaybookDB.TABLE_NAME, "id", "name", "content_type")
        
    def get(self, id):
        sql = "SELECT id, name, content, content_type FROM playbook WHERE id='%s'" %(id)
        conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sql)
        data = list(cursor.fetchall())
        result = None
        if len(data) != 0:
            result = data[0]
        conn.close()
        return result

    def remove(self, id):
        return super(PlaybookDB, self).remove(PlaybookDB.TABLE_NAME, id)

    def remove_all(self):
        return super(PlaybookDB, self).remove_all(PlaybookDB.TABLE_NAME)


class ExecutionLogsDB(AnsibleDB):
    __metaclass__ = Singleton
    TABLE_NAME = "playbook_executions_log"
    def __init__(self):
        AnsibleDB.__init__(self)

    def create_schema(self):
        sql = "DROP TABLE IF EXISTS playbook_executions_log"
        conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sql)

        sql = """
            CREATE TABLE %s (
                execution_id      VARCHAR(64) NOT NULL,
                request           TEXT NOT NULL,
                status            VARCHAR(32),
                result            VARCHAR(32),
                duration          INT,
                execution_summary TEXT,
                logs              BLOB
            )
        """ % (ExecutionLogsDB.TABLE_NAME)
        cursor.execute(sql)

        cursor.execute("SHOW columns FROM %s" %(ExecutionLogsDB.TABLE_NAME))
        result = cursor.fetchall() 
        conn.close()

    def add(self, data):
        execution_id = data.get("execution_id")
        request = data.get("request")
        status = data.get("status") # in_progress, complete
        result = data.get("result") # success, failed
        duration = data.get("duration", -1)
        logs = data.get("logs")
        sql = "INSERT INTO %s (execution_id, request, status, result, duration, logs) VALUES ('%s', '%s', '%s', '%s', '%s', '%s')"  \
              %(ExecutionLogsDB.TABLE_NAME,execution_id, request, status, result, duration, logs)
        try:
            conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
            cursor = conn.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            LOG.error(e)
            conn.rollback()
        else: 
            conn.close()

    def update_logs(self, id, logs):
        sql = "UPDATE  %s SET logs='%s' WHERE execution_id='%s'" \
              %(ExecutionLogsDB.TABLE_NAME, logs, id)
        print sql
        try:
            conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
            cursor = conn.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            print e
            LOG.error(e)
            conn.rollback()
        else: 
            conn.close()

    def update(self, id, status, result, duration, execution_summary):
        sql = "UPDATE %s SET status='%s', result='%s', duration=%d, execution_summary='%s' WHERE execution_id='%s'" \
              %(ExecutionLogsDB.TABLE_NAME, status, result, duration, execution_summary, id)
        print sql
        try:
            conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
            cursor = conn.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            print e
            LOG.error(e)
            conn.rollback()
        else: 
            conn.close()

    def get_all(self):
        return super(ExecutionLogsDB, self).get_all(ExecutionLogsDB.TABLE_NAME, "*")
        
    def get(self, id):
        sql = "SELECT * FROM %s WHERE execution_id='%s'" %(ExecutionLogsDB.TABLE_NAME, id)
        LOG.debug(sql)
        conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(sql)
        data = list(cursor.fetchall())
        LOG.debug(data)
        result = None
        if len(data) != 0:
            result = data[0]
        conn.close()
        return result

    def remove(self, id):
        try:
            sql = "DELETE FROM %s WHERE execution_id='%s'" %(ExecutionLogsDB.TABLE_NAME, id)
            conn = MySQLdb.connect(mysql_host, user, password, AnsibleDB.DB_NAME)
            cursor = conn.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(sql)
            conn.commit()
        except Exception as e:
            print e
            conn.rollback()
        else: 
            conn.close()

    def remove_all(self):
        super(ExecutionLogsDB, self).remove_all(ExecutionLogsDB.TABLE_NAME)


def list_execution_logs():
    ExecutionLogsDB().get_all()

def create_schema():
    PlaybookDB().create_schema()
    ExecutionLogsDB().create_schema()

def list_playbooks():
    PlaybookDB().get_all()

def create_playbook(argv):
    name = argv[0]
    with open(name, 'rb') as f:
        content = f.read()
    db = PlaybookDB()
    
    data = {
        "name": name,
        "content": content,
    }
    db.add(data)


def create_execution_logs():
    db = ExecutionLogsDB()
    data = {
        "execution_id": "100",
        "request": "{}",
        "status": "complete",
        "result": "success",
        "logs": "log data"
    }
    db.add(data)


def update_execution_logs():
    db = ExecutionLogsDB()
    db.update(id="100", status="completed", result="1-failed", logs="1-updated logs", duration=100)
    db.get("100")


def main(argv):
    print "MYSQL Client"

    #create_schema()
    #create_playbook(argv)
    #create_execution_logs()
    #update_execution_logs()
    #list_playbooks()
    #list_execution_logs()
 
    '''
    db.get("abcd")
    db.remove("abcd")
    db.get("abcd")
    db.remove_all()
    '''


    '''
    execution_logs = ExecutionLogsDB()
    execution_logs.create_schema()
    data = {
        "execution_id": "1",
        "playbook_id": "100",
        "playbook_name": "play1",
        "version": "1.0",
        "duration": 100,
        "status": "success",
        "logs": "some log data"
    }
    '''
    

if __name__ == "__main__":
    main(sys.argv[1:])

