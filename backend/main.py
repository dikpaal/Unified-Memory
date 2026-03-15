from api.api_server import APIServer

if __name__ == "__main__":
    server = APIServer()
    
    server.app.run(
        host="localhost",
        port=5001,
        debug=True
    )