import re
from typing import Optional, Union
from word2number import w2n
import logging

logger = logging.getLogger(__name__)

class Duration_Parser:
    def __init__(self, duration_str: str = ""):
        self.duration_str = duration_str

    def parse_flexible_duration(self, duration_input: str) -> Optional[int]:
        """
        Parses flexible duration inputs like "7 days", "two weeks", "1 month", "3", etc.
        Returns an integer representing the duration in days or None if parsing fails.
        Raises ValueError for invalid durations.
        """
        try:
            # Convert duration_input to string if it's not already
            if not isinstance(duration_input, str):
                duration_input = str(duration_input)

            # More flexible regex pattern that handles various formats
            match = re.match(r'(\d+|[\w\s-]+)\s*(day|week|month|days|weeks|months)?', duration_input.lower())
            if not match:
                raise ValueError("Please enter a valid duration (e.g., '7 days', 'two weeks', '1 month', '3').")

            number_part, unit = match.groups()
            number_part = number_part.strip()

            # Try to convert the number part
            try:
                # First try direct integer conversion
                number = int(number_part)
            except ValueError:
                try:
                    # If that fails, try word to number conversion
                    number = w2n.word_to_num(number_part)
                except ValueError:
                    raise ValueError("Please enter a valid number for the duration.")

            # If no unit is specified, assume days
            if not unit:
                unit = "days"
            else:
                unit = unit.lower()

            # Convert to days based on unit
            duration_days = self._convert_to_days(number, unit)

            # Validate the duration
            self._validate_duration(duration_days)

            return duration_days

        except Exception as e:
            # Re-raise our custom errors
            if "Please enter a valid" in str(e):
                raise
            logger.error(f"Error parsing duration: {str(e)}")
            raise ValueError("Something went wrong while processing the duration. Please try again.")

    def _convert_to_days(self, number: int, unit: str) -> int:
        """
        Converts duration to days based on the unit.
        """
        if unit in ["day", "days"]:
            return number
        elif unit in ["week", "weeks"]:
            return number * 7
        elif unit in ["month", "months"]:
            return number * 30
        else:
            raise ValueError("Please specify a valid unit (days, weeks, or months).")

    def _validate_duration(self, duration_days: int) -> None:
        """
        Validates duration constraints.
        Raises ValueError if duration is invalid.
        """
        if duration_days <= 0:
            raise ValueError("Please enter a valid duration greater than zero.")

        if duration_days > 365:  # Add a reasonable upper limit
            raise ValueError("Please enter a duration of one year or less.")

        # Add minimum duration check if needed
        if duration_days < 1:
            raise ValueError("Please enter a duration of at least 1 day.")

   