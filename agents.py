

# importing the required libraries
import os

from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI

from tools import web_search, scarape_url

from dotenv import load_dotenv
load_dotenv()

#   ChatGroq(model="openai/gpt-oss-20b", reasoning_effort="low")
# agent_llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)
# agent_llm = ChatGroq(model="meta-llama/llama-prompt-guard-2-22m", temperature=0)

# agent_llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0
# )

agent_llm = ChatMistralAI(
    model="mistral-small-latest",
    temperature=0
)


chain_llm = ChatGroq(
    # model=os.getenv("WRITER_MODEL", "llama-3.3-70b-versatile"),
    # model="openai/gpt-oss-120b",
    model="openai/gpt-oss-20b",

    temperature=0.3,
)


# 1 agent
def create_search_agent():
    return create_agent(
        model=agent_llm,
        tools=[web_search],
        system_prompt="""You are a research agent.

Your job is to research the user's question with the web search tool.

Rules:
- Call the search tool at most 2 times, then stop searching.
- Prefer recent and reliable sources.
- Do not invent facts.
- Finish with a short list of key findings, each followed by its source URL.""",
    )


# 2 agent
def create_scrap_agent():
    return create_agent(
        model=agent_llm,
        tools=[scarape_url],
        system_prompt="""You are a web scraping agent.

Pick the single most relevant URL from the text you are given and read it with
the scraping tool.

Rules:
- Call the scraping tool exactly once.
- Do not invent information that is not on the page.
- Finish with: important facts, key points, relevant details, and the source URL.""",
    )


# 3 writer chain: turns the collected research into the final report
writter_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert research report writer.

You are given research that has already been collected. Write the report using
ONLY that material. Do not call any tools, do not browse the web, and do not
add facts that are not in the research. If something is unclear or missing,
say so.

Write in clean Markdown."""
    ),
    (
        "human",
        """Write a clear, well-structured research report.

Topic: {topic}

Research material:
{research}

Use this structure:
# <Report title>
## Summary
2-4 sentences.
## Key findings
Bullet points with the most important facts.
## Recent developments
What is new or changing.
## Analysis
What the findings mean, and any limits or uncertainty.
## Sources
A list of the source titles and URLs used.

Be factual, specific and concise."""
    ),
])

writter_chain = writter_prompt | chain_llm | StrOutputParser()


# 4 critic chain
critic_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an expert research report critic.

Review the report written by another AI. Do not call any tools and do not
browse the web. Judge only what is in the report.

Check for:
- Factual accuracy
- Relevance to the topic
- Missing important information
- Unsupported or fabricated claims
- Logical consistency
- Quality of sources and URLs
- Clarity and structure

Do not rewrite the report. Point out the problems and give clear suggestions.
If the report is accurate and complete, say that it passes the review."""
    ),
    (
        "human",
        """Critically review the following research report.

Generated Report:
{report}

Use this structure:

1. Overall Assessment
2. Factual Issues
3. Missing Information
4. Unsupported Claims
5. Source/URL Issues
6. Structure and Clarity Issues
7. Specific Improvements
8. Final Verdict

Start the response with a line in exactly this form: Score: X/10

Final Verdict must be one of: PASS, NEEDS IMPROVEMENT, REJECT.

Be objective, factual and concise."""
    ),
])

critic_chain = critic_prompt | chain_llm | StrOutputParser()