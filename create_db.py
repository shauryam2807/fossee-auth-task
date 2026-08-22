from app import create_app, db
from app.models import User, File, BlacklistedToken

app = create_app()

with app.app_context():
    db.create_all()
    print("Mubarak ho! Database tables successfully create ho gayi hain! 🎉")
