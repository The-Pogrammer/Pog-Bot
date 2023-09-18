import discord
import os
import random

from discord.ext import tasks, commands
from dotenv import load_dotenv
from discordfunctions import *

load_dotenv()
bot = commands.Bot(intents=discord.Intents.all(), command_prefix="p!")
TOKEN = os.getenv('TOKEN')

@bot.event
async def on_ready():
    print("ready")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.tree.command()
async def verifyuserexists(interaction: discord.Interaction, id: str):
    user = await get_user_info(int(id), discord, bot)
    if user[0] is not None:
        await interaction.response.send_message(f"user \"{user[0].name}\" exists.", ephemeral=True)
    else:
        await interaction.response.send_message("user doesn't exist")

@bot.tree.command()
async def furry(interaction: discord.Interaction):
    #get furrylinks.txt
    with open("furrylinks.txt") as file:
        links = file.readlines()
        link = links[random.randint(0, len(links)-1)]

        await interaction.response.defer()

        if (link.startswith("https:")):
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
    
    print(channelinfo)


    try:
        #split into 2000 character segments and send seperately
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

@bot.command()
async def makemeasandwich(ctx):
    responses = ["Make it yourself.", "I'm not a butler.", "Poof! You're a sandwich!"]
    await ctx.send(responses[random.randint(0, len(responses)-1)])

bot.run(TOKEN)