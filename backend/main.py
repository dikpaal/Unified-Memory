from backend.app import UnifiedMemoryService

if __name__ == "__main__":
    server = UnifiedMemoryService()
    
    server.app.run(
        host="localhost",
        port=5001,
        debug=True
    )