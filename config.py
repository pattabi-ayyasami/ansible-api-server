# Server Specific Configurations
server = {
    'port': '8090',
    'host': '0.0.0.0'
}

# Pecan Application Configurations
app = {
    'root': 'ansible_api_server.controllers.root.RootController',
    'modules': ['ansible_api_server', 'ansible_api_server.impl'],
    'static_root': '%(confdir)s/public',
    'template_path': '%(confdir)s/ansible_api_server/templates',
    'debug': True,
    'errors': {
        404: '/error/404',
        '__force_dict__': True
    },
    'force_canonical': False
}

logging = {
    'root': {'level': 'DEBUG', 'handlers': ['console']},
    'loggers': {
        'ansible_api_server': {'level': 'DEBUG', 'handlers': ['console'], 'propagate': False},
        'pecan': {'level': 'DEBUG', 'handlers': ['console'], 'propagate': False},
        'py.warnings': {'handlers': ['console']},
        '__force_dict__': True
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'color'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'color',
            'filename': './logs/ansible-api-server.log',
            'maxBytes': 1024 * 1024,
            'backupCount': 5
        }

    },
    'formatters': {
        'simple': {
            'format': ('%(asctime)s %(levelname)-5.5s [%(name)s]'
                       '[%(threadName)s] %(message)s')
        },
        'color': {
            '()': 'pecan.log.ColorFormatter',
            'format': ('%(asctime)s [%(padded_color_levelname)s] [%(name)s]'
                       '[%(threadName)s] %(message)s'),
        '__force_dict__': True
        }
    }
}

# Custom Configurations must be in Python dictionary format::
#
# foo = {'bar':'baz'}
#
# All configurations are accessible at::
# pecan.conf
