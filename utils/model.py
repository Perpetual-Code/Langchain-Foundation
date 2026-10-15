import os
from typing import cast

from dotenv import load_dotenv
from langchain_groq import ChatGroq


class Models:
    def __init__(self) -> None:
        load_dotenv()
        os.environ["GROQ_API_KEY"] = cast(str, os.getenv("GROQ_API_KEY"))

    def create_groq_model(self):
        return ChatGroq(model="openai/gpt-oss-120b")
