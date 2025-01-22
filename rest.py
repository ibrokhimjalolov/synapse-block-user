from twisted.web.resource import Resource
from synapse.module_api import ModuleApi
from twisted.internet import defer
import json
from twisted.web import server
import re
from .helper import BlockHelper


class BlockUserInfoResource(Resource):
    isLeaf = True

    def __init__(self, config, module_api: ModuleApi, helper: BlockHelper):
        self.config = config
        self.module_api = module_api
        self.helper = helper
        super().__init__()

    def render_GET(self, request):
        d = defer.ensureDeferred(self.process_request(request))

        def on_success(response):
            request.setHeader(b"Content-Type", b"application/json")
            request.write(json.dumps(response).encode("utf-8"))
            request.finish()

        def on_error(err):
            request.setHeader(b"Content-Type", b"application/json")
            request.write(json.dumps({
                "status": "error",
                "message": "Internal server error",
            }).encode("utf-8"))
            request.finish()

        d.addCallback(on_success)
        d.addErrback(on_error)
        return server.NOT_DONE_YET

    async def process_request(self, request):
        requester = await self.module_api.get_user_by_req(request)

        full_path = request.path.decode('utf-8')
        match = re.match(
            r"/_synapse/client/v3/block_user/(?P<user_id>[^/]*)/info$",
            full_path
        )
        other_user_id = match.group("user_id")
        user_id = requester.user.to_string()

        return {
            "user_block": await self.helper.is_block(
                blocked_id=other_user_id,
                blocker_id=user_id
            ),
            "am_i_blocked": await self.helper.is_block(
                blocked_id=user_id,
                blocker_id=other_user_id
            )
        }


class BlockedUserListResource(Resource):
    def __init__(self, config, module_api: ModuleApi, helper: BlockHelper):
        self.config = config
        self.module_api = module_api
        self.helper = helper
        super().__init__()

    def render_GET(self, request):
        d = defer.ensureDeferred(self.process_request(request))

        def on_success(response):
            request.setHeader(b"Content-Type", b"application/json")
            request.write(json.dumps(response).encode("utf-8"))
            request.finish()

        def on_error(err):
            request.setHeader(b"Content-Type", b"application/json")
            request.write(json.dumps({
                "status": "error",
                "message": "Internal server error",
            }).encode("utf-8"))
            request.finish()

        d.addCallback(on_success)
        d.addErrback(on_error)
        return server.NOT_DONE_YET

    async def process_request(self, request):
        requester = await self.module_api.get_user_by_req(request)

        blocked_users = await self.module_api._store.get_global_account_data_by_type_for_user(
            requester.user.to_string(),
            "blocked_users"
        )

        if blocked_users and "blocked_users" in blocked_users:
            blocked_users = blocked_users["blocked_users"]
        else:
            return []
        blocked_users = set(blocked_users)
        if requester.user.to_string() in blocked_users:
            blocked_users.remove(requester.user.to_string())
        sql_args = ', '.join([
            f"${i+1}" for i in range(len(blocked_users))
        ])
        query = f"""
            SELECT profiles.displayname, profiles.avatar_url, profiles.full_user_id
            FROM profiles
            WHERE profiles.full_user_id IN ({sql_args})
        """

        # Use a separate list for processed blocked users
        processed_blocked_users = []

        for displayname, avatar_url, full_user_id in await self.module_api._store.db_pool.execute(
                "block_user_list_resource",
                query,
                *blocked_users
        ):
            processed_blocked_users.append({
                "display_name": displayname,
                "avatar_url": avatar_url,
                "user_id": full_user_id,
            })
        return processed_blocked_users


class BlockUserResource(Resource):

    def __init__(self, config, module_api: ModuleApi, helper: BlockHelper):
        self.config = config
        self.module_api = module_api
        self.helper = helper
        super().__init__()

    def getChild(self, path, request):
        full_path = request.path.decode('utf-8')
        if re.match(
            r"/_synapse/client/v3/block_user/(?P<user_id>[^/]*)/info$",
            full_path
        ):
            return BlockUserInfoResource(self.config, self.module_api, self.helper)
        if re.match(
            r"/_synapse/client/v3/block_user/blocked_users",
            full_path
        ):
            return BlockedUserListResource(self.config, self.module_api, self.helper)
        return super().getChild(path, request)
