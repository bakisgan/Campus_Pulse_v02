from passlib.hash import bcrypt

password = "password1"
hashed_password = bcrypt.hash(password)

print(hashed_password)