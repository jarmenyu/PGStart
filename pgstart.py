#!/usr/bin/env python3

import subprocess
from paramiko import SSHClient, AutoAddPolicy, RSAKey
import sys
import jinja2

def generate_inventory(primary_server, secondary_server):
    template_loader = jinja2.FileSystemLoader(searchpath="./")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("inventory.yml.j2")
    inventory_content = template.render(primary_ip=primary_server, secondary_ip=secondary_server)

    with open("inventory.yml", "w") as f:
        f.write(inventory_content)
    print("Инвентарь для Ansible сгенерирован")

def run_ansible_playbook():
    result = subprocess.run(
        ["ansible-playbook", "-i", "inventory.yml", "playbook.yml"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Ошибка выполнения Ansible: {result.stderr}")
        sys.exit(1)
    print("Ansible playbook выполнен успешно")

def check_load(server):
    key_path = "/home/arslan/.ssh/id_rsa"
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())
    try:
        private_key = RSAKey.from_private_key_file(key_path)
        client.connect(server, username="root", pkey=private_key, timeout=10)
        inp, out, err = client.exec_command("uptime")
        value = out.read().decode().replace(",", ".").replace(":", ".").split('. ')[-2]
        client.close()
        return float(value)
    except Exception as e:
        print(f"Error on servak {server}: {str(e)}")
        return float('inf')


def pick_server(server_list):
    loads = {}
    for server in server_list:
        loads[server] = check_load(server)
        print(f"Нагрузка сервера {server}: {loads[server]}")
    sorted_servers = sorted(loads.items(), key=lambda x: x[1])
    if (len(sorted_servers) != 2):
        print("Не смогли получить данные от серверов")
        sys.exit(1)
    print(f"Целевой сервер: {sorted_servers[0][0]}")
    return sorted_servers[0][0], sorted_servers[1][0]

def main(input_servers):
    servers = input_servers.split(',')
    if len(servers) != 2:
        print("Нужно указать 2 сервера")
        sys.exit(1)
    print("Запуск установки")
    primary_server, secondary_server = pick_server(servers)
    generate_inventory(primary_server, secondary_server)
    run_ansible_playbook()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Нужно написать 2 хоста")
        sys.exit(1)
    main(sys.argv[1])