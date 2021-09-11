import valve.source
import valve.source.a2s
import valve.source.master_server
import discord
import asyncio
import os

# Start Config

# The bot token
bot_token = 'bot token here'

# Command that should be entered for server status (all lowercase)
status_command = "/status"

# Threshold for activity alerts (ping when player count >= this number)
activity_thres = 5

# What name you want to use for the screen
screen_name = "gmod"

# What arguments you want to start the server with
start_args = "bash -c \"cd /home/gmod/server;./srcds_run_x64 -game garrysmod -debug -condebug -console -port 27015\""

# Server Settings
server_address = "127.0.0.1" # IP/Address of the server
server_port = 27015 # Port of the server

# Discord IDs
guild_id = 00000000000000 # ID of the guild
status_channel_id = 00000000000000 # ID of the channel you want crashes to be reported to
activity_alert_channel_id = 00000000000000 # ID of the channel you want activity alerts posted to
activity_alert_role_id = 00000000000000 # ID of the role you want activity alerts to ping
owner_id = 00000000000000 # ID of who should be pinged in the event of a crash

# End Config

client = discord.Client()

@client.event
async def on_ready():
	address = (server_address,server_port)
	failatt = 0
	crashed = False
	playerPingCheck = False
	
	os.system("screen -X -S " + screen_name + " quit")
	os.system("screen -dmS " + screen_name + " " + start_args)
	await client.change_presence(activity=discord.Game(name='Server Offline'))
	await asyncio.sleep(180)
	while True:
		try:
			with valve.source.a2s.ServerQuerier(address) as server:
				info = server.info()
				players = []
				for player in server.players()["players"]:
					if player["name"]:
						players.append(player)
				player_count = len(players)
				failatt = 0
				await client.change_presence(activity=discord.Game(name="Online: " + str(player_count) + " Players"))
				if(player_count >= activity_thres and playerPingCheck==False):
					role = client.get_guild(guild_id).get_role(activity_alert_role_id)
					await client.get_channel(activity_alert_channel_id).send(f"{role.mention}"' Activity Alert! There are now 5+ players in-game.')
					playerPingCheck = True
				if(player_count < activity_thres):
					playerPingCheck = False
				if(crashed==True):
					await client.get_channel(status_channel_id).send('Server has recovered!')
					crashed = False
				print("A2S RESPONSE: {player_count}/{max_players} {server_name}".format(**info))

		except valve.source.NoResponseError:
			print("Server {}:{} timed out!".format(*address))
			failatt = failatt + 1
			if(failatt >= 3):
				print("A2S RESPONSE FAILED! Killing and restarting process")
				await client.change_presence(activity=discord.Game(name='Server Offline'))
				await client.get_channel(status_channel_id).send('<@' + str(owner_id) + '> Server has not responded in 30 seconds. Killing and restarting...')
				os.system("screen -X -S " + screen_name + " quit")
				os.system("screen -dmS " + screen_name + " " + start_args)
				failatt = 0
				crashed = True
				await asyncio.sleep(180)
		await asyncio.sleep(10)

@client.event
async def on_message(message):
	msg = message.content
	if (msg.lower().startswith(status_command)):
		address = (server_address,server_port)
		try:
			with valve.source.a2s.ServerQuerier(address) as server:
				info = server.info()
				players = []
				playerstr = "\n```\n"
				for player in server.players()["players"]:
					if player["name"]:
						players.append(player)
						if (len(players) > 1):
							playerstr = playerstr + "\n" + player["name"]
						else:
							playerstr = playerstr + player["name"]
				playerstr = playerstr + "```"
				player_count = len(players)
				if (player_count > 0):
					await message.channel.send('Status: Online\nThere are currently ' + str(player_count) + ' players on the server.' + playerstr )
				else:
					await message.channel.send('Status: Online\nThere are currently 0 player(s) on the server.')

		except valve.source.NoResponseError:
			await message.channel.send('Status: Offline' )

client.run(bot_token)
