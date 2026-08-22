"""
Appwrite Seed Script - Phase 2
Creates test users and file records with PROPER document-level permissions.
Each user can only access their OWN files (Row Level Security).
"""
import os
from dotenv import load_dotenv
from appwrite.client import Client
from appwrite.services.users import Users
from appwrite.services.databases import Databases
from appwrite.permission import Permission
from appwrite.role import Role
from appwrite.id import ID

load_dotenv()

# -- Appwrite Client Setup --
client = Client()
client.set_endpoint(os.getenv('APPWRITE_ENDPOINT'))
client.set_project(os.getenv('APPWRITE_PROJECT_ID'))
client.set_key(os.getenv('APPWRITE_API_KEY'))

users_service = Users(client)
databases_service = Databases(client)

DATABASE_ID = os.getenv('APPWRITE_DATABASE_ID')
COLLECTION_ID = os.getenv('APPWRITE_COLLECTION_ID')

# -- Seed Data (same passwords as FOSSEE frontend quick-fill) --
SEED_USERS = [
    {
        "email": "alice@example.com",
        "password": "Password123!",
        "name": "Alice Johnson",
        "files": ["project_report.pdf", "notes.txt"]
    },
    {
        "email": "bob@example.com",
        "password": "Password123!",
        "name": "Bob Smith",
        "files": ["resume.pdf", "photo.jpg", "data.csv"]
    },
    {
        "email": "carol@example.com",
        "password": "Password123!",
        "name": "Carol Williams",
        "files": ["thesis.pdf"]
    }
]

print("Appwrite me seed data dala ja raha hai...")
print("")

for user_data in SEED_USERS:
    try:
        # 1. User create karo Appwrite Auth me
        user = users_service.create(
            user_id=ID.unique(),
            email=user_data['email'],
            password=user_data['password'],
            name=user_data['name']
        )
        user_id = user.id if hasattr(user, 'id') else str(user)
        print(f"[OK] User created: {user_data['email']} (ID: {user_id})")

    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            # User already exists, find their ID
            user_list = users_service.list(search=user_data['email'])
            found_users = user_list.users if hasattr(user_list, 'users') else []
            if found_users:
                user_id = found_users[0].id if hasattr(found_users[0], 'id') else str(found_users[0])
                print(f"[EXISTS] User found: {user_data['email']} (ID: {user_id})")
            else:
                print(f"[ERROR] Could not find user: {user_data['email']}")
                continue
        else:
            print(f"[ERROR] {user_data['email']}: {error_msg}")
            continue

    # 2. Us user ki files Appwrite Database me dalo WITH proper permissions
    # SECURITY: Each document gets permissions ONLY for its owner
    for filename in user_data['files']:
        try:
            doc = databases_service.create_document(
                database_id=DATABASE_ID,
                collection_id=COLLECTION_ID,
                document_id=ID.unique(),
                data={
                    "user_id": user_id,
                    "filename": filename,
                    "file_path": f"/storage/{filename}",
                    "file_size": 1024
                },
                permissions=[
                    Permission.read(Role.user(user_id)),     # Only THIS user can read
                    Permission.update(Role.user(user_id)),   # Only THIS user can update
                    Permission.delete(Role.user(user_id)),   # Only THIS user can delete
                ]
            )
            print(f"     File added: {filename} (secured to user {user_id})")
        except Exception as e:
            print(f"     [WARN] File {filename}: {str(e)}")

print("")
print("Appwrite seed complete!")
print("SECURITY: Each file is locked to its owner via document-level permissions.")
print("Other users cannot even see these files (proper Row Level Security).")
