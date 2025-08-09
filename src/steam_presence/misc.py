import os

def get_terminal_width() -> int:
    width: int

    try:
        size = os.get_terminal_size()
        width = size.columns
    except:
        width = 10
    
    return width