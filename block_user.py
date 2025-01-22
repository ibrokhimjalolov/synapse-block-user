from synapse.module_api import ModuleApi
from .rest import BlockUserResource
from .helper import BlockHelper
from synapse.types import JsonDict, create_requester
from synapse.module_api import EventBase


class BlockUserModule:

    def __init__(self, config, api: ModuleApi):
        self.config = config
        self.api = api
        self.event_creation_handler = self.api._hs.get_event_creation_handler()
        self.helper = BlockHelper(config, api)

        api.register_web_resource(
            "/_synapse/client/v3/block_user",
            BlockUserResource(self.config, self.api, self.helper)
        )

        api.register_account_data_callbacks(
            on_account_data_updated=self.on_account_data_updated
        )

        api.register_spam_checker_callbacks(
            user_may_invite=self.user_may_invite,
            check_event_for_spam=self.check_event_for_spam
        )

    async def on_account_data_updated(self, user_id, room_id, account_data_type, content):
        if account_data_type != "blocked_users":
            return

        inserted_users, removed_users = await self.helper.upsert_blocked_users(user_id, content["blocked_users"])

        for user in set(inserted_users + removed_users):

            for direct_room in await self._get_direct_rooms(user_id, user):
                event_dict: JsonDict = {
                    "type": "m.room.member_block",
                    "content": await self.helper.get_room_member_block_content(direct_room),
                    "state_key": "",
                    "room_id": direct_room,
                    "sender": user_id,
                }

                requester = create_requester(user_id)

                await self.event_creation_handler.create_and_send_nonmember_event(
                    requester, event_dict
                )

    async def _get_direct_rooms(self, user1_id, user2_id) -> list:
        rooms = await self.api._store.get_rooms_for_user(user_id=user1_id)

        direct_rooms = []

        for room_id in rooms:
            room_type = str(await self.api._store.get_room_type(room_id))
            if room_type == "m.private":
                if user2_id in (
                    await self.api._store.get_users_in_room(room_id)
                ):
                    direct_rooms.append(room_id)

        return direct_rooms

    async def user_may_invite(self, inviter: str, invitee: str, room_id: str) -> (bool, str):
        if await self.helper.is_block(blocker_id=invitee, blocked_id=inviter):
            return False, "You are blocked by invitee"

        return True

    async def check_event_for_spam(self, event: EventBase) -> bool:
        room_id = event.room_id
        sender = event.sender
        if str(await self.api._store.get_room_type(room_id)) != "m.private":
            return False
        other_room_member = None
        for member in await self.api._store.get_users_in_room(room_id):
            if member != sender:
                other_room_member = member
                break
        if await self.helper.is_block(blocker_id=other_room_member, blocked_id=sender):
            return True
        return False
