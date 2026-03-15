#!/usr/bin/env python3
"""Entry point for Unified Memory API server"""

import os
import logging
from dotenv import load_dotenv
from backend.api.api_server import APIServer

def main():

    load_dotenv()
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    PORT = 5001  
    api_server = APIServer()

    logger.info(f"Starting Unified Memory API server on port {PORT}")
    api_server.app.run(host='localhost', port=PORT, debug=True)

if __name__ == '__main__':
    main()
