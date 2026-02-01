from livekit.agents import function_tool, Agent, RunContext
import typing as t
import logging
from .prompts import SYSTEM_PROMPT
import os
import json
from dotenv import load_dotenv
import aiohttp

import smtplib
from email.mime.text import MIMEText

load_dotenv(".env.local")

logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)

SMTP_HOST = os.environ.get("SMTP_HOST", "sandbox.smtp.mailtrap.io")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 2525))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
DEFAULT_MAIL_SENDER = os.environ.get("DEFAULT_MAIL_SENDER", "")
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

class Assistant(Agent):
    def __init__(self, logger, additional_instructions: str = "") -> None:
        super().__init__(
            instructions=SYSTEM_PROMPT + "\n" + additional_instructions,
        )
        self.logger = logger


    async def on_user_message(self, message: str):

        # Log question
        self.logger.add_question(message)

        if "buy" in message.lower() or "sign up" in message.lower():
            self.logger.trigger_conversion()

        # Simple sentiment heuristic
        if any(word in message.lower() for word in ["great", "awesome", "thanks"]):
            self.logger.set_sentiment("positive")

        if any(word in message.lower() for word in ["bad", "worst", "angry"]):
            self.logger.set_sentiment("negative")


    @function_tool()
    async def log_user_sentiment(
        self,
        context: RunContext,
        sentiment: t.Annotated[t.Literal["positive", "negative", "neutral"], "The sentiment of the user"]
    ) -> str:
        """
        Log the sentiment of the user interactions. 
        Use this tool when the user expresses strong emotion or opinion.
        """
        self.logger.set_sentiment(sentiment)
        return f"Sentiment set to {sentiment}"

    @function_tool()
    async def log_conversion_interest(
        self,
        context: RunContext
    ) -> str:
        """
        Log that the user has shown interest in converting (e.g., buying, signing up, asking for pricing).
        """
        self.logger.trigger_conversion()
        return "Conversion interest logged."    

    @function_tool()
    async def log_key_questions(
        self,
        context: RunContext,
        question: str
    ) -> str:
        """
        Log key questions asked by the user that indicate their interests or concerns.
        Use this tool to record significant questions about features, pricing, or compatibility.
        """
        self.logger.add_question(question)
        return "Question logged."
        
    @function_tool()
    async def add_to_product_waitlist(
        self,
        context: RunContext,
        email: str,
        product_id: str
    ) -> str:
        """
        Add a user's email to the waitlist for a specific product.
        
        Args:
            email: The email address of the user.
            product_id: The ID of the product.
        """
        waitlist_file = os.path.join(os.path.dirname(__file__), "..", "data", "waitlist.json")
        
        try:
            existing_data = []
            if os.path.exists(waitlist_file):
                with open(waitlist_file, "r") as f:
                    try:
                        existing_data = json.load(f)
                        if not isinstance(existing_data, list):
                            existing_data = [existing_data] if existing_data else []
                    except json.JSONDecodeError:
                        pass
            
            entry = {"email": email, "product_id": product_id}
            existing_data.append(entry)
            
            with open(waitlist_file, "w") as f:
                json.dump(existing_data, f, indent=2)
                
            return f"Successfully added {email} to the waitlist for product {product_id}."
        except Exception as e:
            logger.error(f"Failed to add to waitlist: {e}")
            return f"Failed to add to waitlist. Error: {str(e)}"

    @function_tool()
    async def send_mail(
        self,
        context: RunContext,
        recipient: str,
        subject: str,
        body: str 
    ) -> str:
        """
        Send an email to a user with product details or summary.
        
        Args:
            recipient: The email address of the recipient.
            subject: The subject line of the email.
            body: The content of the email.
        """        

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = DEFAULT_MAIL_SENDER
        msg["To"] = recipient

        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(
                    DEFAULT_MAIL_SENDER,
                    [recipient],
                    msg.as_string()
                )
            return "Email sent successfully."
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {e}")
            return f"Failed to send email. Error: {str(e)}"