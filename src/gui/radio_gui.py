"""Radio Server GUI Interface

Basic GUI for testing and controlling the Enhanced Radio Server.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import requests
import json
import os
import subprocess
import sys
import yaml
from datetime import datetime
from pathlib import Path

from src.config.config_manager import ConfigManager


class RadioServerGUI:
    def __init__(self, root):
        self.root = root
        self.config = ConfigManager()

        # Server connection
        self.base_url = f"http://localhost:{self.config.get('server.port', 5000)}"
        self.server_running = False

        self._setup_ui()
        self._start_status_checker()

    def _setup_ui(self):
        """Setup the user interface"""
        gui_config = self.config.get_gui_config()

        self.root.title(gui_config.get('window_title', 'Radio Server Control'))
        self.root.geometry(f"{gui_config.get('window_size', [800, 600])[0]}x{gui_config.get('window_size', [800, 600])[1]}")

        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Setup tabs
        self._setup_control_tab()
        self._setup_generation_tab()
        self._setup_content_tab()
        self._setup_logs_tab()
        self._setup_settings_tab()

    def _setup_control_tab(self):
        """Setup server control tab"""
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="Server Control")

        # Server Status
        status_frame = ttk.LabelFrame(control_frame, text="Server Status")
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = ttk.Label(status_frame, text="Status: Checking...", font=('Arial', 12, 'bold'))
        self.status_label.pack(pady=5)

        self.server_info_text = tk.Text(status_frame, height=6, width=80)
        self.server_info_text.pack(padx=10, pady=5)

        # Server Controls
        controls_frame = ttk.LabelFrame(control_frame, text="Controls")
        controls_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(controls_frame, text="Start Server", command=self._start_server).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(controls_frame, text="Stop Server", command=self._stop_server).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(controls_frame, text="Refresh Status", command=self._refresh_status).pack(side=tk.LEFT, padx=5, pady=5)

        # Scheduler Controls
        scheduler_frame = ttk.LabelFrame(control_frame, text="Scheduler")
        scheduler_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(scheduler_frame, text="Start Scheduler", command=self._start_scheduler).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(scheduler_frame, text="Stop Scheduler", command=self._stop_scheduler).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(scheduler_frame, text="Scheduler Status", command=self._check_scheduler).pack(side=tk.LEFT, padx=5, pady=5)

    def _setup_generation_tab(self):
        """Setup content generation tab"""
        gen_frame = ttk.Frame(self.notebook)
        self.notebook.add(gen_frame, text="Generate Content")

        # Ad Generation
        ad_frame = ttk.LabelFrame(gen_frame, text="Generate Advertisement")
        ad_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(ad_frame, text="Topic:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.ad_topic_var = tk.StringVar()
        self.ad_topic_combo = ttk.Combobox(ad_frame, textvariable=self.ad_topic_var, width=30)
        self.ad_topic_combo.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(ad_frame, text="Personality:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.ad_personality_var = tk.StringVar()
        self.ad_personality_combo = ttk.Combobox(ad_frame, textvariable=self.ad_personality_var, width=20)
        self.ad_personality_combo.grid(row=0, column=3, padx=5, pady=2)

        ttk.Button(ad_frame, text="Generate Ad", command=self._generate_ad).grid(row=0, column=4, padx=5, pady=2)

        # Conversation Generation
        conv_frame = ttk.LabelFrame(gen_frame, text="Generate Conversation")
        conv_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(conv_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.conv_host_var = tk.StringVar()
        self.conv_host_combo = ttk.Combobox(conv_frame, textvariable=self.conv_host_var, width=20)
        self.conv_host_combo.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(conv_frame, text="Guest:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.conv_guest_var = tk.StringVar()
        self.conv_guest_combo = ttk.Combobox(conv_frame, textvariable=self.conv_guest_var, width=20)
        self.conv_guest_combo.grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(conv_frame, text="Topic:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.conv_topic_var = tk.StringVar()
        self.conv_topic_combo = ttk.Combobox(conv_frame, textvariable=self.conv_topic_var, width=30)
        self.conv_topic_combo.grid(row=1, column=1, columnspan=2, padx=5, pady=2)

        ttk.Button(conv_frame, text="Generate Conversation", command=self._generate_conversation).grid(row=1, column=3, padx=5, pady=2)
        ttk.Button(conv_frame, text="Generate with Audio", command=self._generate_conversation_audio).grid(row=1, column=4, padx=5, pady=2)

        # Results
        results_frame = ttk.LabelFrame(gen_frame, text="Generation Results")
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.results_text = scrolledtext.ScrolledText(results_frame, height=15)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Audio Controls
        audio_frame = ttk.Frame(results_frame)
        audio_frame.pack(fill=tk.X, padx=10, pady=5)

        self.audio_file = None
        ttk.Button(audio_frame, text="Play Last Audio", command=self._play_audio).pack(side=tk.LEFT, padx=5)
        ttk.Button(audio_frame, text="Save Audio As...", command=self._save_audio).pack(side=tk.LEFT, padx=5)

    def _setup_content_tab(self):
        """Setup content management tab"""
        content_frame = ttk.Frame(self.notebook)
        self.notebook.add(content_frame, text="Content")

        # Topics
        topics_frame = ttk.LabelFrame(content_frame, text="Topics")
        topics_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.topics_text = scrolledtext.ScrolledText(topics_frame, height=8)
        self.topics_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Personalities
        personalities_frame = ttk.LabelFrame(content_frame, text="Personalities")
        personalities_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.personalities_text = scrolledtext.ScrolledText(personalities_frame, height=8)
        self.personalities_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Refresh button
        ttk.Button(content_frame, text="Refresh Content", command=self._load_content_info).pack(pady=5)

    def _setup_logs_tab(self):
        """Setup logs viewing tab"""
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs & History")

        # Generated Content
        generated_frame = ttk.LabelFrame(logs_frame, text="Generated Content")
        generated_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.generated_listbox = tk.Listbox(generated_frame, height=10)
        self.generated_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.generated_listbox.bind('<Double-Button-1>', self._view_generated_file)

        ttk.Button(generated_frame, text="Refresh Generated Content", command=self._load_generated_content).pack(pady=5)

        # Logs
        log_frame = ttk.LabelFrame(logs_frame, text="Server Logs")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def _setup_settings_tab(self):
        """Setup settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")

        # Configuration display
        config_frame = ttk.LabelFrame(settings_frame, text="Current Configuration")
        config_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.config_text = scrolledtext.ScrolledText(config_frame, height=20)
        self.config_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Config controls
        config_controls = ttk.Frame(settings_frame)
        config_controls.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(config_controls, text="Reload Config", command=self._load_config_display).pack(side=tk.LEFT, padx=5)
        ttk.Button(config_controls, text="Edit Config File", command=self._edit_config_file).pack(side=tk.LEFT, padx=5)

        self._load_config_display()

    def _start_status_checker(self):
        """Start periodic status checking"""
        self._refresh_status()
        # Schedule next check
        self.root.after(self.config.get('gui.auto_refresh_interval', 2000), self._start_status_checker)

    def _refresh_status(self):
        """Check server status"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=2)
            if response.status_code == 200:
                data = response.json()
                self.server_running = True
                self.status_label.config(text="Status: ✓ Running", foreground="green")

                info = f"""Server: {data.get('server', 'Unknown')}
Device: {data.get('tts_device', 'Unknown')}
Topics: {data.get('topics_loaded', 0)}
Personalities: {data.get('personalities_loaded', 0)}
Scheduler: {'Running' if data.get('scheduler_running') else 'Stopped'}
Time: {data.get('time', '')}
OpenRouter: {'Available' if data.get('openrouter_available') else 'Not Available'}"""

                self.server_info_text.delete(1.0, tk.END)
                self.server_info_text.insert(tk.END, info)
            else:
                self.server_running = False
                self.status_label.config(text="Status: ✗ Error", foreground="red")
        except:
            self.server_running = False
            self.status_label.config(text="Status: ✗ Not Running", foreground="red")
            self.server_info_text.delete(1.0, tk.END)
            self.server_info_text.insert(tk.END, "Server is not running or not accessible.")

        # Load content info if server is running
        if self.server_running:
            self._load_dropdown_data()

    def _load_dropdown_data(self):
        """Load topics and personalities for dropdowns"""
        try:
            # Load topics
            response = requests.get(f"{self.base_url}/topics", timeout=2)
            if response.status_code == 200:
                topics = response.json().get('topics', {})
                topic_names = list(topics.keys())
                self.ad_topic_combo['values'] = topic_names
                self.conv_topic_combo['values'] = topic_names

            # Load personalities
            response = requests.get(f"{self.base_url}/personalities", timeout=2)
            if response.status_code == 200:
                personalities = response.json().get('personalities', {})
                personality_names = [p['name'] for p in personalities.values()]
                self.ad_personality_combo['values'] = personality_names
                self.conv_host_combo['values'] = personality_names
                self.conv_guest_combo['values'] = personality_names
        except:
            pass

    def _generate_ad(self):
        """Generate an advertisement"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server is not running!")
            return

        params = {}
        if self.ad_topic_var.get():
            params['topic'] = self.ad_topic_var.get()
        if self.ad_personality_var.get():
            params['personality'] = self.ad_personality_var.get()

        try:
            response = requests.get(f"{self.base_url}/generate/dynamic_ad", params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                result = f"[{datetime.now().strftime('%H:%M:%S')}] AD GENERATED\n"
                result += f"Topic: {data.get('topic', 'Random')}\n"
                result += f"Personality: {data.get('personality', 'Unknown')}\n"
                result += f"Content: {data.get('content', 'No content')}\n"
                if 'audio_url' in data:
                    result += f"Audio: {data['audio_url']}\n"
                    self.audio_file = f"{self.base_url}{data['audio_url']}"
                result += "\n" + "="*60 + "\n"

                self.results_text.insert(tk.END, result)
                self.results_text.see(tk.END)
            else:
                messagebox.showerror("Error", f"Failed to generate ad: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def _generate_conversation(self):
        """Generate a conversation"""
        if not self.server_running:
            messagebox.showwarning("Warning", "Server is not running!")
            return

        params = {}
        if self.conv_host_var.get():
            params['host'] = self.conv_host_var.get()
        if self.conv_guest_var.get():
            params['guest'] = self.conv_guest_var.get()
        if self.conv_topic_var.get():
            params['topic'] = self.conv_topic_var.get()

        try:
            response = requests.get(f"{self.base_url}/generate/dynamic_conversation", params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                result = f"[{datetime.now().strftime('%H:%M:%S')}] CONVERSATION GENERATED\n"
                result += f"Host: {data.get('host', 'Unknown')}\n"
                result += f"Guest: {data.get('guest', 'Unknown')}\n"
                result += f"Topic: {data.get('topic', 'Random')}\n"
                result += f"Content:\n{data.get('content', 'No content')}\n"
                result += "\n" + "="*60 + "\n"

                self.results_text.insert(tk.END, result)
                self.results_text.see(tk.END)
            else:
                messagebox.showerror("Error", f"Failed to generate conversation: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def _generate_conversation_audio(self):
        """Generate conversation with audio using manual test script"""
        messagebox.showinfo("Info", "This will run the manual test script to generate conversation with audio.\nCheck the console for progress.")

        def run_test():
            try:
                subprocess.run(["python", "manual_test.py", "conversation"],
                             cwd=Path.cwd(), check=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to run audio generation: {e}")

        threading.Thread(target=run_test, daemon=True).start()

    def _play_audio(self):
        """Play the last generated audio file"""
        if not self.audio_file:
            messagebox.showwarning("Warning", "No audio file to play!")
            return

        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.audio_file)
            else:  # macOS/Linux
                subprocess.run(['open' if os.sys.platform == 'darwin' else 'xdg-open', self.audio_file])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to play audio: {e}")

    def _save_audio(self):
        """Save audio file to chosen location"""
        if not self.audio_file:
            messagebox.showwarning("Warning", "No audio file to save!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )

        if file_path:
            try:
                response = requests.get(self.audio_file)
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                messagebox.showinfo("Success", f"Audio saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save audio: {e}")

    def _start_server(self):
        """Start the server"""
        def start():
            try:
                subprocess.Popen(["python", "server.py"], cwd=Path.cwd())
                messagebox.showinfo("Info", "Server starting... Please wait a moment.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start server: {e}")

        threading.Thread(target=start, daemon=True).start()

    def _stop_server(self):
        """Stop the server (placeholder - would need process management)"""
        messagebox.showinfo("Info", "To stop the server, close the server console window or use Ctrl+C")

    def _start_scheduler(self):
        """Start the content scheduler"""
        try:
            response = requests.post(f"{self.base_url}/scheduler/start", timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("Success", "Scheduler started!")
            else:
                messagebox.showerror("Error", f"Failed to start scheduler: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def _stop_scheduler(self):
        """Stop the content scheduler"""
        try:
            response = requests.post(f"{self.base_url}/scheduler/stop", timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("Success", "Scheduler stopped!")
            else:
                messagebox.showerror("Error", f"Failed to stop scheduler: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def _check_scheduler(self):
        """Check scheduler status"""
        try:
            response = requests.get(f"{self.base_url}/scheduler/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = "Running" if data.get('running') else "Stopped"
                info = f"Status: {status}\nAd Interval: {data.get('ad_interval')}s\nConversation Interval: {data.get('conversation_interval')}s"
                messagebox.showinfo("Scheduler Status", info)
            else:
                messagebox.showerror("Error", f"Failed to get scheduler status: {response.text}")
        except Exception as e:
            messagebox.showerror("Error", f"Request failed: {e}")

    def _load_content_info(self):
        """Load content information"""
        if not self.server_running:
            return

        try:
            # Load topics
            response = requests.get(f"{self.base_url}/topics", timeout=5)
            if response.status_code == 200:
                topics = response.json().get('topics', {})
                topics_info = "TOPICS:\n\n"
                for name, topic in topics.items():
                    topics_info += f"• {topic['theme']}\n"
                    topics_info += f"  Description: {topic['description']}\n"
                    topics_info += f"  Products: {topic['product_count']}\n\n"

                self.topics_text.delete(1.0, tk.END)
                self.topics_text.insert(tk.END, topics_info)

            # Load personalities
            response = requests.get(f"{self.base_url}/personalities", timeout=5)
            if response.status_code == 200:
                personalities = response.json().get('personalities', {})
                personalities_info = "PERSONALITIES:\n\n"
                for name, personality in personalities.items():
                    personalities_info += f"• {personality['name']} ({personality['role']})\n"
                    personalities_info += f"  Voice: {personality['voice']}\n"
                    personalities_info += f"  Style: {personality['speaking_style']}\n"
                    personalities_info += f"  Catchphrases: {personality['catchphrases_count']}\n\n"

                self.personalities_text.delete(1.0, tk.END)
                self.personalities_text.insert(tk.END, personalities_info)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load content info: {e}")

    def _load_generated_content(self):
        """Load generated content list"""
        if not self.server_running:
            return

        try:
            response = requests.get(f"{self.base_url}/generated_content", timeout=5)
            if response.status_code == 200:
                data = response.json()
                files = data.get('generated_content', [])

                self.generated_listbox.delete(0, tk.END)
                for file_info in files:
                    display_name = f"{file_info['filename']} ({file_info['size']} bytes)"
                    self.generated_listbox.insert(tk.END, display_name)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load generated content: {e}")

    def _view_generated_file(self, event):
        """View selected generated file"""
        selection = self.generated_listbox.curselection()
        if not selection:
            return

        filename = self.generated_listbox.get(selection[0]).split(' (')[0]
        file_path = Path("generated_content") / filename

        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Show content in new window
                viewer_window = tk.Toplevel(self.root)
                viewer_window.title(f"Generated Content - {filename}")
                viewer_window.geometry("600x400")

                text_widget = scrolledtext.ScrolledText(viewer_window)
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_widget.insert(tk.END, content)
                text_widget.config(state=tk.DISABLED)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to read file: {e}")

    def _load_config_display(self):
        """Load and display current configuration"""
        try:
            config_text = yaml.dump(self.config.config, default_flow_style=False, indent=2)
            self.config_text.delete(1.0, tk.END)
            self.config_text.insert(tk.END, config_text)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display config: {e}")

    def _edit_config_file(self):
        """Open config file in system editor"""
        try:
            config_file = self.config.config_file
            if os.name == 'nt':  # Windows
                os.startfile(config_file)
            else:  # macOS/Linux
                subprocess.run(['open' if os.sys.platform == 'darwin' else 'xdg-open', config_file])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open config file: {e}")


def main():
    """Main GUI application"""
    root = tk.Tk()
    app = RadioServerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()