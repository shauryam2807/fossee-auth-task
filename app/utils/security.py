import bcrypt

def hash_password(plain_text_password):
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_text_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def check_password(plain_text_password, hashed_password):
    return bcrypt.checkpw(
        plain_text_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )
