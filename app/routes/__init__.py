# Import individual blueprint instances from their respective modules
# Assuming you have:
# - app/routes/main.py which defines 'bp' for main routes
# - app/routes/admin.py which defines 'bp' for admin routes (or 'admin_bp')

from .routes import bp as route_bp # Import as main_bp to avoid naming conflicts if multiple 'bp' exist
from .version import bp as version_bp # And assuming you have an admin.py with its own blueprint

# You can define a list of all blueprints to make registration cleaner
# This list will be imported by your main app's create_app() function
ALL_APP_BLUEPRINTS = [
    route_bp,
    version_bp,
]

# Optional: You could also define a function to register them, but
# exposing the list is often simpler when you're just registering them once in create_app.
# def register_blueprints(app):
#     """Registers all blueprints from this package with the given Flask application."""
#     for blueprint in ALL_APP_BLUEPRINTS:
#         app.register_blueprint(blueprint)