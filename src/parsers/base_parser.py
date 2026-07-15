from abc import ABC, abstractmethod

from src.models.ucm import UCM


class BaseParser(ABC):
    """
    Base class for all cable parsers.

    Every manufacturer-specific parser converts a cable designation
    into a Universal Cable Model (UCM).
    """

    @abstractmethod
    def parse(self, designation: str, comment: str | None = None) -> UCM:
        """
        Parse a cable designation and return a populated UCM object.

        Parameters
        ----------
        designation : str
            Original cable designation.
        comment : str | None
            Optional invoice comment with extra construction notes.

        Returns
        -------
        UCM
            Universal Cable Model.
        """
        pass
