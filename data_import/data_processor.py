import logging
import json


class DataProcessor:
    def __init__(self, logger):
        self.logger = logger

    def parse_json(self, json_data: str):
        """Parse JSON data."""
        try:
            return json.loads(json_data)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {str(e)}", exc_info=True)
            raise
