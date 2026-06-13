from abc import ABC, abstractmethod


class BaseExperiment(ABC):
    name: str = "experiment"

    @abstractmethod
    def build_context(self):
        pass

    @abstractmethod
    def build_stages(self):
        pass

    def setup(self, context):
        pass

    def teardown(self, context):
        pass

