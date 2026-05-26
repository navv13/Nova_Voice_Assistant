import webbrowser
import subprocess
import sys

APP_MAP = {
    #windows
    "notepad":    ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint":      ["mspaint.exe"],
    "explorer":   ["explorer.exe"],
    #Cross-Platfomr
    "vscode":     ["code"],
    "terminal":   ["cmd.exe"] if sys.platform == "win32" else ["x-terminal-emulator"],   
}

def open_app(app_name: str) -> str:
    key = app_name.lower().strip()
    cmd = APP_MAP.get(key)
    if not cmd:
        return f"Sorry, I don't know how to open '{app_name}'."
    try:
        subprocess.Popen(cmd, shell=True)
        return f"Opening {app_name}'."
    except FileNotFoundError:
        return f"Could not find '{app_name}' on this system."


def web_search(query: str) -> str:
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Searching the web for: {query}"

def open_website(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url}"

def handle_command(text: str):
    lower = text.lower()

    #open website
    for kw in ("open website", "go to", "visit"):
        if kw in lower:
            site = lower.split(kw)[-1].strip()
            return open_website(site)

    #web search
    for kw in ("search for", "search", "google", "look up"):
        if lower.startswith(kw):
            query = lower.replace(kw, "", 1).strip()
            return web_search(query)

    # Open app
    for kw in ("open", "launch", "start"):
        if lower.startswith(kw):
            app = lower.replace(kw, "", 1).strip()
            return open_app(app)
        
    #Youtube
    if "youtube" in lower:
        query = lower.replace("youtube", "").replace("play", "").strip()
        url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Playing '{query}' on YouTube."
    
    return None #Let AI handle it