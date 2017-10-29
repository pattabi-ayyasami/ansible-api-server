from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager


Options = namedtuple('Options', ['connection','module_path', 'diff','forks', 'remote_user', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args', 'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check'])
# initialize needed objects
loader = DataLoader()
options = Options(connection='local', module_path='/path/to/mymodules', diff=False, forks=100, remote_user=None, private_key_file=None, ssh_common_args=None, ssh_extra_args=None, sftp_extra_args=None, scp_extra_args=None, become=None, become_method=None, become_user=None, verbosity=3, check=False)
passwords = dict(vault_pass='secret')

# create inventory and pass to var manager
inventory = InventoryManager(loader=loader)

variable_manager = VariableManager(loader=loader)
variable_manager.set_inventory(inventory)

# create play with tasks
play_source =  dict(
        name = "Ansible Play",
        hosts = 'localhost',
        gather_facts = 'no',
        tasks = [ dict(action=dict(module='debug', args=dict(msg='Hello Galaxy!'))) ]
    )
play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

# actually run it
tqm = None
try:
    tqm = TaskQueueManager(
              inventory=inventory,
              variable_manager=variable_manager,
              loader=loader,
              options=options,
              passwords=passwords,
              stdout_callback='default',
          )
    tqm.load_callbacks()
    result = tqm.run(play)
    stats = tqm._stats
    print stats.summarize('localhost')

    tqm.send_callback(
        "record_logs",
        user_id="pattabi",
        success=True
    )
    
finally:
    if tqm is not None:
        tqm.cleanup()

def main():
    print "main"

if __name__ == "__main__":
    main()
