import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import urllib.parse

def do_nothing() -> int:
	return 0

def install_package(package_name: str, package: str):
	print(f"Installing {package_name}...")
	try:
		_ = subprocess.run(["pip", "install", package], capture_output=True, text=True).returncode
		print(f"Installed {package_name} successfully.")
		return
	except:
		do_nothing()
	try:
		_ = subprocess.run(["pip3", "install", package], capture_output=True, text=True).returncode
		print(f"Installed {package_name} successfully.")
		return
	except:
		do_nothing()
	try:
		_ = subprocess.run(["python", "-m", "pip", "install", package], capture_output=True, text=True).returncode
		print(f"Installed {package_name} successfully.")
		return
	except:
		do_nothing()
	print(f"Failed to install {package_name}, please install it manually using this command:")
	print(f"  pip install {package}")
	exit()

try:
	import requests
except:
	install_package("Requests", "requests")
	import requests

try:
	import colorama
	from colorama import Fore
except:
	install_package("Colorama", "colorama")
	import colorama
	from colorama import Fore

colorama.init()

parser = argparse.ArgumentParser(description="xifil's HMW Updater")

# Define arguments as flags (no value expected)
parser.add_argument("-reverify", action="store_true", help="Reverify all files (recommended if you think you have corrupted game files)")
parser.add_argument("-showskipped", action="store_true", help="Print out files that have been skipped in the checking process in post-check summary")
parser.add_argument("-skipusermaps", action="store_true", help="Skip verification of hmw-usermaps")
parser.add_argument("-nolaunch", action="store_true", help="Don't launch HMW after updating/verifying")

# Parse the arguments
args = parser.parse_args()

arg_in_reverify = args.reverify
arg_in_show_skipped = args.showskipped
arg_in_skip_usermaps = args.skipusermaps
arg_in_no_launch = args.nolaunch

current_cr_line_len = 0
def sys_out(text: str, nl: str = "\n"):
	global current_cr_line_len
	cr_line_pad = ""
	previous_cr_line_len = current_cr_line_len
	if text.startswith("\r"):
		current_cr_line_len = len(text) - 1
		if previous_cr_line_len > current_cr_line_len:
			cr_line_pad = " " * (previous_cr_line_len - current_cr_line_len)
			cr_line_pad += "\b" * (previous_cr_line_len - current_cr_line_len)
	else:
		current_cr_line_len = 0
	sys.stdout.write(text + cr_line_pad + nl)
	sys.stdout.flush()

def get_input(text: str, expected: list[str], accept_empty: bool = False, ignore_case = True) -> str:
	buf = None
	while buf == None or buf == "":
		buf_temp = input(text)
		if len(buf_temp) < 1 and accept_empty:
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
	size_in_bytes = None
	content_size_str = ""
	if response_head.status_code == 200:
		content_size_str = ""
		content_length = response_head.headers.get("Content-Length")
		if content_length is not None:
			size_in_bytes = int(content_length)
			content_size_str = f" {Fore.LIGHTBLACK_EX}({format_size(size_in_bytes)}){Fore.RESET}"
	sys_out(f"Downloading \"{save_path}\"{content_size_str}...", nl="")
	# old download method, would get "stuck" (just really slow) because
	# there was no progress display and the server would keep dying
	# *** AT THE TIME OF TESTING, THAT IS ***
	"""
	response = requests.get(url)
	if response.status_code == 200:
		with open(save_path, "wb") as file:
			file.write(response.content)
		sys_out(f" -> {Fore.GREEN}ok{Fore.RESET}")
	else:
		sys_out(f" -> {Fore.RED}failed ({response.status_code}){Fore.RESET}")
	"""
	while True:
		try:
			response = requests.get(url, stream=True)
			if response.status_code == 200:
				total_bytes_written = 0
				with open(save_path, 'wb') as file:
					for chunk in response.iter_content(chunk_size=16 * 1024): # 16 KB chunk size, very fast
						file.write(chunk)
						total_bytes_written += len(chunk)

						if size_in_bytes is not None and size_in_bytes > 0:
							percent = (total_bytes_written / size_in_bytes) * 100
							size_done_str = f" {Fore.LIGHTBLACK_EX}({format_size(total_bytes_written)} / {format_size(size_in_bytes)}, {percent:.2f}%){Fore.RESET}"
							sys_out(f"\rDownloading \"{save_path}\"{size_done_str}...", nl="")
				sys_out(f"\rDownloading \"{save_path}\"{content_size_str}...", nl="")
				sys_out(f" -> {Fore.GREEN}ok{Fore.RESET}")
				break
			else:
				sys_out(f" -> {Fore.RED}failed ({response.status_code}){Fore.RESET}")
				break
		except:
			continue

sys_out(f"=--------------- Welcome ---------------=")
sys_out(f"  HMW Updater (one that actually works)  ")
sys_out(f"                {Fore.LIGHTRED_EX}by @lifix{Fore.RESET}                ")
sys_out(f"=---------------------------------------=")
sys_out(f"")

sys_out(f"=------------- System Info -------------=")
sys_out(f" Platform: {sys.platform}")
sys_out(f" Platform release: {platform.uname().release}")
sys_out(f"=---------------------------------------=")
sys_out(f"")

renamed_folders = {
	"h2m-mod": "hmw-mod",
	"h2m-usermaps": "hmw-usermaps"
}
renamed_files = {
	"h2m-mod.exe": "hmw-mod.exe",
	"hmw-mod\\zone\\de_h2m_common.ff": "hmw-mod\\zone\\de_hmw_common.ff",
	"hmw-mod\\zone\\eng_h2m_common.ff": "hmw-mod\\zone\\eng_hmw_common.ff",
	"hmw-mod\\zone\\h2m_ar1.ff": "hmw-mod\\zone\\hmw_ar1.ff",
	"hmw-mod\\zone\\h2m_attachments.ff": "hmw-mod\\zone\\hmw_attachments.ff",
	"hmw-mod\\zone\\h2m_clantags.ff": "hmw-mod\\zone\\hmw_clantags.ff",
	"hmw-mod\\zone\\h2m_files.ff": "hmw-mod\\zone\\hmw_files.ff",
	"hmw-mod\\zone\\h2m_killstreak.ff": "hmw-mod\\zone\\hmw_killstreak.ff",
	"hmw-mod\\zone\\h2m_killstreak.pak": "hmw-mod\\zone\\hmw_killstreak.pak",
	"hmw-mod\\zone\\h2m_launcher.ff": "hmw-mod\\zone\\hmw_launcher.ff",
	"hmw-mod\\zone\\h2m_launcher.pak": "hmw-mod\\zone\\hmw_launcher.pak",
	"hmw-mod\\zone\\h2m_launcher-extract.dat": "hmw-mod\\zone\\hmw_launcher-extract.dat",
	"hmw-mod\\zone\\h2m_patch_code_post_gfx_mp.ff": "hmw-mod\\zone\\hmw_patch_code_post_gfx_mp.ff",
	"hmw-mod\\zone\\h2m_patch_common_mp.ff": "hmw-mod\\zone\\hmw_patch_common_mp.ff",
	"hmw-mod\\zone\\h2m_patch_ui_mp.ff": "hmw-mod\\zone\\hmw_patch_ui_mp.ff",
	"hmw-mod\\zone\\h2m_post_gfx.ff": "hmw-mod\\zone\\hmw_post_gfx.ff",
	"hmw-mod\\zone\\h2m_post_gfx.pak": "hmw-mod\\zone\\hmw_post_gfx.pak",
	"hmw-mod\\zone\\h2m_pre_gfx.ff": "hmw-mod\\zone\\hmw_pre_gfx.ff",
	"hmw-mod\\zone\\h2m_rangers.ff": "hmw-mod\\zone\\hmw_rangers.ff",
	"hmw-mod\\zone\\h2m_rangers.pak": "hmw-mod\\zone\\hmw_rangers.pak",
	"hmw-mod\\zone\\h2m_shotgun.ff": "hmw-mod\\zone\\hmw_shotgun.ff",
	"hmw-mod\\zone\\h2m_smg.ff": "hmw-mod\\zone\\hmw_smg.ff",
	"hmw-mod\\zone\\rus_h2m_common.ff": "hmw-mod\\zone\\rus_hmw_common.ff",
	"hmw-mod\\zone\\spa_h2m_common.ff": "hmw-mod\\zone\\spa_hmw_common.ff",
	"players2\\user\\h2mcdta": "players2\\user\\hmwcdta",
	"players2\\user\\h2mdta": "players2\\user\\hmwdta"
}
game_executable = "hmw-mod.exe"
file_manifest_link = "https://price.horizonmw.org/manifest.json"
cached_files_manifest = "hmw-updater-cache.json"
stored_cache = {}
current_cache = {}
ignore_list = []

def should_file_be_ignored(file: str) -> bool:
	global ignore_list
	for ignored_file in ignore_list:
		if file.lower().startswith(ignored_file):
			return True
	return False

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
	if module["Name"] == "launcher":
		continue
	sys_out(f"{Fore.LIGHTBLACK_EX}Adding module \"{module['Name']}-{module['Version']}\" to verification list...{Fore.RESET}")
	for file_path, file_hash in module["FilesWithHashes"].items():
		for cached_module, cached_module_data in current_cache.items():
			cached_files_to_remove = []
			for cached_file, cached_file_hash in cached_module_data.items():
				if cached_file == file_path:
					cached_files_to_remove.append(cached_file)
			for cached_file_to_remove in cached_files_to_remove:
				current_cache[cached_module].pop(cached_file_to_remove)
	current_cache[f"{module['Name']}-{module['Version']}"] = {}
	for file_path, file_hash in module["FilesWithHashes"].items():
		current_cache[f"{module['Name']}-{module['Version']}"][file_path] = file_hash

for ignored_file in file_manifest["IgnorePaths"]:
	ignore_list.append(ignored_file.lower())

skip_cached_files = False

if os.path.exists(cached_files_manifest):
	with open(cached_files_manifest, "r") as file:
		stored_cache = json.load(file)
	# skip_cached_files_in = get_input("Would you like to skip verification of cached files? (Y/n): ", ["y", "n"], True)
	# skip_cached_files = skip_cached_files_in.lower() != "n"
	skip_cached_files = not arg_in_reverify

checked_files = []
missing_files = []
skipped_files = []
not_matching_files = []

# skip_user_maps_in = get_input("Would you like to skip verification of \"hmw-usermaps\"? (y/N): ", ["y", "n"], True)
# skip_user_maps = skip_user_maps_in.lower() == "y"
skip_user_maps = arg_in_skip_usermaps

def verify_files():
	global arg_in_show_skipped
	global current_cache
	global stored_cache
	global skip_cached_files
	global checked_files
	global missing_files
	global skipped_files
	global not_matching_files
	global skip_user_maps
	checked_files = []
	missing_files = []
	skipped_files = []
	not_matching_files = []
	for module_name, module in current_cache.items():
		for file_path, file_hash in module.items():
			if should_file_be_ignored(file_path):
				continue
			cached_hash = None
			if module_name in stored_cache:
				if file_path in stored_cache[module_name]:
					cached_hash = stored_cache[module_name][file_path]
			else:
				stored_cache[module_name] = {}
			file_path_sys = file_path
			if not is_windows():
				file_path_sys = file_path_sys.replace("\\", "/")
			if not os.path.isfile(file_path_sys) and file_path in stored_cache[module_name]:
				del stored_cache[module_name][file_path]
				cached_hash = None
			sys_out(f"{Fore.RESET}[{Fore.LIGHTCYAN_EX}{module_name}{Fore.RESET}] Checking {file_path}...", nl="")
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

	if arg_in_show_skipped:
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

verify_files()

has_downloaded_any_new_files = False
for module in file_manifest["Modules"]:
	module_name = f"{module['Name']}-{module['Version']}"
	download_path = module["DownloadInfo"]["DownloadPath"].rstrip("/").rstrip("\\")
	for file_path, file_hash in module["FilesWithHashes"].items():
		if should_file_be_ignored(file_path):
			continue
		if (not file_path in missing_files and not file_path in not_matching_files) or file_path in skipped_files:
			continue
		if module_name in stored_cache:
			if file_path in stored_cache[module_name]:
				del stored_cache[module_name][file_path]
		download_link = f"https://price.horizonmw.org/{download_path}/{urllib.parse.quote(file_path.replace('\\', '/'))}"
		download_file(download_link, file_path)
		has_downloaded_any_new_files = True

if has_downloaded_any_new_files:
	skip_cached_files = True
	verify_files()

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
	# open_game_in = get_input("Would you like to open the game? (Y/n): ", ["y", "n"], True)
	# open_game = open_game_in.lower() != "n"
	open_game = not arg_in_no_launch
	if open_game:
		subprocess.Popen(["cmd.exe", "/C", "start", game_executable])
		sys_out(f"{Fore.GREEN}Enjoy!{Fore.RESET}")
	else:
		sys_out(f"{Fore.GREEN}Goodbye!{Fore.RESET}")
else:
	sys_out(f"As you are not on Windows, the game can't be opened through here. Please run it in a Windows/Wine+Linux Build environment, and it should work.")
