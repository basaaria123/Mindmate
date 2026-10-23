import re

from openai.types.chat import ChatCompletionMessageParam

from app.schemas.assistant import AssistantReply, ChatMessage
from app.services.llm_client import create_llm_client, get_model
from app.utils.prompts import load_prompt, render_prompt

# Reasoning models may return their thinking inline; only the answer is shown to the learner.
THINKING = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
MAX_TURNS = 12


def chat_reply(messages: list[ChatMessage], memory: str, think_harder: bool = False) -> AssistantReply:
    """Answer the latest user message with the learner's memory as context.

    Nemotron Nano answers by default; "Think harder" in the chat switches to
    Nemotron Ultra. Only the last MAX_TURNS messages are sent. An empty answer is
    retried once, then rejected.
    """

    if not messages or messages[-1].role != "user":
        raise ValueError("The conversation must end with a user message.")

    client = create_llm_client()
    model = get_model("reasoning" if think_harder else "fast")
    request: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": load_prompt("assistant.system")},
        {"role": "system", "content": render_prompt("assistant", memory=memory)},
    ]
    request += [{"role": m.role, "content": m.content} for m in messages[-MAX_TURNS:]]

    for attempt in range(2):
        response = client.chat.completions.create(model=model, messages=request, temperature=0.3, max_tokens=900)
        text = THINKING.sub("", response.choices[0].message.content or "").strip()
        if text:
            return AssistantReply(reply=text, model=model)
        if attempt == 1:
            raise ValueError("The Assistant returned an empty response after one retry.")

    raise RuntimeError("Unexpected error in the Assistant.")
