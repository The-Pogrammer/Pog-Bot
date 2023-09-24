import discord
import os
import random
import requests
import time
import pickle

from discord.ext import tasks, commands
from discord.ext.commands import CommandOnCooldown
from dotenv import load_dotenv
from supportscripts.discordfunctions import *

furryblacklist = [1150221079021883442]

load_dotenv()
bot = commands.Bot(intents=discord.Intents.all(), command_prefix="p!")
TOKEN = os.getenv('TOKEN')

@bot.event
async def on_ready():
    print("ready")

    global servers

    try:
        servers = pickle.load(open("variables/servers.pickle", "rb"))
    except:
        pass

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.id != 697959912302444614 or message.content.startswith("p!"):
        return

    if message.channel.id in furryblacklist:
        return

    if message.guild.id in servers:
        await message.delete()

        webhooks = await message.channel.webhooks()
        bot_user = bot.user
        bot_webhooks = [webhook for webhook in webhooks if webhook.user == bot_user]
        with open("proxy.jpeg", "rb") as avatar_file:
            avatar_file = avatar_file.read()
            if len(bot_webhooks) == 0:
                webhook = await message.channel.create_webhook(name="pogwammew", avatar=avatar_file)

                # Send message content
                if message.content:
                    await webhook.send(message.content)

                # Send attachments as separate messages
                for attachment in message.attachments:
                    await webhook.send(file=await attachment.to_file())
            else:
                webhook = bot_webhooks[0]  # Assuming there is only one bot webhook in the channel
                
                await webhook.edit(name="pogwammew")
                
                if message.content:
                    await webhook.send(message.content)

                # Send attachments as separate messages
                for attachment in message.attachments:
                    await webhook.send(file=await attachment.to_file())

    

@bot.tree.command()
async def verifyuserexists(interaction: discord.Interaction, id: str):
    user = await get_user_info(int(id), discord, bot)
    if user[0] is not None:
        await interaction.response.send_message(f"user \"{user[0].name}\" exists.", ephemeral=True)
    else:
        await interaction.response.send_message("user doesn't exist")

@bot.tree.command()
async def furry(interaction: discord.Interaction):
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
async def checkchanneldescriptions(interaction: discord.Interaction):
    #whitlist for only me :)
    if interaction.user.id != 697959912302444614:
        await interaction.response.send_message("Sorry, you can't use this command", ephemeral=True)
        return
    
    channelinfo = []
    for channel in interaction.guild.channels:
        if isinstance(channel, discord.TextChannel):
            description = channel.topic if channel.topic else "No description"
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

#toggle furry
@bot.command()
async def toggleFurry(ctx):
    if ctx.author.id != 697959912302444614:
        await ctx.send("Sorry, you can't use this command")
        return

    if ctx.guild.id not in servers:
        servers.append(ctx.guild.id)
    else:
        servers.remove(ctx.guild.id)

    #toggled furry off/on
    await ctx.send("toggled furry " + ("on" if servers.count(ctx.guild.id) > 0 else "off"))

    try:
        pickle.dump(servers, open("variables/servers.pickle", "wb"))
    except:
        pass

@bot.command()
async def updatepfps(ctx):
    if ctx.author.id != 697959912302444614:
        await ctx.send("Sorry, you can't use this command")
        return

    with open("proxy.jpeg", "rb") as avatar_file:
        avatar_file = avatar_file.read()
        webhooks = await ctx.guild.webhooks()
        bot_user = ctx.bot.user
        for webhook in webhooks:
            if webhook.user == bot_user:
                await webhook.edit(avatar=avatar_file)

    await ctx.send("All updated!")

@bot.command()
async def makemeasandwich(ctx):
    responses = ["Make it yourself.", "I'm not a butler.", "Poof! You're a sandwich!"]
    await ctx.send(responses[random.randint(0, len(responses)-1)])

bot.run(TOKEN)