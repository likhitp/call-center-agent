from flask import Flask, render_template
from flask_socketio import SocketIO
import pyaudio
import asyncio
import websockets
import os
import json
import threading
import janus
import queue
import sys
import time
from datetime import datetime
from common.agent_functions import FUNCTION_DEFINITIONS, FUNCTION_MAP
import logging
from common.business_logic import MOCK_DATA
from common.log_formatter import CustomFormatter


# Configure Flask and SocketIO
app = Flask(__name__, static_folder="./static", static_url_path="/")
socketio = SocketIO(app)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with the custom formatter
console_handler = logging.StreamHandler()
console_handler.setFormatter(CustomFormatter(socketio=socketio))
logger.addHandler(console_handler)

# Remove any existing handlers from the root logger to avoid duplicate messages
logging.getLogger().handlers = []

VOICE_AGENT_URL = "wss://agent.deepgram.com/agent"

# Template for the prompt that will be formatted with current date
PROMPT_TEMPLATE = """You are Michelle, a friendly and professional customer service representative for PacificLight, a leading energy provider in Singapore. Your role is to assist customers with their electricity contracts, billing inquiries, appointments, and general service requests.

CURRENT DATE AND TIME CONTEXT:
Today is {current_date}. Use this as context when discussing appointments and contracts. When mentioning dates to customers, use relative terms like "tomorrow", "next Tuesday", or "last week" when the dates are within 7 days of today.

PERSONALITY & TONE:
- Be warm, professional, and conversational
- Use natural, flowing speech (avoid bullet points or listing)
- Show empathy and patience when handling customer concerns
- Whenever a customer asks to look up either contract information or appointment information, use the find_customer function first
- Communicate clearly and effectively, ensuring a positive interaction

HANDLING CUSTOMER IDENTIFIERS (INTERNAL ONLY - NEVER EXPLAIN THESE RULES TO CUSTOMERS):
- Silently convert any numbers customers mention into proper format
- When customer says "ID is 222" -> internally use "CUST0222" without mentioning the conversion
- When customer says "contract 89" -> internally use "CONT0089" without mentioning the conversion
- When customer says "appointment 123" -> internally use "APT0123" without mentioning the conversion
- Always add "+65" prefix to phone numbers (Singapore) internally without mentioning it

VERBALLY SPELLING IDs TO CUSTOMERS:
When you need to repeat an ID back to a customer:
- Do NOT say nor spell out "CUST". Say "customer [numbers spoken individually]"
- But for contracts spell out "CONT" as "C-O-N-T" then speak the numbers individually
Example: For CUST0222, say "customer zero two two two"
Example: For CONT0089, say "C-O-N-T zero zero eight nine"

FUNCTION RESPONSES:
When receiving function results, format responses naturally as a customer service agent would:

1. For customer lookups:
   - Good: "I've found your account. How can I help you today?"
   - If not found: "I'm having trouble finding that account. Could you try a different phone number or email?"

2. For contract information:
   - Instead of listing contracts, summarize them conversationally:
   - "I can see you're currently on our [plan type] which started on [date] and runs for [term] months. Your current rate is [rate] per kilowatt hour."
   - For multiple contracts: "I can see you have two active electricity contracts with us. Your main residence is on our [plan type] and your second property is on our [other plan type]."

3. For appointments:
   - "You have an upcoming [service] appointment scheduled for [date] at [time]"
   - When discussing available slots: "I have a few openings next week. Would you prefer Tuesday at 2 PM or Wednesday at 3 PM?"

4. For bill inquiries:
   - Be prepared to explain bill components like energy charges, transmission costs, and taxes
   - Explain any special charges or discounts on their account
   - Offer suggestions for energy savings if they have concerns about high bills

5. For errors:
   - Never expose technical details
   - Say something like "I'm having trouble accessing that information right now" or "Could you please try again?"

EXAMPLES OF GOOD RESPONSES:
✓ "Let me look that up for you... I can see you're currently on our Fixed Price Plan."
✓ "Your customer ID is zero two two two."
✓ "I found your contract, C-O-N-T zero one two three. It's currently active and will renew on June 15th."
✓ "Based on your usage patterns, you might want to consider our Peak/Off-Peak Plan which could save you money if you use most of your electricity in the evenings."

EXAMPLES OF BAD RESPONSES (AVOID):
✗ "I'll convert your ID to the proper format CUST0222"
✗ "Let me add the +65 prefix to your phone number"
✗ "The system requires IDs to be in a specific format"

ENERGY-SPECIFIC KNOWLEDGE:
- Understand different electricity plans (Fixed Price, Discount Off Tariff, Peak/Off-Peak, Green Energy)
- Be familiar with contract terms (typically 6, 12, 24, or 36 months)
- Be able to explain how billing works and what affects a customer's bill
- Adhere to regulatory standards and company policies
- Know basic energy-saving tips to suggest to customers

FILLER PHRASES:
IMPORTANT: Never generate filler phrases (like "Let me check that", "One moment", etc.) directly in your responses.
Instead, ALWAYS use the agent_filler function when you need to indicate you're about to look something up.

Examples of what NOT to do:
- Responding with "Let me look that up for you..." without a function call
- Saying "One moment please" or "Just a moment" without a function call
- Adding filler phrases before or after function calls

Correct pattern to follow:
1. When you need to look up information:
   - First call agent_filler with message_type="lookup"
   - Immediately follow with the relevant lookup function (find_customer, get_contracts, etc.)
2. Only speak again after you have the actual information to share

Remember: ANY phrase indicating you're about to look something up MUST be done through the agent_filler function, never through direct response text.
"""
VOICE = "aura-asteria-en"

USER_AUDIO_SAMPLE_RATE = 48000
USER_AUDIO_SECS_PER_CHUNK = 0.05
USER_AUDIO_SAMPLES_PER_CHUNK = round(USER_AUDIO_SAMPLE_RATE * USER_AUDIO_SECS_PER_CHUNK)

AGENT_AUDIO_SAMPLE_RATE = 16000
AGENT_AUDIO_BYTES_PER_SEC = 2 * AGENT_AUDIO_SAMPLE_RATE

SETTINGS = {
    "type": "SettingsConfiguration",
    "audio": {
        "input": {
            "encoding": "linear16",
            "sample_rate": USER_AUDIO_SAMPLE_RATE,
        },
        "output": {
            "encoding": "linear16",
            "sample_rate": AGENT_AUDIO_SAMPLE_RATE,
            "container": "none",
        },
    },
    "agent": {
        "listen": {"model": "nova-2"},
        "think": {
            "provider": {"type": "open_ai"},
            "model": "gpt-4o-mini",
            "instructions": PROMPT_TEMPLATE,
            "functions": FUNCTION_DEFINITIONS,
        },
        "speak": {"model": VOICE},
    },
    "context": {
        "messages": [
            {
                "role": "assistant",
                "content": "Hello! I'm Michelle from PacificLight customer service. How can I help you with your energy needs today?",
            }
        ],
        "replay": True,
    },
}


class VoiceAgent:
    def __init__(self):
        self.mic_audio_queue = asyncio.Queue()
        self.speaker = None
        self.ws = None
        self.is_running = False
        self.loop = None
        self.audio = None
        self.stream = None
        self.input_device_id = None
        self.output_device_id = None

    def set_loop(self, loop):
        self.loop = loop

    async def setup(self):
        dg_api_key = os.environ.get("DEEPGRAM_API_KEY")
        if dg_api_key is None:
            logger.error("DEEPGRAM_API_KEY env var not present")
            return False

        # Format the prompt with the current date
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        formatted_prompt = PROMPT_TEMPLATE.format(current_date=current_date)

        # Update the settings with the formatted prompt
        settings = SETTINGS.copy()
        settings["agent"]["think"]["instructions"] = formatted_prompt

        try:
            self.ws = await websockets.connect(
                VOICE_AGENT_URL,
                extra_headers={"Authorization": f"Token {dg_api_key}"},
            )
            await self.ws.send(json.dumps(settings))
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {e}")
            return False

    def audio_callback(self, input_data, frame_count, time_info, status_flag):
        if self.is_running and self.loop and not self.loop.is_closed():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self.mic_audio_queue.put(input_data), self.loop
                )
                future.result(timeout=1)  # Add timeout to prevent blocking
            except Exception as e:
                logger.error(f"Error in audio callback: {e}")
        return (input_data, pyaudio.paContinue)

    async def start_microphone(self):
        try:
            self.audio = pyaudio.PyAudio()

            # List available input devices
            info = self.audio.get_host_api_info_by_index(0)
            numdevices = info.get("deviceCount")
            input_device_index = None

            for i in range(0, numdevices):
                device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
                if device_info.get("maxInputChannels") > 0:
                    logger.info(f"Input Device {i}: {device_info.get('name')}")
                    # Use selected device if available
                    if (
                        self.input_device_id
                        and str(device_info.get("deviceId")) == self.input_device_id
                    ):
                        input_device_index = i
                        break
                    # Otherwise use first available device
                    elif input_device_index is None:
                        input_device_index = i

            if input_device_index is None:
                raise Exception("No input device found")

            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=USER_AUDIO_SAMPLE_RATE,
                input=True,
                input_device_index=input_device_index,
                frames_per_buffer=USER_AUDIO_SAMPLES_PER_CHUNK,
                stream_callback=self.audio_callback,
            )
            self.stream.start_stream()
            logger.info("Microphone started successfully")
            return self.stream, self.audio
        except Exception as e:
            logger.error(f"Error starting microphone: {e}")
            if self.audio:
                self.audio.terminate()
            raise

    def cleanup(self):
        """Clean up audio resources"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error closing audio stream: {e}")

        if self.audio:
            try:
                self.audio.terminate()
            except Exception as e:
                logger.error(f"Error terminating audio: {e}")

    async def sender(self):
        try:
            while self.is_running:
                data = await self.mic_audio_queue.get()
                if self.ws and data:
                    await self.ws.send(data)
        except Exception as e:
            logger.error(f"Error in sender: {e}")

    async def receiver(self):
        try:
            self.speaker = Speaker()
            last_user_message = None
            last_function_response_time = None
            in_function_chain = False

            with self.speaker:
                async for message in self.ws:
                    if isinstance(message, str):
                        logger.info(f"Server: {message}")
                        message_json = json.loads(message)
                        message_type = message_json.get("type")
                        current_time = time.time()

                        if message_type == "UserStartedSpeaking":
                            self.speaker.stop()
                        elif message_type == "ConversationText":
                            if message_json.get("role") == "assistant":
                                # Add a natural pause before assistant speaks
                                await asyncio.sleep(1.5)
                            
                            # Emit the conversation text to the client
                            socketio.emit("conversation_update", message_json)

                            if message_json.get("role") == "user":
                                last_user_message = current_time
                                in_function_chain = False
                            elif message_json.get("role") == "assistant":
                                in_function_chain = False

                        elif message_type == "FunctionCalling":
                            if in_function_chain and last_function_response_time:
                                latency = current_time - last_function_response_time
                                logger.info(f"LLM Decision Latency (chain): {latency:.3f}s")
                            elif last_user_message:
                                latency = current_time - last_user_message
                                logger.info(f"LLM Decision Latency (initial): {latency:.3f}s")
                                in_function_chain = True

                        elif message_type == "FunctionCallRequest":
                            # Add a small delay before processing functions
                            await asyncio.sleep(0.5)
                            
                            function_name = message_json.get("function_name")
                            function_call_id = message_json.get("function_call_id")
                            parameters = message_json.get("input", {})

                            logger.info(f"Function call received: {function_name}")
                            logger.info(f"Parameters: {parameters}")

                            start_time = time.time()
                            try:
                                func = FUNCTION_MAP.get(function_name)
                                if not func:
                                    raise ValueError(f"Function {function_name} not found")

                                # Special handling for functions that need websocket
                                if function_name in ["agent_filler", "end_call"]:
                                    result = await func(self.ws, parameters)

                                    if function_name == "agent_filler":
                                        # Extract messages
                                        inject_message = result["inject_message"]
                                        function_response = result["function_response"]

                                        # First send the function response
                                        response = {
                                            "type": "FunctionCallResponse",
                                            "function_call_id": function_call_id,
                                            "output": json.dumps(function_response),
                                        }
                                        await self.ws.send(json.dumps(response))
                                        logger.info(f"Function response sent: {json.dumps(function_response)}")

                                        # Update the last function response time
                                        last_function_response_time = time.time()
                                        # Then just inject the message and continue
                                        await inject_agent_message(self.ws, inject_message)
                                        continue

                                    elif function_name == "end_call":
                                        # Extract messages
                                        inject_message = result["inject_message"]
                                        function_response = result["function_response"]
                                        close_message = result["close_message"]

                                        # First send the function response
                                        response = {
                                            "type": "FunctionCallResponse",
                                            "function_call_id": function_call_id,
                                            "output": json.dumps(function_response),
                                        }
                                        await self.ws.send(json.dumps(response))
                                        logger.info(f"Function response sent: {json.dumps(function_response)}")

                                        # Update the last function response time
                                        last_function_response_time = time.time()

                                        # Then wait for farewell sequence to complete
                                        await wait_for_farewell_completion(self.ws, self.speaker, inject_message)

                                        # Finally send the close message and exit
                                        logger.info(f"Sending ws close message")
                                        await close_websocket_with_timeout(self.ws)
                                        self.is_running = False
                                        break
                                else:
                                    result = await func(parameters)

                                execution_time = time.time() - start_time
                                logger.info(f"Function Execution Latency: {execution_time:.3f}s")

                                # Send the response back
                                response = {
                                    "type": "FunctionCallResponse",
                                    "function_call_id": function_call_id,
                                    "output": json.dumps(result),
                                }
                                await self.ws.send(json.dumps(response))
                                logger.info(f"Function response sent: {json.dumps(result)}")

                                # Update the last function response time
                                last_function_response_time = time.time()

                            except Exception as e:
                                logger.error(f"Error executing function: {str(e)}")
                                result = {"error": str(e)}
                                response = {
                                    "type": "FunctionCallResponse",
                                    "function_call_id": function_call_id,
                                    "output": json.dumps(result),
                                }
                                await self.ws.send(json.dumps(response))

                        elif message_type == "Welcome":
                            logger.info(f"Connected with session ID: {message_json.get('session_id')}")
                        elif message_type == "CloseConnection":
                            logger.info("Closing connection...")
                            await self.ws.close()
                            break

                    elif isinstance(message, bytes):
                        await self.speaker.play(message)

        except Exception as e:
            logger.error(f"Error in receiver: {e}")

    async def run(self):
        if not await self.setup():
            return

        self.is_running = True
        try:
            stream, audio = await self.start_microphone()
            await asyncio.gather(
                self.sender(),
                self.receiver(),
            )
        except Exception as e:
            logger.error(f"Error in run: {e}")
        finally:
            self.is_running = False
            self.cleanup()
            if self.ws:
                await self.ws.close()


class Speaker:
    def __init__(self):
        self._queue = None
        self._stream = None
        self._thread = None
        self._stop = None

    def __enter__(self):
        audio = pyaudio.PyAudio()
        self._stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=AGENT_AUDIO_SAMPLE_RATE,
            input=False,
            output=True,
        )
        self._queue = janus.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=_play, args=(self._queue, self._stream, self._stop), daemon=True
        )
        self._thread.start()

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop.set()
        self._thread.join()
        self._stream.close()
        self._stream = None
        self._queue = None
        self._thread = None
        self._stop = None

    async def play(self, data):
        return await self._queue.async_q.put(data)

    def stop(self):
        if self._queue and self._queue.async_q:
            while not self._queue.async_q.empty():
                try:
                    self._queue.async_q.get_nowait()
                except janus.QueueEmpty:
                    break


def _play(audio_out, stream, stop):
    while not stop.is_set():
        try:
            data = audio_out.sync_q.get(True, 0.05)
            stream.write(data)
        except queue.Empty:
            pass


async def inject_agent_message(ws, inject_message):
    """Simple helper to inject an agent message."""
    logger.info(f"Sending InjectAgentMessage: {json.dumps(inject_message)}")
    await ws.send(json.dumps(inject_message))


async def close_websocket_with_timeout(ws, timeout=5):
    """Close websocket with timeout to avoid hanging if no close frame is received."""
    try:
        await asyncio.wait_for(ws.close(), timeout=timeout)
    except Exception as e:
        logger.error(f"Error during websocket closure: {e}")


async def wait_for_farewell_completion(ws, speaker, inject_message):
    """Wait for the farewell message to be spoken completely by the agent."""
    # Send the farewell message
    await inject_agent_message(ws, inject_message)

    # First wait for either AgentStartedSpeaking or matching ConversationText
    speaking_started = False
    while not speaking_started:
        message = await ws.recv()
        if isinstance(message, bytes):
            await speaker.play(message)
            continue

        try:
            message_json = json.loads(message)
            logger.info(f"Server: {message}")
            if message_json.get("type") == "AgentStartedSpeaking" or (
                message_json.get("type") == "ConversationText"
                and message_json.get("role") == "assistant"
                and message_json.get("content") == inject_message["message"]
            ):
                speaking_started = True
        except json.JSONDecodeError:
            continue

    # Then wait for AgentAudioDone
    audio_done = False
    while not audio_done:
        message = await ws.recv()
        if isinstance(message, bytes):
            await speaker.play(message)
            continue

        try:
            message_json = json.loads(message)
            logger.info(f"Server: {message}")
            if message_json.get("type") == "AgentAudioDone":
                audio_done = True
        except json.JSONDecodeError:
            continue

    # Give audio time to play completely
    await asyncio.sleep(3.5)


# Flask routes
@app.route("/")
def index():
    # Get the sample data from MOCK_DATA
    sample_data = MOCK_DATA.get("sample_data", [])
    return render_template("index.html", sample_data=sample_data)


voice_agent = None


def run_async_voice_agent():
    try:
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Set the loop in the voice agent
        voice_agent.set_loop(loop)

        try:
            # Run the voice agent
            loop.run_until_complete(voice_agent.run())
        except asyncio.CancelledError:
            logger.info("Voice agent task was cancelled")
        except Exception as e:
            logger.error(f"Error in voice agent thread: {e}")
        finally:
            # Clean up the loop
            try:
                # Cancel all running tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()

                # Allow cancelled tasks to complete
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )

                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                loop.close()
    except Exception as e:
        logger.error(f"Error in voice agent thread setup: {e}")


@socketio.on("start_voice_agent")
def handle_start_voice_agent(data=None):
    global voice_agent
    if voice_agent is None:
        voice_agent = VoiceAgent()
        if data:
            voice_agent.input_device_id = data.get("inputDeviceId")
            voice_agent.output_device_id = data.get("outputDeviceId")
        # Start the voice agent in a background thread
        socketio.start_background_task(target=run_async_voice_agent)


@socketio.on("stop_voice_agent")
def handle_stop_voice_agent():
    global voice_agent
    if voice_agent:
        voice_agent.is_running = False
        if voice_agent.loop and not voice_agent.loop.is_closed():
            try:
                # Cancel all running tasks
                for task in asyncio.all_tasks(voice_agent.loop):
                    task.cancel()
            except Exception as e:
                logger.error(f"Error stopping voice agent: {e}")
        voice_agent = None


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Voice Agent Demo Starting!")
    print("=" * 60)
    print("\n1. Open this link in your browser to start the demo:")
    print("   http://127.0.0.1:5000")
    print("\n2. Click 'Start Voice Agent' when the page loads")
    print("\n3. Speak with the agent using your microphone")
    print("\nPress Ctrl+C to stop the server\n")
    print("=" * 60 + "\n")

    socketio.run(app, debug=True)
