from dotenv import load_dotenv

from livekit import agents, rtc
from livekit.agents import AgentServer,AgentSession, Agent, room_io
from livekit.plugins import noise_cancellation, silero, bey
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from utils.tools import Assistant
from utils.interaction_logger import InteractionLogger
import asyncio
import aiohttp

import json
import os

load_dotenv(".env.local")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

server = AgentServer()

async def fetch_product_details(product_id: str):
    print(f"📡 Fetching product details for ID: {product_id}...")
    try:
        url = f"{API_BASE_URL}/product/{product_id}"
        async with aiohttp.ClientSession() as http_session:
            async with http_session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ API Success: {data.get('productName')}")
                    return data
                else:
                    print(f"❌ API Error: Status {resp.status} for URL {url}")
                    text = await resp.text()
                    print(f"❌ API Response: {text}")
    except Exception as e:
        print(f"❌ Exception in fetch_product_details: {e}")
    return None

@server.rtc_session()
async def my_agent(ctx: agents.JobContext):
    session_done = asyncio.Event()
    session = AgentSession(
        stt="assemblyai/universal-streaming:en",
        llm="google/gemini-3-flash",
        tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    avatar = bey.AvatarSession(
    avatar_id=os.environ.get("BEY_AVATAR_ID")
    )

    await avatar.start(session, room=ctx.room)

    interaction_logger = InteractionLogger()

    # State to hold the fetched product context
    fetched_product_info = None
    fetched_user_name = None
    fetched_user_email = None

    async def handle_participant_connected(participant: rtc.RemoteParticipant):
        nonlocal fetched_product_info, fetched_user_name, fetched_user_email
        print("Participant joined:", participant.identity)
        print("Raw metadata:", participant.metadata)

        if participant.metadata:
            try:
                data = json.loads(participant.metadata)
                print("Product query:", data.get("product_query"))
                
                fetched_user_name = data.get("user_name")
                fetched_user_email = data.get("user_email")

                p_id = data.get("product_query")
                if p_id:
                    info = await fetch_product_details(p_id)
                    if info:
                        print(f"✅ Fetched product info: {info.get('productName')}")
                        fetched_product_info = info
                        # Update logger
                        interaction_logger.update_product_info(
                            product_id=info.get("productId"),
                            product_name=info.get("productName")
                        )
            except json.JSONDecodeError:
                print("Basic metadata (failed to parse JSON):", participant.metadata)
        else:
            print("No metadata found on join for", participant.identity)

    def on_participant_connected(participant: rtc.RemoteParticipant):
        asyncio.create_task(handle_participant_connected(participant))

    def on_participant_metadata_changed(participant: rtc.RemoteParticipant, *args):
        # We can reuse the handler logic, technically re-fetching if metadata changes
        asyncio.create_task(handle_participant_connected(participant))

    def on_room_disconnected():
        print("🔌 Room disconnected")
        session_done.set()

    ctx.room.on("participant_connected", on_participant_connected)
    ctx.room.on("participant_metadata_changed", on_participant_metadata_changed)
    ctx.room.on("disconnected", on_room_disconnected)

    print(f"🔌 Connecting to room to fetch metadata...")
    await ctx.connect(auto_subscribe=agents.AutoSubscribe.SUBSCRIBE_ALL)
    print(f"✅ Connected to room: {ctx.room.name}")

    # Check existing participants and wait for data fetch
    print(f"👥 Checking {len(ctx.room.remote_participants)} existing participants")
    for participant in ctx.room.remote_participants.values():
        await handle_participant_connected(participant)

    try: 
        additional_context = ""
        
        # Inject user context
        if fetched_user_name or fetched_user_email:
            additional_context += "\n\nCURRENT USER CONTEXT:\n"
            if fetched_user_name:
                additional_context += f"Name: {fetched_user_name}\n"
            if fetched_user_email:
                additional_context += f"Email: {fetched_user_email}\n"

        # Inject product context into the agent's instructions if available
        if fetched_product_info:
            additional_context += (
                f"\n\nCURRENT PRODUCT CONTEXT:\n"
                f"You are currently presenting the '{fetched_product_info.get('productName')}'.\n"
                f"Description: {fetched_product_info.get('description')}\n"
                f"Price: {fetched_product_info.get('price')} {fetched_product_info.get('currency')}\n"
                f"Details: {json.dumps(fetched_product_info.get('details'))}\n"
            )
        
        assistant = Assistant(logger=interaction_logger, additional_instructions=additional_context)

        await session.start(
            room=ctx.room,
            agent=assistant,
        )

        greeting_instructions = "Greet the user and offer your assistance."
        if fetched_product_info:
            greeting_msg = f"Greet the user"
            if fetched_user_name:
                greeting_msg += f" {fetched_user_name}"
            greeting_msg += f". Acknowledge that they are looking at the {fetched_product_info.get('productName')} and offer to answer questions about it."
            greeting_instructions = greeting_msg

        await session.generate_reply(
            instructions=greeting_instructions
        )

        await session_done.wait()

    finally:
        print("\nSession ended. Generating interaction log...\n")

        # finalize + save JSON
        interaction_logger.finalize()
        interaction_logger.save("data/interaction_log.json")
