import tiktoken
from tqdm import tqdm
from pypdf import PdfReader
import streamlit as st
from typing import List # <--- Added

# --- Pydantic and LangChain Parser Imports ---
from pydantic import BaseModel, Field
from langchain.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

import highlight.prompts as prompts

# --- Define the Pydantic Model for Approach ---
class ApproachPoints(BaseModel):
    points: List[str] = Field(description="List of 2-3 short bullet points describing the methodological approach using active verbs.")
    # You could add more validation here if needed, e.g., using validators for list length

class ImpactPoints(BaseModel): # <--- New Model
    points: List[str] = Field(description="List of 3 concise bullet points stating key results/outcomes, highlighting profound or surprising findings.")


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
            # Read the content before the indicator on the last page
            content_part, _, _ = page_content.partition(reference_indicator)
            content += content_part
            n_pages += 1 # Count the last page
            break # Stop reading after finding references

        else:
            content += page_content
            n_pages += 1

    # Ensure content after reference_indicator is removed even if not caught by partition
    # (This might be redundant if partition works correctly)
    if reference_indicator in content:
       content = content.split(reference_indicator)[0]


    return {
        "content": content,
        "n_pages": n_pages,
        "n_characters": len(content),
        "n_words": len(content.split()), # Use split() for better word count
        "n_tokens": get_token_count(content)
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
    content = bytes.decode(file_object.read(), 'utf-8')

    return {
        "content": content,
        "n_pages": 1,
        "n_characters": len(content),
        "n_words": len(content.replace("\n", " ").split()),
        "n_tokens": get_token_count(content)
    }


def content_reduction(
    client,
    document_list, # Assuming this is a list of strings or LangChain Documents
    system_scope,
    model,
    package: str = "langchain_azure_openai"
):
    """
    Reduce the input text by removing irrelevant content. (Note: Untested in this context)

    Args:
        client: The LLM client instance.
        document_list (list): A list of documents/text chunks to process.
        system_scope (str): The system scope or context for the prompt.
        model (str): The model to use for content reduction.
        package (str): The client package type.

    Returns:
        str: The content with irrelevant parts removed.
    """

    prompt_template = "Remove irrelevant content from the following text.\n\n{text}\n\nReduced Content:" # Adjusted prompt slightly

    reduced_content = ""
    for i in tqdm(range(len(document_list))):
        # Adapt based on whether document_list contains strings or LangChain Document objects
        page_content = document_list[i] if isinstance(document_list[i], str) else document_list[i].page_content
        page_tokens = get_token_count(page_content, model=model)

        messages = [
            {"role": "system", "content": system_scope},
            {"role": "user", "content": prompt_template.format(text=page_content)}
        ]

        # Estimate max tokens for response - difficult, maybe allow model default?
        # Let's set a reasonable upper bound, e.g., original tokens, but this could truncate.
        max_response_tokens = page_tokens

        try:
            if package == "openai":
                response = client.chat.completions.create(
                    model=model,
                    max_tokens=max_response_tokens,
                    temperature=0.0,
                    messages=messages
                )
                reduced_content += response.choices[0].message.content + "\n\n" # Add separator

            elif package == "langchain_azure_openai":
                response = client.invoke(
                    messages,
                    max_tokens=max_response_tokens,
                    temperature=0.0,
                )
                reduced_content += response.content + "\n\n" # Add separator (Fix: Use +=)
            else:
                raise ValueError(f"Unsupported package: {package}")
        except Exception as e:
             print(f"Warning: Failed to reduce content chunk {i}: {e}") # Add warning
             # Optionally add original content back? Or skip? Let's skip problematic chunks.
             # reduced_content += page_content + "\n\n" # Option to keep original if reduction fails


    return reduced_content.strip()


# --- NEW: Function for Structured Output Generation ---
def generate_structured_content(
    client,
    system_scope,
    user_prompt: str, # The user-facing part of the prompt
    pydantic_parser: PydanticOutputParser,
    max_tokens=500,
    temperature=0.0,
    max_allowable_tokens=150000, # Use the value from session state later
    model="gpt-4o",
    package="langchain_azure_openai"
):
    """
    Generates structured content using the LLM based on a Pydantic model.
    """
    # Create a PromptTemplate that includes the user prompt AND the format instructions
    prompt_template = PromptTemplate(
        template="{format_instructions}\nUser Request:\n{user_prompt}", # Added "User Request:" label
        input_variables=["user_prompt"],
        partial_variables={"format_instructions": pydantic_parser.get_format_instructions()}
    )

    formatted_prompt = prompt_template.format_prompt(user_prompt=user_prompt).to_string()

    # --- Token Check (Approximate) ---
    n_prompt_tokens = get_token_count(formatted_prompt, model=model) + max_tokens
    if n_prompt_tokens > max_allowable_tokens:
         raise RuntimeError(
             f"ERROR: Estimated prompt tokens ({n_prompt_tokens}) exceed max allowable ({max_allowable_tokens}). Reduce input text or parameters."
        )

    # --- LLM Call ---
    messages = [
        {"role": "system", "content": system_scope},
        {"role": "user", "content": formatted_prompt}
    ]

    raw_output = "" # Initialize raw_output
    try:
        if package == "openai":
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
                # response_format={"type": "json_object"} # Uncomment if model/API supports guaranteed JSON mode
            )
            raw_output = response.choices[0].message.content

        elif package == "langchain_azure_openai":
            response = client.invoke(
                messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            raw_output = response.content
        else:
            raise ValueError(f"Unsupported package: {package}")

        # --- Parse the Output ---
        parsed_output = pydantic_parser.parse(raw_output)
        return parsed_output

    except Exception as e:
        # Catch potential parsing errors or API errors
        # Include raw output in the error message for debugging
        error_message = f"Failed to generate or parse structured content: {e}"
        if raw_output:
             error_message += f"\nRaw LLM Output:\n---\n{raw_output}\n---"
        raise RuntimeError(error_message)


# --- Original function for standard text generation ---
def generate_prompt_content(
    client,
    system_scope,
    prompt, # This is the fully formatted user prompt string
    max_tokens=50,
    temperature=0.0,
    max_allowable_tokens=150000, # Use the value from session state later
    model="gpt-4o",
    package="langchain_azure_openai"
):
    """
    Generate simple text content using the OpenAI API based on the provided prompt and parameters.
    """

    n_prompt_tokens = get_token_count(prompt, model=model) + max_tokens # Check full prompt tokens

    if n_prompt_tokens > max_allowable_tokens:
        raise RuntimeError((
            f"ERROR: Input text + prompt tokens ({n_prompt_tokens}) exceed the maximum ",
            f"allowable tokens ({max_allowable_tokens})."
        ))

    messages = [
        {"role": "system", "content": system_scope},
        {"role": "user", "content": prompt}
    ]

    content_result = "" # Initialize
    try:
        if package == "openai":
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )
            content_result = response.choices[0].message.content

        elif package == "langchain_azure_openai":
            response = client.invoke(
                messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            content_result = response.content
        else:
            raise ValueError(f"Unsupported package: {package}")

        return content_result.strip() # Strip whitespace from result

    except Exception as e:
        raise RuntimeError(f"Failed to generate content: {e}")


# --- MODIFIED: Function to format the *user* part of the prompt ---
def generate_prompt(
    content: str, # Renamed from 'client' which wasn't used here
    prompt_name: str,
    additional_content: str = None,
) -> str:
    """
    Formats the user-specific part of the prompt based on the prompt name and content.
    Does NOT include system scope or formatting instructions.

    Args:
        content (str): The main text content from the document.
        prompt_name (str): The key for the desired prompt in prompts.prompt_queue.
        additional_content (str, optional): Extra content needed by some prompts
                                            (e.g., title for subtitle, objective for approach,
                                             figure ID for selected_figure_caption). Defaults to None.

    Returns:
        str: The formatted user prompt string ready for the LLM.

    Raises:
        ValueError: If prompt_name is unknown or required additional_content is missing.
        KeyError: If content formatting fails for the specific prompt.
    """
    try:
        prompt_template_string = prompts.prompt_queue[prompt_name]
    except KeyError:
        raise ValueError(f"Unknown prompt_name: '{prompt_name}'")

    try:
        if prompt_name in ("objective",):
             # Objective prompt expects example texts and main content
             user_prompt_string = prompt_template_string.format(
                prompts.EXAMPLE_TEXT_ONE,
                prompts.EXAMPLE_TEXT_TWO,
                content
             )
        elif prompt_name in ("approach", "subtitle", "selected_figure_caption"):
             # These prompts expect main content and additional_content
             if additional_content is None:
                 raise ValueError(f"additional_content is required for prompt '{prompt_name}'")
             user_prompt_string = prompt_template_string.format(content, additional_content)
        else:
             # Default: Assume prompt expects only main content {0}
             user_prompt_string = prompt_template_string.format(content)

        return user_prompt_string

    except Exception as e: # Catch formatting errors, missing keys etc.
        raise KeyError(f"Error formatting prompt '{prompt_name}': {e}. Check prompt template and arguments.")


# --- Original function for generating content AND handling simple UI display/word count ---
# NOTE: This is kept for the simpler text fields in the Streamlit app.
# It is NOT used for the structured 'approach' and 'impacts' generation.
def generate_content(
    client, # Needs client
    container,
    content,
    prompt_name="title",
    result_title="Title Result:",
    max_tokens=50,
    temperature=0.0,
    box_height=200,
    additional_content=None,
    max_word_count=100, # Used for post-generation check
    min_word_count=75, # Used for post-generation check
    max_allowable_tokens: int = 150000,
    model: str = "gpt-4o",
    package: str = "langchain_azure_openai"
):
    """
    Generates simple text content, displays it in a Streamlit container,
    and performs optional word count reduction.
    """

    try:
        # 1. Format the user prompt string
        user_prompt_string = generate_prompt(
            content=content,
            prompt_name=prompt_name,
            additional_content=additional_content
        )

        # 2. Generate the text content using the standard generation function
        response = generate_prompt_content(
            client=client,
            system_scope=prompts.SYSTEM_SCOPE,
            prompt=user_prompt_string,
            max_tokens=max_tokens,
            temperature=temperature,
            max_allowable_tokens=max_allowable_tokens,
            model=model,
            package=package
        )

        # 3. Optional: Word count reduction (if needed and defined)
        word_count = len(response.split())
        if prompt_name != "reduce_wordcount" and word_count > max_word_count: # Avoid reducing the reducer itself
             st.write(f"Initial word count ({word_count}) > max ({max_word_count}). Attempting reduction...")
             try:
                 # Format the reduction prompt (assuming it exists and takes min, max, text)
                 reduction_user_prompt = generate_prompt(
                    content=response, # Pass the oversized response as content
                    prompt_name="reduce_wordcount",
                    # Use format to pass min/max counts - requires prompt "reduce_wordcount"
                    # in prompt_queue to accept {0}, {1}, {2} or similar.
                    # Let's assume it takes response as {0} and min/max are hardcoded or passed differently.
                    # Revisit reduce_wordcount prompt definition.
                    # Assuming reduce_wordcount prompt is: "Reduce ... {0} words and {1} words. Text: ```{2}```"
                    additional_content=f"{min_word_count} :: {max_word_count}" # Hacky way to pass min/max if needed, adjust prompt
                 )
                 # Reformat reduction prompt based on actual template
                 reduction_user_prompt = prompts.prompt_queue["reduce_wordcount"].format(min_word_count, max_word_count, response)


                 # Call generation again for reduction
                 reduced_response = generate_prompt_content(
                    client=client,
                    system_scope=prompts.SYSTEM_SCOPE, # Use same system scope?
                    prompt=reduction_user_prompt,
                    max_tokens=max_tokens, # Use similar max tokens? Might need adjustment.
                    temperature=temperature, # Use same temperature?
                    max_allowable_tokens=max_allowable_tokens,
                    model=model,
                    package=package
                 )
                 response = reduced_response # Update response with reduced version
                 st.write(f"Reduced word count: {len(response.split())}")
             except Exception as reduction_error:
                 st.warning(f"Word count reduction failed: {reduction_error}. Using original response.")


        # 4. Display in Streamlit container
        container.markdown(result_title)
        container.text_area(
            label=result_title, # For accessibility, even if hidden
            value=response,
            label_visibility="collapsed",
            height=box_height
        )
        st.write(f"Final word count: {len(response.split())}") # Display final count

        return response

    except Exception as e:
         # Display error in the container
         container.error(f"Error generating content for '{prompt_name}': {e}")
         return None # Return None or empty string on error
