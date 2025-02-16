from flask import Flask, send_from_directory, jsonify, request
import os
from .wiki import Wiki
from flask_cors import cross_origin
from .db import Entity
from slugify import slugify


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
            entities = self.wiki.get_entities(order_by=Entity.title)
            data = {
                'entities': [{
                    'title': ent.title,
                    'desc': ent.desc,
                    'slug': ent.slug,
                    'is_written': ent.is_written
                } for ent in entities]
            }
            return jsonify(data)
        
        @self.app.route('/api/page', methods=('GET',))
        @cross_origin()
        def api_page():
            entity_slug = request.args.get('slug')
            entity_slug = slugify(entity_slug, max_length=255)
            entities = self.wiki.get_entities(slug=entity_slug)
            if not len(entities): 
                return jsonify({'message': f'Entity with slug {entity_slug} not found'}), 404
            ent = entities[0]
            data = {
                'entity': {
                    'title': ent.title,
                    'desc': ent.desc,
                    'slug': ent.slug,
                    'markdown': ent.markdown
                }
            }
            return jsonify(data)

    def run(self, host='127.0.0.1', port=5000, debug=True):
        # Run the Flask application
        self.app.run(host=host, port=port, debug=debug)
