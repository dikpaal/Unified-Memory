from flask import Flask, request, jsonify
from flask_cors import CORS
from services.memory_service import MemoryService


class APIServer:

    def __init__(self):

        self.app = Flask(__name__)
        CORS(self.app)

        self.memory_service = MemoryService()

        self.register_routes()

    def register_routes(self):

        self.app.add_url_rule(
            "/sync",
            view_func=self.sync,
            methods=["POST"]
        )

        self.app.add_url_rule(
            "/memories",
            view_func=self.get_memories,
            methods=["GET"]
        )

        self.app.add_url_rule(
            "/load",
            view_func=self.load,
            methods=["GET"]
        )

    def sync(self):

        data = request.json
        messages = data.get("messages", [])
        metadata = data.get("metadata", {})

        memories = self.memory_service.sync_memories(
            messages,
            metadata
        )

        return jsonify({
            "success": True,
            "count": len(memories)
        })

    def get_memories(self):

        memories = self.memory_service.get_all_memories()

        return jsonify({
            "success": True,
            "memories": memories
        })

    def load(self):

        platform = request.args.get("platform")

        memories = self.memory_service.load_cross_platform_memories(platform)

        return jsonify({
            "memory_count": len(memories)
        })