import asyncio, aiohttp, atproto
import sys, json
from atproto_client import AsyncClient
from atproto import AtUri
from urllib.parse import *
from dateutil import parser
from discord import Webhook, Embed, ButtonStyle, Color
from discord.ui import Button, View
from websockets.asyncio.client import connect

# opening our data file, parsing params, generating our websocket url.
with open("config.json", "r") as file:
    data = json.load(file)
bsky_color = Color.from_str("#1283fe")
client = AsyncClient("https://public.api.bsky.app")


def get_at_uri(content):
    did = content["did"]
    collection = content["commit"]["collection"]
    rkey = content["commit"]["rkey"]
    return AtUri.from_str(f"at://{did}/{collection}/{rkey}")


async def construct_embeds(
    at_uri: AtUri,
    profile: atproto.models.AppBskyActorDefs.ProfileViewDetailed,
    is_repost: bool,
):
    response = await client.get_post(at_uri.rkey, at_uri.host)
    post = response.value
    author = await client.get_profile(at_uri.host)
    author_url = f"https://bsky.app/profile/{author.handle}"
    profile_url = f"https://bsky.app/profile/{profile.handle}"
    link_url = f"{author_url}/post/{at_uri.rkey}"
    timestamp = parser.parse(post.created_at)
    embed = Embed(
        color=bsky_color,
        description=post.text,
        timestamp=timestamp,
        url=link_url,
    )
    if is_repost:
        embed.add_field(
            name=":repeat: Reposted by",
            value=f"[@{profile.handle}]({profile_url})",
            inline=False,
        )
    embed.set_author(
        name=f"{author.display_name} (@{author.handle})",
        icon_url=author.avatar,
        url=author_url,
    )
    embed.set_footer(
        text="BlueSky",
        icon_url="https://bsky.app/static/apple-touch-icon.png",
    )
    embeds = [embed]
    if post.embed is not None:
        match post.embed.py_type:
            case "app.bsky.embed.images":
                for image in post.embed.images:
                    blob = image.image.ref.link
                    image_url = f"https://cdn.bsky.app/img/feed_fullsize/plain/{author.did}/{blob}"
                    image_embed = embed.copy()
                    image_embed.set_image(url=image_url)
                    embeds.append(image_embed)
            case "app.bsky.embed.video":
                pass
            case "app.bsky.embed.record":
                pass
            case "app.bsky.embed.recordWithMedia":
                pass
            case "app.bsky.embed.external":
                pass
    return embeds


async def send(content: dict):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(data["discordWebhook"], session=session)
        profile = await client.get_profile(content["did"])
        is_repost = False
        match content["commit"]["collection"]:
            case "app.bsky.feed.post":
                at_uri = get_at_uri(content)
            case _:
                at_uri = AtUri.from_str(content["commit"]["record"]["subject"]["uri"])
                is_repost = True
        embeds = await construct_embeds(at_uri, profile, is_repost)
        await webhook.send(
            embeds=embeds,
            username=f"{profile.display_name} (@{profile.handle})",
            avatar_url=profile.avatar,
            # view=view,
            wait=True,
        )


async def main():
    query_params = urlencode(data["queryParams"], doseq=True)
    websocket_url = f"wss://{data["jetstreamUrl"]}/subscribe?{query_params}"
    async with connect(websocket_url) as ws:
        print("Connected and listening...")
        while True:
            try:
                response = await ws.recv(decode=False)
                content = json.loads(response)
                if content["commit"]["operation"] == "create":
                    await send(content)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
