"""Send iMessage via macOS Messages.app using AppleScript."""

import subprocess
import logging

log = logging.getLogger("forge.imessage")


def send_imessage(recipient: str, message: str) -> dict:
    """
    Send an iMessage to a phone number or Apple ID.
    recipient: phone number (+1XXXXXXXXXX) or email
    message: plain text body
    Returns {"sent": True} or {"sent": False, "error": "..."}
    """
    escaped_msg = message.replace("\\", "\\\\").replace('"', '\\"')
    escaped_recipient = recipient.replace("\\", "\\\\").replace('"', '\\"')

    script = f'''
    tell application "Messages"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant "{escaped_recipient}" of targetService
        send "{escaped_msg}" to targetBuddy
    end tell
    '''

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            log.info(f"iMessage sent to {recipient}")
            return {"sent": True}
        else:
            err = result.stderr.strip()
            log.error(f"iMessage failed: {err}")
            return {"sent": False, "error": err}
    except subprocess.TimeoutExpired:
        log.error("iMessage timed out")
        return {"sent": False, "error": "timeout"}
    except Exception as e:
        log.error(f"iMessage error: {e}")
        return {"sent": False, "error": str(e)}
