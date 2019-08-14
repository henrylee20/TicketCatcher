import abc


class Process(metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def processes() -> dict:
        pass
