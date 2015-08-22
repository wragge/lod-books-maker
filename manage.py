from maker import app
from flask.ext.script import Server, Manager
from flask.ext.migrate import MigrateCommand

manager = Manager(app)
manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host='192.168.0.13'))


manager.run()
