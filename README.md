# BlueSky to Discord Webhook

This is a very basic webhook ping-pong server - it listens on the [BlueSky Jetstream](https://github.com/bluesky-social/jetstream) service for certain commits - reposts, posts - and then forwards them to a specified webhook in a Discord Server.

To set up this project, create a new virtual environment. This project was built using `python3.13`, so please use this version or newer.

Run the below to set up a virtual environment on unix-based systems:

```bash
python3.13 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

Set up a `data.json` file by copying [`data_example.json`](data_example.json) into a new file. Then, set the `discordWebhook` variable to the URL of the discord webhook ([steps 0 through 1 of this tutorial to find the URL](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)), and set the `wantedDids` variable to the [DID's](https://docs.bsky.app/docs/advanced-guides/resolving-identities) of the BlueSky accounts you wish to forward. You can find the DID of your accounts via a service such as [PDSls](https://pdsls.dev). You can between 1 and 100 BlueSky accounts for this to work.

Then, to run the project as a background process:

```bash
python webhook.py &
```
