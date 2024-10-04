# cookiebot - tg-ytdlp-bot

support me on https://buymeacoffee.com/upekshaip

download private youtube/ videos using cookie file

## Full documentation available on - https://upekshaip.com/projects/-O0t36gRpfJR1p8KB7vU

## Deploy on VM

- First, You need to add your bot to the **logging channel** and **subscription channel**. Both are required.
- Give me a strar and fork this repository. Then change the **\_config.py** file to **config.py**
- Add your configuration for the **config.py** file.

#### Setup debian/any for docker

- ```sh
  sudo apt-get update
  ```
- ```sh
  sudo apt -y install apt-transport-https ca-certificates curl gnupg2 software-properties-common
  ```
- ```sh
  curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
  ```
- ```sh
  echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list
  ```
- ```sh
  sudo apt update
  ```
- ```sh
  sudo apt install -y docker-ce docker-ce-cli containerd.io
  ```
- ```sh
  docker -v
  ```

#### Setting the config.py file

- ```sh
  git clone https://github.com/upekshaip/tg-ytdlp-bot.git
  ```
- ```sh
  cd tg-ytdlp-bot
  ```
- ```sh
  sudo mv _config.py config.py
  ```
- ```sh
  nano config.py
  ```
- Now you can edit your config before the deployment
- After your edit process please follow as below

#### Install Dockerfile

- ```sh
  sudo docker build . -t tg-public-bot
  ```
- ```sh
  sudo docker ps -a
  ```
- ```sh
  sudo docker run tg-public-bot
  ```

### additions

- added Config obj for configurations
- can add custom name for playlist. 1st video will start "bla bla - Part 1" and so on.
  It must give a range if you need the custom name like -> (https://blabla.blaa*1*3*name)
- no need to give a range for videos for only one. simply give the url (https://blabla.blaa)
- if you give only a playlist url, bot will download the first video of that playlist.
- if you want to download a range of videos, give a specific rang like -> (https://blabla.blaa*1*3)

### User commands

- /check_cookie - Check cookie file
- /help - Help message
- /start - start the bot
- /clean - clean your working directory
- /usage - See your usage

### Admin commands

- start - Start the bot
- help - Send help text
- run_time - Show bot runtime
- log - Get user logs (ex: /log 10101010)
- broadcast - Send message to all users (You needs to reply any message with this command. then that message will be broadcasteds)
- clean - clean your working directory
- usage - Get all logs
- check_cookie - Check cookie file
- save_as_cookie - Save txt as cookie (save text as cookie)
- download_cookie - Download the cookie file
- block_user - Block user (ex: /block_user 10101010)
- unblock_user - Unblock user (ex: /unblock_user 10101010)
- all_users - Get all users
- all_blocked - Get all blocked users
- all_unblocked - Get all unblocked users

#### Link command pattern spec (Just send the link)

https://blabla.blaa

- download video with real name
- download only the 1st video of the playlist

https://blabla.blaa*1*3

- download the given range of playlist with real name

https://blabla.blaa*1*3*name

- download the given range of playlist with coustom name
- video names are like this ->
  - "name - Part 1"
  - "name - Part 2"

## Added new

- Added cookie download feature for each user
- added db per user

## TODO:

- Need to add custom formatter selector for download
- Need to add mp3 support
- Need to add Google drive support to store files
