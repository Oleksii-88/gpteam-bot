#!/bin/bash

# Установка Docker и docker-compose
setup_docker() {
    echo "Installing Docker and docker-compose..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
}

# Настройка файрвола
setup_firewall() {
    echo "Setting up firewall..."
    sudo apt-get update
    sudo apt-get install -y ufw
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 8000/tcp
    sudo ufw --force enable
}

# Установка Certbot для SSL
setup_ssl() {
    echo "Installing Certbot..."
    sudo apt-get install -y certbot python3-certbot-nginx
}

# Основной процесс установки
main() {
    # Обновление системы
    sudo apt-get update && sudo apt-get upgrade -y

    # Установка необходимых пакетов
    sudo apt-get install -y curl git

    # Установка Docker и docker-compose
    setup_docker

    # Настройка файрвола
    setup_firewall

    # Установка SSL
    setup_ssl

    echo "Installation complete!"
    echo "Now you can:"
    echo "1. Copy your project files to the server"
    echo "2. Run: docker-compose up -d"
    echo "3. Set up SSL with: sudo certbot --nginx"
}

main
