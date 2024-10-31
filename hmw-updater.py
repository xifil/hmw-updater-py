import hashlib
import json
import os
import platform
import subprocess
import sys
import urllib.parse

try:
	import requests
except:
	print("Installing Requests...")
	res = subprocess.run(["pip", "install", "requests"], capture_output=True, text=True).returncode
	try:
		import requests
		print("Installed Requests successfully.")
	except:
		print("Failed to install Requests, please install it manually using this command:")
		print("  pip install requests")
		exit()

try:
	import colorama
	from colorama import Fore
except:
	print("Installing Colorama...")
	res = subprocess.run(["pip", "install", "colorama"], capture_output=True, text=True).returncode
	try:
		import colorama
		from colorama import Fore
		print("Installed Colorama successfully.")
	except:
		print("Failed to install Colorama, please install it manually using this command:")
		print("  pip install colorama")
		exit()

colorama.init()

def sys_out(text: str, nl: str = "\n"):
	sys.stdout.write(text + nl)
	sys.stdout.flush()

def get_input(text: str, expected: list[str], accept_empty: bool = False, ignore_case = True) -> str:
	buf = None
	while buf == None or buf == "":
		buf_temp = input(text)
		if len(buf_temp) < 1:
			return buf_temp
		for expected_item in expected:
			if (ignore_case and buf_temp.lower() == expected_item.lower()) or (not ignore_case and buf_temp == expected_item):
				buf = buf_temp
				break
	return buf

def format_size(size) -> str:
	if size == 0:
		return "0 B"
	size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	i = int(min(max(0, size.bit_length() // 10), len(size_name) - 1))
	p = 1024 ** i
	s = round(size / p, 2)
	return f"{s} {size_name[i]}"

def is_windows() -> bool:
	return sys.platform.startswith('win')

def download_file(url, save_path_in):
	save_path = save_path_in
	if not is_windows():
		save_path = save_path.replace("\\", "/")
	parent_dir = os.path.dirname(save_path)
	if len(parent_dir) > 0:
		os.makedirs(os.path.dirname(save_path), exist_ok=True)
	response_head = requests.head(url)
	if response_head.status_code == 200:
		content_size_str = ""
		content_length = response_head.headers.get("Content-Length")
		if content_length is not None:
			size_in_bytes = int(content_length)
			content_size_str = f" {Fore.LIGHTBLACK_EX}({format_size(size_in_bytes)}){Fore.RESET}"
		sys_out(f"Downloading \"{save_path}\"{content_size_str}...", nl="")
	else:
		sys_out(f"Downloading \"{save_path}\"...", nl="")
	response = requests.get(url)
	if response.status_code == 200:
		with open(save_path, "wb") as file:
			file.write(response.content)
		sys_out(f" -> {Fore.GREEN}ok{Fore.RESET}")
	else:
		sys_out(f" -> {Fore.RED}failed ({response.status_code}){Fore.RESET}")

sys_out(f"=---------------------------------------=")
sys_out(f"  HMW Updater (one that actually works)  ")
sys_out(f"                {Fore.LIGHTRED_EX}by @lifix{Fore.RESET}                ")
sys_out(f"=---------------------------------------=")
sys_out(f"")

renamed_folders = {
	"h2m-mod": "hmw-mod",
	"h2m-usermaps": "hmw-usermaps"
}
renamed_files = {
	"h2m-mod.exe": "hmw-mod.exe",
	"players2\\user\\h2mcdta": "players2\\user\\hmwcdta",
	"players2\\user\\h2mdta": "players2\\user\\hmwdta"
}
game_executable = "hmw-mod.exe"
file_manifest_link = "https://price.horizonmw.org/manifest.json"
cached_files_manifest = "hmw-updater-cache.json"
stored_cache = {}
current_cache = {}

for old_name_in, new_name_in in renamed_folders.items():
	old_name = old_name_in
	new_name = new_name_in
	if not is_windows():
		old_name = old_name.replace("\\", "/")
		new_name = new_name.replace("\\", "/")
	if os.path.isdir(old_name) and not os.path.isdir(new_name):
		sys_out(f"{Fore.LIGHTBLACK_EX}Renaming \"{old_name}\" to \"{new_name}\"...{Fore.RESET}")
		os.rename(old_name, new_name)

for old_name_in, new_name_in in renamed_files.items():
	old_name = old_name_in
	new_name = new_name_in
	if not is_windows():
		old_name = old_name.replace("\\", "/")
		new_name = new_name.replace("\\", "/")
	if os.path.isfile(old_name) and not os.path.isfile(new_name):
		sys_out(f"{Fore.LIGHTBLACK_EX}Renaming \"{old_name}\" to \"{new_name}\"...{Fore.RESET}")
		os.rename(old_name, new_name)

file_manifest = {}
file_manifest_response = requests.get(file_manifest_link)
if file_manifest_response.status_code == 200:
	file_manifest = file_manifest_response.json()
	sys_out(f"{Fore.GREEN}Obtained file manifest.{Fore.RESET}")
else:
	sys_out(f"{Fore.LIGHTRED_EX}Failed to obtain file manifest. ({file_manifest_response.status_code}){Fore.RESET}")
	exit()

for module in file_manifest["Modules"]:
	current_cache[module["Name"]] = {}
	sys_out(f"{Fore.LIGHTBLACK_EX}Adding module \"{module["Name"]}\" to verification list...{Fore.RESET}")
	for file_path, file_hash in module["FilesWithHashes"].items():
		current_cache[module["Name"]][file_path] = file_hash

skip_cached_files = False

if os.path.exists(cached_files_manifest):
	with open(cached_files_manifest, "r") as file:
		stored_cache = json.load(file)
	skip_cached_files_in = get_input("Would you like to skip verification of cached files? (Y/n): ", ["y", "n"], True)
	skip_cached_files = skip_cached_files_in.lower() != "n"

checked_files = []
missing_files = []
skipped_files = []
not_matching_files = []

skip_user_maps_in = get_input("Would you like to skip verification of \"hmw-usermaps\"? (y/N): ", ["y", "n"], True)
skip_user_maps = skip_user_maps_in.lower() == "y"

for module_name, module in current_cache.items():
	for file_path, file_hash in module.items():
		cached_hash = None
		if module_name in stored_cache:
			if file_path in stored_cache[module_name]:
				cached_hash = stored_cache[module_name][file_path]
		else:
			stored_cache[module_name] = {}
		file_path_sys = file_path
		if not is_windows():
			file_path_sys = file_path_sys.replace("\\", "/")
		sys_out(f"Checking {file_path}...", nl="")
		if not os.path.isfile(file_path_sys):
			missing_files.append(file_path)
			sys_out(f" -> {Fore.RED}missing{Fore.RESET}")
			continue
		if (skip_user_maps and "hmw-usermaps\\" in file_path) or (skip_cached_files and cached_hash != None and file_hash == cached_hash):
			skipped_files.append(file_path)
			sys_out(f" -> {Fore.LIGHTBLACK_EX}skipped{Fore.RESET}")
			continue
		current_file_hash = hashlib.sha256(open(file_path_sys, "rb").read()).hexdigest()
		stored_cache[module_name][file_path] = current_file_hash
		if file_hash == current_file_hash:
			sys_out(f" -> {Fore.GREEN}ok{Fore.RESET}")
		else:
			sys_out(f" -> {Fore.YELLOW}incorrect{Fore.RESET}")
			not_matching_files.append(file_path)
		checked_files.append(file_path)

sys_out(f"Checked {len(checked_files)} file{'' if len(checked_files) == 1 else 's'}")

if len(skipped_files) > 0:
	sys_out("\nSkipped:")
for skipped_file in skipped_files:
	sys_out(f" - {Fore.LIGHTBLACK_EX}{skipped_file}{Fore.RESET}")

if len(missing_files) > 0:
	sys_out("\nMissing:")
for missing_file in missing_files:
	sys_out(f" - {Fore.RED}{missing_file}{Fore.RESET}")

if len(not_matching_files) > 0:
	sys_out("\nIncorrect:")
for not_matching_file in not_matching_files:
	sys_out(f" - {Fore.YELLOW}{not_matching_file}{Fore.RESET}")

for module in file_manifest["Modules"]:
	download_path = module["DownloadInfo"]["DownloadPath"].rstrip("/").rstrip("\\")
	for file_path, file_hash in module["FilesWithHashes"].items():
		if (not file_path in missing_files and not file_path in not_matching_files) or file_path in skipped_files:
			continue
		download_link = f"https://price.horizonmw.org/{download_path}/{urllib.parse.quote(file_path.replace('\\', '/'))}"
		download_file(download_link, file_path)

with open(cached_files_manifest, "w") as file:
	json.dump(stored_cache, file, indent="\t")

if "wine" in platform.uname().release.lower() or not is_windows():
	sys_out("I've detected you aren't running the updater on a Windows device.")
	download_linux_in = get_input("Would you like to download the Linux-compatible build of hmw-mod.exe? (Y/n): ", ["y", "n"], True)
	download_linux = download_linux_in.lower() != "n"
	if download_linux:
		github_repo_linux = "MichaelDeets/HorizonMW-Client"
		github_manifest_link = f"https://api.github.com/repos/{github_repo_linux}/releases/latest"
		github_manifest = {}
		github_manifest_response = requests.get(github_manifest_link)
		if github_manifest_response.status_code == 200:
			github_manifest = github_manifest_response.json()
			sys_out(f"{Fore.GREEN}Obtained GitHub manifest.{Fore.RESET}")
		else:
			sys_out(f"{Fore.LIGHTRED_EX}Failed to obtain GitHub manifest. ({github_manifest_response.status_code}){Fore.RESET}")
			exit()
		if "tag_name" not in github_manifest:
			sys_out(f"{Fore.LIGHTRED_EX}GitHub manifest is invalid.")
			exit()
		download_file(f"https://github.com/{github_repo_linux}/releases/download/{github_manifest['tag_name']}/hmw-mod.exe", game_executable)

sys_out("My job here is done. GLHF.")

if is_windows():
	open_game_in = get_input("Would you like to open the game? (Y/n): ", ["y", "n"], True)
	open_game = open_game_in.lower() != "n"
	if open_game:
		res = subprocess.run(["cmd.exe", "/C", "start", game_executable], capture_output=True, text=True).returncode
		sys_out(f"{Fore.GREEN}Enjoy!{Fore.RESET}")
	else:
		sys_out(f"{Fore.GREEN}Goodbye!{Fore.RESET}")
else:
	sys_out(f"As you are not on Windows, the game can't be opened through here. Please run it in a Windows/Wine+Linux Build environment, and it should work.")
