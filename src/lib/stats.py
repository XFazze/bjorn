import lib.general as general


class Database(general.Database):
    def __init__(self):
        super().__init__("data/stats.sqlite")
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
                    "vc_time",
                    "vc_joins",
                    "vc_leaves",
                    "vc_time_muted",
                    "vc_time_deafened",
                    "vc_time_streaming",
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
                ],
                "joined": [
                    "user_id",
                    "timestamp"
                ],
                "muted": [
                    "user_id",
                    "timestamp"
                ],
                "deafened": [
                    "user_id",
                    "timestamp"
                ],
                "streaming": [
                    "user_id",
                    "timestamp"
                ]
            }
        )

    def insert_user(self, user_id):
        self.cursor.execute(
            f"""
                INSERT INTO user (user_id) VALUES ({user_id})
            """
        )
        self.connection.commit()

    def insert_guild_user(self, user_id, guild_id):
        self.cursor.execute(
            f"""
                INSERT INTO guild (user_id, guild_id) VALUES ({user_id}, {guild_id})
            """
        )
        self.connection.commit()

    def insert_text_channel_user(self, user_id, guild_id, channel_id):
        self.cursor.execute(
            f"""
                INSERT INTO text_channel (user_id, guild_id, channel_id) VALUES ({user_id}, {guild_id}, {channel_id})
            """
        )
        self.connection.commit()

    def insert_voice_channel_user(self, user_id, guild_id, channel_id):
        self.cursor.execute(
            f"""
                INSERT INTO voice_channel (user_id, guild_id, channel_id) VALUES ({user_id}, {guild_id}, {channel_id})
            """
        )
        self.connection.commit()

    def get_user(self, user_id):
        self.cursor.execute(
            f"""
                SELECT * FROM user WHERE user_id = {user_id}
            """
        )
        return self.cursor.fetchone()

    def get_guild_user(self, user_id, guild_id):
        self.cursor.execute(
            f"""
                SELECT * FROM guild WHERE user_id = {user_id} AND guild_id = {guild_id}
            """
        )
        return self.cursor.fetchone()

    def get_text_channel_user(self, user_id, guild_id, channel_id):
        self.cursor.execute(
            f"""
                SELECT * FROM text_channel WHERE user_id = {user_id} AND guild_id = {guild_id} AND channel_id = {channel_id}
            """
        )
        return self.cursor.fetchone()

    def get_voice_channel_user(self, user_id, guild_id, channel_id):
        self.cursor.execute(
            f"""
                SELECT * FROM voice_channel WHERE user_id = {user_id} AND guild_id = {guild_id} AND channel_id = {channel_id}
            """
        )
        return self.cursor.fetchone()

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

    def update_guild_user(self, user_id, guild_id, messages=0, commands=0, vc_time=0, vc_joins=0, vc_leaves=0, vc_time_muted=0, vc_time_deafened=0, vc_time_streaming=0):
        self.cursor.execute(
            f"""
                UPDATE guild SET \
                messages = messages + {messages}, \
                commands = commands + {commands}, \
                vc_time = vc_time + {vc_time}, \
                vc_joins = vc_joins + {vc_joins}, \
                vc_leaves = vc_leaves + {vc_leaves}, \
                vc_time_muted = vc_time_muted + {vc_time_muted}, \
                vc_time_deafened = vc_time_deafened + {vc_time_deafened}, \
                vc_time_streaming = vc_time_streaming + {vc_time_streaming} \
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

    def get_joined_users(self):
        self.cursor.execute(
            f"""
                SELECT user_id, timestamp FROM joined
            """
        )
        return self.cursor.fetchall()

    def get_muted_users(self):
        self.cursor.execute(
            f"""
                SELECT user_id, timestamp FROM muted
            """
        )
        return self.cursor.fetchall()

    def get_deafened_users(self):
        self.cursor.execute(
            f"""
                SELECT user_id, timestamp FROM deafened
            """
        )
        return self.cursor.fetchall()

    def get_streaming_users(self):
        self.cursor.execute(
            f"""
                SELECT user_id, timestamp FROM streaming
            """
        )
        return self.cursor.fetchall()

    def insert_joined_user(self, user_id, timestamp):
        self.cursor.execute(
            f"""
                INSERT INTO joined (user_id, timestamp) \
                VALUES ({user_id}, {timestamp})
            """
        )
        self.connection.commit()

    def insert_muted_user(self, user_id, timestamp):
        self.cursor.execute(
            f"""
                INSERT INTO muted (user_id, timestamp) \
                VALUES ({user_id}, {timestamp})
            """
        )
        self.connection.commit()

    def insert_deafened_user(self, user_id, timestamp):
        self.cursor.execute(
            f"""
                INSERT INTO deafened (user_id, timestamp) \
                VALUES ({user_id}, {timestamp})
            """
        )
        self.connection.commit()

    def insert_streaming_user(self, user_id, timestamp):
        self.cursor.execute(
            f"""
                INSERT INTO streaming (user_id, timestamp) \
                VALUES ({user_id}, {timestamp})
            """
        )
        self.connection.commit()

    def remove_joined_user(self, user_id):
        self.cursor.execute(
            f"""
                DELETE FROM joined WHERE user_id = {user_id}
            """
        )
        self.connection.commit()

    def remove_muted_user(self, user_id):
        self.cursor.execute(
            f"""
                DELETE FROM muted WHERE user_id = {user_id}
            """
        )
        self.connection.commit()

    def remove_deafened_user(self, user_id):
        self.cursor.execute(
            f"""
                DELETE FROM deafened WHERE user_id = {user_id}
            """
        )
        self.connection.commit()

    def remove_streaming_user(self, user_id):
        self.cursor.execute(
            f"""
                DELETE FROM streaming WHERE user_id = {user_id}
            """
        )
        self.connection.commit()

    def ensure_user_entry(self, user_id):
        self.cursor.execute(
            f"""
                SELECT * FROM user WHERE user_id = {user_id}
            """
        )
        if self.cursor.fetchone() is None:
            self.insert_user(user_id)

    def ensure_guild_entry(self, user_id, guild_id):
        self.cursor.execute(
            f"""
                SELECT * FROM guild WHERE user_id = {user_id} AND guild_id = {guild_id}
            """
        )
        if self.cursor.fetchone() is None:
            self.insert_guild(user_id, guild_id)

    def ensure_text_channel_entry(self, user_id, guild_id, channel_id):
        self.cursor.execute(
            f"""
                SELECT * FROM text_channel WHERE user_id = {user_id} AND guild_id = {guild_id} AND channel_id = {channel_id}
            """
        )
        if self.cursor.fetchone() is None:
            self.insert_text_channel(user_id, guild_id, channel_id)

    def ensure_voice_channel_entry(self, user_id, guild_id, channel_id):
        self.cursor.execute(
            f"""
                SELECT * FROM voice_channel WHERE user_id = {user_id} AND guild_id = {guild_id} AND channel_id = {channel_id}
            """
        )
        if self.cursor.fetchone() is None:
            self.insert_voice_channel(user_id, guild_id, channel_id)
