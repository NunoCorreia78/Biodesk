import inspect
from ficha_paciente.services import database_service
print('module:', database_service)
print('DatabaseService class:', getattr(database_service, 'DatabaseService', None))
if hasattr(database_service, 'DatabaseService'):
    print('init sig:', inspect.signature(database_service.DatabaseService.__init__))
