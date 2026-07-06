from importlib import import_module
r = import_module('app.api.routes').router
for route in sorted(r.routes, key=lambda x: x.path):
    print(route.path)
