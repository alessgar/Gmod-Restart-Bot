import valve.source
import valve.source.a2s
import valve.source.master_server
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
import asyncio
import os
import a2s

# Start Config

# The bot token
bot_token = 'bot token here'

# Threshold for activity alerts (ping when player count >= this number)
activity_thres = 5

# How many players will it have to go below the threshold to be able to ping again for activity
activity_gap_cooldown = 2

# What name you want to use for the screen
screen_name = "gmod"

# What arguments you want to start the server with
start_args = "bash -c \"cd /home/gmod/server;./srcds_run_x64 -game garrysmod -debug -condebug -console -port 27015\""

# Server Settings
server_address = "server.opifex.dev" # IP/Address of the server
server_port = 27015 # Port of the server

# Discord IDs
guild_id = 000000000000000000 # ID of the guild
status_channel_id = 000000000000000000 # ID of the channel you want crashes to be reported to
activity_alert_channel_id = 000000000000000000 # ID of the channel you want activity alerts posted to
activity_alert_role_id = 000000000000000000 # ID of the role you want activity alerts to ping
owner_id = 000000000000000000 # ID of who should be pinged in the event of a crash
restart_role_id = 000000000000000000 # ID of the role you want to be able to do restarts

guild_ids = [guild_id]

# End Config

description = '''Bot Description Here'''

intents = discord.Intents.all()
client = commands.Bot(command_prefix='/', description=description, intents=intents)

slash = SlashCommand(client, sync_commands=True)
restart_flag = False

@client.event
async def on_ready():
	global restart_flag
	restart_flag = False
	address = (server_address,server_port)
	failatt = 0
	crashed = False
	playerPingCheck = False
	
	os.system("screen -X -S " + screen_name + " quit")
	os.system("screen -dmS " + screen_name + " " + start_args)
	await client.change_presence(status=discord.Status.dnd,activity=discord.Game(name='Server Offline'))
	await asyncio.sleep(180)
	while True:
		try:
			server = a2s.info(address)
			player = a2s.players(address)
			players = []
			for player in a2s.players(address):
				if player and player.name:
					players.append(player)
			player_count = len(players)
			failatt = 0
			if(player_count==0):
				await client.change_presence(status=discord.Status.idle,activity=discord.Game(name="Online: " + str(player_count) + " Players"))
			else:
				await client.change_presence(status=discord.Status.online,activity=discord.Game(name="Online: " + str(player_count) + " Players"))
			if(player_count >= activity_thres and playerPingCheck==False):
				role = client.get_guild(guild_id).get_role(activity_alert_role_id)
				await client.get_channel(activity_alert_channel_id).send(f"{role.mention}"' Activity Alert! There are now 5+ players in-game.')
				playerPingCheck = True
			if(player_count <= (activity_thres - activity_gap_cooldown)):
				playerPingCheck = False
			if(restart_flag == True and player_count == 0):
				restart_flag = False
				await client.get_channel(status_channel_id).send('No more players are on the server, and there is a restart flag set! Killing server...')
				os.system("screen -X -S " + screen_name + " quit")
			if(crashed==True):
				await client.get_channel(status_channel_id).send('Server has recovered!')
				crashed = False
			print("A2S RESPONSE: {player_count}/{max_players} {server_name}".format(player_count=player_count, max_players=server.max_players, server_name=server.server_name))

		except Exception as e:
			print(e)
			print("Server {}:{} timed out!".format(*address))
			failatt = failatt + 1
			if(failatt >= 3):
				print("A2S RESPONSE FAILED! Killing and restarting process")
				restart_flag = False
				await client.change_presence(status=discord.Status.dnd,activity=discord.Game(name='Server Offline'))
				await client.get_channel(status_channel_id).send('<@' + str(owner_id) + '> Server has not responded in 30 seconds. Killing and restarting...')
				os.system("screen -X -S " + screen_name + " quit")
				os.system("screen -dmS " + screen_name + " " + start_args)
				failatt = 0
				crashed = True
				await asyncio.sleep(180)
		await asyncio.sleep(10)

@slash.slash(name="status",description="Query the Server Status.", guild_ids=guild_ids)
async def _status(ctx: SlashContext):
	global restart_flag
	address = (server_address,server_port)
	channel = ctx.channel
	await ctx.send(content='Querying...')
	try:
		server = a2s.info(address)
		players = []
		playerstr = "\n```\n"
		for player in a2s.players(address):
			if player and player.name:
				players.append(player)
				if (len(players) > 1):
					playerstr = playerstr + "\n" + player.name
				else:
					playerstr = playerstr + player.name
		playerstr = playerstr + "```"
		player_count = len(players)
		if (player_count > 0):
			await channel.send(content='Status: Online\nThere are currently ' + str(player_count) + ' players on the server.' + playerstr )
		else:
			await channel.send(content='Status: Online\nThere are currently 0 player(s) on the server.')
	except:
		await channel.send(content='Status: Offline')
			
@slash.slash(name="restart",description="Set a restart to occur when no players are on.", guild_ids=guild_ids)
async def _restart(ctx: SlashContext):
	global restart_flag
	role = client.get_guild(guild_id).get_role(restart_role_id)
	if(role in ctx.author.roles):
		if(restart_flag==True):
			restart_flag = False
			await ctx.send(content='Delayed restart cancelled.')
		else:
			restart_flag = True
			await ctx.send(content='Delayed restart set! The server will restart when no players are on the server!')
			
@slash.slash(name="forcerestart",description="Immediately restart the server.", guild_ids=guild_ids)
async def _forcerestart(ctx: SlashContext):
	global restart_flag
	role = client.get_guild(guild_id).get_role(restart_role_id)
	if(role in ctx.author.roles):
		restart_flag = False
		os.system("screen -X -S " + screen_name + " quit")
		await ctx.send(content='Forcing a restart! Killing server...')

client.run(bot_token)
