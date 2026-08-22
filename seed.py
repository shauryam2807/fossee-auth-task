from app import create_app, db
from app.models import User, File
from app.utils.security import hash_password

# Passwords match the FOSSEE frontend quick-fill buttons
SEED_USERS = [
    {
        "email": "alice@example.com",
        "password": "Password123!",
        "full_name": "Alice Johnson",
        "files": ["project_report.pdf", "notes.txt"]
    },
    {
        "email": "bob@example.com", 
        "password": "Password123!",
        "full_name": "Bob Smith",
        "files": ["resume.pdf", "photo.jpg", "data.csv"]
    },
    {
        "email": "carol@example.com",
        "password": "Password123!",
        "full_name": "Carol Williams",
        "files": ["thesis.pdf"]
    }
]

app = create_app()

with app.app_context():
    print("Database me seed data (dummy data) daala ja raha hai...")
    
    db.drop_all()
    db.create_all()
    
    for user_data in SEED_USERS:
        hashed_pwd = hash_password(user_data['password'])
        user = User(
            email=user_data['email'],
            password=hashed_pwd,
            full_name=user_data['full_name']
        )
        db.session.add(user)
        db.session.flush() 
        
        for filename in user_data['files']:
            file = File(
                user_id=user.id,
                filename=filename,
                file_path=f"/fake/storage/path/{filename}",
                file_size=1024
            )
            db.session.add(file)
            
    db.session.commit()
    print("✅ Seed data successfully add ho gaya! 3 Users aur unki files ready hain.")
    print("   Login credentials: alice/bob/carol@example.com — Password123!")
