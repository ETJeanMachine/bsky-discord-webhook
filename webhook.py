import asyncio, aiohttp
import sys, json, time
from urllib.parse import *
from websockets.asyncio.client import connect

# opening our data file, parsing params, generating our websocket url.
with open("config.json", "r") as file:
    data = json.load(file)
query_params = urlencode(data["queryParams"], doseq=True)
websocket_url = f"wss://{data["jetstreamUrl"]}/subscribe?{query_params}"
discord_webhook = data["discordWebhook"]


def construct_payload(content: dict):
    did = content["did"]
    profile = profiles[did]
    commit = content["commit"]
    record = content["commit"]["record"]

    url = (
        f"https://bsky.app/profile/{did}/post/{commit["rkey"]}"
        if record["$type"] == "app.bsky.feed.post"
        else record["subject"]["uri"].replace("at://", "🔁\nhttps://bsky.app/profile/").replace("app.bsky.feed.", "")
    )

    payload = {
        "username": f"@{profile["handle"]}",
        "avatar_url": profile["avatar"],
        "content": url,
    }
    return payload


async def send(content: dict):
    async with aiohttp.ClientSession() as session:
        payload = construct_payload(content)
        params = {"wait": "true"}
        response = await session.post(discord_webhook, params=params, json=payload)
        resp_json = await response.json()
        print(resp_json)


async def handler():
    async with connect(websocket_url) as ws:
        while True:
            try:
                response = await ws.recv(decode=False)
                content = json.loads(response)
                if content["commit"]["operation"] == "create":
                    await send(content)
            except KeyboardInterrupt:
                exit(1)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                await asyncio.sleep(5)


async def main():
    # fetching the profiles of our DID's
    async with aiohttp.ClientSession() as session:
        actors = {"actors": data["queryParams"]["wantedDids"]}
        response = await session.get(
            "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfiles", params=actors
        )
        resp_json = await response.json()
        profile_list = resp_json["profiles"]
        global profiles
        profiles = {item["did"]: item for item in profile_list}
    await handler()


asyncio.run(main())
