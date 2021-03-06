from ariadne import ObjectType, convert_kwargs_to_snake_case

from server.store import users, messages, queue

mutation = ObjectType("Mutation")


@mutation.field("createMessage")
@convert_kwargs_to_snake_case
async def resolve_create_message(obj, info, content, sender_id, recipient_id):
    try:
        message = {
            "content": content,
            "sender_id": sender_id,
            "recipient_id": recipient_id
        }
        messages.append(message)
        await queue.put(message)  # add the message to the queue
        return {"success": True, "message": message}
    except Exception as error:
        return {"success": False, "errors": [str(error)]}


@mutation.field("createUser")
@convert_kwargs_to_snake_case
async def resolve_create_user(obj, info, username):
    try:
        isYetInStore = len(
            list(filter(lambda u: u['username'] == username, users))) > 0
        if not isYetInStore:
            user = {"user_id": len(users) + 1, "username": username}
            users.append(user)
            return {"success": True, "user": user}
        return {"success": False, "errors": ["Username is taken"]}

    except Exception as error:
        return {"success": False, "errors": [str(error)]}
