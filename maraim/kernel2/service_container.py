class ServiceContainer:
    def __init__(self):
        self._factories = {}
        self._instances = {}

    def register(self, name, factory, singleton=True):
        self._factories[name] = {"factory": factory, "singleton": singleton}
        return self

    def resolve(self, name):
        if name in self._instances:
            return self._instances[name]
        if name not in self._factories:
            raise KeyError(f"Service not registered: {name}")
        spec = self._factories[name]
        instance = spec["factory"]()
        if spec["singleton"]:
            self._instances[name] = instance
        return instance

    def list_services(self):
        return sorted(set(self._factories.keys()) | set(self._instances.keys()))
