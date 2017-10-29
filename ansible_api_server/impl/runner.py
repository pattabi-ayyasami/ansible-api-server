import os
from tempfile import NamedTemporaryFile
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.parsing.dataloader import DataLoader
from ansible.executor import playbook_executor
from ansible.utils.display import Display

from options import Options

class Runner(object):

    def __init__(self, execution_id, playbook_dir, 
                 options, playbook_name, 
                 extra_vars, become_password=None):

        self.execution_id = execution_id
        self.extra_vars = extra_vars
        self.playbook_name = playbook_name
        self.options = Options()
        for k,v in options.iteritems():
            setattr(self.options, k,v)
        print options

        # Set global verbosity
        self.display = Display()
        self.display.verbosity = self.options.verbosity
        # Executor appears to have it's own 
        # verbosity object/setting as well
        playbook_executor.verbosity = self.options.verbosity

        # Become Pass Needed if not logging in as user root
        passwords = {'become_pass': become_password}

        # Gets data from YAML/JSON files
        self.loader = DataLoader()
        # Set inventory, using most of above objects
        temp_dir = "/home/pattabi/ansible/ansible_api_server/ansible_api_server/data"
        self.inventory = InventoryManager(loader=self.loader, sources=[temp_dir + "/" + "hosts"])

        # All the variables from all the various places
        self.variable_manager = VariableManager(loader=self.loader)
        self.variable_manager.set_inventory(self.inventory)
        self.variable_manager.extra_vars = self.extra_vars

        # Setup playbook executor, but don't run until run() called
        self.pbex = playbook_executor.PlaybookExecutor(
            playbooks=[playbook_dir + "/" + playbook_name], 
            inventory=self.inventory, 
            variable_manager=self.variable_manager,
            loader=self.loader, 
            options=self.options, 
            passwords=passwords)

    def run(self):
        # Results of PlaybookExecutor
        self.pbex.run()
        stats = self.pbex._tqm._stats

        # Test if success for record_logs
        run_success = True
        target_hosts = sorted(stats.processed.keys())
        for h in target_hosts:
            t = stats.summarize(h)
            if t['unreachable'] > 0 or t['failures'] > 0:
                run_success = False

        # Dirty hack to send callback to save logs with data we want
        # Note that function "record_logs" is one I created and put into
        # the playbook callback file
        self.pbex._tqm.send_callback(
            'record_logs', 
            self.execution_id,
            success=run_success
        )

        return stats
