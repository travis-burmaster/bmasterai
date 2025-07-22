# Example showing how to create multiple interacting agents with BMasterAI
# This demonstrates agent-to-agent communication and coordination

import bmasterai
from bmasterai import Agent, AgentSystem
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize the agent system
        system = AgentSystem(
            name="retail_system",
            description="A multi-agent system simulating a retail environment"
        )

        # Create customer service agent
        customer_service = Agent(
            name="customer_service",
            role="Handle customer inquiries and route requests",
            goals=["Provide excellent customer service", 
                  "Route requests to appropriate departments"]
        )

        # Create inventory manager agent
        inventory_manager = Agent(
            name="inventory_manager", 
            role="Track and manage product inventory",
            goals=["Maintain optimal stock levels",
                  "Process inventory requests"]
        )

        # Create sales agent
        sales_agent = Agent(
            name="sales",
            role="Process sales and handle transactions",
            goals=["Complete sales transactions",
                  "Upsell relevant products"]
        )

        # Add agents to the system
        system.add_agent(customer_service)
        system.add_agent(inventory_manager)
        system.add_agent(sales_agent)

        # Configure communication channels
        system.enable_communication(
            from_agent=customer_service,
            to_agent=inventory_manager,
            channel_type="async"
        )
        
        system.enable_communication(
            from_agent=customer_service,
            to_agent=sales_agent,
            channel_type="sync"
        )

        # Simulate customer inquiry workflow
        customer_inquiry = "I'd like to purchase 5 units of product ABC123"
        
        # Customer service agent processes initial request
        response = customer_service.process_message(customer_inquiry)
        
        # Check inventory
        inventory_status = inventory_manager.check_inventory("ABC123", 5)
        
        if inventory_status["available"]:
            # Process sale
            transaction = sales_agent.process_sale({
                "product_id": "ABC123",
                "quantity": 5,
                "customer_inquiry": customer_inquiry
            })
            
            # Update inventory
            inventory_manager.update_inventory("ABC123", -5)
        
        # Monitor system status
        system_status = system.get_status()
        logger.info(f"System Status: {system_status}")

    except bmasterai.AgentError as e:
        logger.error(f"Agent error occurred: {str(e)}")
        raise
    except bmasterai.SystemError as e:
        logger.error(f"System error occurred: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()