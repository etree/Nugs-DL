# Nugs-DL
Tool written in Python to download streamable tracks from nugs.net.

**This is the initial version, so the following are NOT implemented yet:**
- CLI support    
- tagging customization    

![](https://thoas.feralhosting.com/sorrow/Nugs-DL/ss01.jpg)

# Setup
## Mandatory ##
The following field values need to be inputted into the config file:
- email
- password - in plain text
- quality - quality track to fetch from API. 1 = 16-bit FLAC, 2 = ALAC, 3 = VBR L4 AAC.

**You can't download ANY tracks with a free account.**

# Update Log #
### 5th July 19 - Release 1 ###

# Misc Info
- Written around Python v3.6.7.    
- The cookie to auth with the API will be caught from the login & subscriber info get requests.    
- Any special characters that your OS doesn't support in filenames will be replaced with "-".    
- Filename clashes will be handled inside of album folders. If a clash occurs inside an album folder, the previous file will be deleted.     
If you need to get in touch: Sorrow#5631, [Reddit](https://www.reddit.com/user/Sorrow446)

# Disclaimer
I will not be responsible for how you use Nugs-DL.    
Nugs brand and name is the registered trademark of its respective owner.    
Nugs-DL has no partnership, sponsorship or endorsement with Nugs.    
