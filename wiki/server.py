from flask import Flask, send_from_directory, jsonify
import os
from .wiki import Wiki
from flask_cors import cross_origin


class Server():
    def __init__(self, wiki: Wiki):
        self.app = Flask(__name__, static_folder='static')
        self.wiki = wiki
        self.setup_routes()

    def setup_routes(self):
        # Route to serve static files
        @self.app.route('/', defaults={'path': ''})
        @self.app.route('/<path:path>')
        def serve_static_files(path):
            if path != "" and os.path.exists(self.app.static_folder + '/' + path):
                return send_from_directory(self.app.static_folder, path)
            else:
                return send_from_directory(self.app.static_folder, 'index.html')

        @self.app.route('/api/index', methods=('GET',))
        @cross_origin()
        def api_index():
            entities = self.wiki.get_entities()
            data = {
                'entities': [{
                    'title': ent.title,
                    'desc': ent.desc,
                    'slug': ent.slug
                } for ent in entities]
            }
            return jsonify(data)

    def run(self, host='127.0.0.1', port=5000, debug=True):
        # Run the Flask application
        self.app.run(host=host, port=port, debug=debug)
