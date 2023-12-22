from datetime import datetime
import requests

# just shorthand for logs and errors - easier to write in script
def log(input):
    print(f"[{datetime.now().strftime('%b %d %Y - %H:%M:%S')}] {input}")

# a seperate log function to be used whilst you have debug mode active, a thing mostly just for developing steam presence
def logDebug(input):
    print("[DEBUG] ", end="")
    log(input)

def error(input):
    print(f"    ERROR: [{datetime.now().strftime('%b %d %Y - %H:%M:%S')}] {input}")

# i've gotten the error `requests.exceptions.ConnectionError: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))` a lot;
# this just seems to sometimes happens if your network conection is a bit wack, this function is a replacement for requests.get() and basically just does error handling and stuff
def makeWebRequest(URL, loops=0):
    logDebug(f"making a web request to {URL}")
    try:
        r = requests.get(URL)
        return r
    except Exception as e:
        if loops > 10:
            error(f"falling back... the script got caught in a loop while fetching data from `{URL}`")
            return "error"
        elif "104 'Connection reset by peer'" in str(e):
            return makeWebRequest(URL, loops+1)
        else:
            # error(f"falling back... exception met whilst trying to fetch data from `{URL}`\nfull error: {e}")
            return "error"

def removeChars(inputString: str, ignoredChars: str) -> str:
    # removes all characters in the ingoredChars string from the inputString
    for ignoredChar in ignoredChars:
        if ignoredChar in inputString:
            for j in range(len(inputString) - 1, 0, -1):
                if inputString[j] in ignoredChar:
                    inputString = inputString[:j] + inputString[j+1:]

    return inputString