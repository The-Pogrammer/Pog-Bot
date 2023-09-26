import discord
import os
import random
import requests
import time
import pickle

from PIL import Image
from io import BytesIO

from discord.ext import tasks, commands
from discord.ext.commands import CommandOnCooldown
from dotenv import load_dotenv

furryblacklist = [1150221079021883442]

load_dotenv()
bot = commands.Bot(intents=discord.Intents.all(), command_prefix="p!")
TOKEN = os.getenv('TOKEN')

class FurryUser(commands.Bot):
    def __init__(self, furryurl, name, servers):
        self.furryurl = furryurl
        self.name = name
        self.servers = servers

@bot.event
async def on_ready():
    print("ready")

    global furry_Users
    global banned_from_fursona

    try:
        furry_Users = pickle.load(open("variables/furry_Users.pickle", "rb"))
    except:
        furry_Users = {}

    try:
        banned_from_fursona = pickle.load(open("variables/banfursona.pickle", "rb"))
    except:
        banned_from_fursona = []

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.content.startswith("p!") or message.channel.id in furryblacklist or message.author.bot:
        return

    if message.author.id in furry_Users and message.guild.id in furry_Users[message.author.id].servers:
        await message.delete()

        if message.guild.id in furry_Users[message.author.id].servers:
            user = furry_Users[message.author.id]

            #if a webhook doesn't exist, create one
            webhooks = await message.channel.webhooks()
            webhooks = [webhook for webhook in webhooks if webhook.user == bot.user]
                
            if len(webhooks) == 0:
                await message.channel.create_webhook(name="Pog Bot Proxy")

            webhooks = await message.channel.webhooks()
            webhooks = [webhook for webhook in webhooks if webhook.user == bot.user]
            webhook = webhooks[0]

            webhook = await webhook.edit(name=user.name, avatar=user.furryurl)

            await webhook.send(message.content)

            if message.attachments:
                for attachment in message.attachments:
                    await webhook.send(attachment.url)

@bot.tree.command()
async def createfursona(interaction: discord.Interaction, furryurl: discord.Attachment, name: str):
    """
    Create a fursona.
    """

    # Check if user is already furry
    if interaction.user.id in furry_Users:
        await interaction.response.send_message("You already have a furry!", ephemeral=True)
        return

    if interaction.user.id in banned_from_fursona:
        await interaction.response.send_message("You're banned from fursona!", ephemeral=True)
        return

    # Read attachment data
    attachment_data = await furryurl.read()

    # Open the image using Pillow
    image = Image.open(BytesIO(attachment_data))

    # Convert the image to RGB mode
    image = image.convert("RGB")

    # Resize the image to reduce its size
    # Adjust the size as per your requirements
    resized_image = image.resize((500, 500))

    # Save the resized image to a BytesIO object
    compressed_data = BytesIO()
    resized_image.save(compressed_data, format="JPEG")

    # Reset the file pointer of the BytesIO object
    compressed_data.seek(0)

    # Update furry_Users with the compressed image data
    furry_Users.update({interaction.user.id: FurryUser(compressed_data.read(), name, [interaction.guild.id])})

    try:
        pickle.dump(furry_Users, open("variables/furry_Users.pickle", "wb"))
    except:
        pass

    await interaction.response.send_message("furry created", ephemeral=True)

#slash command only I can see and use
@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def removefursona(interaction: discord.Interaction, userid: str):
    """
    Remove a fursona. Admin only.
    """

    userid = int(userid)
    
    if userid not in furry_Users:
        await interaction.response.send_message("That user has no fursona.", ephemeral=True)
        return

    furry_Users.pop(userid)
    pickle.dump(furry_Users, open("variables/furry_Users.pickle", "wb"))

    await interaction.response.send_message("Removed fursona.", ephemeral=True)


@bot.tree.command()
async def togglefursona(interaction: discord.Interaction):
    """
    Toggle your fursona in this server.
    """
    if interaction.user.id not in furry_Users:
        await interaction.response.send_message("You're not a furry!", ephemeral=True)
        return

    if interaction.guild.id in furry_Users[interaction.user.id].servers:
        furry_Users[interaction.user.id].servers.remove(interaction.guild.id)
    else:
        furry_Users[interaction.user.id].servers.append(interaction.guild.id)

    pickle.dump(furry_Users, open("variables/furry_Users.pickle", "wb"))

    await interaction.response.send_message("Fursona toggled " + ("on" if interaction.guild.id in furry_Users[interaction.user.id].servers else "off") + " in this server.", ephemeral=True)

@bot.tree.command()
async def editfursona(interaction: discord.Interaction, furryurl: discord.Attachment = None, name: str = None):
    """
    Edit your fursona.
    """

    # Check if user is already furry
    if interaction.user.id not in furry_Users:
        await interaction.response.send_message("You're not a furry!", ephemeral=True)
        return

    if furryurl is None and name is None:
        await interaction.response.send_message("You need to provide either a furryurl or a name.", ephemeral=True)
        return

    if furryurl is not None:
        
        # Read attachment data
        attachment_data = await furryurl.read()

        # Open the image using Pillow
        image = Image.open(BytesIO(attachment_data))

        # Convert the image to RGB mode
        image = image.convert("RGB")

        # Resize the image to reduce its size
        # Adjust the size as per your requirements
        resized_image = image.resize((500, 500))

        # Save the resized image to a BytesIO object
        compressed_data = BytesIO()
        resized_image.save(compressed_data, format="JPEG")

        # Reset the file pointer of the BytesIO object
        compressed_data.seek(0)

        furry_Users[interaction.user.id].furryurl = compressed_data.read()

    if name is not None:
        furry_Users[interaction.user.id].name = name

    try:
        pickle.dump(furry_Users, open("variables/furry_Users.pickle", "wb"))
    except:
        pass

    await interaction.response.send_message("Fursona edited.", ephemeral=True)

@bot.tree.command()
async def furry(interaction: discord.Interaction):
    """
    Display a random speechbubble furry.
    """
    if interaction.channel.id in furryblacklist:
        await interaction.response.send_message("Sorry, you can't use this command here.", ephemeral=True)
        return
    
    #get furrylinks.txt
    with open("furrylinks.txt") as file:
        links = file.readlines()
        link = links[random.randint(0, len(links)-1)]

        await interaction.response.defer()

        if (not link.startswith("file:")):
            await interaction.followup.send(link)
        else:
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "speechbubblefurries", link.strip().replace("file:", "", 1))

            with open(file_path, "rb") as file:
                await interaction.followup.send(file=discord.File(file))

@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def banuserfromfursona(interaction: discord.Interaction, userid: str):
    """
    Ban a user from fursona. Admin only.
    """

    userid = int(userid)
    if userid in furry_Users:
        furry_Users.pop(userid)
        pickle.dump(furry_Users, open("variables/furry_Users.pickle", "wb"))
    
    banned_from_fursona.append(userid)
    pickle.dump(banned_from_fursona, open("variables/banfursona.pickle", "wb"))

    await interaction.response.send_message("User banned from fursona.", ephemeral=True)

@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def checkchanneldescriptions(interaction: discord.Interaction, filter: str = ""):
    """
    Check channel descriptions, optionally with a filter.
    """
    
    channelinfo = []
    for channel in interaction.guild.channels:
        if isinstance(channel, discord.TextChannel):
            description = channel.topic if channel.topic else "No description"
            if filter in description:
                channelinfo.append(channel.name + ": " + description)

    try:
        message = "\n\n".join(channelinfo)
        with open("channelinfo.txt", "w") as file:
            #replace characters that can't be encoded
            message = message.encode("ascii", "ignore").decode()
            
            file.write(message)
            
        await interaction.response.send_message(file=discord.File("channelinfo.txt"))

        #delete file
        os.remove("channelinfo.txt")


    except Exception as e:
        print(e)
    

#command that sends the length of "furrylinks.txt" in terms of newlines
@bot.tree.command()
async def uniquefurries(interaction: discord.Interaction):
    """
    see the number of unique furries pog bot can send.
    """
    with open("furrylinks.txt") as file:
        await interaction.response.send(f"{len(file.readlines())}")

@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def createfurryfile(ctx):
    """
    Compose all the furries pog bot can send into a single file.
    """

    with open("furrylinks.txt") as file:
        links = file.readlines()

        folder_name = "furrylinks"
        os.makedirs(folder_name, exist_ok=True)

        for i, link in enumerate(links):
            if not link.startswith("file:"):
                link = link.strip()
                file_name = os.path.basename(link)
                file_name_without_extension, file_extension = os.path.splitext(file_name)

                # Generate a unique identifier using the current timestamp
                extrabit = str(i+1)

                # Create a new file name with the unique identifier
                new_file_name = f"{extrabit}{file_extension}"
                
                file_path = os.path.join(folder_name, new_file_name)
                response = requests.get(link)

                if response.status_code == 200:
                    with open(file_path, 'wb') as file:
                        file.write(response.content)
                        
                    # await ctx.send(f"Downloaded: {link}")
                else:
                    print(f"Failed to download: {link}")
            
        await ctx.send("ran command")

@bot.command()
async def makemeasandwich(ctx):
    responses = ["Make it yourself.", "I'm not a butler.", "Poof! You're a sandwich!"]
    await ctx.send(responses[random.randint(0, len(responses)-1)])

bot.run(TOKEN)