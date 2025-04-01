"""A custom exception for handling data integrity violations.

This exception should be raised when data fails to meet integrity requirements,
such as schema validation, referential integrity, or business rule constraints.
It provides context about the integrity violation by storing both an explanatory
message and the problematic data.
"""

from typing import Any, Optional


class DataIntegrityError(Exception):
    """Exception raised for errors in the data integrity.

    Args:
        message: Explanation of the error.
        data: The data that caused the integrity violation.

    Attributes:
        message: A string explaining the error.
        data: The data that caused the integrity violation.
    """

    def __init__(
        self,
        message: str = 'Data integrity violation encountered.',
        data: Optional[Any] = None,
    ) -> None:
        """Initialize the DataIntegrityError.

        Args:
            message: Explanation of the error. Defaults to generic message.
            data: The data that caused the error. Defaults to None.
        """
        self.message = message
        self.data = data
        super().__init__(self.message)

    def __str__(self) -> str:
        """Create string representation of the error.

        Returns:
            String containing error message and optionally the problematic data.
        """
        if self.data:
            return f'{self.message} Data: {self.data}'
        return self.message
