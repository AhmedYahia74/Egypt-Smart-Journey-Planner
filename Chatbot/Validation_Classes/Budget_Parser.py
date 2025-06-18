import re
from typing import Optional, Union
from word2number import w2n
import logging

logger = logging.getLogger(__name__)

class Budget_Parser:
    def __init__(self, budget_str: str = ""):
        self.budget_str = budget_str

    def parse_flexible_budget(self, budget_input: str) -> Optional[float]:
        """
        Parses flexible budget inputs like "500 dollars", "one hundred USD", "$1000", etc.
        Returns a float representing the budget amount or None if parsing fails.
        Raises ValueError for invalid budgets.
        """
        try:
            # Convert budget_input to string if it's not already
            if not isinstance(budget_input, str):
                budget_input = str(budget_input)

            # More flexible regex pattern that handles various formats
            match = re.match(r'(\$?\d+|[\w\s-]+\$?)\s*(dollar|dollars|usd)?', budget_input, re.IGNORECASE)
            if not match:
                raise ValueError("Please enter a valid budget (e.g., '500 dollars', 'one hundred USD').")

            number_part, currency = match.groups()

            # Clean up the number part
            if number_part.startswith('$'):
                number_part = number_part[1:]
            elif number_part.endswith('$'):
                number_part = number_part[:-1]

            # Try to convert the number part
            try:
                # First try direct integer conversion
                budget = int(number_part)
            except ValueError:
                try:
                    # If direct conversion fails, try word to number conversion
                    budget = w2n.word_to_num(number_part)
                except ValueError:
                    raise ValueError("Please enter a valid number for the budget.")

            # Validate budget constraints
            self._validate_budget_amount(budget)

            return float(budget)

        except Exception as e:
            # Re-raise our custom errors
            if "Please enter a valid" in str(e):
                raise
            logger.error(f"Error parsing budget: {str(e)}")
            raise ValueError("Something went wrong while processing your budget. Please try again.")

    def _validate_budget_amount(self, budget: float) -> None:
        """
        Validates budget amount constraints.
        Raises ValueError if budget is invalid.
        """
        if budget <= 0:
            raise ValueError("Please enter a valid positive budget.")

        # Add reasonable budget limits
        if budget > 1000000:  # Example upper limit
            raise ValueError("Please enter a more reasonable budget amount.")
