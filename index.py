from typing import Dict
import discord
import os
import random
import requests
import time
import pickle
import weakref

from PIL import Image
from io import BytesIO

from discord import app_commands
from discord.ext import tasks, commands
from discord.ext.commands import CommandOnCooldown
from dotenv import load_dotenv

furryblacklist = [1150221079021883442]

load_dotenv()
bot = commands.Bot(intents=discord.Intents.all(), command_prefix="p!")
TOKEN = os.getenv("TOKEN")

@bot.event
async def on_ready():
    print("ready")

    global furry_Users
    global banned_from_fursona

    try:
        furry_Users = load("variables/furry_Users.pickle")
    except:
        furry_Users = {}

    try:
        banned_from_fursona = load("variables/banfursona.pickle")
    except:
        banned_from_fursona = []

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)

@bot.event
async def on_message(message: discord.Message):
    await bot.process_commands(message)

    
    if (
        message.content.startswith("p!")
        or message.channel.id in furryblacklist
        or message.author.bot
        or message.channel.type != discord.ChannelType.text
        or message.attachments
    ):
        return

    if (
        message.author.id in furry_Users
        and message.guild.id in furry_Users[message.author.id].servers
    ):
        await message.delete()
        
        if message.guild.id in furry_Users[message.author.id].servers:
            user = furry_Users[message.author.id]

            # if a webhook doesn't exist, create one
            webhooks = await message.channel.webhooks()
            webhooks = [webhook for webhook in webhooks if webhook.user == bot.user]

            if len(webhooks) == 0:
                await message.channel.create_webhook(name="Pog Bot Proxy")

            webhooks = await message.channel.webhooks()
            webhooks = [webhook for webhook in webhooks if webhook.user == bot.user]
            webhook: discord.Webhook = webhooks[0]

            webhook = await webhook.edit(name=user.name, avatar=user.furryurl)

            if message.reference is not None:
                replied_message = await message.channel.fetch_message(
                    message.reference.message_id
                )

                if replied_message.content == "":
                    repliedcontent = "**Attachment**"
                else:
                    repliedcontent = replied_message.content

                embed = discord.Embed(
                    title="Reply to:",
                    url=replied_message.jump_url,
                    description=repliedcontent,
                )
                embed.set_author(
                    name=replied_message.author.name,
                    icon_url=replied_message.author.avatar,
                )

                last_message = await webhook.send(
                    message.content,
                    embed=embed,
                    allowed_mentions=discord.AllowedMentions.none(),
                    wait=True,
                )
                furry_Users[message.author.id].last_message = last_message.id
            else:
                if message.content != "":
                    last_message = await webhook.send(
                        message.content,
                        allowed_mentions=discord.AllowedMentions.none(),
                        wait=True,
                    )
                    furry_Users[message.author.id].last_message = last_message.id

@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def force_stop(interaction: discord.Interaction):
    await interaction.response.send_message("Resetting...", ephemeral=True)
    await bot.close()

@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def check_channel_descriptions(
    interaction: discord.Interaction, filter: str = ""
):
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
# Fursona Functions
# ----------------------------

def exclude_weak_refs(obj):
    # Recursively remove or replace weak references in the object
    if isinstance(obj, weakref.ReferenceType):
        return None  # Replace weak reference with None
    elif isinstance(obj, list):
        return [exclude_weak_refs(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: exclude_weak_refs(value) for key, value in obj.items()}
    elif isinstance(obj, tuple):
        return tuple(exclude_weak_refs(item) for item in obj)
    else:
        return obj

class FurryUser(commands.Bot):
    def __init__(self, furryurl, name, servers):
        self.furryurl = furryurl
        self.name = name
        self.servers = servers
        self.last_message = None

    def __str__(self):
        return f"{self.name}:{self.furryurl}:{self.servers}:{self.last_message}"

# Modify the save function
async def save(data, filepath):
    # Exclude weak references from data
    data = exclude_weak_refs(data)

    with open(filepath, "wb") as file:
        pickle.dump(data, file)


def load(filepath) -> Dict[int, FurryUser]:
    with open(filepath, "rb") as file:
        data = pickle.load(file)
    return data

@bot.tree.command()
@commands.check(lambda ctx: furry_Users[ctx.author.id].last_message is not None)
async def edit_last_message(interaction: discord.Interaction, content: str):
    """
    Edit your fursona's last message.
    """
    id = furry_Users[interaction.user.id].last_message

    # Fetch the message by ID
    message = await interaction.channel.fetch_message(id)

    # Fetch the webhook that sent the message
    webhook = await interaction.channel.webhooks()
    webhook = [webhook for webhook in webhook if webhook.user == bot.user][0]

    # Check if the message is a webhook message created by the bot
    if message.webhook_id and message.author.bot:
        # Edit the message content
        await webhook.edit_message(message.id, content=content)
        await interaction.response.send_message("Message edited", ephemeral=True)
    else:
        await interaction.response.send_message(
            "Cannot edit the message.", ephemeral=True
        )

@bot.tree.command()
@commands.check(lambda ctx: furry_Users[ctx.author.id].last_message is not None)
async def delete_last_message(interaction: discord.Interaction):
    """
    Delete your fursona's last message.
    """
    id = furry_Users[interaction.user.id].last_message
    # get webhook message by id
    message = await interaction.channel.fetch_message(id)

    await message.delete()
    await interaction.response.send_message("Message deleted", ephemeral=True)


@bot.tree.command()
async def create_fursona(
    interaction: discord.Interaction, furryurl: discord.Attachment, name: str
):
    """
    Create a fursona.
    """

    # Check if user is already furry
    if interaction.user.id in furry_Users:
        await interaction.response.send_message(
            "You already have a furry!", ephemeral=True
        )
        return

    if interaction.user.id in banned_from_fursona:
        await interaction.response.send_message(
            "You're banned from fursona!", ephemeral=True
        )
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
    furry_Users.update(
        {
            interaction.user.id: FurryUser(
                compressed_data.read(), name, [interaction.guild.id]
            )
        }
    )

    try:
        await save(furry_Users, "variables/furry_Users.pickle")
    except Exception as e:
        print(e)
        pass

    await interaction.response.send_message("furry created", ephemeral=True)


@bot.tree.command()
async def toggle_fursona(interaction: discord.Interaction):
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

    await save(furry_Users, "variables/furry_Users.pickle")

    await interaction.response.send_message(
        "Fursona toggled "
        + (
            "on"
            if interaction.guild.id in furry_Users[interaction.user.id].servers
            else "off"
        )
        + " in this server.",
        ephemeral=True,
    )


@bot.tree.command()
async def edit_fursona(
    interaction: discord.Interaction,
    furryurl: discord.Attachment = None,
    name: str = None,
):
    """
    Edit your fursona.
    """

    # Check if user is already furry
    if interaction.user.id not in furry_Users:
        await interaction.response.send_message("You're not a furry!", ephemeral=True)
        return

    if furryurl is None and name is None:
        await interaction.response.send_message(
            "You need to provide either a furryurl or a name.", ephemeral=True
        )
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
        await save(furry_Users, "variables/furry_Users.pickle")
    except:
        pass

    await interaction.response.send_message("Fursona edited.", ephemeral=True)


@bot.tree.command()
async def furry(interaction: discord.Interaction):
    """
    Display a random speechbubble furry.
    """
    if interaction.channel.id in furryblacklist:
        await interaction.response.send_message(
            "Sorry, you can't use this command here.", ephemeral=True
        )
        return

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

@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def debug_add_fursona(interaction: discord.Interaction, id: str, image : discord.Attachment, name: str):
    attachment_data = await image.read()

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
    
    furry_Users.update(
        {
            int(id): FurryUser(compressed_data.read(), name, [interaction.guild.id])
        }
    )
    await save(furry_Users, "variables/furry_Users.pickle")

    await interaction.response.send_message("Fursona added.", ephemeral=True)

@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def list_fursona(interaction: discord.Interaction):
    """
    Lists all current fursonas and their owners
    """
    # create a file, and add every user's fursona name and id to it
    with open("furryinfo.txt", "w") as file:
        for fursona in furry_Users:
            file.write(str(fursona) + " " + furry_Users[fursona].name + "\n")

    await interaction.response.send_message("Fursonas listed.", ephemeral=True)


@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def remove_fursona(interaction: discord.Interaction, userid: str):
    """
    Remove a fursona. Admin only.
    """

    userid = int(userid)

    if userid not in furry_Users:
        await interaction.response.send_message(
            "That user has no fursona.", ephemeral=True
        )
        return

    furry_Users.pop(userid)
    await save(furry_Users, "variables/furry_Users.pickle")

    await interaction.response.send_message("Removed fursona.", ephemeral=True)


@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def ban_user_from_fursona(interaction: discord.Interaction, userid: str):
    """
    Ban a user from fursona. Admin only.
    """

    userid = int(userid)
    if userid in furry_Users:
        furry_Users.pop(userid)
        await save(furry_Users, "variables/furry_Users.pickle")

    banned_from_fursona.append(userid)
    pickle.dump(banned_from_fursona, open("variables/banfursona.pickle", "wb"))

    await interaction.response.send_message("User banned from fursona.", ephemeral=True)


# command that sends the length of "furrylinks.txt" in terms of newlines
@bot.tree.command()
async def unique_furries(interaction: discord.Interaction):
    """
    see the number of unique furries pog bot can send.
    """
    with open("furrylinks.txt") as file:
        await interaction.response.send(f"{len(file.readlines())}")


@bot.tree.command()
@commands.check(lambda ctx: ctx.author.id == 697959912302444614)
async def create_furry_file(interaction: discord.Interaction):
    """
    Compose all the furries pog bot can send into a single file.
    """
    interaction.response.defer()

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

        await interaction.response.send("ran command")


bot.run(TOKEN)
