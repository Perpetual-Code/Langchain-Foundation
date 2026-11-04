import copy
import os
import random
from enum import Enum
from typing import Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

# ---------------------------------------------------------------------------
# INFO Useful if a * is used instead of named imports
# ---------------------------------------------------------------------------
__all__ = [
    "INVOKE_OPTIONS",
    "Models",
    "Trace",
    "get_invoke_options",
    "invoke_options",
]

# ---------------------------------------------------------------------------
# INFO INVOKE Options for Nvidia models only
# ---------------------------------------------------------------------------
INVOKE_OPTIONS: dict[str, Any] = {
    "seed": random.randint(10, 100),
    "chat_template_kwargs": {"enable_thinking": True},
}

invoke_options = INVOKE_OPTIONS


def get_invoke_options() -> dict[str, Any]:
    return copy.deepcopy(INVOKE_OPTIONS)


# ---------------------------------------------------------------------------
# INFO Helpers
# ---------------------------------------------------------------------------
def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(
            f"{name} is not set. Add it to your .env file "
            f"or export it before creating that model/client."
        )
    return value


# ---------------------------------------------------------------------------
# INFO Tracing With LangSmith
# ---------------------------------------------------------------------------


class Trace:
    def __init__(self) -> None:
        os.environ["LANGSMITH_TRACING"] = "true"
        # os.environ["LANGSMITH_API_KEY"] = cast(str, os.getenv("LANGSMITH_API_KEY"))
        _require_env("LANGSMITH_API_KEY")
        os.environ["LANGSMITH_PROJECT"] = "langchain-tutorial"


# ---------------------------------------------------------------------------
# INFO Available models
# ---------------------------------------------------------------------------


class ModelName(str, Enum):
    NEMOTRON_ULTRA_3_550b = "nvidia/nemotron-3-ultra-550b-a55b"
    NEMOTRON_3_5_BOLT_E4B = "nvidia/nemotron-3.5-bolt-e4b"
    NEMOTRON_3_5_SUPER_VL_120b_a12b = "nvidia/nemotron-3.5-super-vl-120b-a12b"
    META_MUSE = "meta/muse-glimmer-30b"
    GOOGLE_GEMMA_4_31b = "google/gemma-4-31b-it"
    MINIMAX_M3_1_FLASH = "minimaxai/minimax-m3.1-flash"
    MISTRALAI_MISTRAL_LARGE_4 = "mistralai/mistral-large-4-1t-a52b"
    STEPFUN__STEP_5 = "stepfun-ai/step-5-preview"


#   "nvidia/nemotron-3-ultra-550b-a55b",
#     "nvidia/nemotron-3.5-bolt-e4b",
#     "nvidia/nemotron-3.5-super-vl-120b-a12b",
#     "meta/muse-glimmer-30b",
#     "google/gemma-4-31b-it",
#     "minimaxai/minimax-m3.1-flash",
#     "mistralai/mistral-large-4-1t-a52b",
#     "stepfun-ai/step-5-preview",
#     "deepseek-ai/deepseek-v4.1-flash",  # NOTE Use openAI to create instance
#     "z-ai/glm-5.3-flash",  # NOTE Use openAI to create instance


# ---------------------------------------------------------------------------
# INFO Chat models
# ---------------------------------------------------------------------------
class Models:
    def __init__(self) -> None:
        # os.environ["GROQ_API_KEY"] = cast(str, os.getenv("GROQ_API_KEY"))
        # os.environ["NVIDIA_API_KEY"] = cast(str, os.getenv("NVIDIA_API_KEY"))
        pass

    def create_groq_model(self) -> ChatGroq:
        _require_env("GROQ_API_KEY")
        return ChatGroq(model="openai/gpt-oss-120b")

    def create_nvidia_model(
        self,
        model_name: str,
        temperature: int = 1,
        top_p: int = 1,
        max_completion_tokens: int = 1024,
    ) -> ChatNVIDIA:
        print(f"Creating model {model_name}")
        _require_env("NVIDIA_API_KEY")
        return ChatNVIDIA(
            # model="nvidia/nemotron-3-ultra-550b-a55b",
            # model="minimaxai/minimax-m3.1-flash",
            model=model_name,
            temperature=temperature,
            top_p=top_p,
            max_completion_tokens=max_completion_tokens,
        )
