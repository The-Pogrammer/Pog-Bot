from typing import Dict
import discord
import os
import random
import requests
import pickle
import traceback
import asyncio
import aiohttp

from discord import app_commands
from discord.ext import tasks, commands
from discord.ext.commands import CommandOnCooldown
from dotenv import load_dotenv
from pydub import AudioSegment

import csv

load_dotenv()
bot = commands.Bot(intents=discord.Intents.all(), command_prefix="p!")
TOKEN = os.getenv("TOKEN")

is_initialized = False

@bot.event
async def on_ready():
    #print number of servers
    print(len(bot.guilds))

    global is_initialized

    if not is_initialized:
        print("ready")

        try:
            bot.tree.add_command(utility_commands)
        except:
            pass

        try:
            bot.tree.add_command(profile_commands)
        except:
            pass

        try:
            bot.tree.add_command(audio_commands)
        except:
            pass

        try:
            bot.tree.add_command(furry_commands)
        except:
            pass

        try:
            synced = await bot.tree.sync()
            print(f"Synced {len(synced)} command(s)")
        except Exception as e:
            print(e)

        is_initialized = True

def save(content, filename):
    with open(filename, "wb") as file:
        pickle.dump(content, file)

@bot.event
async def on_error(event, *args, **kwargs):
    """
    Handles any unhandled exceptions in event handlers
    """
    # Log the error or perform any other desired actions
    print("An error occurred in an event handler")
    traceback.print_exc()

    # You can also send an error message to a specific channel or user
    # channel = bot.get_channel(YOUR_CHANNEL_ID)
    # await channel.send("An error occurred. Please check the logs for more details.")

#when sticker is sent by bot owner, log it
@bot.event
async def on_message(message: discord.Message):
    #if message is a prefix command, run it
    if message.content.startswith("p!"):
        await bot.process_commands(message)
        return

# -----------------------------
# local profiles
# -----------------------------

def userdoesntexist(id):
    embed = discord.Embed(
        title="User Not Found", 
        description=f"That user doesn't have a profile in this server.", 
        color=discord.Color.red()
    )
    return embed

profile_commands = app_commands.Group(
    name="profile",
    description="Profile related commands",
)

@profile_commands.command()
async def edit(interaction: discord.Interaction, status: str = None, about_me: str = None, pronouns: str = None, sexuality: str = None, age: int = None, color: str = None):
    """Edits your profile"""
    await interaction.response.defer(ephemeral=False, thinking=True)

    # compose a list of all the folder names in "ProfileData/Servers"
    Profiles = [name for name in os.listdir("ProfileData/Users")]

    if str(interaction.user.id) + ".csv" not in Profiles:
        #create file [userid].csv
        with open(f"ProfileData/Users/{interaction.user.id}.csv", "w", newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["servers", "avatar", "name", "status", "about_me", "pronouns", "sexuality", "age", "color"])
            writer.writerow([str(interaction.guild.id), interaction.user.display_avatar, interaction.user.display_name, status, about_me, pronouns, sexuality, age, color])
    else:
        with open(f"ProfileData/Users/{interaction.user.id}.csv", "r+", newline='', encoding='utf-8') as file:
            # get "servers" column
            reader = csv.reader(file)
            rows = list(reader)
            for row in rows:
                serverexists = False
                if len(row) <= 0:
                    #delete empty row
                    rows.remove(row)

                if row[0] == str(interaction.guild.id):
                    row[1] = interaction.user.display_avatar
                    row[2] = interaction.user.display_name
                    if not status is None:
                        if len(status) > 150:
                            await interaction.channel.send("your status cannot exceed 150 characters!")
                        else:
                            row[3] = status
                    if not about_me is None:
                        if len(about_me) > 250:
                            await interaction.channel.send("Your about me cannot exceed 250 characters!")
                        else:
                            row[4] = about_me
                    if not pronouns is None:
                        row[5] = pronouns
                    if not sexuality is None:
                        row[6] = sexuality
                    if not age is None:
                        row[7] = age
                    if not color is None:
                        try: 
                            discord.Color.from_str(color)
                        except:
                            await interaction.channel.send("That is not a valid color!")
                        else:
                            row[8] = color
                    serverexists = True
                    break

            if not serverexists:
                rows.append([str(interaction.guild.id), interaction.user.display_avatar, interaction.user.display_name, status, about_me, pronouns, sexuality, age, color])
        
            file.seek(0)  # Move the cursor back to the beginning of the file
            writer = csv.writer(file)
            writer.writerows(rows)
            file.truncate()  # Remove any remaining content after the updated rows
    
    await interaction.followup.send("Profile updated!")

@profile_commands.command()
async def view(interaction: discord.Interaction, user_id: str = None, user: discord.User = None):
    """View your profile"""
    # if neither is defined, use the author, but if one is defined, use it
    if user_id is None and user is None:
        user_id = interaction.user.id

    if user_id is None and not user is None:
        user_id = user.id

    #check if ProfileData/Users/[user_id].csv exists
    Profiles = [name for name in os.listdir("ProfileData/Users")]
    
    if str(user_id) + ".csv" not in Profiles:
        embed = userdoesntexist(user_id)
        await interaction.response.send_message(embed=embed)
        return

    with open(f"ProfileData/Users/{user_id}.csv", "r", newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == str(interaction.guild.id):
                avatar = row[1]
                name = row[2]
                status = row[3]
                about_me = row[4]
                pronouns = row[5]
                sexuality = row[6]
                age = row[7]
                try:
                    color = discord.Color.from_str(row[8])
                except:
                    color = discord.Color.blue()
                    

                embed = discord.Embed(color=color)
                embed.set_author(name=name, icon_url=avatar)
                if status != "":
                    embed.title = status
                if about_me != "":
                    embed.description = about_me
                if pronouns != "":
                    embed.add_field(name="Pronouns", value=pronouns, inline=True)
                if sexuality != "":
                    embed.add_field(name="Sexuality", value=sexuality, inline=True)
                if age != "":
                    embed.add_field(name="Age", value=age, inline=True)

                await interaction.response.send_message(embed=embed)
                break
        
        #if no response was ever sent, send response
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=userdoesntexist(user_id))
    
# -----------------------------
# disclaimer stuff
# -----------------------------

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

# ----------------------------
# Misc Commands
# ----------------------------

@bot.command()
async def download_voice(interaction: discord.Interaction):
    # Check if the command was used in a guild
    if interaction.guild is None:
        await interaction.send("This command can only be used in a server.")
        return

    # Get the replied message
    replied_message = interaction.message.reference.resolved

    # Check if the replied message is a voice message
    if replied_message.attachments:
        # Download the voice clip
        voice_url = replied_message.attachments[0].url
        response = requests.get(voice_url)
        voice_data = response.content

        # Save the voice clip as an MP3 file
        mp3_file = "voice.mp3"
        with open(mp3_file, "wb") as f:
            f.write(voice_data)

        # Send the MP3 file in chat
        await interaction.send(file=discord.File(mp3_file))

        # Delete the MP3 file
        os.remove(mp3_file)
    else:
        await interaction.send("The replied message is not a voice message.")

@bot.tree.command()
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

# ----------------------------
# Furry Commands
# ----------------------------

furry_commands = app_commands.Group(
    name="furry", description="Furry Commands"
)

@furry_commands.command()
async def send_furry(interaction: discord.Interaction, index: int = None):
    """Sends a random furry image"""
    # open folder "FurryImages" (located in same directory as index.py)
    FurryFolder = sorted(os.listdir("FurryImages"), key=lambda x: int(''.join(filter(str.isdigit, x))))

    if index is None:
        index = random.randint(0, len(FurryFolder) - 1)
        random_selected = True
    else:
        index = index - 1
        random_selected = False

    # handle out of range index
    if index < 0 or index >= len(FurryFolder):
        await interaction.response.send_message("Index out of range.", ephemeral=True)
        return

    SelectedImage = FurryFolder[index]

    if random_selected:
        await interaction.response.send_message(f"Furry index: {index + 1}", ephemeral=True)
    else:
        await interaction.response.defer()

    await interaction.followup.send(file=discord.File(f"FurryImages/{SelectedImage}"))


# ----------------------------
# vc commands
# ----------------------------

audio_commands = app_commands.Group(name="audio", description="Audio Commands")

# command that stops the bot from playing audio in vc
@audio_commands.command()
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

#command that plays an inputed mp3 file in the discord vc of the user using the command
@audio_commands.command()
async def play_file(interaction: discord.Interaction, file: discord.Attachment):
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

        embed = discord.Embed(title="File Played")
        embed.add_field(name="", value=f"{interaction.user.mention} played \"[{file.filename}]({file.url})\"")

        await interaction.channel.send(embed=embed)
    except Exception as e:
        print(f"Error occurred: {e}")
        await interaction.response.send_message("Error. :(", ephemeral=True)

@bot.event
async def on_voice_state_update(member, before, after):
    if before.channel is not None:
        remaining_members = len(before.channel.members)
        if remaining_members == 1 and before.channel.members[0] == bot.user:
            await before.channel.guild.voice_client.disconnect()

# ----------------------------
# Utility Commands
# ----------------------------

utility_commands = app_commands.Group(name="utility", description="Utility Commands")

@utility_commands.command()
async def count_messages(interaction: discord.Interaction, messageid: str):
    """
    Count messages between the newest message and messageid
    """
    try:
        message = await interaction.channel.fetch_message(int(messageid))
        message_count = 0
        async for msg in interaction.channel.history(after=message):
            message_count += 1
        await interaction.response.send_message(f"Count: {message_count}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Error: {e}", ephemeral=True)
@utility_commands.command()
async def find_messages(interaction: discord.Interaction, str: str):
    """
    Find messages in the current server
    """
    await interaction.response.defer(ephemeral=True)
    channels = interaction.guild.channels
    locations = []
    for channel in channels:
        if isinstance(channel, discord.TextChannel):
            async for message in channel.history(limit=100):
                if str in message.content:
                    locations.append(message.jump_url)
    await interaction.followup.send(locations)
                     
@utility_commands.command()
async def sync_permissions(interaction: discord.Interaction):
    """
    Sync permissions in the current category
    """
    Category = interaction.channel.category
    if Category is None:
        await interaction.response.send_message(
            "This command can only be used in a category channel.", ephemeral=True
        )
        return
    await interaction.response.defer(ephemeral=True)
    for channel in Category.channels:
        if isinstance(channel, discord.TextChannel or discord.VoiceChannel):
            await channel.edit(sync_permissions=True)

    await interaction.followup.send("Synced all channels!")

@utility_commands.command()
async def purge_reactions(interaction: discord.Interaction, message_id: int = None):
    """
    Purge reactions
    """
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "You are not authorized to use this command.", ephemeral=True
        )
        return
    
    await interaction.response.defer(ephemeral=True)
    if not message_id is None:

        message = await interaction.channel.fetch_message(message_id)
        await message.clear_reactions()
    else:
        # purge reactions from the last 10 messages in the channel it was run in
        async for message in interaction.channel.history(limit=10):
            await message.clear_reactions()

    await interaction.followup.send("Purged reactions.")

@utility_commands.command()
async def purge(interaction: discord.Interaction, amount: int):
    """
    Purge messages
    """
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "You are not authorized to use this command.", ephemeral=True
        )
        return
    await interaction.response.defer()
    await interaction.channel.purge(limit=amount)

@utility_commands.command()
async def getpfpurl(interaction: discord.Interaction, user: discord.User = None):
    """
    Get user pfp url
    """
    if user is None:
        user = interaction.user
    await interaction.response.send_message(
        f"{user.display_avatar.url}", ephemeral=True
    )
    

@utility_commands.command()
async def get_server_pfp(interaction: discord.Interaction):
    """
    Get server pfp
    """
    await interaction.response.send_message(
        f"{interaction.guild.icon}", ephemeral=True
    )

@utility_commands.command()
async def update_eula(interaction: discord.Interaction):
    """
    Update EULA
    """
    if not interaction.user.id == 860236790610001940:
        await interaction.response.send_message(
            "You are not authorized to use this command.", ephemeral=True
        )
        return

    with open("disclaimer.txt") as file:
        disclaimertext = file.read()
    
    embed = discord.Embed(
        title="Disclaimer Update",
        description=disclaimertext,
        color=discord.Color.red()
    )

    for server in bot.guilds:
        for channel in server.channels:
            if channel.name == "pog-bot-announcements":
                await channel.send(embed=embed)

                break

    await interaction.response.send_message("Updated EULA", ephemeral=True)

# easter eggs
@bot.command()
async def bonk(ctx):
    await ctx.send("https://tenor.com/view/yoshi-mario-yoshis-island-super-smash-brother-super-smash-brother-n64-gif-21681448")

@bot.command()
async def jumpscare(ctx):
    with open("jumpscare.txt", "r", encoding="utf-8") as file:
        content = file.read()
    
        await ctx.send(content)

@bot.command()
async def makemeasandwich(ctx):
    responses = ["Make it yourself.", "I'm not a butler.", "Poof! You're a sandwich!"]
    await ctx.send(random.choice(responses))

bot.run(TOKEN)