from synapse.module_api import ModuleApi


class BlockHelper:

    def __init__(self, config, api: ModuleApi):
        self.config = config
        self.api = api

    async def get_blocked_users(self, user_id):
        return await self.api._store.db_pool.simple_select_onecol(
            table="blocked_users",
            keyvalues={"blocker_user_id": user_id},
            retcol="blocked_user_id",
            desc="get_blocked_users",
        )

    async def upsert_blocked_users(self, user_id, blocked_users) -> list:
        previously_blocked_users = set(await self.get_blocked_users(user_id))
        currently_ignored_users = set(blocked_users)

        if user_id in currently_ignored_users:
            # remove self from blocked users
            currently_ignored_users.remove(user_id)

        await self.api._store.db_pool.simple_delete_many(
            table="blocked_users",
            column="blocked_user_id",
            iterable=previously_blocked_users - currently_ignored_users,
            keyvalues={"blocker_user_id": user_id},
            desc="delete_blocked_users",
        )

        await self.api._store.db_pool.simple_insert_many(
            table="blocked_users",
            values=[
                [user_id, user]
                for user in currently_ignored_users - previously_blocked_users
            ],
            keys=["blocker_user_id", "blocked_user_id"],
            desc="insert_blocked_users",
        )

        return [
            list(currently_ignored_users - previously_blocked_users),
            list(previously_blocked_users - currently_ignored_users),
        ]

    async def get_room_member_block_content(self, room_id):
        room_members = await self.api._store.get_users_in_room(room_id)

        content = {}

        for member in room_members:
            content[member] = list()
            for other in room_members:
                if member == other:
                    continue

                if await self.is_block(blocker_id=member, blocked_id=other):
                    content[member].append(other)

        return content

    async def is_block(self, blocked_id, blocker_id) -> bool:
        return bool(await self.api._store.db_pool.simple_select_onecol(
            table="blocked_users",
            keyvalues={
                "blocker_user_id": blocker_id,
                "blocked_user_id": blocked_id,
            },
            retcol="blocked_user_id",
            desc="is_blocked",
        ))
