import tiktoken
from tqdm import tqdm
from pypdf import PdfReader
import streamlit as st

import highlight.prompts as prompts

from pathlib import Path
from typing import Union

try:
    import tomllib
except ImportError:
    import tomli as tomllib


def get_token_count(text, model="gpt-4o"):
    """
    Calculate the number of tokens in the provided text using the specified model for tokenization.

    Args:
        text (str): The text content to be tokenized.
        model (str): The model to use for tokenization. Default is "gpt-4o".

    Returns:
        int: The total number of tokens in the text.
    """

    encoding = tiktoken.encoding_for_model(model)
    encoded_text = encoding.encode(text)
    n_text_tokens = len(encoded_text)

    return n_text_tokens


def read_config(config_file: Union[str, Path]) -> dict:
    """
    Read the configuration file and return its contents as a dictionary.

    Args:
        config_file (str | Path): The path to the configuration file.

    Returns:
        dict: The contents of the configuration file as a dictionary.
    """
    with open(config_file, "rb") as cf:
        config = tomllib.load(cf)
    return config


def read_pdf(file_object: object, reference_indicator: str = "References\n") -> dict:
    """
    Extract text content from a PDF file until a specified reference indicator is encountered.

    Args:
        file_object (object): The PDF file object to read from.
        reference_indicator (str): The string indicating the start of the reference section. Default is "References\n".

    Returns:
        dict: A dictionary containing:
            - content (str): The extracted text content.
            - n_pages (int): The number of pages read.
            - n_characters (int): The number of characters in the extracted content.
            - n_words (int): The number of words in the extracted content.
            - n_tokens (int): The number of tokens in the extracted content.
    """

    content = ""
    n_pages = 0

    # creating a pdf reader object
    reader = PdfReader(file_object)

    for page in reader.pages:

        page_content = page.extract_text()

        if reference_indicator in page_content:
            content += page_content
            break

        else:
            content += page_content

        n_pages += 1

    content = content.split(reference_indicator)[0]

    return {
        "content": content,
        "n_pages": n_pages,
        "n_characters": len(content),
        "n_words": len(content.split(" ")),
        "n_tokens": get_token_count(content),
    }


def read_text(file_object: object) -> dict:
    """
    Read the content of a text file and return its content along with various metadata.

    Args:
        file_object (object): The file object to read from.

    Returns:
        dict: A dictionary containing:
            - content (str): The extracted text content.
            - n_pages (int): The number of pages (always 1 for text files).
            - n_characters (int): The number of characters in the extracted content.
            - n_words (int): The number of words in the extracted content.
            - n_tokens (int): The number of tokens in the extracted content.
    """
    content = bytes.decode(file_object.read(), "utf-8")

    return {
        "content": content,
        "n_pages": 1,
        "n_characters": len(content),
        "n_words": len(content.replace("\n", " ").split()),
        "n_tokens": get_token_count(content),
    }


def content_reduction(client, document_list, system_scope, model):
    """
    Reduce the input text by removing irrelevant content.

    Args:
        client (OpenAI): The OpenAI client instance.
        document_list (list): A list of documents to process.
        system_scope (str): The system scope or context for the prompt.
        model (str): The model to use for content reduction.

    Returns:
        str: The content with irrelevant parts removed.
    """

    prompt = """Remove irrelevant content from the following text.\n\n{text}\n\n}"""

    content = ""
    for i in tqdm(range(len(document_list))):
        page_content = document_list[i].page_content
        page_tokens = get_token_count(page_content)

        messages = [
            ("system", system_scope),
            ("user", prompt.format(text=page_content)),
        ]

        response = client.with_config(
            configurable={"model": model, "max_tokens": page_tokens, "temperature": 0.0}
        ).invoke(messages)

        content += response.content

    return content


def generate_prompt_content(
    client,
    system_scope,
    prompt,
    max_tokens=50,
    temperature=0.0,
    max_allowable_tokens=8192,
    model="gpt-4o",
):
    """
    Generate content using the OpenAI API based on the provided prompt and parameters.

    Args:
        client (OpenAI): The OpenAI client instance.
        system_scope (str): The system scope or context for the prompt.
        prompt (str): The user prompt to generate content from.
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 50.
        temperature (float, optional): The sampling temperature. Defaults to 0.0.
        max_allowable_tokens (int, optional): The maximum allowable tokens for the prompt and response. Defaults to 8192.
        model (str, optional): The model to use for content generation. Defaults to "gpt-4o".

    Returns:
        str: The generated content.

    Raises:
        RuntimeError: If the total number of tokens in the prompt and response exceeds max_allowable_tokens.
    """

    n_prompt_tokens = get_token_count(prompt) + max_tokens

    if n_prompt_tokens > max_allowable_tokens:
        raise RuntimeError(
            (
                f"ERROR:  input text tokens needs to be reduced due to exceeding the maximum ",
                " allowable tokens per prompt by {n_prompt_tokens - max_allowable_tokens} tokens.",
            )
        )

    messages = [
        ("system", system_scope),
        ("user", prompt),
    ]

    response = client.with_config(
        configurable={
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
    ).invoke(messages)

    content = response.content

    return content


def generate_content(
    client,
    container,
    content,
    prompt_name="title",
    result_title="Title Result:",
    max_tokens=50,
    temperature=0.0,
    box_height=200,
    additional_content=None,
    max_word_count=100,
    min_word_count=75,
    max_allowable_tokens: int = 150000,
    model="gpt-4o",
):
    """
    Generate content using the OpenAI API based on the provided parameters and display it in a Streamlit container.

    Args:
        container (streamlit.container): The Streamlit container to display the generated content.
        content (str): The text content to be used for generating the prompt.
        prompt_name (str, optional): The name of the prompt to use. Defaults to "title".
        result_title (str, optional): The title to display above the generated content. Defaults to "Title Result:".
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 50.
        temperature (float, optional): The sampling temperature. Defaults to 0.0.
        box_height (int, optional): The height of the text area box to display the generated content. Defaults to 200.
        additional_content (str, optional): Additional content to include in the prompt. Defaults to None.
        max_word_count (int, optional): The maximum word count for the generated content. Defaults to 100.
        min_word_count (int, optional): The minimum word count for the generated content. Defaults to 75.
        max_allowable_tokens (int, optional): The maximum allowable tokens for the content. Defaults to 150000.
        model (str, optional): The model to use for content generation. Defaults to "gpt-4o".

    Returns:
        str: The generated content.
    """

    response = generate_prompt(
        client,
        content=content,
        prompt_name=prompt_name,
        temperature=temperature,
        max_tokens=max_tokens,
        max_allowable_tokens=max_allowable_tokens,
        additional_content=additional_content,
        model=model,
    )

    container.markdown(result_title)

    word_count = len(response.split())

    if word_count > max_word_count:

        # construct word count reduction prompt
        reduction_prompt = prompts.prompt_queue["reduce_wordcount"].format(
            min_word_count, max_word_count, response
        )

        messages = [
            ("system", prompts.prompt_queue["system"]),
            ("user", reduction_prompt),
        ]

        reduced_response = client.with_config(
            configurable={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        ).invoke(messages)

        response = reduced_response.content

    container.text_area(
        label=result_title,
        value=response,
        label_visibility="collapsed",
        height=box_height,
    )

    st.write(f"Word count:  {len(response.split())}")

    return response


def generate_prompt(
    client,
    content: str,
    prompt_name: str = "title",
    max_tokens: int = 50,
    max_allowable_tokens: int = 150000,
    temperature: float = 0.0,
    additional_content: str = None,
    model: str = "gpt-4",
) -> str:
    """
    Generate a prompt using the provided parameters and the prompt queue.

    Args:
        client: The OpenAI client to use for generating the prompt.
        content (str): The main text content to be used in the prompt.
        prompt_name (str, optional): The name of the prompt to use. Defaults to "title".
        max_tokens (int, optional): The maximum number of tokens to generate. Defaults to 50.
        max_allowable_tokens (int, optional): The maximum allowable tokens for the content. Defaults to 150000.
        temperature (float, optional): The sampling temperature. Defaults to 0.0.
        additional_content (str, optional): Additional content to include in the prompt. Defaults to None.
        model (str, optional): The model to use for content generation. Defaults to "gpt-4".

    Returns:
        str: The generated prompt.
    """

    if prompt_name in ("objective",):
        prompt = prompts.prompt_queue[prompt_name].format(
            prompts.EXAMPLE_TEXT_ONE, prompts.EXAMPLE_TEXT_TWO, content
        )

    elif prompt_name in ("approach",):
        if additional_content is None:
            additional_content = content
        prompt = prompts.prompt_queue[prompt_name].format(content, additional_content)

    elif prompt_name in ("subtitle",):
        if additional_content is None:
            additional_content = content
        prompt = prompts.prompt_queue[prompt_name].format(content, additional_content)

    elif prompt_name in (
        "figure",
        "caption",
        "impact",
        "summary",
        "title",
        "science",
        "ppt_impact",
        "figure_caption",
        "figure_choice",
        "citation",
        "funding",
    ):
        prompt = prompts.prompt_queue[prompt_name].format(content)

    return generate_prompt_content(
        client=client,
        system_scope=prompts.SYSTEM_SCOPE,
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        max_allowable_tokens=max_allowable_tokens,
        model=model,
    )
