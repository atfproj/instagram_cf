# Настройка VPN на продакшн сервере

## Вариант 1: Настроить systemd для автозапуска VPN

```bash
# Создать systemd service для VPN
sudo nano /etc/systemd/system/vpn-instagram.service
```

```ini
[Unit]
Description=VPN для Instagram
After=network.target

[Service]
Type=simple
ExecStart=/путь/к/vpn/клиенту --config /путь/к/конфигу
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Включить автозапуск
sudo systemctl enable vpn-instagram.service
sudo systemctl start vpn-instagram.service
sudo systemctl status vpn-instagram.service
```

## Вариант 2: Docker контейнеры через VPN

### Способ A: Весь Docker через VPN (проще)

```bash
# Перезапустить Docker после включения VPN
sudo systemctl restart docker

# Перезапустить контейнеры
cd /path/to/project
docker-compose down
docker-compose up -d
```

### Способ B: Маршрутизация только Instagram через VPN

```bash
# Создать маршрут только для Instagram IP
# Получаем IP Instagram
nslookup www.instagram.com

# Добавляем маршрут через VPN интерфейс
sudo ip route add 157.240.0.0/16 via <VPN_GATEWAY> dev <VPN_INTERFACE>
```

## Вариант 3: Использовать VPN в docker-compose

Обновить `docker-compose.yml`:

```yaml
services:
  app:
    image: your-app
    network_mode: "service:vpn"  # Использовать сеть VPN контейнера
    depends_on:
      - vpn

  vpn:
    image: dperson/openvpn-client
    cap_add:
      - NET_ADMIN
    devices:
      - /dev/net/tun
    volumes:
      - /path/to/vpn/config.ovpn:/vpn/vpn.conf
    environment:
      - VPN_CONFIG=/vpn/vpn.conf
```

## Проверка после настройки

```bash
# Проверить, что VPN работает
curl https://api.ipify.org  # Должен показать VPN IP

# Проверить доступ к Instagram
curl -I https://www.instagram.com

# Проверить в контейнере
docker exec -it instagram_cf_app curl -I https://www.instagram.com
```

## Мониторинг VPN

```bash
# Скрипт для проверки VPN и перезапуска при падении
# /usr/local/bin/check-vpn.sh
#!/bin/bash

VPN_IP="89.169.10.184"  # Ваш VPN IP
CURRENT_IP=$(curl -s https://api.ipify.org)

if [ "$CURRENT_IP" != "$VPN_IP" ]; then
    echo "VPN упал! Перезапускаем..."
    systemctl restart vpn-instagram.service
    sleep 10
    systemctl restart docker
fi
```

Добавить в cron:

```bash
# Проверять каждые 5 минут
*/5 * * * * /usr/local/bin/check-vpn.sh >> /var/log/vpn-monitor.log 2>&1
```


