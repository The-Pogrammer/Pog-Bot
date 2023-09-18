import discord
import os
import random

from discord.ext import tasks, commands
from dotenv import load_dotenv
from customExpressionHandler import expressionHandler
from discordfunctions import get_user_info, get_guild_info

load_dotenv()
bot = commands.Bot(intents=discord.Intents.all(), command_prefix="p!")
TOKEN = os.getenv('TOKEN')

whitelist = [697959912302444614, 373266820792188928, 853754440509947914]
blacklist = []

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
async def runprogram(interaction: discord.Interaction, code: str):
    if interaction.user.id not in whitelist and interaction.user.id not in blacklist:
        await interaction.response.send_message("Sorry, you can't use this command", ephemeral=True)
        return
    
    print(interaction.user.display_name + ": " + code)

    handler = expressionHandler()

    splitcode = code.split(";")
    for segment in splitcode:
        try:
            handler.intereptExpression(segment)
        except Exception as e:
            print(e)
            await interaction.response.send_message("error :(", ephemeral=True)
            return
        
    await interaction.response.send_message(str(handler))

@bot.tree.command()
async def furry(interaction: discord.Interaction):
    #get furrylinks.txt
    with open("furrylinks.txt") as file:
        links = file.readlines()
        await interaction.response.send_message(links[random.randint(0, len(links)-1)])


@bot.command()
async def makemeasandwich(ctx):
    responses = ["Make it yourself.", "I'm not a butler.", "Poof! You're a sandwich!"]
    await ctx.send(responses[random.randint(0, len(responses)-1)])

bot.run(TOKEN)