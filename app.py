import io
import os
import importlib

from docxtpl import DocxTemplate
from pptx import Presentation
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor 

import streamlit as st
# from openai import OpenAI
from langchain_openai import AzureChatOpenAI, OpenAI

import highlight as hlt
from highlight.utils import ApproachPoints, PydanticOutputParser, ImpactPoints
import highlight.prompts as prompts


if "reduce_document" not in st.session_state:
    st.session_state.reduce_document = False

if "content_dict" not in st.session_state:
    st.session_state.content_dict = {}

if "model" not in st.session_state:
    st.session_state.model = "gpt-4o"

if "package" not in st.session_state:
    st.session_state.package = "langchain_azure_openai"

if "access" not in st.session_state:
    st.session_state.access = False 

# parameters for word document
if "title_response" not in st.session_state:
    st.session_state.title_response = None

if "subtitle_response" not in st.session_state:
    st.session_state.subtitle_response = None

if "photo" not in st.session_state:
    st.session_state.photo = None

if "photo_link" not in st.session_state:
    st.session_state.photo_link = None

if "photo_site_name" not in st.session_state:
    st.session_state.photo_site_name = None

if "image_caption" not in st.session_state:
    st.session_state.image_caption = None

if "science_response" not in st.session_state:
    st.session_state.science_response = None

if "impact_response" not in st.session_state:
    st.session_state.impact_response = None

if "summary_response" not in st.session_state:
    st.session_state.summary_response = None

if "funding" not in st.session_state:
    st.session_state.funding = None

if "citation" not in st.session_state:
    st.session_state.citation = None

if "related_links" not in st.session_state:
    st.session_state.related_links = None

# additional word doc content that is not in the template
if "figure_response" not in st.session_state:
    st.session_state.figure_response = None

if "figure_caption" not in st.session_state:
    st.session_state.figure_caption = None

if "caption_response" not in st.session_state:
    st.session_state.caption_response = None

if "output_file" not in st.session_state:
    st.session_state.output_file = None

# parameters for the ppt slide
if "objective_response" not in st.session_state:
    st.session_state.objective_response = None

if "approach_response" not in st.session_state:
    st.session_state.approach_response = None

if "ppt_impact_response" not in st.session_state:
    st.session_state.ppt_impact_response = None

if "figure_recommendation" not in st.session_state:
    st.session_state.figure_recommendation = None

if "citation" not in st.session_state:
    st.session_state.citation = None

if "search_phrase" not in st.session_state:
    st.session_state.search_phrase = None

if "point_of_contact" not in st.session_state:
    st.session_state.point_of_contact = None

if "project_info" not in st.session_state:
    st.session_state.project_info = {
        os.getenv("IM3_ACCESS", default=None): {
            "key": os.getenv("IM3_AZURE_OPENAI_API_KEY", default=None),
            "endpoint": os.getenv("IM3_AZURE_OPENAI_ENDPOINT", default=None),
            "deployment": "gpt-4o",
            "version": "2024-02-01",
            "project": "IM3"
        },
    }

if "active_project" not in st.session_state:
    st.session_state.active_project = "Other"

if "project_dict" not in st.session_state:
    st.session_state.project_dict = {
        "IM3": "Jennie Rice\nIM3 Principal Investigator\njennie.rice@pnnl.gov",
        "GCIMS": "Marshall Wise\nGCIMS Principal Investigator\nmarshall.wise@pnnl.gov",
        "COMPASS-GLM": "Robert Hetland\nCOMPASS-GLM Principal Investigator\nrobert.hetland@pnnl.gov",
        "ICoM": "Ian Kraucunas\nICoM Principal Investigator\nian.kraucunas@pnnl.gov",
        "Puget Sound": "Ning Sun\nPuget Sound Scoping and Pilot Study Principal Investigator\nning.sun@pnnl.gov",
        "Other": "First and Last Name\nCorresponding Project Name with POC Credentials\nEmail Address",
    }

# Figure selection state
if "figure_list" not in st.session_state:
    st.session_state.figure_list = None # Will hold the list ['Figure 1', 'Fig 2', ...]

if "selected_figure" not in st.session_state:
    st.session_state.selected_figure = None # Will hold the user's choice, e.g., 'Figure 1'

if "selected_figure_caption" not in st.session_state:
    st.session_state.selected_figure_caption = None # Will hold the generated caption for the selected figure


# Force responsive layout for columns also on mobile
st.write(
    """<style>
    [data-testid="column"] {
        width: calc(50% - 1rem);
        flex: 1 1 calc(50% - 1rem);
        min-width: calc(50% - 1rem);
    }
    </style>""",
    unsafe_allow_html=True,
)

st.markdown(
    """<h1 style='text-align: center;'>
        <span style='font-size:40px;'>&#128220;</span>  PAIGE  <span style='font-size:40px;'>&#128220;</span>
    </h1>
    <h3 style='text-align: center;'>The Pnnl AI assistant for GEnerating highlights</h3>
    <h5 style='text-align: center;'>Go from publication to a first draft highlight <i>fast</i>!</h5>
    """,
     unsafe_allow_html=True
)

with st.expander("**How to Use PAIGE**", expanded=False):
    st.markdown((
        "Simply: \n" + 
        "1. Enter in your OpenAI API key or project password \n"
        "2. Load the PDF document of your publication into the app \n" +  
        "3. Generate each part of your document in order \n" + 
        "4. Export the document to your local machine \n" + 
        "5. Repeat to generate the PowerPoint slide as well \n" + 
        "\n :memo: Note: Some parts of this process were left to be manual. " + 
        "These include finding images that are free and open to use from a reliable " + 
        "source and choosing which figure from the paper to use in the PowerPoint slide. " + 
        "But don't worry, PAIGE offers helpers along the way."
    ))

if st.session_state.model in (["gpt-4o"]):
    st.session_state.max_allowable_tokens = 150000

# validate project and access key
if st.session_state.access is False:
    user_input = st.text_input(
        "Enter your API key or project password:", 
        type="password",
    )

    if user_input:
        if user_input in st.session_state.project_info.keys():
            project_info = st.session_state.project_info[user_input]
            st.session_state.active_project = project_info["project"]

            if st.session_state.package == "langchain_azure_openai":

                # setup environment locally
                os.environ["OPENAI_API_TYPE"]="azure"
                os.environ["OPENAI_API_VERSION"]=project_info["version"]
                os.environ["OPENAI_API_BASE"]=project_info["endpoint"]
                os.environ["OPENAI_API_KEY"]=project_info["key"]
                os.environ["OPENAI_CHAT_MODEL"]=project_info["deployment"]

                st.success(f"Hello {st.session_state.active_project} representative!", icon="✅")
                st.session_state.access = True

                st.session_state.client = AzureChatOpenAI(
                    deployment_name=project_info["deployment"],
                    azure_endpoint=project_info["endpoint"]
                )

        else:
            st.error(f"Invalid key or password.  Please provide a valid entry.", icon="🚨")
            st.session_state.access = False
            user_input = False

if st.session_state.access:

    st.markdown("### Upload file to process:")
    uploaded_file = st.file_uploader(
        label="### Select PDF or text file to upload",
        type=["pdf", "txt"],
        help="Select PDF or text file to upload",
    )

    if uploaded_file is not None:

        if uploaded_file.type == "text/plain":
            content_dict = hlt.read_text(uploaded_file)

        elif uploaded_file.type == "application/pdf":
            content_dict = hlt.read_pdf(uploaded_file)

        st.session_state.output_file = uploaded_file.name

        st.code(f"""File specs:\n
        - Number of pages:  {content_dict['n_pages']}
        - Number of characters:  {content_dict['n_characters']}
        - Number of words: {content_dict['n_words']}
        - Number of tokens: {content_dict['n_tokens']}
        """)

        if content_dict['n_tokens'] > st.session_state.max_allowable_tokens:
            msg = f"""
        The number of tokens in your document exceeds the maximum allowable tokens.
        This will cause your queries to fail.
        The queries account for the number of tokens in a prompt + the number of tokens in your document.
        
        Maximum allowable token count: {st.session_state.max_allowable_tokens}
        
        Your documents token count: {content_dict['n_tokens']}
        
        Token deficit: {content_dict['n_tokens'] - st.session_state.max_allowable_tokens}
        """
            st.error(msg, icon="🚨")

            st.session_state.reduce_document = st.radio(
                """Would you like me to attempt to reduce the size of 
            your document by keeping only relevant information? 
            If so, I will give you a file to download with the content 
            so you only have to do this once.
            If you choose to go through with this, it may take a while
            to process, usually on the order of 15 minutes for a 20K token
            document.
            Alternatively, you can copy and paste the contents that you
            know are of interest into a text file and upload that
            instead.
        
            """,
                ("Yes", "No"),
            )

        # word document content
        st.markdown("### Content to fill in Word document template:")

        # title section
        title_container = st.container()
        title_container.markdown("##### Generate title from text content")

        # title criteria
        title_container.markdown("""
        The title should meet the following criteria:
        - No colons are allowed in the output.
        - Should pique the interest of the reader while still being somewhat descriptive.
        - Be understandable to a general audience.
        - Should be only once sentence.
        - Should have a maximum length of 10 words.
        """)

        title_container.markdown("Set desired temperature:")

        # title slider
        title_temperature = title_container.slider(
            "Title Temperature",
            0.0,
            1.0,
            0.2,
            label_visibility="collapsed"
        )

        # build container content
        if title_container.button('Generate Title'):

            st.session_state.title_response = hlt.generate_content(
                client=st.session_state.client,
                container=title_container,
                content=content_dict["content"],
                prompt_name="title",
                result_title="Title Result:",
                max_tokens=50,
                temperature=title_temperature,
                box_height=50,
                max_allowable_tokens=st.session_state.max_allowable_tokens,
                model=st.session_state.model
            )

        else:
            if st.session_state.title_response is not None:
                title_container.markdown("Title Result:")
                title_container.text_area(
                    label="Title Result:",
                    value=st.session_state.title_response,
                    label_visibility="collapsed",
                    height=50
                )

        # subtitle section
        subtitle_container = st.container()
        subtitle_container.markdown("##### Generate subtitle from text content")

        # subtitle criteria
        subtitle_container.markdown("""
        The subtitle should meet the following criteria:
        - Be an extension of and related to, but not directly quote, the title.
        - Provide information that will make the audience want to find out more about the research.
        - Do not use more than 155 characters including spaces.
        """)

        subtitle_container.markdown("Set desired temperature:")

        # subtitle slider
        subtitle_temperature = subtitle_container.slider(
            "Subtitle Temperature",
            0.0,
            1.0,
            0.5,
            label_visibility="collapsed"
        )

        # build container content
        if subtitle_container.button('Generate Subtitle'):

            if st.session_state.title_response is None:
                st.write("Please generate a Title first.  Subtitle generation considers the title response.")
            else:

                st.session_state.subtitle_response = hlt.generate_content(
                    client=st.session_state.client,
                    container=subtitle_container,
                    content=content_dict["content"],
                    prompt_name="subtitle",
                    result_title="Subtitle Result:",
                    max_tokens=100,
                    temperature=subtitle_temperature,
                    box_height=50,
                    additional_content=st.session_state.title_response,
                    max_word_count=100,
                    min_word_count=75,
                    max_allowable_tokens=st.session_state.max_allowable_tokens,
                    model=st.session_state.model
                )

        else:
            if st.session_state.subtitle_response is not None:
                subtitle_container.markdown("Subtitle Result:")
                subtitle_container.text_area(
                    label="Subtitle Result:",
                    value=st.session_state.subtitle_response,
                    label_visibility="collapsed",
                    height=50
                )

        # science section
        science_container = st.container()
        science_container.markdown("##### Generate science summary from text content")

        # science criteria
        science_container.markdown("""
        **GOAL**:  Describe the scientific results for a non-expert, non-scientist audience.
        
        The description should meet the following criteria:
        - Answer what the big challenge in this field of science is that the research addresses.
        - State what the key finding is.
        - Explain the science, not the process.
        - Be understandable to a high school senior or college freshman.
        - Use short sentences and succinct words.
        - Avoid technical terms if possible.  If technical terms are necessary, define them.
        - Provide the necessary context so someone can have a very basic understanding of what you did. 
        - Start with topics that the reader already may know and move on to more complex ideas.
        - Use present tense.
        - In general, the description should speak about the research or researchers in first person.
        - Use a minimum of 75 words and a maximum of 100 words. 
        """)

        science_container.markdown("Set desired temperature:")

        # slider
        science_temperature = science_container.slider(
            "Science Summary Temperature",
            0.0,
            1.0,
            0.3,
            label_visibility="collapsed"
        )

        # build container content
        if science_container.button('Generate Science Summary'):
            st.session_state.science_response = hlt.generate_content(
                client=st.session_state.client,
                container=science_container,
                content=content_dict["content"],
                prompt_name="science",
                result_title="Science Summary Result:",
                max_tokens=200,
                temperature=science_temperature,
                box_height=250,
                max_word_count=100,
                min_word_count=75,
                max_allowable_tokens=st.session_state.max_allowable_tokens,
                model=st.session_state.model
            )

        else:
            if st.session_state.science_response is not None:
                science_container.markdown("Science Summary Result:")
                science_container.text_area(
                    label="Science Summary Result:",
                    value=st.session_state.science_response,
                    label_visibility="collapsed",
                    height=250
                )

        # impact section
        impact_container = st.container()
        impact_container.markdown("##### Generate impact summary from text content")

        impact_container.markdown("""
        **GOAL**: Describe the impact of the research to a non-expert, non-scientist audience.
        
        The description should meet the following criteria:
        - Answer why the findings presented are important, i.e., what problem the research is trying to solve.
        - Answer if the finding is the first of its kind.
        - Answer what was innovative or distinct about the research.
        - Answer what the research enables other scientists in your field to do next.
        - Include other scientific fields potentially impacted. 
        - Be understandable to a high school senior or college freshman. 
        - Use short sentences and succinct words.
        - Avoid technical terms if possible.  If technical terms are necessary, define them.
        - Use present tense.
        - In general, the description should speak about the research or researchers in first person.
        - Use a minimum of 75 words and a maximum of 100 words. 
        """)


        impact_container.markdown("Set desired temperature:")

        # slider
        impact_temperature = impact_container.slider(
            "Impact Summary Temperature",
            0.0,
            1.0,
            0.0,
            label_visibility="collapsed"
        )

        # build container content
        if impact_container.button('Generate Impact Summary'):
            st.session_state.impact_response = hlt.generate_content(
                client=st.session_state.client,
                container=impact_container,
                content=content_dict["content"],
                prompt_name="impact",
                result_title="Impact Summary Result:",
                max_tokens=700,
                temperature=impact_temperature,
                box_height=250,
                max_word_count=100,
                min_word_count=75,
                max_allowable_tokens=st.session_state.max_allowable_tokens,
                model=st.session_state.model
            )

        else:
            if st.session_state.impact_response is not None:
                impact_container.markdown("Impact Summary Result:")
                impact_container.text_area(
                    label="Impact Summary Result:",
                    value=st.session_state.impact_response,
                    label_visibility="collapsed",
                    height=250
                )

        # general summary section
        summary_container = st.container()
        summary_container.markdown("##### Generate general summary from text content")

        summary_container.markdown("""
        **GOAL**: Generate a general summary of the current research.
        
        The summary should meet the following criteria:
        - Should relay key findings and value.
        - The summary should be still accessible to the non-specialist but may be more technical if necessary. 
        - Do not mention the names of institutions. 
        - If there is a United States Department of Energy Office of Science user facility involved, such as NERSC, you can mention the user facility. 
        - Should be 1 or 2 paragraphs detailing the research.
        - Use present tense.
        - In general, the description should speak about the research or researchers in first person.
        - Use no more than 200 words.
        """)

        summary_container.markdown("Set desired temperature:")

        # slider
        summary_temperature = summary_container.slider(
            "General Summary Temperature",
            0.0,
            1.0,
            0.3,
            label_visibility="collapsed"
        )

        # build container content
        if summary_container.button('Generate General Summary'):
            st.session_state.summary_response = hlt.generate_content(
                client=st.session_state.client,
                container=summary_container,
                content=content_dict["content"],
                prompt_name="summary",
                result_title="General Summary Result:",
                max_tokens=700,
                temperature=summary_temperature,
                box_height=400,
                max_word_count=200,
                min_word_count=100,
                max_allowable_tokens=st.session_state.max_allowable_tokens,
                model=st.session_state.model
            )

        else:
            if st.session_state.summary_response is not None:
                summary_container.markdown("General Summary Result:")
                summary_container.text_area(
                    label="General Summary Result:",
                    value=st.session_state.summary_response,
                    label_visibility="collapsed",
                    height=400
                )

        # figure recommendations section
        figure_container = st.container()
        figure_container.markdown("##### Generate figure search string recommendations from the general summary")
        figure_container.markdown("These search strings can be used to find relevant splash images from search engines that host open-licenced images.")

        # slider
        figure_container.markdown("Set desired temperature:")
        figure_temperature = figure_container.slider(
            "Figure Recommendations Temperature",
            0.0,
            1.0,
            0.9,
            label_visibility="collapsed"
        )

        # build container content
        if figure_container.button('Generate Figure Search Strings'):

            if st.session_state.summary_response is None:
                st.write("Please generate a general summary first.")
            else:
                st.session_state.figure_response = hlt.generate_content(
                    client=st.session_state.client,
                    container=figure_container,
                    content=st.session_state.summary_response,
                    prompt_name="figure",
                    result_title="Figure Search String Recommendations Result:",
                    max_tokens=200,
                    temperature=figure_temperature,
                    box_height=200,
                    max_allowable_tokens=st.session_state.max_allowable_tokens,
                    model=st.session_state.model
                )

        else:
            if st.session_state.figure_response is not None:

                figure_container.markdown("Figure Recommendations Result:")
                figure_container.text_area(
                    label="Figure Recommendations Result:",
                    value=st.session_state.figure_response,
                    label_visibility="collapsed",
                    height=200
                )


        figure_summary_container = st.container()
        figure_summary_container.markdown(
            "##### Generate a general figure caption that summarizes the research briefly. This is intended for use with the artisitc photo placed in the Word document."
        )

        # slider
        figure_summary_container.markdown("Set desired temperature:")
        figure_summary_temperature = figure_summary_container.slider(
            "Figure Caption Temperature",
            0.0,
            1.0,
            0.1,
            label_visibility="collapsed"
        )

        # build container content
        if figure_summary_container.button('Generate Figure Caption'):

            if st.session_state.summary_response is None:
                st.write("Please generate a general summary first.")
            else:
                st.session_state.figure_caption = hlt.generate_content(
                    client=st.session_state.client,
                    container=figure_summary_container,
                    content=st.session_state.summary_response,
                    prompt_name="figure_caption",
                    result_title="Figure Caption Result:",
                    max_tokens=300,
                    temperature=figure_summary_temperature,
                    box_height=200,
                    max_allowable_tokens=st.session_state.max_allowable_tokens,
                    model=st.session_state.model
                ).replace('"', "")

        else:
            if st.session_state.figure_caption is not None:
                figure_container.markdown("Figure Caption Result:")
                figure_container.text_area(
                    label="Figure Caption Result:",
                    value=st.session_state.figure_caption,
                    label_visibility="collapsed",
                    height=200
                )

        # citation recommendations section
        citation_container = st.container()
        citation_container.markdown("##### Citation for the paper in Chicago style")
        citation_container.markdown("This will only use what is represented in the publication provided.")

        if citation_container.button('Generate Citation'):
            st.session_state.citation = hlt.generate_content(
                client=st.session_state.client,
                container=citation_container,
                content=content_dict["content"],
                prompt_name="citation",
                result_title="",
                max_tokens=300,
                temperature=0.0,
                box_height=200,
                max_allowable_tokens=st.session_state.max_allowable_tokens,
                model=st.session_state.model
            ).replace('"', "")

        else:
            if st.session_state.citation is not None:
                citation_container.text_area(
                    label="Citation",
                    value=st.session_state.citation,
                    label_visibility="collapsed",
                    height=200
                )

        # funding recommendations section
        funding_container = st.container()
        funding_container.markdown("##### Funding statement from the paper")
        funding_container.markdown((
            "Note:  Some journals house this information in the sidebar of the PDF " + 
            "and add in another similar, but very different, statment in the text. " + 
            "Please ensure you review this statement thouroughly to prevent any errors."
        ))

        if funding_container.button('Generate Funding Statement'):
            st.session_state.funding = hlt.generate_content(
                client=st.session_state.client,
                container=funding_container,
                content=content_dict["content"],
                prompt_name="funding",
                result_title="",
                max_tokens=300,
                temperature=0.0,
                box_height=200,
                max_allowable_tokens=st.session_state.max_allowable_tokens,
                model=st.session_state.model
            ).replace('"', "")

        else:
            if st.session_state.funding is not None:
                funding_container.text_area(
                    label="Funding statement",
                    value=st.session_state.funding,
                    label_visibility="collapsed",
                    height=200
                )

        # point of contact box
        poc_container = st.container()
        poc_container.markdown("##### Point of contact for the research by project")

        # select the POC information from the dropdown
        st.session_state.point_of_contact = st.session_state.project_dict[
            poc_container.selectbox(
            label="Select the project who funded the work:",
            options=[
                st.session_state.active_project,
                "COMPASS-GLM", 
                "GCIMS", 
                "ICoM",
                "IM3",
                "Puget Sound",
                "Other",
            ])
        ]

        
        poc_container.write("What will be written to the document as the point of contact:")
        poc_parts = st.session_state.point_of_contact.split("\n")
        poc_container.success(
            f"""
            {poc_parts[0]}\n
            {poc_parts[1]}\n
            {poc_parts[2]}\n
            """
        )

        export_container = st.container()
        export_container.markdown("##### Export Word document with new content when ready")

        # template parameters
        word_parameters = {
            'title': st.session_state.title_response,
            'subtitle': st.session_state.subtitle_response,
            'photo': st.session_state.photo,
            'photo_link': st.session_state.photo_link,
            'photo_site_name': st.session_state.photo_site_name,
            'image_caption': st.session_state.figure_caption,
            'science': st.session_state.science_response,
            'impact': st.session_state.impact_response,
            'summary': st.session_state.summary_response,
            'funding': st.session_state.funding,
            'citation': st.session_state.citation,
            'related_links': st.session_state.related_links,
            'point_of_contact': st.session_state.point_of_contact,
        }

        # template word document
        word_template_file = importlib.resources.files('highlight.data').joinpath('highlight_template.docx')
        template = DocxTemplate(word_template_file)

        template.render(word_parameters)
        bio = io.BytesIO()
        template.save(bio)
        if template:
            export_container.download_button(
                label="Export Word Document",
                data=bio.getvalue(),
                file_name="modified_template.docx",
                mime="docx"
            )

        # power point slide content
        st.markdown("### Content to fill in PowerPoint template:")

        # objective section
        objective_container = st.container()
        objective_container.markdown("##### Generate objective summary from text content")

        objective_container.markdown("""
        **GOAL**:  Generate one sentence stating the core purpose of the study.
        
        The sentence should meet the following criteria:
        - Use active verbs for the start of each point.
        - Use present tense.
        - Do not include methodology related to statistical, technological, and theory based
        """)

        objective_container.markdown("Set desired temperature:")

        # slider
        objective_temperature = objective_container.slider(
            "Objective Temperature",
            0.0,
            1.0,
            0.3,
            label_visibility="collapsed"
        )

        # build container content
        if objective_container.button('Generate Objective'):
            st.session_state.objective_response = hlt.generate_content(
                client=st.session_state.client,
                container=objective_container,
                content=content_dict["content"],
                prompt_name="objective",
                result_title="Objective Result:",
                max_tokens=300,
                temperature=objective_temperature,
                box_height=250,
                max_allowable_tokens=st.session_state.max_allowable_tokens,
                model=st.session_state.model
            )

        else:
            if st.session_state.objective_response is not None:
                objective_container.markdown("Objective Result:")
                objective_container.text_area(
                    label="Objective Result:",
                    value=st.session_state.objective_response,
                    label_visibility="collapsed",
                    height=250
                )

# -- PPT:  START APPROACH SECTION -->
        # approach section
        approach_container = st.container()
        approach_container.markdown("##### Generate approach summary from text content")

        approach_container.markdown("""
        **GOAL**:  Clearly and concisely state in 2-3 short points how this work accomplished the stated objective from a methodolgocial perspecive.
        - Based off of the objective summary 
        - Only include methodology including but not limited to: statistical, technological, and theory based approaches. 
        - Use a different action verb to start sentences than what is used to begin the objective statement.
        - Use active verbs for the start of each point.  
        - Use present tense.
        """)

        approach_container.markdown("Set desired temperature:")

        # slider
        approach_temperature = approach_container.slider(
            "Approach Temperature",
            0.0,
            1.0,
            0.1,
            label_visibility="collapsed"
        )

        # build container content
        if approach_container.button('Generate Approach'):
            if st.session_state.objective_response is None:
                approach_container.warning("Please generate the Objective first.")
            else:
                with st.spinner("Generating approach points..."):
                    try:
                        # 1. Get the user prompt string
                        user_prompt_for_approach = hlt.generate_prompt(
                            content=content_dict["content"],
                            prompt_name="approach",
                            additional_content=st.session_state.objective_response
                        )

                        # 2. Instantiate the parser
                        parser = PydanticOutputParser(pydantic_object=ApproachPoints)

                        # 3. Call the structured generation function
                        structured_result = hlt.generate_structured_content(
                            client=st.session_state.client,
                            system_scope=prompts.SYSTEM_SCOPE,
                            user_prompt=user_prompt_for_approach,
                            pydantic_parser=parser,
                            max_tokens=300, # Adjust as needed
                            temperature=approach_temperature,
                            max_allowable_tokens=st.session_state.max_allowable_tokens,
                            model=st.session_state.model,
                            package=st.session_state.package
                        )

                        # 4. Store the list of points
                        st.session_state.approach_response = structured_result.points
                        # approach_container.success("Approach points generated!")

                    except Exception as e:
                        st.session_state.approach_response = None
                        # approach_container.error(f"Failed to generate approach: {e}")

         # Display the approach points in an editable text box
        if st.session_state.approach_response is not None: # Check if it exists (could be an empty list)
            approach_container.markdown("Approach Result:")
            response_data = st.session_state.approach_response # Should be a list of strings

            # --- Prepare string value for the text_area ---
            if isinstance(response_data, list):
                # Format the list into a multi-line string with bullets
                # Ensure points don't already start with '-' before adding one
                # Include only non-empty points
                current_text_value = "\n".join([
                    f"{str(point).strip()}" if str(point).strip().startswith("-") else f"- {str(point).strip()}"
                    for point in response_data if str(point).strip()
                ])
            elif isinstance(response_data, str):
                # Fallback if it somehow received a string (shouldn't happen ideally)
                current_text_value = response_data
                # approach_container.warning("Approach data was a string, expected a list. Displaying as is.")
            else:
                # Handle unexpected types
                approach_container.error(f"Cannot display approach result: Unexpected data type {type(response_data)}")
                current_text_value = "" # Default to empty

            # --- Use st.text_area for display and editing ---
            edited_text = approach_container.text_area(
                label="Approach Result (Editable):", # Label for accessibility
                value=current_text_value,
                height=250, # Adjust height as needed
                key="approach_edit_area", # Add a unique key
                label_visibility="collapsed" # Hide label visually
            )

            # --- Update session state with the potentially edited content ---
            # Parse the edited text FROM the text area back into a LIST
            updated_approach_list = [
                line.strip().lstrip('- ') # Remove leading bullet and space
                for line in edited_text.split('\n') if line.strip() # Split lines, ignore empty
            ]

            # Store the updated list back into session state
            # This ensures consistency for PowerPoint generation etc.
            st.session_state.approach_response = updated_approach_list

# <-- PPT:  END APPROACH SECTION --

# -- PPT:  START IMPACT SECTION -->

        # power point impact section
        ppt_impact_container = st.container()
        ppt_impact_container.markdown("##### Generate impact points from text content")

        ppt_impact_container.markdown("""
        **GOAL**:  Clearly and concisely state in 3 points the key results and outcomes from this research. 
        - State what the results indicate.
        - Include results that may be considered profound or surprising.
        - Each point should be 1 concise sentence.
        - Use present tense.
        """
        )

        ppt_impact_container.markdown("Set desired temperature:")

        # slider
        ppt_impact_temperature = ppt_impact_container.slider(
            "Impact Points Temperature",
            0.0,
            1.0,
            0.1,
            label_visibility="collapsed"
        )

        if ppt_impact_container.button('Generate Impact Points'):
            with st.spinner("Generating impact points..."):
                try:
                    # 1. Get the user prompt string
                    user_prompt_for_impact = hlt.generate_prompt(
                        content=content_dict["content"],
                        prompt_name="ppt_impact"
                        # No additional_content needed for ppt_impact
                    )

                    # 2. Instantiate the parser with the new model
                    parser = PydanticOutputParser(pydantic_object=ImpactPoints)

                    # 3. Call the structured generation function
                    structured_result = hlt.generate_structured_content(
                        client=st.session_state.client,
                        system_scope=prompts.SYSTEM_SCOPE,
                        user_prompt=user_prompt_for_impact,
                        pydantic_parser=parser,
                        max_tokens=300, # Adjust as needed
                        temperature=ppt_impact_temperature,
                        max_allowable_tokens=st.session_state.max_allowable_tokens,
                        model=st.session_state.model,
                        package=st.session_state.package
                    )

                    # 4. Store the list of points
                    st.session_state.ppt_impact_response = structured_result.points
                    # ppt_impact_container.success("Impact points generated!")

                except Exception as e:
                    st.session_state.ppt_impact_response = None
                    # ppt_impact_container.error(f"Failed to generate impact points: {e}")


        # --- Updated Display Logic (Editable Text Area) ---
        if st.session_state.ppt_impact_response is not None:
            ppt_impact_container.markdown("Impact Points Result (Editable):")
            response_data = st.session_state.ppt_impact_response # Should be a list

            # Prepare string value for the text_area
            if isinstance(response_data, list):
                current_text_value = "\n".join([
                    f"{str(point).strip()}" if str(point).strip().startswith("-") else f"- {str(point).strip()}"
                    for point in response_data if str(point).strip()
                ])
            elif isinstance(response_data, str): # Fallback
                current_text_value = response_data
                # ppt_impact_container.warning("Impact data was a string, expected a list.")
            else: # Handle unexpected
                ppt_impact_container.error(f"Cannot display impact result: Unexpected data type {type(response_data)}")
                current_text_value = ""

            # Use st.text_area for display and editing
            edited_text = ppt_impact_container.text_area(
                label="Impact Points Result (Editable):",
                value=current_text_value,
                height=250, # Adjust height
                key="ppt_impact_edit_area", # Unique key
                label_visibility="collapsed"
            )

            # Parse the edited text back into a LIST and update session state
            updated_impact_list = [
                line.strip().lstrip('- ')
                for line in edited_text.split('\n') if line.strip()
            ]
            st.session_state.ppt_impact_response = updated_impact_list


# <-- PPT:  END IMPACT SECTION --


        # --- New Figure Selection and Caption Section ---
        st.markdown("##### Select Figure and Generate Caption for PowerPoint:")
        figure_select_container = st.container(border=True) # Use border for visual grouping

        figure_select_container.markdown("##### 1. Extract Figure/Table List from Paper")
        if figure_select_container.button("List Figures/Tables"):
            with st.spinner("Extracting figure list from paper..."):
                try:
                    # Use the lower-level generate_prompt function to get the raw list
                    figure_list_raw = hlt.generate_prompt(
                        client=st.session_state.client,
                        content=content_dict["content"],
                        prompt_name="figure_list",
                        max_tokens=500, # Adjust as needed
                        temperature=0.0, # Low temp for extraction
                        max_allowable_tokens=st.session_state.max_allowable_tokens,
                        model=st.session_state.model,
                        package=st.session_state.package
                    )

                    
                    parsed_figures = {}
                    lines = figure_list_raw.strip().split('\n')
                    for line in lines:
                        # Primary Filter: Skip line if it seems to be a table reference
                        if line.strip().lower().startswith("table"):
                            continue # Skip this line entirely

                        if ' :: ' in line:
                            parts = line.split(' :: ', 1)
                            identifier = parts[0].strip()
                            description = parts[1].strip()

                            # Secondary Filter: Double-check identifier doesn't start with "Table"
                            if identifier and description and not identifier.lower().startswith("table"):
                                parsed_figures[identifier] = description
                            # else: # Optional logging for filtered items
                                # print(f"Filtered out potential table: {identifier}")

                    st.session_state.figure_data = parsed_figures
                    st.session_state.selected_figure_id = None # Reset selection
                    st.session_state.selected_figure_caption = None # Reset caption

                    if not st.session_state.figure_data:
                        # Updated message
                        figure_select_container.warning("Could not extract any figure identifiers with descriptions. Ensure figures are clearly captioned in the PDF.")
                    else:
                        # Updated message
                        figure_select_container.success(f"Found {len(st.session_state.figure_data)} figures with descriptions.")

                except Exception as e:
                    figure_select_container.error(f"Error extracting figure list: {e}")
                    st.session_state.figure_data = None


        if st.session_state.figure_list:
            figure_select_container.markdown("##### 2. Select Figure/Table")
            # Add a 'None' option to allow deselection or represent initial state
            options = ["<Select a Figure/Table>"] + st.session_state.figure_list
            selected = figure_select_container.selectbox(
                "Choose the figure or table you want to use:",
                options=options,
                index=options.index(st.session_state.selected_figure) if st.session_state.selected_figure in options else 0,
                label_visibility="collapsed"
            )

            # Update session state only if a valid selection is made
            if selected != "<Select a Figure/Table>":
                if st.session_state.selected_figure != selected:
                    st.session_state.selected_figure = selected
                    st.session_state.selected_figure_caption = None # Reset caption when selection changes
            else:
                 st.session_state.selected_figure = None # Set back to None if placeholder is chosen


        if st.session_state.selected_figure:
            figure_select_container.markdown(f"##### 3. Generate Caption for {st.session_state.selected_figure}")

            # Caption Temperature Slider
            figure_select_container.markdown("Set desired temperature for caption generation:")
            caption_temperature = figure_select_container.slider(
                "Selected Figure Caption Temperature",
                0.0, 1.0, 0.2, # Default to slightly creative but mostly factual
                key="selected_fig_caption_temp", # Unique key
                label_visibility="collapsed"
            )

            if figure_select_container.button(f"Generate Caption for {st.session_state.selected_figure}"):
                 with st.spinner(f"Generating caption for {st.session_state.selected_figure}..."):
                    try:
                        # Use generate_prompt again for the caption
                         caption_response = hlt.generate_prompt(
                            client=st.session_state.client,
                            content=content_dict["content"],
                            prompt_name="selected_figure_caption",
                            additional_content=st.session_state.selected_figure, # Pass the selected figure ID
                            max_tokens=150, # ~50 words + buffer
                            temperature=caption_temperature,
                            max_allowable_tokens=st.session_state.max_allowable_tokens,
                            model=st.session_state.model,
                            package=st.session_state.package
                         )
                         st.session_state.selected_figure_caption = caption_response.strip()
                         figure_select_container.success("Caption generated!")
                    except Exception as e:
                         figure_select_container.error(f"Error generating caption: {e}")
                         st.session_state.selected_figure_caption = None

        # Display the generated caption if available
        if st.session_state.selected_figure_caption:
             figure_select_container.markdown("##### Generated Caption:")
             figure_select_container.text_area(
                 label="Generated Caption Result:",
                 value=st.session_state.selected_figure_caption,
                 height=100,
                 key="selected_fig_caption_display",
                 label_visibility="collapsed"
             )
        elif st.session_state.selected_figure:
            # Show if figure selected but caption not generated yet
             figure_select_container.info("Click the button above to generate the caption.")


# -- PPT:  START EXPORT -->

        # Add PowerPoint export container at the end
        export_ppt_container = st.container()
        export_ppt_container.markdown("##### Export PowerPoint Presentation with New Content")

        if (st.session_state.title_response is not None and
            st.session_state.objective_response is not None and
            st.session_state.ppt_impact_response is not None and
            st.session_state.approach_response is not None):

            try:
                # Load the PowerPoint template
                ppt_template_file = importlib.resources.files('highlight.data').joinpath('highlight_template.pptx')
                prs = Presentation(ppt_template_file)

                # --- Use the approach list directly ---
                # Ensure approach_response is actually a list
                approach_points = []
                if isinstance(st.session_state.approach_response, list):
                    approach_points = st.session_state.approach_response
                elif st.session_state.approach_response: # Handle case if it's still a string somehow?
                     approach_points = st.session_state.approach_response.split('\n') # Fallback
                else:
                    approach_points = ["Approach not generated."] # Default if missing

                impact_points = [] # Define impact_points similarly
                if isinstance(st.session_state.ppt_impact_response, list): # Assuming ppt_impact is also structured
                    impact_points = st.session_state.ppt_impact_response
                elif st.session_state.ppt_impact_response:
                    impact_points = st.session_state.ppt_impact_response.split('\n')
                else:
                    impact_points = ["Impact points not generated."]

                # Iterate over all slides to find the text boxes labeled "impact_0", "impact_1", "impact_2"
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if shape.has_text_frame:

                            # Add this block to handle the figure caption:
                            if "caption" in shape.text_frame.text:
                                if st.session_state.selected_figure_caption:
                                    shape.text_frame.text = st.session_state.selected_figure_caption
                                    # Adjust font size/style as needed
                                    for paragraph in shape.text_frame.paragraphs:
                                        paragraph.font.size = Pt(10)  # Set font size to 10
                                        paragraph.font.name = 'Arial'  # Set font to Arial
                                        paragraph.font.bold = True  # Set font to bold
                                        paragraph.font.color.rgb = RGBColor(0, 0, 255)  # Set font color to blue
                                        paragraph.alignment = PP_ALIGN.CENTER  # Example alignment
                                else:
                                    # Handle case where caption wasn't generated - maybe leave placeholder or put default text
                                    shape.text_frame.text = "[Figure caption not generated]"

                            # Handle title insertion and maintain font size and bold
                            if "title" in shape.text_frame.text:
                                shape.text_frame.text = st.session_state.title_response

                                # Ensure font size and bold settings are maintained for each paragraph
                                for paragraph in shape.text_frame.paragraphs:
                                    for run in paragraph.runs:
                                        run.font.size = Pt(24)  # Example size, adjust as needed
                                        run.font.bold = True  # Maintain bold
                                        run.alignment = PP_ALIGN.LEFT  # Align title

                            # Handle citation insertion and maintain font size and bold
                            if "citation" in shape.text_frame.text:
                                shape.text_frame.text = st.session_state.citation

                                # Ensure font size and bold settings are maintained for each paragraph
                                for paragraph in shape.text_frame.paragraphs:
                                    for run in paragraph.runs:
                                        run.font.size = Pt(11)  # Example size for citation, adjust as needed
                                        run.font.bold = False  # Citation typically isn't bold
                                        run.alignment = PP_ALIGN.LEFT  # Align citation

                            if shape.text_frame.text == "objective_0":
                                # Set the text of the text box to the objective response
                                shape.text_frame.text = st.session_state.objective_response

                                # Optional: Adjust font size and alignment for the objective
                                for paragraph in shape.text_frame.paragraphs:
                                    paragraph.font.size = Pt(13)  # Set font size
                                    paragraph.alignment = PP_ALIGN.LEFT  # Set alignment

                            # Handle approach bullet points
                            if "approach_0" in shape.text_frame.text:
                                shape.text_frame.clear()
                                # Use the list directly
                                for i, approach_point in enumerate(approach_points[:3]): # Limit to 3 points
                                    p = shape.text_frame.add_paragraph()
                                    # Remove leading hyphens if they exist before adding to PPT
                                    p.text = approach_point.strip().lstrip('- ')
                                    p.level = 0
                                    p.font.size = Pt(13)
                                    p.alignment = PP_ALIGN.LEFT

                            # Handle the impact bullet points
                            # (Consider making ppt_impact structured too for consistency)
                            if "impact_0" in shape.text_frame.text:
                                shape.text_frame.clear()
                                for i, impact_point in enumerate(impact_points[:3]): # Limit to 3
                                    p = shape.text_frame.add_paragraph()
                                    p.text = impact_point.strip().lstrip('- ')
                                    p.level = 0
                                    p.font.size = Pt(13)
                                    p.alignment = PP_ALIGN.LEFT

                # Save the modified presentation to a BytesIO object
                ppt_io = io.BytesIO()
                prs.save(ppt_io)
                ppt_io.seek(0)

                # Provide a download button for the user
                ppt_export_success = export_ppt_container.download_button(
                    label="Export PowerPoint Presentation",
                    data=ppt_io,
                    file_name="modified_highlight_template.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                )

                if ppt_export_success:
                    export_ppt_container.success("PowerPoint presentation generated successfully!", icon="✅")

            except Exception as e:
                export_ppt_container.error(f"An error occurred while generating the PowerPoint: {e}", icon="🚨")

        else:
            export_ppt_container.warning("Please generate the title, objective, impact, and citation responses before exporting.", icon="⚠️")
