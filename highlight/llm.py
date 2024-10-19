from typing import Literal
from langchain_core.runnables import Runnable, ConfigurableField


def get_llm(
    provider: Literal["openai", "ollama", "dartmouth"], max_context_length: int
) -> Runnable:
    """Returns a LangChain Runnable interfacing with the specified provider"""
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model_name="not-specified").configurable_fields(
            model=ConfigurableField(id="model"),
            max_tokens=ConfigurableField(id="max_tokens"),
            temperature=ConfigurableField(id="temperature"),
        )
    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model="not-specified", max_tokens=1
        ).configurable_fields(
            model=ConfigurableField(id="model"),
            max_output_tokens=ConfigurableField(id="max_tokens"),
            temperature=ConfigurableField(id="temperature"),
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI().configurable_fields(
            model_name=ConfigurableField(id="model"),
            max_tokens=ConfigurableField(id="max_tokens"),
            temperature=ConfigurableField(id="temperature"),
        )
    elif provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model="llama3", num_ctx=max_context_length
        ).configurable_fields(
            model=ConfigurableField(id="model"),
            num_predict=ConfigurableField(id="max_tokens"),
            temperature=ConfigurableField(id="temperature"),
        )
    elif provider == "dartmouth":
        from langchain_dartmouth.llms import ChatDartmouth

        return ChatDartmouth().configurable_fields(
            model_name=ConfigurableField(id="model"),
            max_tokens=ConfigurableField(id="max_tokens"),
            temperature=ConfigurableField(id="temperature"),
        )
    else:
        raise ValueError("Invalid provider")


def list_llms(config: dict):
    """List all Large Language Models available in the configuration"""
    llms = []
    for provider, spec in config["llm"].items():
        for model in spec["models"]:
            llms.append(f"{provider}: {model}")
    return llms
