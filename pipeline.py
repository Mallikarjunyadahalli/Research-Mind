
from agents import create_search_agent, create_scrap_agent, writter_chain, critic_chain


def run_research_pipeline(topic: str):
    state = {}

    print("\n" + " =" *50)
    print("Search agent is wworking...")
    print("="*50)

    search_agent = create_search_agent()

    search_result = search_agent.invoke({
        "messages" : [("user", f"Find recent, Reliable and detailed infromation about: {topic}")]
    })

    state["search_results"] = search_result['messages'][-1].content

    print("\n search result ", state['search_results'])


    # step 2
    print("\n" + " =" *50)
    print("Reader agent is scraping top resources...")
    print("="*50)

    reader_agent = create_scrap_agent()
    reader_result = reader_agent.invoke({
        "messages" : [("user",
                       
                f"Based on the following search results about '{topic}',"
                f"pick the most relevant URL and scrape it for deeper content. \n\n"
                f"Search result: \n{state['search_results'][:800]}"
                       )]
    })
    state['scraped_content'] = reader_result['messages'][-1].content

    print("\n scraped content \n", state['scraped_content'])

    # step - 3 === writer chain 

    print("\n" + " =" *50)
    print("step - 3 - writting the drafting report...")
    print("="*50)

    reasearch_combined = (
        f"SEARCH RESULTS: \n {state['search_results']} \n\n"
        f"DETAILD SCRAPED CONTENT: \n {state['scraped_content']}"
    )

    state['report'] = writter_chain.invoke({
        "topic" : topic,
        "research" : reasearch_combined
    }
    )


    print("\n Final report ", state['report'])

    # critic report

    print("\n" + " =" *50)
    print("step - 4 - writting is reviewing the report...")
    print("="*50)


    state['feedback'] = critic_chain.invoke({
        "report" : state['report']
    })

    print("\n Critic report ", state['feedback'])


    return state



if __name__ == "__main__":
    topic = input("Enter a research topic: ")
    run_research_pipeline(topic)