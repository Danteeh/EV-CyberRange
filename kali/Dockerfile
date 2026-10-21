# EV-CyberRange Kali Linux Attack Host
FROM kalilinux/kali-rolling:latest

ENV DEBIAN_FRONTEND=noninteractive

# Install packages
RUN apt-get update && apt-get install -y \
    xfce4 xfce4-terminal dbus-x11 \
    tigervnc-standalone-server tigervnc-tools \
    novnc websockify \
    nmap wireshark tshark tcpdump \
    ettercap-text-only netcat-openbsd socat hping3 \
    dsniff \
    mosquitto-clients \
    python3 python3-pip python3-venv \
    mitmproxy curl wget vim nano git jq \
    iputils-ping net-tools iproute2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python tools
RUN python3 -m venv /opt/attack-tools && \
    /opt/attack-tools/bin/pip install paho-mqtt scapy requests rich click

ENV PATH="/opt/attack-tools/bin:$PATH"

# Create directories
RUN mkdir -p /root/tools /root/captures /root/.vnc /root/.config/tigervnc

# VNC config
RUN echo "kaliattack" | tigervncpasswd -f > /root/.config/tigervnc/passwd && \
    chmod 600 /root/.config/tigervnc/passwd

# xstartup
RUN echo '#!/bin/bash\nexec startxfce4' > /root/.vnc/xstartup && \
    chmod +x /root/.vnc/xstartup

# Startup script
RUN echo '#!/bin/bash\n\
rm -rf /tmp/.X*-lock /tmp/.X11-unix/* 2>/dev/null\n\
export USER=root\n\
tigervncserver :1 -geometry 1920x1080 -depth 24 -SecurityTypes None --I-KNOW-THIS-IS-INSECURE\n\
websockify --web /usr/share/novnc 6080 localhost:5901 &\n\
sleep infinity' > /start.sh && chmod +x /start.sh

# Copy attack tools
COPY tools/ /root/tools/
RUN chmod +x /root/tools/*.py 2>/dev/null || true

WORKDIR /root
EXPOSE 5901 6080
CMD ["/start.sh"]
