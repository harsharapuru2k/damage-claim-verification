from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """All agents return a dict and never raise — errors return a safe default state."""

    @abstractmethod
    def run(self, **kwargs) -> dict:
        ...

    def _safe_run(self, **kwargs) -> dict:
        try:
            return self.run(**kwargs)
        except Exception as e:
            print(f"  [{self.__class__.__name__}] error: {e}")
            return self._error_state(str(e))

    def _error_state(self, reason: str) -> dict:
        return {"error": reason}
