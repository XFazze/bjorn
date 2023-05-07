import lib.general as general


class Database(general.Database):
    def __init__(self, db_path):
        super().__init__(db_path)
        self.create_tables(
            {
                "user": [
                    "user_id",
                    "messages",
                    "commands",
                    "reactions",
                    "vc_time",
                    "vc_joins",
                    "vc_leaves",
                    "vc_time_muted",
                    "vc_time_deafened",
                    "vc_time_streaming"
                ],
                "guild": [
                    "user_id",
                    "guild_id",
                    "messages",
                    "commands"
                ],
                "text_channel": [
                    "user_id",
                    "guild_id",
                    "channel_id",
                    "messages",
                    "commands"
                ],
                "voice_channel": [
                    "user_id",
                    "guild_id",
                    "channel_id",
                    "vc_time",
                    "vc_joins",
                    "vc_leaves",
                    "vc_time_streaming",
                    "vc_time_muted",
                    "vc_time_deafened"
                ],
                "daily_user": [
                    "user_id",
                    "date",
                    "messages",
                    "commands",
                    "reactions",
                    "vc_time",
                    "vc_joins",
                    "vc_leaves",
                    "vc_time_streaming",
                    "vc_time_muted",
                    "vc_time_deafened"
                ],
                "daily_guild": [
                    "user_id",
                    "guild_id",
                    "date",
                    "messages",
                    "commands",
                    "vc_time",
                    "vc_joins",
                    "vc_leaves",
                    "vc_time_streaming",
                    "vc_time_muted",
                    "vc_time_deafened"
                ],
                "daily_text_channel": [
                    "user_id",
                    "guild_id",
                    "channel_id",
                    "date",
                    "messages",
                    "commands"
                ],
                "daily_voice_channel": [
                    "user_id",
                    "guild_id",
                    "channel_id",
                    "date",
                    "vc_time",
                    "vc_joins",
                    "vc_leaves",
                    "vc_time_streaming",
                    "vc_time_muted",
                    "vc_time_deafened"
                ]
            }
        )

    def update_user(self, user_id, messages=0, commands=0, reactions=0, vc_time=0, vc_joins=0, vc_leaves=0, vc_time_muted=0, vc_time_deafened=0, vc_time_streaming=0):
        self.cursor.execute(
            f"""
                UPDATE player SET \
                messages = messages + {messages}, \
                commands = commands + {commands}, \
                reactions = reactions + {reactions}, \
                vc_time = vc_time + {vc_time}, \
                vc_joins = vc_joins + {vc_joins}, \
                vc_leaves = vc_leaves + {vc_leaves}, \
                vc_time_muted = vc_time_muted + {vc_time_muted}, \
                vc_time_deafened = vc_time_deafened + {vc_time_deafened}, \
                vc_time_streaming = vc_time_streaming + {vc_time_streaming} \
                WHERE user_id = {user_id}
            """
        )
        self.connection.commit()

    def update_guild_user(self, user_id, guild_id, messages=0, commands=0):
        self.cursor.execute(
            f"""
                UPDATE guild SET \
                messages = messages + {messages}, \
                commands = commands + {commands} \
                WHERE user_id = {user_id} AND guild_id = {guild_id}
            """
        )
        self.connection.commit()

    def update_text_channel_user(self, user_id, guild_id, channel_id, messages=0, commands=0):
        self.cursor.execute(
            f"""
                UPDATE text_channel SET \
                messages = messages + {messages}, \
                commands = commands + {commands} \
                WHERE user_id = {user_id} AND guild_id = {guild_id} AND channel_id = {channel_id}
            """
        )
        self.connection.commit()

    def update_voice_channel_user(self, user_id, guild_id, channel_id, vc_time=0, vc_joins=0, vc_leaves=0, vc_time_muted=0, vc_time_deafened=0, vc_time_streaming=0):
        self.cursor.execute(
            f"""
                UPDATE voice_channel SET \
                vc_time = vc_time + {vc_time}, \
                vc_joins = vc_joins + {vc_joins}, \
                vc_leaves = vc_leaves + {vc_leaves}, \
                vc_time_muted = vc_time_muted + {vc_time_muted}, \
                vc_time_deafened = vc_time_deafened + {vc_time_deafened}, \
                vc_time_streaming = vc_time_streaming + {vc_time_streaming} \
                WHERE user_id = {user_id} AND guild_id = {guild_id} AND channel_id = {channel_id}
            """
        )
        self.connection.commit()

    def insert_daily_user(self, user_id, date, messages=0, commands=0, reactions=0, vc_time=0, vc_joins=0, vc_leaves=0, vc_time_muted=0, vc_time_deafened=0, vc_time_streaming=0):
        self.cursor.execute(
            f"""
                INSERT INTO daily_user (user_id, date, messages, commands, reactions, vc_time, vc_joins, vc_leaves, vc_time_muted, vc_time_deafened, vc_time_streaming) \
                VALUES ({user_id}, {date}, {messages}, {commands}, {reactions}, {vc_time}, {vc_joins}, {vc_leaves}, {vc_time_muted}, {vc_time_deafened}, {vc_time_streaming})
            """
        )
        self.connection.commit()

    def insert_daily_guild_user(self, user_id, guild_id, date, messages=0, commands=0, vc_time=0, vc_joins=0, vc_leaves=0, vc_time_muted=0, vc_time_deafened=0, vc_time_streaming=0):
        self.cursor.execute(
            f"""
                INSERT INTO daily_guild (user_id, guild_id, date, messages, commands, vc_time, vc_joins, vc_leaves, vc_time_muted, vc_time_deafened, vc_time_streaming) \
                VALUES ({user_id}, {guild_id}, {date}, {messages}, {commands}, {vc_time}, {vc_joins}, {vc_leaves}, {vc_time_muted}, {vc_time_deafened}, {vc_time_streaming})
            """
        )
        self.connection.commit()

    def insert_daily_text_channel_user(self, user_id, guild_id, channel_id, date, messages=0, commands=0):
        self.cursor.execute(
            f"""
                INSERT INTO daily_text_channel (user_id, guild_id, channel_id, date, messages, commands) \
                VALUES ({user_id}, {guild_id}, {channel_id}, {date}, {messages}, {commands})
            """
        )
        self.connection.commit()

    def insert_daily_voice_channel_user(self, user_id, guild_id, channel_id, date, vc_time=0, vc_joins=0, vc_leaves=0, vc_time_muted=0, vc_time_deafened=0, vc_time_streaming=0):
        self.cursor.execute(
            f"""
                INSERT INTO daily_voice_channel (user_id, guild_id, channel_id, date, vc_time, vc_joins, vc_leaves, vc_time_muted, vc_time_deafened, vc_time_streaming) \
                VALUES ({user_id}, {guild_id}, {channel_id}, {date}, {vc_time}, {vc_joins}, {vc_leaves}, {vc_time_muted}, {vc_time_deafened}, {vc_time_streaming})
            """
        )
        self.connection.commit()
