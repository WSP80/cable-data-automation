from abc import ABC, abstractmethod

from src.models.ucm import UCM


class BaseGenerator(ABC):
    """
    Base class for cable designation generators.
    """

    @abstractmethod
    def generate(self, ucm: UCM) -> str:
        """
        Generate a manufacturer-specific cable designation
        from the Universal Cable Model.

        Parameters
        ----------
        ucm : UCM

        Returns
        -------
        str
            Cable designation.
        """
        pass