# globals
EXAMPLE_TEXT_ONE = """Multisector Dynamics: Advancing the Science of Complex Adaptive Human-Earth Systems.  The field of MultiSector Dynamics (MSD) explores the dynamics and co-evolutionary pathways of human and Earth systems with a focus on critical goods, services, and amenities delivered to people through interdependent sectors. This commentary lays out core definitions and concepts, identifies MSD science questions in the context of the current state of knowledge, and describes ongoing activities to expand capacities for open science, leverage revolutions in data and computing, and grow and diversify the MSD workforce. Central to our vision is the ambition of advancing the next generation of complex adaptive human-Earth systems science to better address interconnected risks, increase resilience, and improve sustainability. This will require convergent research and the integration of ideas and methods from multiple disciplines. Understanding the tradeoffs, synergies, and complexities that exist in coupled human-Earth systems is particularly important in the context of energy transitions and increased future shocks."""
EXAMPLE_TEXT_TWO = """The Role of Regional Connections in Planning for Future Power System Operations Under Climate Extremes.  Identifying the sensitivity of future power systems to climate extremes must consider the concurrent effects of changing climate and evolving power systems. We investigated the sensitivity of a Western U.S. power system to isolated and combined heat and drought when it has low (5%) and moderate (31%) variable renewable energy shares, representing historic and future systems. We used an electricity operational model combined with a model of historically extreme drought (for hydropower and freshwater-reliant thermoelectric generators) over the Western U.S. and a synthetic, regionally extreme heat event in Southern California (for thermoelectric generators and electricity load). We found that the drought has the highest impact on summertime production cost (+10% to +12%), while temperature-based deratings have minimal effect (at most +1%). The Southern California heat wave scenario impacting load increases summertime regional net imports to Southern California by 10–14%, while the drought decreases them by 6–12%. Combined heat and drought conditions have a moderate effect on imports to Southern California (−2%) in the historic system and a stronger effect (+8%) in the future system. Southern California dependence on other regions decreases in the summertime with the moderate increase in variable renewable energy (−34% imports), but hourly peak regional imports are maintained under those infrastructure changes. By combining synthetic and historically driven conditions to test two infrastructures, we consolidate the importance of considering compounded heat wave and drought in planning studies and suggest that region-to-region energy transfers during peak periods are key to optimal operations under climate extremes."""
SYSTEM_SCOPE = """You are a technical science editor.  You are constructing high impact highlight content from recent publications."""

prompt_queue = {
    "system": """You are a technical science editor.  You are constructing high impact highlight content from recent publications.""",

    "title": """
    Generate a title for the text delimited by triple backticks. 
    
    The title should meet the following criteria:
    - No colons are allowed in the output.
    - Should pique the interest of the reader while still being somewhat descriptive.
    - Be understandable to a general audience.
    - Do not use the intro "unraveling" or "unlocking the secrets"
    - Should be only once sentence.
    - Should have a maximum length of 10 words.
    - Return only the title.
    - Do not use words like "revolutionizing" or "unraveling"
    
    The following is an example to use for formatting only.  Do not use it in the response.  \
    The example is delimited by three pound signs.
    ###
    Unraveling the Complex Web of Urban Land Teleconnections
    ###

    The following is the input text delimited by triple backticks.  Do not use colons in the response.
    ```{0}```
    """,

    "subtitle": """
    Generate a subtitle for the text delimited by triple backticks.
    
    The subtitle should meet the following criteria:
    - Strictly do not allow colons in the response text.
    - Be an extension of and related to, but not directly quote, this title delimited by single backticks `{1}`
    - Provide information that will make the audience want to find out more about the research.
    - Do not use more than 155 characters including spaces.
    - Return only the subtitle.
    - Only capitalize the first letter of the starting word in the sentence unless the word is a proper noun.
    - Add a period at the end of the response.
    
    The following is an example to use for formatting only.  Do not use it in the response.  \
    The example is delimited by three pound signs.
    ###
    Exploring the intricate dynamics of urban-rural relationships and their impact on land use change.
    ###

    The following is the input text delimited by triple backticks.  Do not use colons in the response.
    ```{0}```
    """,

    "science": """
    Describe the scientific results for a non-expert, non-scientist audience for the text delimited by triple backticks.
    
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
    - Produce only one paragraph.
    - Return only the description.
    
    Finally, do not exceed 100 words in the response.
    
    ```{0}```
    """,

    "impact": """
    Describe the impact of the research to a non-expert, non-scientist audience for the text delimited by triple backticks.
    
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
    
    Finally, do not exceed 100 words in the response.


    ```{0}```
    """,

    "summary": """
    Generate a summary of the current research represented in the text delimited by triple backticks.
    
    The summary should meet the following criteria:
    - Should relay key findings and value.
    - The summary should be still accessible to the non-specialist but may be more technical if necessary. 
    - Do not mention the names of institutions. 
    - If there is a United States Department of Energy Office of Science user facility involved, such as NERSC, you can mention the user facility. 
    - Should be 1 or 2 paragraphs detailing the research.
    - Use present tense.
    - In general, the description should speak about the research or researchers in first person.
    - Use no more than 200 words.
    - Return only the summary.
    
    Finally, do not exceed 200 words in the response.

    
    ```{0}```
    """,

    "figure": """
    Generate a list of 5 search strings for use in the website that hosts free stock photos  \
    (e.g., https://www.pexels.com/) that would be representative of an aspect of the following research statement \
    delimited by triple backticks.  

    ```{0}```
    """,

    "caption": """
    Generate a caption for a photograph describing an aspect of the research for the text delimited by triple backticks.
    
    The caption should meet the following criteria:
    - The caption should be greater than 200 characters and less than 255 character long.

    ```{0}```
    """,

    "objective": """
    Generate one sentence stating the core purpose of the study.

    The sentence should meet the following criteria:
    - Use active verbs for the start of each point.
    - Use present tense.
    - Do not include methodology related to statistical, technological, and theory based
    - Return only the summary.

    The following are example responses separated by three pound signs from input text.  The example section starts \
    with two pound signs and ends with four pound signs:
    ##
    TEXT: {0}
    RESPONSE: Define key terms and concepts for the field of MultiSector Dynamics and identifies important science questions driving the field forward.
    ###
    TEXT: {1}
    RESPONSE: Understand the effects of temperature and drought extremes on the Western U.S. power grid, while taking into account the increasing penetration of variable renewable energy sources, using a high-resolution operational power system model.
    ####

    Here is the input text delimited by triple backticks:
    ```{2}```
    """,

    "approach": """Clearly and concisely state in 2-3 short points how this work accomplished the stated objective from a methodolgocial perspecive.
    - The objective statement is: {1}
    - Base the points on the main text provided below delimited by triple backticks.
    - Do not restate the objective or include results in the points.
    - Only include methodology including but not limited to: statistical, technological, and theory based approaches.
    - Use a different action verb to start each point than what is used to begin the objective statement.
    - Use active verbs for the start of each point.
    - Use present tense.
    - Ensure the points directly relate to achieving the stated objective.

    ```
    {0}
    ```
    """,

     "ppt_impact": """Clearly and concisely state in 3 bullet points the key results and outcomes from this research based on the text delimited by triple backticks.
    - State what the results indicate.
    - Include results that may be considered profound or surprising.
    - Each point should be 1 concise sentence.
    - Use present tense.
    - Do not start sentences with 'The'.

    ```
    {0}
    ```
    """,

    "reduce_wordcount": """Reduce the current text to be greater than {0} words and less than or equal to {1} words.  \
    The following is the text delimited by triple backquotes:
     
     ```{2}```
    """,

    "figure_caption": """Summarize the key findings of the paper as a figure caption.
    - Limit the response to 25 words.
    
    TEXT: {0}
    RESPONSE:
    """,

    "figure_choice": """What figure from the results of the paper best represents the high impact content that can be easily understood by a non-technical, non-scientifc audience.
    Limit the response to:
    1. The figure name as it is written in the text,
    2. An explanation of why it was chosen,
    3. What the figure is about as a figure caption in less than 50 words. Use the figure name in the caption.  Start this point with the phrase "CAPTION:  "

    TEXT: {0}
    RESPONSE:
    """,

    "citation": """Generate the citation for this publication in Chicago style. 
    Do not use the example directly.  
    
    # Example:
    Hadjimichael, A., J. Yoon, P. Reed, N. Voisin, W. Xu. 2023. “Exploring the Consistency of Water Scarcity Inferences between Large-Scale Hydrologic and Node-Based Water System Model Representations of the Upper Colorado River Basin,” J. Water Resour. Plann. Manage., 149(2): 04022081. DOI: 10.1061/JWRMD5.WRENG-5522

    TEXT: {0}
    RESPONSE:
    """,

    "funding": """Extract the funding statement from the content provided. 
    Only provide the funding statment.  Do not provide header content like **Funding Statement:**.

    TEXT: {0}
    RESPONSE:
    """,

    "figure_list": """
    Scan the text delimited by triple backticks. Identify all **figure references** (e.g., "Figure 1", "Fig. 2a").
    **IMPORTANT: Do NOT include references to Tables (e.g., "Table 1"). Only include items identified explicitly as Figures.**

    For each identified figure:
    1. Extract its identifier (e.g., "Figure 1", "Fig. 2a").
    2. Find the corresponding caption text in the paper for that figure.
    3. Create a very short summary (5-10 words) of what the figure shows based on its caption.
    Return a list where each line contains the figure identifier, followed by ' :: ', followed by the short summary.
    - Do not include figures if you cannot find their caption.
    - Ensure each entry is on a new line.
    - Do not include any other text, introduction, or explanation.

    Example Response (Notice no Tables):
    Figure 1 :: Model simulation results under baseline conditions.
    Figure 2a :: Comparison of observed vs. simulated streamflow.
    Figure 2b :: Spatial map of precipitation anomalies.
    Figure 3 :: Sensitivity analysis of parameter X.

    TEXT:
    ```{0}```

    RESPONSE:
    """,

    "selected_figure_caption": """
    Based on the text delimited by triple backticks, generate a concise caption for the specific figure identified as '{1}'.
    - The caption should explain what the figure shows or represents in the context of the research.
    - Aim for clarity and conciseness, understandable to a non-expert if possible.
    - Limit the response to a single sentence or at most 50 words.
    - Do not include the figure identifier (like '{1}:') at the beginning of the caption.
    - Return only the caption text.

    TEXT:
    ```{0}```

    FIGURE IDENTIFIER: {1}

    RESPONSE:
    """,

}
