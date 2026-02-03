import sys
import os
import logging

# Setup path to import core packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'packages/core/src')))

# Configure logging
logging.basicConfig(level=logging.INFO)

from core.agent.tools import media_tool

def test_media():
    query = "mcr i dont love you"
    print(f"Testing media_tool with query: {query}")
    
    # Execute the tool directly
    result = media_tool.execute("play_music", {"query": query}, 1, None)
    
    print("\nResult:")
    print(result)

if __name__ == "__main__":
    test_media()
