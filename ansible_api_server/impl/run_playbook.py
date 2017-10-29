import logging
import os
import json
import shutil
import sys
import tarfile
import tempfile
import time
import zipfile

from ansible_api_server.db import mysqldb as db
from multiprocessing import Process

from options import Options
from runner import Runner


LOG = logging.getLogger(__name__)


class PlaybookExecutor:
    def play(self, execution_id, inputs):
        playbook_id = inputs.get("playbook_id")
        playbook_name = inputs.get("playbook_name")
        options = inputs.get("options", {})
        extra_vars = inputs.get("env_parameters")

        PLAYBOOK_DIR = tempfile.mkdtemp()
        LOG.debug("Playbook directory: %s", PLAYBOOK_DIR)
        try:
            start_time = time.time()

            playbook_info = db.PlaybookDB().get(playbook_id)
            LOG.debug("Playbook: %s", playbook_info)
            name = playbook_info.get("name")
            content_type = playbook_info.get("content_type")
            content = playbook_info.get("content")
            playbook_file = PLAYBOOK_DIR + "/" + name
            LOG.debug("Playbook File: %s", playbook_file)
            with open(playbook_file, 'w') as f:
                f.write(content)
                
            if content_type == "application/x-tar":
                archive = tarfile.open(PLAYBOOK_DIR + "/" + name, 'r')
                archive.extractall(PLAYBOOK_DIR)
                archive.close()
            elif content_type == "application/zip":
                archive = zipfile.ZipFile(PLAYBOOK_DIR + "/" + name, 'r')
                archive.extractall(PLAYBOOK_DIR)
                archive.close()
            elif content_type == "application/gzip":
                archive = tarfile.open(PLAYBOOK_DIR + "/" + name, mode='r:gz')
                archive.extractall(PLAYBOOK_DIR)
                archive.close()
            else:
                LOG.debug("Content type is %s. No need to extract", content_type)

            runner = Runner(execution_id=execution_id,
                            playbook_dir=PLAYBOOK_DIR, 
                            options=options,
                            playbook_name=playbook_name,
                            extra_vars=extra_vars)
            print "Run the playbook ..."
            stats = runner.run()

            status = "COMPLETED"
            result = "SUCCESS"
            execution_summary = {}
            target_hosts = sorted(stats.processed.keys())
            for h in target_hosts:
                t = stats.summarize(h)
                execution_summary[h] = {
                    "ok": t['ok'],
                    "changed": t['changed'],
                    "unreachable": t['unreachable'],
                    "skipped": t['skipped'],
                    "failed": t['failures']
                }   
                if t['unreachable'] > 0 or t['failures'] > 0:
                    result = "FAILED"
            print "======================================================="
            print "Result: %s" %result
            print "Execution Summary: %s" %json.dumps(execution_summary, indent=4)
            print "======================================================="
            end_time = time.time()
            duration = end_time - start_time
            print "Duration: %d" %duration
            db.ExecutionLogsDB().update(execution_id, status, result, duration, json.dumps(execution_summary, indent=4))

            LOG.debug("Execution of the playbook complete")
        except Exception as e:
            LOG.error(e)
            raise e
        else:
            print("Removing the %s temporary directory" %PLAYBOOK_DIR)
            shutil.rmtree(PLAYBOOK_DIR)

    def run_ansible_playbook(self, execution_id, inputs):
        p = Process(target=self.play,
                    args = (execution_id, inputs))
        p.start()


if __name__ == "__main__":
    main(sys.argv[1:])
