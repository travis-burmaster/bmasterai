# Basic Setup Example for BMasterAI
# This example demonstrates installation and initial configuration

# First, install BMasterAI using pip:
# pip install bmasterai

import bmasterai
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        # Initialize BMasterAI with your API key
        # Get your API key from https://bmasterai.com/dashboard
        api_key = "YOUR_API_KEY"
        bmaster = bmasterai.BMasterAI(api_key=api_key)

        # Configure default settings
        bmaster.configure(
            model="gpt-4",  # Default language model
            temperature=0.7,  # Creativity level (0.0-1.0)
            max_tokens=1000,  # Maximum response length
            cache_dir=Path("./cache"),  # Local cache directory
            timeout=30  # API request timeout in seconds
        )

        # Verify configuration
        config = bmaster.get_config()
        logger.info("BMasterAI configured successfully:")
        logger.info(f"Model: {config.model}")
        logger.info(f"Temperature: {config.temperature}")
        logger.info(f"Max tokens: {config.max_tokens}")
        logger.info(f"Cache directory: {config.cache_dir}")

        # Test connection
        status = bmaster.test_connection()
        if status.ok:
            logger.info("Successfully connected to BMasterAI!")
        else:
            logger.error(f"Connection test failed: {status.error}")

    except bmasterai.AuthenticationError:
        logger.error("Failed to authenticate. Please check your API key.")
    except bmasterai.ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()