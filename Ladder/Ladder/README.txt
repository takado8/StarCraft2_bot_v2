1. Move the 'Maps' folder to "C:/Program Files (x86)/StarCraft II/".
   For more maps use the !maps command on our discord or download them here https://github.com/Blizzard/s2client-proto#map-packs
   Remember to put the map files directly in /Maps/.
2. To add your bot, make a directory in the 'Bots' folder that is named exactly as your bot. Put your bot files inside this subfolder. You also need to create a LadderBots.json file. Follow the example configurations that are in the example bots corresponding to the API you use. It should look similar to this:

{
  "Bots": {
    "CppBot": {
      "Race": "Protoss",
      "Type": "BinaryCpp",
      "RootPath": "./",
      "FileName": "CppBot.exe",
      "Debug": true,
      "SurrenderPhrase": "pineapple"
    }
  }
}

3. Execute LadderGUI.exe.
4. Select the matches you want to play.
5. Get more bots: Some bots can be downloaded on http://sc2ai.net/

Additional requirements:
For pythonBot games python-sc2 must be installed first. I used anaconda for this. https://github.com/Dentosal/python-sc2
For ocraft bots you need to install Java 9 or newer.

Troubleshooting:
-After you press "Generate & Run" a console window opens but closes immediately. Nothing happens after that.
	Make sure the folder in Bots/ for your bot has exactly the same name you have given it in the LadderBots.json file. Try again. You can also start the ladder manager executable ('Ladder/Sc2LadderServer.exe') from a console and check if all maps and all bots are found.
-Your bot bot crashes immediately:
	Usually stderr is written to a log file inside the bot directory. Maybe you can find the error there. If not set the debug option in the LadderBots.json file to true. Now stdout is also written to file. Hopefully, you find the problem there.
-The two SC2 screens stay black:
	Go to Documents/StarCraft II/ and rename Variables.txt to Variables_old.txt. Start the normal SC2 client once. Try again. Be careful to not delete the Variables.txt in case you are playing the game. Those are the settings used ingame (scroll speed, language, etc).
-Anything else:
	Don't hesitate and ask on our Discord https://discord.gg/qTZ65sh
-My antivirus complains:
	Never trust executables from strangers. You can get a second opinion for example from here: https://www.virustotal.com (never trust links from strangers :P) But in the end it is your call if you want to execute them.
	
Suggestions for improvements? Please make a github issue here: https://github.com/Cryptyc/Sc2LadderServer/issues