from flask import Flask, send_from_directory, jsonify, request
import os
from .wiki import Wiki
from flask_cors import cross_origin
from .db import Entity, Source
from slugify import slugify
from flask import g


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
            if path != "" and not os.path.splitext(path)[1]:
                path += '.html'
            if path != "" and os.path.exists(self.app.static_folder + '/' + path):
                return send_from_directory(self.app.static_folder, path)
            else:
                return send_from_directory(self.app.static_folder, 'index.html')

        @self.app.route('/api/index', methods=('GET',))
        @cross_origin()
        def api_index():
            entities = self.wiki.get_all_entities()
            data = {
                'entities': [{
                    'title': ent.title,
                    'desc': ent.desc,
                    'slug': ent.slug,
                    'is_written': ent.is_written
                } for ent in entities]
            }
            return jsonify(data)
        
        @self.app.route('/api/sources', methods=('GET',))
        @cross_origin()
        def api_sources():
            sources = self.wiki.get_all_sources()
            data = {
                'sources': [{
                    'title': src.title,
                    'id': src.id,
                } for src in sources]
            }
            return jsonify(data)
        
        @self.app.route('/api/page', methods=('GET',))
        @cross_origin()
        def api_page():
            entity_slug = request.args.get('slug')
            entity_slug = slugify(entity_slug, max_length=255)
            ent = self.wiki.get_entity_by_slug(entity_slug)
            if not ent: 
                return jsonify({'message': f'Entity with slug {entity_slug} not found'}), 404
            data = {
                'entity': {
                    'title': ent.title,
                    'desc': ent.desc,
                    'slug': ent.slug,
                    'markdown': ent.markdown
                }
            }
            return jsonify(data)
        
        @self.app.route('/api/source', methods=('GET',))
        @cross_origin()
        def api_source():
            source_id = request.args.get('id')
            src = self.wiki.get_source_by_id(id=source_id)
            if not src:
                return jsonify({'message': f'Source with id {source_id} not found'}), 404
            data = {
                'source': {
                    'title': src.title,
                    'id': src.id,
                }
            }
            return jsonify(data)

    def run(self, host='127.0.0.1', port=5000, debug=True):
        # Run the Flask application
        self.app.run(host=host, port=port, debug=debug)
