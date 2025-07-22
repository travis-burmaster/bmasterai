# Example showing how to create and configure a simple AI agent
# This demonstrates core agent setup and basic interactions

from bmasterai import Agent, AgentConfig
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Create agent configuration
        config = AgentConfig(
            name="SimpleAgent",
            description="A basic agent that can respond to queries",
            model="gpt-3.5-turbo",  # Default language model
            temperature=0.7,         # Controls randomness in responses
            max_tokens=150          # Maximum response length
        )

        # Initialize the agent
        agent = Agent(config)
        
        # Define some basic knowledge/rules for the agent
        await agent.learn([
            "My name is SimpleAgent",
            "I help users with basic tasks",
            "I should be polite and professional"
        ])

        # Example interactions
        queries = [
            "What is your name?",
            "Can you help me with a task?",
            "Tell me about yourself"
        ]

        # Process each query and get responses
        for query in queries:
            try:
                response = await agent.process(query)
                logger.info(f"Query: {query}")
                logger.info(f"Response: {response}\n")
            except Exception as e:
                logger.error(f"Error processing query '{query}': {str(e)}")

        # Example of using agent capabilities
        await agent.add_capability("math", "I can perform basic mathematical calculations")
        
        # Test mathematical capability
        math_query = "What is 15 + 27?"
        try:
            response = await agent.process(math_query)
            logger.info(f"Math Query: {math_query}")
            logger.info(f"Response: {response}")
        except Exception as e:
            logger.error(f"Error processing math query: {str(e)}")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
    except Exception as e:
        logger.error(f"Program terminated with error: {str(e)}")
        raise