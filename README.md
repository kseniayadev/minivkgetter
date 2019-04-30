# minivkgetter
Simple example of use VK API. This project is going to increments, but in other idea

# Usage

Firstly, install all requirements

After, run in terminal cli.py

Then, type this commands:
- **localcreate**
- **settoken <your_service_vk_token>**
- **activatetestmode** ; (if you dont enable app)

This commands setup a server. For get information you can use two commands:
- **online <user_id>** --- this command show online status
- **watch <user_id> online** --- this command add user to list. It will be update when you run *update* command

(Now only online status for open pages (for all) supported)

All information about watching store in *~/.vkgetter/<uid>/online* in format 
  <timestamp>,<last_seen>,<online>

For stop a server type **shutdown**
