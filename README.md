# arp-proxy-scapy
arp-proxy-scapy for overlapped networks

#### Пересечение сетей.
![net](https://github.com/Prototype-X/arp-proxy-scapy/blob/master/img/arp-proxy-scapy-1.png)

На интерфейсе роутера используется сеть 10.0.0.0/8 при этом на других интерфейсах этого же роутера используются куски из сети 10.0.0.0/8: 10.0.1.0/24 и 10.0.2.0/24. При этом в сети 10.0.0.0/8 нет ни одного хоста из сетей 10.0.1.0/24 и 10.0.2.0/24, эти сети как бы вырезаны из большой сети 10.0.0.0/8

#### Проблемы возникающие при пересечении сетей:
![trouble](https://github.com/Prototype-X/arp-proxy-scapy/blob/master/img/arp-proxy-scapy-2.png)

Проблема заключается в том что хосты из большой сети 10.0.0.0/8 не смогут общаться с хостами из сетей 10.0.1.0/24 и 10.0.2.0/24, так как хосты в сети 10.0.0.0/8 считают что находятся в одном широковещательном сегменте с сетями 10.0.1.0/24 и 10.0.2.0/24 и будут отправлять широковещательные arp запросы who-is для хостов из сетей 10.0.1.0/24 и 10.0.2.0/24 на которые будет не кому ответить.

Пример arp request/reply:

![arp-request](https://github.com/Prototype-X/arp-proxy-scapy/blob/master/img/arp-request.png)

![arp-reply](https://github.com/Prototype-X/arp-proxy-scapy/blob/master/img/arp-reply.png)

#### Решение проблемы коммуникации между хостами в пересекающихся сетях:

1. НИКОГДА НЕ СОЗДАВАТЬ ПЕРЕСЕЧЕНИЕ СЕТЕЙ!!!
2. Включить arp-proxy на интерфейсе роутера с сетью 10.0.0.0/8
3. private vlan + arp-proxy при этом на каждом порту свитча должен быть только один ip
4. ip unnumbered interface + arp-proxy + vlan
5. Написать свою arp-proxy (c блэкджеком и шлюхами)

Самое верное решение №1.
Самое простое решение №2 включить arp-proxy на интерфейсе роутера с сетью 10.0.0.0/8, но у разных вендоров arp-proxy может работать по разному. Например у Juniper arp-proxy имеет два режима работы: Restricted и Unrestricted.

* Restricted—The switch responds to ARP requests in which the physical networks of the source and target are different and does not respond if the source and target IP addresses are on the same subnet. In this mode, hosts on the same subnet communicate without proxy ARP. We recommend that you use this mode on the switch.
* Unrestricted—The switch responds to all ARP requests for which it has a route to the destination. This is the default mode (because it is the default mode in Juniper Networks Junos operating system (Junos OS) configurations other than those on the switch). We recommend using restricted mode on the switch.

У Cisco arp-proxy включена по умолчанию и ее режим работы аналогичен Restricted режиму у Juniper.

Arp-proxy в режиме Restricted ничем нам не поможет, так как IP адрес отправителя и IP адрес получателя будут в одной сети. Включение же arp-proxy в режиме Unrestricted решит проблему, но создаст другую, так как arp-proxy отвечает на любые запросы будет срабатывать механизм определения дублирующихся ip адресов. При отправке хостом сообщения gratuitous arp хост получит ответ от arp-proxy.

Варианты №3 и №4 сводятся к изоляции хостов одной сети друг от друга на уровне L2 и коммуникации между хостами через L3 интерфейс роутера и требуют внесения изменений в конфигурацию сетевого оборудования, а также имеют свои ограничения и особенности.

Вариант №5 кажется довольно не простым на первый взгляд. Для написанию своей arp-proxy используем python3 и scapy - инструмент для манипуляции сетевыми пакетами.

Подключим в сеть 10.0.0.0/8 новый хост с Linux на борту и запущенной arp-proxy, где будем перехватывать пакеты c arp-request в которых IP адрес запрашиваемого хоста попадает в сети 10.0.1.0/24 и 10.0.2.0/24 и отвечать на них arp-reply с указанием MAC адреса шлюза сети 10.0.0.0/8. В результате чего пакеты предназначенные для сетей 10.0.1.0/24 и 10.0.2.0/24 будут отправлены шлюзу сети 10.0.0.0/8 и доставлены адресату.

![Ok](https://github.com/Prototype-X/arp-proxy-scapy/blob/master/img/arp-proxy-scapy-3.png)

Пример лога arp-proxy.py:
```text
2017-03-12 00:35:00,984 INFO STDOUT: -----------------------------------
2017-03-12 00:35:00,985 INFO STDOUT: ARP receive:
2017-03-12 00:35:00,985 INFO STDOUT: -----------------------------------
2017-03-12 00:35:00,986 INFO STDOUT: ###[ Ethernet ]###
2017-03-12 00:35:00,986 INFO STDOUT:   dst       = ff:ff:ff:ff:ff:ff
2017-03-12 00:35:00,986 INFO STDOUT:   src       = e4:8d:8c:79:dc:2e
2017-03-12 00:35:00,986 INFO STDOUT:   type      = 0x806
2017-03-12 00:35:00,987 INFO STDOUT: ###[ ARP ]###
2017-03-12 00:35:00,987 INFO STDOUT:      hwtype    = 0x1
2017-03-12 00:35:00,987 INFO STDOUT:      ptype     = 0x800
2017-03-12 00:35:00,987 INFO STDOUT:      hwlen     = 6
2017-03-12 00:35:00,987 INFO STDOUT:      plen      = 4
2017-03-12 00:35:00,988 INFO STDOUT:      op        = who-has
2017-03-12 00:35:00,988 INFO STDOUT:      hwsrc     = e4:8d:8c:79:dc:2e
2017-03-12 00:35:00,988 INFO STDOUT:      psrc      = 10.0.0.100
2017-03-12 00:35:00,988 INFO STDOUT:      hwdst     = 00:00:00:00:00:00
2017-03-12 00:35:00,988 INFO STDOUT:      pdst      = 10.0.1.55
2017-03-12 00:35:00,988 INFO STDOUT: ###[ Padding ]###
2017-03-12 00:35:00,989 INFO STDOUT:         load      = '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
2017-03-12 00:35:00,989 INFO STDOUT: -----------------------------------
2017-03-12 00:35:00,989 INFO STDOUT: -----------------------------------
2017-03-12 00:35:00,989 INFO STDOUT: ARP send:
2017-03-12 00:35:00,989 INFO STDOUT: -----------------------------------
2017-03-12 00:35:00,989 INFO STDOUT: ###[ Ethernet ]###
2017-03-12 00:35:00,989 INFO STDOUT:   dst       = e4:8d:8c:79:dc:2e
2017-03-12 00:35:00,989 INFO STDOUT:   src       = 00:0c:29:85:7d:35
2017-03-12 00:35:00,990 INFO STDOUT:   type      = 0x806
2017-03-12 00:35:00,990 INFO STDOUT: ###[ ARP ]###
2017-03-12 00:35:00,990 INFO STDOUT:      hwtype    = 0x1
2017-03-12 00:35:00,990 INFO STDOUT:      ptype     = 0x800
2017-03-12 00:35:00,990 INFO STDOUT:      hwlen     = 6
2017-03-12 00:35:00,990 INFO STDOUT:      plen      = 4
2017-03-12 00:35:00,990 INFO STDOUT:      op        = is-at
2017-03-12 00:35:00,991 INFO STDOUT:      hwsrc     = 90:fa:3d:aa:bb:cc
2017-03-12 00:35:00,991 INFO STDOUT:      psrc      = 10.0.1.55
2017-03-12 00:35:00,991 INFO STDOUT:      hwdst     = e4:8d:8c:79:dc:2e
2017-03-12 00:35:00,991 INFO STDOUT:      pdst      = 10.0.0.100
2017-03-12 00:35:00,991 INFO STDOUT: -----------------------------------
```
#### Установка arp-proxy.py

В нашем окружении используем дистрибутив Ubuntu server 16.04 и модный systemd для запуска скрипта как сервис.

```text
mkdir /opt/arp-proxy
cp ~/arp-proxy.py /opt/arp-proxy/
```
Создадим файл с настройками для запуска скрипта systemd:
```text
touch /lib/systemd/system/arp-proxy.service
```
arp-proxy.service
```text
[Unit]
Description=arp-proxy for overlapped networks

[Service]
Type=simple
ExecStart=/opt/arp-proxy/arp-proxy.py eth0 00:05:00:05:00:05
StandardOutput=null
Restart=always

[Install]
WantedBy=multi-user.target
```
Активируем и запустим наш сервис:
```text
sudo systemctl enable arp-proxy.service
sudo systemctl start arp-proxy.service
```
Статус сервиса:
```text
sudo systemctl status arp-proxy.service
● arp-proxy.service - arp-proxy for overlapped networks
   Loaded: loaded (/lib/systemd/system/arp-proxy.service; enabled; vendor preset: enabled)
   Active: active (running) since Вс 2017-03-12 18:41:01 MSK; 7s ago
 Main PID: 10294 (python3)
    Tasks: 1
   Memory: 18.6M
      CPU: 981ms
   CGroup: /system.slice/arp-proxy.service
           └─10294 python3 /opt/arp-proxy/arp-proxy.py
```
[Управляем сервисами в systemd](https://www.digitalocean.com/community/tutorials/how-to-use-systemctl-to-manage-systemd-services-and-units)

#### scapy

Установка scapy:
```text
sudo pip3 install scapy-python3
```
[scapy documentation](https://scapy.readthedocs.io/en/latest/)

[scapy doc pdf](http://www.secdev.org/projects/scapy/files/scapydoc.pdf)
