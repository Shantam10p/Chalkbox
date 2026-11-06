import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

load_dotenv()


class EssayState(TypedDict):
    topic: str
    draft: str
    essay: str


def create_qwen_model() -> ChatOllama:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:8080/ollama")
    model = os.getenv("OLLAMA_MODEL", "qwen3:32b")
    api_key = os.getenv("QWEN_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    return ChatOllama(
        base_url=base_url,
        model=model,
        temperature=0.7,
        num_predict=int(os.getenv("OLLAMA_NUM_PREDICT", "8192")),
        num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "32768")),
        client_kwargs={"headers": headers} if headers else {},
        sync_client_kwargs={"headers": headers} if headers else {},
    )


def create_essay_workflow():
    llm = create_qwen_model()

    draft_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a concise essay-writing assistant. Write a clear, well-organized essay.",
            ),
            (
                "human",
                "Write an essay of about {word_count} words about: {topic}",
            ),
        ]
    )
    edit_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Polish essays for clarity, flow, grammar, and readability. Preserve the original meaning.",
            ),
            (
                "human",
                "Improve this draft and return only the final essay:\n\n{draft}",
            ),
        ]
    )

    def draft(state: EssayState) -> dict:
        result = draft_prompt | llm | StrOutputParser()
        draft_text = result.invoke({"topic": state["topic"], "word_count": 500})
        return {"draft": draft_text}

    def refine(state: EssayState) -> dict:
        result = edit_prompt | llm | StrOutputParser()
        essay = result.invoke({"draft": state["draft"]})
        return {"essay": essay}

    workflow = StateGraph(EssayState)
    workflow.add_node("writer", draft)
    workflow.add_node("editor", refine)
    workflow.add_edge(START, "writer")
    workflow.add_edge("writer", "editor")
    workflow.add_edge("editor", END)
    return workflow.compile()


def write_essay(topic: str) -> str:
    workflow = create_essay_workflow()
    result = workflow.invoke({"topic": topic, "draft": "", "essay": ""})
    return result["essay"]
