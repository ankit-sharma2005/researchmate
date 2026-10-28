from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search,scrap_url
import os
from dotenv import load_dotenv
load_dotenv()
# model setup
llm = ChatOllama(model = 'llama3.2')
# first agent
def build_search_agent():
    return create_agent(model =  llm,tools=[web_search])
# second agent
def build_scraper_agent():
    return create_agent(model = llm,tools = [scrap_url])

# writer chain
writer_prompt = ChatPromptTemplate.from_messages([
    ('system','''you are an expert research writer clear, structured and insightful reports.'''),
    ('user','''write a detailed research report on the topic below.
    Topic : {topic}
    Research gathered : {research}
    {research}
    Structure the report as :
    - introduction
    - key findings(minimum 3 well-explained points)
    - conclusion
    - sources (list all urls found in the research)

    be detailed , factual and professional.'''),

])
writer_chain = writer_prompt |llm|StrOutputParser()

# critic_chain

critic_prompt = ChatPromptTemplate.from_messages([
    ('system','''you are a constructive research critic. be honest and specific.'''),
    ('user','''review the research report below and evaluate it strictly.
    report : {report}
    respond in this exact format:
    score : x/10
    strengths : -...
    -...
    areas to improve :
    -...
    -...
    one line verdict :
    ...''')
])

critic_chain = critic_prompt | llm |StrOutputParser()
revise_prompt = ChatPromptTemplate.from_messages([
    ('system', '''you are an expert research writer who improves reports using feedback.'''),
    ('user', '''improve the report below using the critic feedback.
    Use only the research provided. Do not invent URLs.
    Topic : {topic}
    Research : {research}
    Current report : {report}
    Critic feedback : {feedback}
    Return the full improved report in the same structure.''')
])
revise_chain = revise_prompt | llm | StrOutputParser()
# --- claim verification ---
claims_prompt = ChatPromptTemplate.from_messages([
    ('system', 'you extract factual claims from reports.'),
    ('user', '''List the key factual claims made in the report below.
    One claim per line, maximum 8, no numbering, no extra text.
    Report : {report}''')
])
claims_chain = claims_prompt | llm | StrOutputParser()

verify_prompt = ChatPromptTemplate.from_messages([
    ('system', 'you are a strict fact checker. you only use the evidence given.'),
    ('user', '''Evidence : {evidence}

    Claim : {claim}

    Is the claim clearly supported by the evidence above?
    Answer with exactly one word: SUPPORTED or UNSUPPORTED.''')
])
verify_chain = verify_prompt | llm | StrOutputParser()

# --- multi-perspective ---
perspective_prompt = ChatPromptTemplate.from_messages([
    ('system', 'you are a neutral analyst who compares viewpoints fairly.'),
    ('user', '''Using ONLY the research below, write a short comparison on: {topic}
    Research : {research}

    Use this structure:
    ## Viewpoints
    (group the sources by stance, name the source for each)
    ## Where sources agree
    ## Where sources disagree
    ## What is unclear
    Do not take a side. Do not invent URLs or facts.''')
])
perspective_chain = perspective_prompt | llm | StrOutputParser()