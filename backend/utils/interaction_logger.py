import uuid
import json
import os

class InteractionLogger:
    def __init__(self):
        self.data = {
            "session_id": str(uuid.uuid4()),
            "product_id": "",
            "product_name": "",
            "user_sentiment": "",
            "key_questions_asked": [],
            "conversion_triggered": False,
            "follow_up_needed": False
        }

    def add_question(self, question: str):
        self.data["key_questions_asked"].append(question)

    def update_product_info(self, product_id: str, product_name: str):
        self.data["product_id"] = product_id
        self.data["product_name"] = product_name

    def trigger_conversion(self):
        self.data["conversion_triggered"] = True

    def set_sentiment(self, sentiment: str):
        if sentiment in ["positive", "neutral", "negative"]:
            self.data["user_sentiment"] = sentiment

    def finalize(self):
        # follow-up needed if negative or no conversion
        if self.data["user_sentiment"] == "negative":
            self.data["follow_up_needed"] = True

        if not self.data["conversion_triggered"]:
            self.data["follow_up_needed"] = True

    def save(self, filename="data/interaction_log.json"):
        existing_logs = []
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        existing_logs = content
                    elif isinstance(content, dict):
                        existing_logs = [content]
            except (json.JSONDecodeError, ValueError):
                pass
        
        existing_logs.append(self.data)

        with open(filename, "w") as f:
            json.dump(existing_logs, f, indent=2)

        print("Interaction log saved (appended):", filename)
        print(self.data)
