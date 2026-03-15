from backend.app import UnifiedMemoryService

if __name__ == '__main__':
    
    PORT = 5001  # Changed from 5000 (macOS uses 5000 for AirPlay)
    unified_memory_service = UnifiedMemoryService()
    unified_memory_service.app.run(host='localhost', port=PORT, debug=True)