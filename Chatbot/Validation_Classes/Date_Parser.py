import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, Union, Tuple

class Date_Parser:
    def __init__(self, date_str: str = ""):
        self.date_str = date_str

    def parse_flexible_date(self, date_input: str) -> Optional[Union[datetime, Tuple[datetime, datetime]]]:
        """Parses flexible date inputs like "next week", "15th October", "summer", etc."""
        date_input = date_input.lower()
        today = datetime.now()
        
        # Handle relative dates
        if "today" in date_input:
            return (today, today)
        elif "tomorrow" in date_input:
            start_date = today + timedelta(days=1)
            return (start_date, start_date)
        elif "yesterday" in date_input:
            raise ValueError("Cannot plan trips for past dates. Please select a future date.")
        elif "next week" in date_input:
            start_date = today + timedelta(weeks=1)
            end_date = start_date + timedelta(days=6)
            return (start_date, end_date)
        elif "next month" in date_input:
            start_date = today + relativedelta(months=1, day=1)
            end_date = start_date + relativedelta(day=31)
            return (start_date, end_date)
        elif "next year" in date_input:
            start_date = today + relativedelta(years=1, month=1, day=1)
            end_date = start_date + relativedelta(month=12, day=31)
            return (start_date, end_date)
        elif "next season" in date_input:
            return self.get_next_season_range(today)
        elif "next quarter" in date_input:
            return self.get_next_quarter_range(today)

        # Handle seasons
        if "summer" in date_input:
            return self.get_season_range(today.year, "summer")
        elif "autumn" in date_input or "fall" in date_input:
            return self.get_season_range(today.year, "autumn")
        elif "winter" in date_input:
            return self.get_season_range(today.year, "winter")
        elif "spring" in date_input:
            return self.get_season_range(today.year, "spring")

        # Handle absolute dates
        absolute_date = self.parse_absolute_date(date_input)
        if absolute_date:
            return absolute_date

        # Handle months
        month_range = self.parse_month_range(date_input)
        if month_range:
            return month_range

        return None

    def parse_absolute_date(self, date_input: str) -> Optional[datetime]:
        """Parses absolute dates like "15th October", "1st January", etc."""
        try:
            date_input = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_input)

            # Try parsing with common date formats
            date_formats = [
                "%d %B %Y",  # 15 October 2023
                "%d %b %Y",  # 15 Oct 2023
                "%d %B",  # 15 October (assumes current year)
                "%d %b",  # 15 Oct (assumes current year)
            ]

            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_input, fmt)
                    
                    # Check if the date is in the past
                    today = datetime.now()
                    if parsed_date.date() < today.date():
                        raise ValueError(f"Cannot plan trips for past dates. '{date_input}' is in the past. Please select a future date.")
                    
                    return parsed_date
                except ValueError as e:
                    # If it's our custom error, re-raise it
                    if "Cannot plan trips for past dates" in str(e):
                        raise
                    continue
            return None
        except Exception as e:
            # Re-raise our custom error
            if "Cannot plan trips for past dates" in str(e):
                raise
            return None

    def parse_month_range(self, date_input: str) -> Optional[Tuple[datetime, datetime]]:
        """Parse month names like "March", "June", etc."""
        try:
            month_names = {
                "january": 1, "february": 2, "march": 3, "april": 4,
                "may": 5, "june": 6, "july": 7, "august": 8,
                "september": 9, "october": 10, "november": 11, "december": 12,
            }

            for month_name, month_num in month_names.items():
                if month_name in date_input:
                    year = datetime.now().year
                    start_date = datetime(year, month_num, 1)
                    
                    # Check if the month is in the past
                    today = datetime.now()
                    if start_date.date() < today.date():
                        raise ValueError(f"Cannot plan trips for past months. '{month_name.capitalize()}' is in the past. Please select a future month.")
                    
                    end_date = start_date + relativedelta(day=31)
                    return (start_date, end_date)
            return None
        except Exception as e:
            # Re-raise our custom error
            if "Cannot plan trips for past months" in str(e):
                raise
            return None

    def get_season_range(self, year: int, season: str) -> Tuple[datetime, datetime]:
        """Returns the start and end dates of a season for a given year."""
        today = datetime.now()
        
        if season == "spring":
            start_date = datetime(year, 3, 1)
        elif season == "summer":
            start_date = datetime(year, 6, 1)
        elif season == "autumn":
            start_date = datetime(year, 9, 1)
        elif season == "winter":
            start_date = datetime(year, 12, 1)
        else:
            # Default to spring if season is invalid
            start_date = datetime(year, 3, 1)
        
        # Check if the season is in the past
        if start_date.date() < today.date():
            raise ValueError(f"Cannot plan trips for past seasons. '{season.capitalize()}' {year} is in the past. Please select a future season.")
        
        if season == "spring":
            return (start_date, datetime(year, 5, 31))
        elif season == "summer":
            return (start_date, datetime(year, 8, 31))
        elif season == "autumn":
            return (start_date, datetime(year, 11, 30))
        elif season == "winter":
            return (start_date, datetime(year + 1, 2, 28))
        else:
            # Default to spring if season is invalid
            return (start_date, datetime(year, 5, 31))

    def get_next_season_range(self, today: datetime) -> Tuple[datetime, datetime]:
        """Returns the start and end dates of the next season."""
        current_month = today.month
        if current_month < 3:
            return (datetime(today.year, 3, 1), datetime(today.year, 5, 31))  # Spring
        elif current_month < 6:
            return (datetime(today.year, 6, 1), datetime(today.year, 8, 31))  # Summer
        elif current_month < 9:
            return (datetime(today.year, 9, 1), datetime(today.year, 11, 30))  # Autumn
        elif current_month < 12:
            return (datetime(today.year, 12, 1), datetime(today.year + 1, 2, 28))  # Winter
        else:
            return (datetime(today.year + 1, 3, 1), datetime(today.year + 1, 5, 31))  # Next spring

    def get_next_quarter_range(self, today: datetime) -> Tuple[datetime, datetime]:
        """Returns the start and end dates of the next quarter."""
        current_month = today.month
        if current_month < 4:
            return (datetime(today.year, 4, 1), datetime(today.year, 6, 30))
        elif current_month < 7:
            return (datetime(today.year, 7, 1), datetime(today.year, 9, 30))
        elif current_month < 10:
            return (datetime(today.year, 10, 1), datetime(today.year, 12, 31))
        else:
            return (datetime(today.year + 1, 1, 1), datetime(today.year + 1, 3, 31))
