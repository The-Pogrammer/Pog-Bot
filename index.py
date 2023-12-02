from typing import Dict
import discord
import os
import random
import requests
import ffmpeg
import time
import pickle
import weakref
import asyncio


from PIL import Image
from io import BytesIO

from discord import app_commands
from discord.ext import tasks, commands
from discord.ext.commands import CommandOnCooldown
from dotenv import load_dotenv

load_dotenv()
bot = commands.Bot(intents=discord.Intents.all(), command_prefix="p!")
TOKEN = os.getenv("TOKEN")


@bot.event
async def on_ready():
    print("ready")

    try:
        bot.tree.add_command(utility_commands)
    except Exception:
        pass
    
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
# on bot joining server, create a channel, add the disclaimer, and follow the announcement channel
@bot.event
async def on_guild_join(guild):
    print("Joined a server")
    # create a channel
    channel = await guild.create_text_channel(name="pog-bot-announcements")

    with open("disclaimer.txt", "r") as file:
        disclaimertext = file.read()

    embed = discord.Embed(
        title="Disclaimer",
        description=disclaimertext,
        color=discord.Color.red()
    )

    await channel.send(embed=embed)

    # follow the announcement channel
    announcementguild = bot.get_guild(952708168419508304)
    announcementchannel = announcementguild.get_channel(1171195796050423939)
    await announcementchannel.follow(destination=channel)
    
@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None:
        remaining_members = len(before.channel.members)
        if remaining_members == 1 and before.channel.members[0] == bot.user:
            await before.channel.guild.voice_client.disconnect()
            
# ----------------------------
# Misc Commands
# ----------------------------
#command that plays an inputed mp3 file in the discord vc of the user using the command
@bot.tree.command()
async def play(interaction: discord.Interaction, file: discord.Attachment):
    """Plays an inputed mp3 file in the discord vc of the user using the command"""
    vc = interaction.guild.voice_client

    if not interaction.user.voice:
        await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
        return

    if vc and vc.is_playing():
        vc.stop()
    #connect only if not already connected
    if not vc:
        vc = await interaction.user.voice.channel.connect()
    try:
        vc.play(discord.FFmpegPCMAudio(file.url))
        await interaction.response.send_message("Playing!", ephemeral=True)

        embed = discord.Embed(title="File Played")
        embed.add_field(name = "", value=f"{interaction.user.mention} played \"[{file.filename}]({file.url})\"")
    
        await interaction.channel.send(embed=embed)
    except:
        await interaction.response.send_message("Error. :(", ephemeral=True)

    
# command that stops the bot from playing audio in vc
@bot.tree.command()
async def stop(interaction: discord.Interaction):
    """Stops the bot from playing audio in vc"""
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        #leave vc
        await vc.disconnect()
        await interaction.response.send_message("Stopped.", ephemeral=True)
    else:
        await interaction.response.send_message("Not playing, or not in vc.", ephemeral=True)

@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def force_stop(interaction: discord.Interaction):
    await interaction.response.send_message("Resetting...", ephemeral=True)
    await bot.close()

@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def check_channel_descriptions(
    interaction: discord.Interaction, filter: str, archive: discord.CategoryChannel = None
):
    """
    Check channel descriptions, optionally with a filter.
    """

    channelinfo = []
    for channel in interaction.guild.channels:
        if isinstance(channel, discord.TextChannel):
            description = channel.topic if channel.topic else "No description"
            if filter in description and ((not channel.category == archive) or archive is None):
                channelinfo.append(channel.name + ": " + description)


    if len(channelinfo) == 0:
        await interaction.response.send_message(f"No channels found with text, \"{filter}\"")
        return

    try:
        message = "\n\n".join(channelinfo)
        with open("channelinfo.txt", "w") as file:
            # replace characters that can't be encoded
            message = message.encode("ascii", "ignore").decode()

            file.write(message)

        await interaction.response.send_message(file=discord.File("channelinfo.txt"))

        # delete file
        os.remove("channelinfo.txt")

    except Exception as e:
        print(e)

@bot.command()
async def makemeasandwich(ctx):
    responses = ["Make it yourself.", "I'm not a butler.", "Poof! You're a sandwich!"]
    await ctx.send(random.choice(responses))

# ----------------------------
# Utility Commands
# ----------------------------

utility_commands = app_commands.Group(name="utility", description="Utility Commands")

@utility_commands.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def rand(
    interaction: discord.Interaction, 
    min: int = 1, 
    max: int = 100
):
    """
    Random number between min and max (inclusive)
    """
    await interaction.response.send_message(
        f"{random.randint(min, max)}", ephemeral=True
    )
    

@utility_commands.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def send_embed(
    interaction: discord.Interaction
):
    """
    Disclaimer embed
    """
    # get disclaimertext from disclaimer.txt
    with open("disclaimer.txt", "r") as file:
        disclaimertext = file.read()

    embed = discord.Embed(
        title="Disclaimer",
        description=disclaimertext,
        color=discord.Color.red()
    )

    for guild in bot.guilds:
        pogannouncements = [chan for chan in guild.channels if chan.name == "pog-bot-announcements"]
        if pogannouncements:
            await pogannouncements[0].send(embed=embed)

@utility_commands.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def get_server_pfp(interaction: discord.Interaction):
    """
    Get server pfp
    """
    await interaction.response.send_message(
        f"{interaction.guild.icon}", ephemeral=True
    )

@utility_commands.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def role_hierarchy(interaction: discord.Interaction, emp: bool = True):
    """
    Print role hierarchy in reverse order
    """
    roles = interaction.guild.roles
    reversed_roles = reversed(roles)
    role_hierarchy = "\n".join([f"• {role.mention}" for role in reversed_roles if role.name != "@everyone"])
    
    embed = discord.Embed(
        title="Role Hierarchy",
        description=role_hierarchy,
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(
        embed=embed,
        ephemeral=emp,
        allowed_mentions=discord.AllowedMentions.none()
    )

@utility_commands.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def bot_permissions(interaction: discord.Interaction, filter: bool = None, emp: bool = True):
    """
    Print bot permissions in guild
    """
    bot_user = interaction.client.user
    permissions = interaction.guild.get_member(bot_user.id).guild_permissions
    
    if filter is not None:
        filtered_permissions = [f"{permission}: {':white_check_mark:' if value else ':x:'}" for permission, value in permissions if value == filter]
        color = discord.Color.green() if filter else discord.Color.red()
    else:
        filtered_permissions = [f"{permission}: {':white_check_mark:' if value else ':x:'}" for permission, value in permissions]
        color = discord.Color.blue()
    
    if filtered_permissions:
        permissions_str = "\n".join(filtered_permissions)
    else:
        permissions_str = "No matching permissions found."
    
    embed = discord.Embed(
        title="Bot Permissions",
        description=permissions_str,
        color=color
    )
    
    await interaction.response.send_message(
        embed=embed,
        ephemeral=emp
    )

#print info about every guild the bot is in
@utility_commands.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def guilds(interaction: discord.Interaction):
    """
    Print info about every guild the bot is in
    """
    guilds = "\n".join([f"• {guild.name} ({guild.id})" for guild in interaction.client.guilds])
    
    embed = discord.Embed(
        title="Guilds",
        description=guilds,
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(
        embed=embed,
        ephemeral=False
    )

# ----------------------------
# Furry Commands
# ----------------------------

@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def create_furry_file(interaction: discord.Interaction):
    """
    Compose all the furries pog bot can send into a single file.
    """
    await interaction.response.defer()

    with open("furrylinks.txt") as file:
        links = file.readlines()

        folder_name = "furrylinks"
        os.makedirs(folder_name, exist_ok=True)

        for i, link in enumerate(links):
            if not link.startswith("file:"):
                link = link.strip()
                file_name = os.path.basename(link)
                file_name_without_extension, file_extension = os.path.splitext(
                    file_name
                )

                # Generate a unique identifier using the current timestamp
                extrabit = str(i + 1)

                # Create a new file name with the unique identifier
                new_file_name = f"{extrabit}{file_extension}"

                file_path = os.path.join(folder_name, new_file_name)
                response = requests.get(link)

                if response.status_code == 200:
                    with open(file_path, "wb") as file:
                        file.write(response.content)

                    # await ctx.send(f"Downloaded: {link}")
                else:
                    print(f"Failed to download: {link}")

        await interaction.response.send_message("ran command")

# command that sends the length of "furrylinks.txt" in terms of newlines
@bot.tree.command()
async def count_unique_furries(interaction: discord.Interaction):
    """
    see the number of unique furries pog bot can send.
    """
    with open("furrylinks.txt") as file:
        await interaction.response.send_message(f"{len(file.readlines())}")
        
@bot.tree.command()
async def furry(interaction: discord.Interaction):
    """
    Display a random speechbubble furry.
    """

    # get furrylinks.txt
    with open("furrylinks.txt") as file:
        links = file.readlines()
        link = random.choice(links)

        await interaction.response.defer()

        if not link.startswith("file:"):
            await interaction.followup.send(link)
        else:
            file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "speechbubblefurries",
                link.strip().replace("file:", "", 1),
            )

            with open(file_path, "rb") as file:
                await interaction.followup.send(file=discord.File(file))
        
bot.run(TOKEN)
