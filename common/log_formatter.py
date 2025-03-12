import logging
import json
from datetime import datetime
from flask_socketio import SocketIO


class CustomFormatter(
    logging.Formatter,
):
    """Custom formatter to color-code log messages based on their content."""

    def __init__(self, socketio: SocketIO = None):
        self.socketio = socketio

    # ANSI escape codes for colors - using accessible palette
    COLORS = {
        "RESET": "\033[0m",
        "WHITE": "\033[38;5;231m",  # Default text color
        "BLUE": "\033[38;5;116m",  # User/STT messages
        "GREEN": "\033[38;5;114m",  # Agent speaking/TTS
        "VIOLET": "\033[38;5;183m",  # Function calls
        "YELLOW": "\033[38;5;186m",  # Latency info
    }

    def format(self, record):
        # Default format string
        format_str = "%(asctime)s.%(msecs)03d %(levelname)s: %(message)s"

        # Default to white
        color = self.COLORS["WHITE"]

        msg = str(record.msg).lower()

        # Check for JSON content
        if "server:" in msg and "{" in msg:
            try:
                # Extract the JSON part
                json_str = msg[msg.find("{") : msg.rfind("}") + 1]
                data = json.loads(json_str)

                # User/STT related messages
                if data.get("type") in ["userstartedspeaking", "endofthought"] or (
                    data.get("type") == "conversationtext"
                    and data.get("role") == "user"
                ):
                    color = self.COLORS["BLUE"]

                # Agent speaking/TTS related messages
                elif data.get("type") in ["agentstartedspeaking", "agentaudiodone"] or (
                    data.get("type") == "conversationtext"
                    and data.get("role") == "assistant"
                ):
                    color = self.COLORS["GREEN"]

                # Agent thinking/function calling
                elif data.get("type") in ["functioncalling", "functioncallrequest"]:
                    color = self.COLORS["VIOLET"]

            except (json.JSONDecodeError, KeyError):
                pass

        # Non-JSON messages
        else:
            if any(
                phrase in msg
                for phrase in ["function response", "parameters", "function call"]
            ):
                color = self.COLORS["VIOLET"]
            elif "injectagentmessage" in msg:
                color = self.COLORS["GREEN"]
            elif any(
                phrase in msg
                for phrase in ["decision latency", "function execution latency"]
            ):
                color = self.COLORS["YELLOW"]

        # Apply the color to the format string
        formatter = logging.Formatter(
            color + format_str + self.COLORS["RESET"], datefmt="%H:%M:%S"
        )
        formatted_message = formatter.format(record)
        # Emit the log message to the client with timestamp
        if self.socketio:
            try:
                self.socketio.emit(
                    "log_message",
                    {
                        "message": formatted_message,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
            except Exception as e:
                print(f"Error emitting log message: {e}")

        return formatted_message
