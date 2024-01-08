import tkinter as tk
from tkinter import simpledialog, messagebox
import subprocess
import os
import sys
import shutil
import zipfile
import logging

# Setup logging
logging.basicConfig(filename='container_manager.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CONTAINERS_FOLDER = 'containers'
NETWORK_CONFIG_FILE = 'network_config.txt'
BACKUPS_FOLDER = 'backups'
CONFIG_FILE = 'config.txt'

# Setup config file and default values
DEFAULT_PORT = 8000
config = {
    'containers_folder': 'containers',
    'backups_folder': 'backups',
    'default_port': DEFAULT_PORT,
    'network_config_file': 'network_config.txt',
}

def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as config_file:
            lines = config_file.readlines()
            for line in lines:
                key, value = line.strip().split('=')
                config[key] = value
    except FileNotFoundError:
        pass  # Use default values if the config file doesn't exist
    except Exception as e:
        logging.error(f"Failed to load config: {str(e)}")

def save_config():
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as config_file:
            for key, value in config.items():
                config_file.write(f"{key}={value}\n")
    except Exception as e:
        logging.error(f"Failed to save config: {str(e)}")

def create_container():
    venv_name = simpledialog.askstring("Create Container", "Enter the name of the container (venv):")
    if venv_name:
        containers_path = os.path.join(os.getcwd(), config['containers_folder'])
        venv_path = os.path.join(containers_path, venv_name)

        try:
            subprocess.run([sys.executable, "-m", "venv", venv_path], check=True)
            messagebox.showinfo("Success", f"Container '{venv_name}' created successfully.")
            refresh_container_list()
        except subprocess.CalledProcessError:
            messagebox.showerror("Error", f"Failed to create container '{venv_name}'.")
            logging.error(f"Failed to create container '{venv_name}'.")

def delete_container():
    selected_container = containers_listbox.get(tk.ACTIVE)
    if not selected_container:
        messagebox.showerror("Error", "Please select a container (venv) from the list.")
        return

    venv_path = os.path.join(os.getcwd(), config['containers_folder'], selected_container)
    try:
        shutil.rmtree(venv_path)
        messagebox.showinfo("Success", f"Container '{selected_container}' deleted successfully.")
        refresh_container_list()
        remove_network_config(selected_container)
    except FileNotFoundError:
        messagebox.showerror("Error", f"Container '{selected_container}' not found.")
        logging.error(f"Container '{selected_container}' not found.")
    except OSError:
        messagebox.showerror("Error", f"Failed to delete container '{selected_container}'. Check if it's empty.")
        logging.error(f"Failed to delete container '{selected_container}'.")

def configure_network(config):
    selected_container = containers_listbox.get(tk.ACTIVE)
    if not selected_container:
        messagebox.showerror("Error", "Please select a container (venv) from the list.")
        return

    current_config = load_network_config(config)

    # Get network configuration parameters from the user
    ip_address = simpledialog.askstring("Network Configuration", f"Enter IP address for {selected_container} (optional):",
                                        initialvalue=current_config.get('ip', ''))
    port_number = simpledialog.askinteger("Network Configuration", f"Enter port number for {selected_container}:",
                                          initialvalue=current_config.get('port', config['default_port']))

    if port_number is not None:
        save_network_config(selected_container, ip_address, port_number, config)
        messagebox.showinfo("Success", f"Network configuration for container '{selected_container}' saved successfully.")
    else:
        messagebox.showerror("Error", "Please enter a valid port number.")

    # Refresh the list after configuring network
    refresh_container_list()

def backup_container():
    selected_container = containers_listbox.get(tk.ACTIVE)
    if not selected_container:
        messagebox.showerror("Error", "Please select a container (venv) from the list.")
        return

    backup_path = os.path.join(os.getcwd(), config['backups_folder'])
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)

    zip_filename = f"{selected_container}_backup.zip"
    zip_filepath = os.path.join(backup_path, zip_filename)
    container_path = os.path.join(os.getcwd(), config['containers_folder'], selected_container)
    network_config_path = os.path.join(container_path, NETWORK_CONFIG_FILE)

    try:
        with zipfile.ZipFile(zip_filepath, 'w') as zip_file:
            zip_file.write(container_path, arcname=os.path.basename(container_path))
            if os.path.exists(network_config_path):
                zip_file.write(network_config_path, arcname=NETWORK_CONFIG_FILE)

        messagebox.showinfo("Success", f"Backup for container '{selected_container}' created successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to create backup for container '{selected_container}': {str(e)}")
        logging.error(f"Failed to create backup for container '{selected_container}': {str(e)}")

def restore_container():
    selected_container = containers_listbox.get(tk.ACTIVE)
    if not selected_container:
        messagebox.showerror("Error", "Please select a container (venv) from the list.")
        return

    backup_path = os.path.join(os.getcwd(), config['backups_folder'])
    zip_filename = f"{selected_container}_backup.zip"
    zip_filepath = os.path.join(backup_path, zip_filename)
    container_path = os.path.join(os.getcwd(), config['containers_folder'], selected_container)
    network_config_path = os.path.join(container_path, NETWORK_CONFIG_FILE)

    try:
        with zipfile.ZipFile(zip_filepath, 'r') as zip_file:
            zip_file.extractall(container_path)

        messagebox.showinfo("Success", f"Container '{selected_container}' restored successfully.")
        refresh_container_list()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to restore container '{selected_container}': {str(e)}")
        logging.error(f"Failed to restore container '{selected_container}': {str(e)}")

def load_network_config(config):
    config_path = os.path.join(os.getcwd(), config['network_config_file'])
    network_config = {}

    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for line in lines:
                container, ip, port = line.strip().split(':')
                network_config[container] = {'ip': ip, 'port': int(port)}
    except FileNotFoundError:
        pass  # Return an empty dictionary if the file doesn't exist
    except Exception as e:
        logging.error(f"Failed to load network config: {str(e)}")

    return network_config

def save_network_config(container, ip, port, config):
    config_path = os.path.join(os.getcwd(), config['network_config_file'])

    with open(config_path, 'a', encoding='utf-8') as file:
        file.write(f"{container}:{ip}:{port}\n")

def remove_network_config(container):
    config_path = os.path.join(os.getcwd(), config['network_config_file'])

    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        with open(config_path, 'w', encoding='utf-8') as file:
            for line in lines:
                existing_container, _, _ = line.strip().split(':')
                if existing_container != container:
                    file.write(line)
    except FileNotFoundError:
        pass  # Ignore if the file doesn't exist
    except Exception as e:
        logging.error(f"Failed to remove network config for container '{container}': {str(e)}")

def edit_container():
    selected_container = containers_listbox.get(tk.ACTIVE)
    if not selected_container:
        messagebox.showerror("Error", "Please select a container (venv) from the list.")
        return

    container_path = os.path.join(os.getcwd(), CONTAINERS_FOLDER, selected_container)

    # Open the terminal emulator in the highlighted container directory
    try:
        terminal_emulator = get_default_terminal_emulator()
        subprocess.run([terminal_emulator], cwd=container_path)
    except FileNotFoundError:
        messagebox.showerror("Error", "Failed to open the terminal emulator.")

def get_default_terminal_emulator():
    # Function to get the default terminal emulator on Linux
    try:
        process = subprocess.Popen(['xdg-terminal', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        process.communicate()
        if process.returncode == 0:
            return 'xdg-terminal'
    except FileNotFoundError:
        pass  # Ignore if xdg-terminal is not found

    # Use a fallback option if xdg-terminal is not available
    return 'x-terminal-emulator'

def is_venv_active(venv_path):
    try:
        result = subprocess.run(["bash", "-c", f"source {venv_path}/bin/activate && echo 'Active'"], capture_output=True, text=True)
        return result.stdout.strip() == 'Active'
    except subprocess.CalledProcessError:
        return False

def refresh_container_list():
    containers_listbox.delete(0, tk.END)
    containers_path = os.path.join(os.getcwd(), config['containers_folder'])

    if not os.path.exists(containers_path):
        os.makedirs(containers_path)

    containers = [d for d in os.listdir(containers_path) if os.path.isdir(os.path.join(containers_path, d))]
    for container in containers:
        container_path = os.path.join(containers_path, container)
        is_active = is_venv_active(os.path.join(container_path, "venv"))
        status = "Active" if is_active else "Inactive"
        containers_listbox.insert(tk.END, f"{container} - {status}")

def main():
    global containers_listbox
    global root  # Add global declaration for root

    # Create the main window
    root = tk.Tk()
    root.title("Container Manager")
    root.geometry("800x600")

    # Apply a dark theme
    root.tk_setPalette(background="#282c34", foreground="white", activeBackground="#4e5a65", activeForeground="white")

    # Create menu bar
    menubar = tk.Menu(root)
    root.config(menu=menubar)

    # Load config
    load_config()

    # Create "Containers" menu
    containers_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Containers", menu=containers_menu)

    # Add submenu options
    containers_menu.add_command(label="Create Container", command=create_container)
    containers_menu.add_command(label="Delete Container", command=delete_container)
    containers_menu.add_command(label="Edit Container", command=edit_container)

    # Create "Network" menu
    network_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Network", menu=network_menu)

    # Add submenu options
    network_menu.add_command(label="Configure Network", command=lambda: configure_network(config))

    # Create "Backups" menu
    backups_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Backups", menu=backups_menu)

    # Add submenu options
    backups_menu.add_command(label="Backup", command=backup_container)
    backups_menu.add_command(label="Restore", command=restore_container)

    # Create a listbox to display containers
    containers_listbox = tk.Listbox(root, selectbackground="#4e5a65", selectforeground="white", bg="#282c34", fg="white")
    containers_listbox.pack(expand=True, fill=tk.BOTH)

    # Refresh container list
    refresh_container_list()

    # Start the Tkinter event loop
    root.mainloop()

if __name__ == "__main__":
    main()
