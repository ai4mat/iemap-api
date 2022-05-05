import asyncio

messages = []
users = []

queue = asyncio.Queue()


def create_user(username):
    isYetInStore = filter(lambda u: u.username == username, users)
    if not isYetInStore:
        user = {"user_id": len(users) + 1, "username": username}
        users.append(user)
        return {"success": True, "user": user}
