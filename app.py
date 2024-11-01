from flask import Flask, jsonify
from flask_mongoengine import MongoEngine
from config import Config
from api import crud_bp, graph_bp

# Initialize the Flask app and database
app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {
    "host": Config.MONGO_URI
}
db = MongoEngine(app)

# Check the connection by pinging the database within the application context
with app.app_context():
    try:
        db.connection.admin.command('ping')
        print("Connected to MongoDB!")
    except Exception as e:
        print("Failed to connect to MongoDB:", e)

# Register blueprints
app.register_blueprint(crud_bp, url_prefix='/crud')
app.register_blueprint(graph_bp, url_prefix='/graph')

# Root endpoint
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "SERVER IS RUNNING"}), 200

if __name__ == '__main__':
    app.run(debug=True)
