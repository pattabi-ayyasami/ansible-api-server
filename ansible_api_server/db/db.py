import os
import io
import sys
import zipfile
import tarfile
import tempfile
import shutil
import uuid
import errno 

from tinydb import TinyDB, Query

from ansible_api_server.utils.utils import Util

def is_archive(archive):
    if zipfile.is_zipfile(archive):
        return True
    if tarfile.is_tarfile(archive):
        return True
    return False

    
DB_PATH = "/home/pattabi/ansible/ansible_api_server/ansible_api_server/data/db"
DB_NAME = DB_PATH + "/" + "ansible-playbooks-db.json"
class PlaybooksDB(object):
    def __init__(self):
        self.db = TinyDB(DB_NAME)
        self.playbooks = self.db.table('playbooks', cache_size=30)

    def add(self, name, archive, file_name, archive_type=None):
        query = Query()
        if self.does_exist(name):
            print "Playbook %s already exists" %name
            return

        is_archive_file = is_archive(archive)
        id = str(uuid.uuid1())
      
        content_path = DB_PATH + "/" + id
        try:
            os.makedirs(content_path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

        shutil.copyfile(archive, content_path + "/" + file_name)
        self.playbooks.insert({"id": id,
                               "name": name, 
                               "archive_file_name": file_name, 
                               "archive_type": archive_type,
                               "content": content_path, 
                               "is_archive": is_archive_file})
        return id

    def get(self, id):
        query = Query()
        return self.playbooks.get(query.id == id)

    def get_all(self):
        return self.playbooks.all()

    def remove(self, id):
        query = Query()
        result = self.playbooks.remove(query.id == id)
        if result:
            print "Deleting the archive of playbook %s" %id
            shutil.rmtree(DB_PATH + "/" + id)
        else:
            print "Playbook %s does not exist in DB" %id

    def does_exist(self, name):
        query = Query()
        return True if len(self.playbooks.search(query.name == name)) != 0 else False
    
    def get_content(self, id):
        entry = self.get(id)
        if entry is None:
            print('Playbook %s does not exist.', id)
            return None
        else:
            temp_package_loc =  DB_PATH + "/" + entry["name"] + ".zip"
            Util.zip_dir(entry["content"], temp_package_loc)
            return temp_package_loc

     

def main(argv):
    name = argv[0]
    archive = argv[1]
    archive_type = argv[2]

    db = PlaybooksDB()
    id = db.add(name, archive, archive, archive_type)
    playbooks =  db.get_all()


if __name__ == "__main__":
    main(sys.argv[1:])

