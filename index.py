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

    try:
        furry_Users = pickle.load(open("variables/furry_Users.pickle", "rb"))
    except:
        servers = []
        furry_Users = {}
        pass

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
async def togglesona(interaction: discord.Interaction):
    await interaction.response.send_message("This command is currently disabled due to Pogrammer feeling bad about annoying people with furry shit.", ephemeral=True)
    return
    if interaction.user.id not in furry_Users:
        await interaction.response.send_message("You're not a furry!", ephemeral=True)
        return

    if interaction.guild.id in furry_Users[interaction.user.id].servers:
        furry_Users[interaction.user.id].servers.remove(interaction.guild.id)
    else:
        furry_Users[interaction.user.id].servers.append(interaction.guild.id)

    pickle.dump(furry_Users, open("variables/furry_Users.pickle", "wb"))

    await interaction.response.send_message("toggled")

@bot.tree.command()
async def furry(interaction: discord.Interaction):
    await interaction.response.send_message("This command is currently disabled due to Pogrammer feeling bad about annoying people with furry shit.", ephemeral=True)
    return

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
async def checkchanneldescriptions(interaction: discord.Interaction, filter: str = ""):
    #whitlist for only me :)
    if interaction.user.id != 697959912302444614:
        await interaction.response.send_message("Sorry, you can't use this command", ephemeral=True)
        return
    
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

@bot.tree.command()
async def createfurry(interaction: discord.Interaction, furryurl: discord.Attachment, name: str):
    await interaction.response.send_message("This command is currently disabled due to Pogrammer feeling bad about annoying people with furry shit.", ephemeral=True)
    return
    # Check if user is already furry
    if interaction.user.id in furry_Users:
        await interaction.response.send_message("You already have a furry!", ephemeral=True)
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

    await interaction.response.send_message("furry created")

    

@bot.command()
async def reset(ctx):
    if ctx.author.id != 697959912302444614:
        await ctx.send("Sorry, you can't use this command")
        return

    furry_Users.clear()

    pickle.dump(furry_Users, open("variables/furry_Users.pickle", "wb"))

    await ctx.send("reset")
    

#command that sends the length of "furrylinks.txt" in terms of newlines
@bot.command()
async def uniquefurries(ctx):
    with open("furrylinks.txt") as file:
        await ctx.send(f"{len(file.readlines())}")

@bot.command()
async def createfurryfile(ctx):
    if ctx.author.id != 697959912302444614:
        await ctx.send("Sorry, you can't use this command")
        return

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
async def remove_webhooks(ctx):
    if ctx.author.id != 697959912302444614:
        await ctx.send("Sorry, you can't use this command")
        return

    webhooks = await ctx.guild.webhooks()
    bot_user = ctx.bot.user
    for webhook in webhooks:
        if webhook.user == bot_user:
            await webhook.delete()
    await ctx.send("Removed all bot webhooks")

@bot.command()
async def makemeasandwich(ctx):
    responses = ["Make it yourself.", "I'm not a butler.", "Poof! You're a sandwich!"]
    await ctx.send(responses[random.randint(0, len(responses)-1)])

bot.run(TOKEN)



#set avatar_file to the attached file
#    try:
#        avatar_file = await ctx.message.attachments[0].read()
#    except:
#        return
#
#    for webhook in webhooks:
#            if webhook.user == ctx.bot.user:
#                await webhook.edit(avatar=avatar_file)
#
#                await webhook.send("test")