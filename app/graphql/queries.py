from datetime import datetime
from ariadne import ObjectType, convert_kwargs_to_snake_case
from server.store import messages, users

query = ObjectType("Query")


@query.field("health")
def resolve_hello(*_):
    return "Reply from IEMAP GraphQL(Ariadne) at " + datetime.utcnow(
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    #  naturaltime(date=datetime.now())


@query.field("messages")
@convert_kwargs_to_snake_case
async def resolve_messages(obj, info, user_id):

    def filter_by_userid(message):
        return message["sender_id"] == user_id or \
               message["recipient_id"] == user_id

    user_messages = filter(filter_by_userid, messages)
    return {"success": True, "messages": user_messages}


@query.field("userId")
@convert_kwargs_to_snake_case
async def resolve_user_id(obj, info, username):
    user = users.get(username)
    if user:
        return user["user_id"]


@query.field("users")
@convert_kwargs_to_snake_case
async def resolve_users(obj, info):
    return users