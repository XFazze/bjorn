from discord.ext import commands, tasks
import time

import lib.general as general

class Active_people_database(general.Database):
    def __init__(self):
        super().__init__("data/activePeople.db")
        self.cursor.execute(
            f"""
                    CREATE TABLE IF NOT EXISTS user(user_id UNIQUE, timestamp)
                """
        )

    def update_user(self, user_id):
        timestamp = int(time.time())
        self.cursor.execute(
            f"""
                INSERT OR REPLACE INTO user(user_id, timestamp)  VALUES({user_id}, {timestamp})
            """
        )
        self.connection.commit()
    
    def get_users_within_14days(self):
        res = self.cursor.execute(f"SELECT user_id, timestamp FROM user").fetchall()
        seconds_14days = 60*60*24*14
        time_now_seconds = time.time()
        filter(lambda user: user[1]+seconds_14days < time_now_seconds, res)
        users_ids = [user[0] for user in res]
        return users_ids


class activePeople(general.Bjorn_cog):
    def __init__(self, bot):
        super().__init__(bot)
        self.bot = bot
        self.update_active_people.start()
        self.db = Active_people_database()
        self.active_role_id = 1105823135091130428
        self.inactive_role_id = 1105823231488831538

    def cog_unload(self):
        self.update_active_people.cancel()

    @tasks.loop(seconds=60.0)
    async def update_active_people(self):
        try:
            guild_object = self.bot.get_guild(self.loading_id)
            active_role_object = guild_object.get_role(self.active_role_id)
            inactive_role_object = guild_object.get_role(self.inactive_role_id)
            
            active_users = self.db.get_users_within_14days()
            for member in guild_object.members:
                if member.bot:
                    continue
                
                if member.id in active_users:  # active member
                    if inactive_role_object in member.roles:
                        await member.remove_roles(inactive_role_object)
                    
                    if active_role_object not in member.roles: 
                        await member.add_roles(active_role_object)
                else: # inactive member
                    if active_role_object in member.roles: 
                        await member.remove_roles(active_role_object)
                    
                    if inactive_role_object not in member.roles: 
                        await member.add_roles(inactive_role_object)
        except Exception as e:
            print("update_active_people error: ", e)
            pass

    @update_active_people.before_loop
    async def before_update_active_people(self):
        print("update_active_people enabled")
        await self.bot.wait_until_ready()
        
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel is None or member.guild.id != self.loading_id or not member or member.bot:
            return
        try:
            print("on voice stat eupdate")
            self.db.update_user(member.id)
        except Exception as e:
            print("update_active_people on_voice_state_update error: ", e)
            pass
            
        
   

async def setup(bot):
    await bot.add_cog(activePeople(bot))
