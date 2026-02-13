import re

def format_uzbek_name(name: str) -> str:
    """
    Format Uzbek names to Title Case, but correctly handle apostrophes.
    Standard .title() converts "g'ofurov" -> "G'Ofurov".
    This function ensures "G'ofurov".
    
    Handles: ', `, ’, ‘
    """
    if not name:
        return ""
    
    # 1. Standard Title Case
    formatted = str(name).strip().title()
    
    # 2. Fix the Apostrophe Capitalization
    # We want to lowercase the letter AFTER the apostrophe if it's currently uppercase
    def replacer(match):
        return match.group(1) + match.group(2).lower()
    
    # Regex: Lookbehind for a letter, capture apostrophe, capture Uppercase letter
    return re.sub(r"(?<=[a-zA-Z])(['`’‘])([A-Z])", replacer, formatted)
