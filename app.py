from flask import Flask,send_from_directory 
from flask_socketio import SocketIO
from src.config import Config
from src.routes import routes

# failed to download CTLT

# Create a custom static folder handler
def static_folder_handler(app):
    @app.route('/vendor/<path:filename>')
    def vendor_static(filename):
        return send_from_directory('static/vendor', filename)

    @app.route('/css/<path:filename>')
    def css_static(filename):
        return send_from_directory('static/css', filename)

    @app.route('/js/<path:filename>')
    def js_static(filename):
        return send_from_directory('static/js', filename)

    @app.route('/image/<path:filename>')
    def image_static(filename):
        return send_from_directory('image', filename)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    socketio = SocketIO(app)
    
    # Register static folder handlers
    static_folder_handler(app)
    # Initialize routes
    routes.init_app(app, socketio)
    
    return app, socketio

app, socketio = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
    #socketio.run(app, debug=True, port=8000)
