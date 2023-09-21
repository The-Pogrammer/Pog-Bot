async def get_user_info(user_id, discord, bot):
    try:
        user = bot.get_user(user_id)
        return [user, "found user"]
    except discord.NotFound:
        return [None, "doesn't exist"]
    except discord.HTTPException:
        return [None, "bot failure"]
    
async def get_guild_info(guild_id, discord, bot):
    try:
        guild = bot.get_guild(guild_id)
        return [guild, "found guild"]
    except discord.NotFound:
        return [None, "doesn't exist"]
    except discord.HTTPException:
        return [None, "bot failure"]