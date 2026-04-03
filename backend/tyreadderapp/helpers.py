def optimize_value(value):
        """
        Remove spaces, colons, dashes, and lowercase the string.
        """
        return str(value or "").replace(" ", "").replace(":", "").replace("-", "").lower()