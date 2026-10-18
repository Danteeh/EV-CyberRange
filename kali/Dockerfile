# EV-CyberRange Kali Linux Attack Host
# Custom image with EV charging attack tools pre-installed

FROM kalilinux/kali-rolling:latest

LABEL maintainer="EV-CyberRange Lab"
LABEL description="Kali Linux attack host for EV charging security research"

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1
ENV VNC_PORT=5901
ENV NOVNC_PORT=6080

# Update and install base tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    # VNC and desktop
    xfce4 \
    xfce4-terminal \
    dbus-x11 \
    tigervnc-standalone-server \
    tigervnc-common \
    novnc \
    websockify \
    # Network tools
    nmap \
    wireshark \
    tshark \
    tcpdump \
    ettercap-text-only \
    arpwatch \
    dsniff \
    netcat-openbsd \
    socat \
    hping3 \
    # MQTT tools
    mosquitto-clients \
    # Python for custom tools
    python3 \
    python3-pip \
    python3-venv \
    python3-scapy \
    # Web/proxy tools
    mitmproxy \
    # General utilities
    curl \
    wget \
    vim \
    nano \
    git \
    jq \
    iputils-ping \
    net-tools \
    iproute2 \
    procps \
    # Clean up
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create Python virtual environment for attack tools
RUN python3 -m venv /opt/attack-tools
ENV PATH="/opt/attack-tools/bin:$PATH"

# Install Python attack libraries
RUN /opt/attack-tools/bin/pip install --no-cache-dir \
    paho-mqtt \
    scapy \
    requests \
    colorama \
    rich \
    click

# Create directory structure
RUN mkdir -p /root/tools \
             /root/captures \
             /root/logs \
             /root/evidence \
             /root/.vnc

# VNC password (change in production!)
RUN echo "kaliattack" | vncpasswd -f > /root/.vnc/passwd && \
    chmod 600 /root/.vnc/passwd

# Copy custom attack tools
COPY tools/ /root/tools/
RUN chmod +x /root/tools/*.py 2>/dev/null || true
RUN chmod +x /root/tools/*.sh 2>/dev/null || true

# VNC startup script
RUN echo '#!/bin/bash\n\
rm -rf /tmp/.X1-lock /tmp/.X11-unix/X1 2>/dev/null\n\
vncserver :1 -geometry 1920x1080 -depth 24\n\
websockify --web /usr/share/novnc $NOVNC_PORT localhost:$VNC_PORT &\n\
tail -f /root/.vnc/*.log\n' > /root/start-vnc.sh && \
    chmod +x /root/start-vnc.sh

# xstartup for VNC
RUN echo '#!/bin/bash\n\
unset SESSION_MANAGER\n\
unset DBUS_SESSION_BUS_ADDRESS\n\
exec startxfce4\n' > /root/.vnc/xstartup && \
    chmod +x /root/.vnc/xstartup

# Working directory
WORKDIR /root

# Expose ports
EXPOSE 5901 6080

# Default command: start VNC and noVNC
CMD ["/root/start-vnc.sh"]
