#!/usr/bin/env python3
#
# Copyright 2022 joshpatten
# Copyright 2024-2026 jbergquist
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# MODIFICATIONS from original:
# - 2024-2026: Flask port, modern web interface, packaging (jbergquist)
# - 2026: Added localhost HTTPS with self-signed certificates (commit cf999ac)
"""
Proxmox VDI Client - Modern Web Interface
A Flask-based web client for Proxmox VE Virtual Desktop Infrastructure.
Compatible with PVE 7, 8, and 9.
"""

import os
import sys
import json
import random
import subprocess
import argparse
import webbrowser
import urllib3
from configparser import ConfigParser
from io import StringIO
import time
from threading import Thread
import logging

from vdiclient.platform import Platform
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash,
    send_file,
)
import proxmoxer
import requests

# Flask app with template/static paths in vdiclient package
_package_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vdiclient")
logger = logging.getLogger(__name__)
app = Flask(
    __name__,
    template_folder=os.path.join(_package_dir, "templates"),
    static_folder=os.path.join(_package_dir, "static"),
)
app.secret_key = os.urandom(32)


class G:
    """Global application state."""

    spiceproxy_conv = {}
    proxmox = None
    icon = None
    vvcmd = None
    inidebug = False
    addl_params = None
    imagefile = None
    kiosk = False
    viewer_kiosk = True
    fullscreen = True
    show_reset = False
    show_hibernate = False
    current_hostset = "DEFAULT"
    title = "VDI Login"
    hosts = {}
    theme = "LightBlue"
    guest_type = "both"
    width = None
    height = None
    authenticated = False
    session_timeout = 0  # seconds, 0 = disabled
    server_shutdown_timeout = 0  # seconds, 0 = disabled
    last_activity_time = None  # timestamp of last user activity
    server_start_time = None  # timestamp when server started
    localhosttls = False  # Enable HTTPS on localhost with self-signed cert
    ssl_cert_path = None  # Path to generated certificate
    ssl_key_path = None  # Path to generated private key
    log_level = None  # Log level from ini file (overridden by CLI/env)


def loadconfig(
    config_location=None,
    config_type="file",
    config_username=None,
    config_password=None,
    ssl_verify=True,
):
    """Load configuration from file or HTTP source."""
    config = ConfigParser(delimiters="=")

    if config_type == "file":
        if config_location:
            if not os.path.isfile(config_location):
                logger.error("Configuration file not found: %s", config_location)
                return False
        else:
            # Use platform abstraction for config paths
            config_list = Platform.get_config_search_paths()
            for location in config_list:
                if os.path.exists(location):
                    config_location = location
                    break
            if not config_location:
                logger.error("No configuration file found in any default location")
                return False
        try:
            config.read(config_location)
        except Exception:
            logger.exception("Unable to read configuration file")
            return False

    elif config_type == "http":
        if not config_location:
            logger.error("--config_type http requires --config_location URL")
            return False
        try:
            if config_username and config_password:
                r = requests.get(
                    url=config_location,
                    auth=(config_username, config_password),
                    verify=ssl_verify,
                )
            else:
                r = requests.get(url=config_location, verify=ssl_verify)
            config.read_string(r.text)
        except Exception:
            logger.exception(
                "Unable to read configuration from URL: %s", config_location
            )
            return False

    if "General" not in config:
        logger.error("No [General] section defined in configuration")
        return False

    general = config["General"]
    if "title" in general:
        G.title = general["title"]
    if "theme" in general:
        G.theme = general["theme"]
    if "icon" in general:
        if os.path.exists(general["icon"]):
            G.icon = general["icon"]
    if "logo" in general:
        if os.path.exists(general["logo"]):
            G.imagefile = general["logo"]
    if "kiosk" in general:
        G.kiosk = general.getboolean("kiosk")
    if "viewer_kiosk" in general:
        G.viewer_kiosk = general.getboolean("viewer_kiosk")
    if "fullscreen" in general:
        G.fullscreen = general.getboolean("fullscreen")
    if "inidebug" in general:
        G.inidebug = general.getboolean("inidebug")
    if "guest_type" in general:
        G.guest_type = general["guest_type"]
    if "show_reset" in general:
        G.show_reset = general.getboolean("show_reset")
    if "window_width" in general:
        G.width = general.getint("window_width")
    if "window_height" in general:
        G.height = general.getint("window_height")

    if "session_timeout" in general:
        G.session_timeout = general.getint("session_timeout")
        if G.session_timeout < 0:
            logger.warning("session_timeout cannot be negative, setting to 0")
            G.session_timeout = 0

    if "server_shutdown_timeout" in general:
        G.server_shutdown_timeout = general.getint("server_shutdown_timeout")
        if G.server_shutdown_timeout < 0:
            logger.warning("server_shutdown_timeout cannot be negative, setting to 0")
            G.server_shutdown_timeout = 0

    if "localhosttls" in general:
        G.localhosttls = general.getboolean("localhosttls")

    if "log_level" in general:
        G.log_level = general["log_level"]

    if "Authentication" in config:  # Legacy configuration
        G.hosts["DEFAULT"] = _default_hostset()
        if "Hosts" not in config:
            logger.error("No [Hosts] section defined in configuration")
            return False
        for key in config["Hosts"]:
            G.hosts["DEFAULT"]["hostpool"].append(
                {"host": key, "port": int(config["Hosts"][key])}
            )
        auth = config["Authentication"]
        _parse_host_options(G.hosts["DEFAULT"], auth)
    else:  # New style multi-cluster config
        i = 0
        for section in config.sections():
            if section.startswith("Hosts."):
                _, group = section.split(".", 1)
                if i == 0:
                    G.current_hostset = group
                G.hosts[group] = _default_hostset()
                try:
                    hostjson = json.loads(config[section]["hostpool"])
                except Exception:
                    logger.exception("Could not parse hostpool in [%s]", section)
                    return False
                for key, value in hostjson.items():
                    G.hosts[group]["hostpool"].append({"host": key, "port": int(value)})
                _parse_host_options(G.hosts[group], config[section])
                i += 1

    if "SpiceProxyRedirect" in config:
        for key in config["SpiceProxyRedirect"]:
            G.spiceproxy_conv[key] = config["SpiceProxyRedirect"][key]
    if "AdditionalParameters" in config:
        G.addl_params = {}
        for key in config["AdditionalParameters"]:
            G.addl_params[key] = config["AdditionalParameters"][key]
    return True


def _default_hostset():
    """Return a default host configuration dictionary."""
    return {
        "hostpool": [],
        "backend": "pve",
        "user": "",
        "token_name": None,
        "token_value": None,
        "totp": False,
        "verify_ssl": True,
        "pwresetcmd": None,
        "auto_vmid": None,
        "knock_seq": [],
    }


def _parse_host_options(hostset, section):
    """Parse host options from a config section into a hostset dict."""
    if "auth_backend" in section:
        hostset["backend"] = section["auth_backend"]
    if "user" in section:
        hostset["user"] = section["user"]
    if "token_name" in section:
        hostset["token_name"] = section["token_name"]
    if "token_value" in section:
        hostset["token_value"] = section["token_value"]
    if "auth_totp" in section:
        hostset["totp"] = section.getboolean("auth_totp")
    if "tls_verify" in section:
        hostset["verify_ssl"] = section.getboolean("tls_verify")
    if "pwresetcmd" in section:
        hostset["pwresetcmd"] = section["pwresetcmd"]
    if "auto_vmid" in section:
        hostset["auto_vmid"] = section.getint("auto_vmid")
    if "knock_seq" in section:
        try:
            hostset["knock_seq"] = json.loads(section["knock_seq"])
        except Exception:
            logger.warning("Knock sequence not valid JSON, skipping", exc_info=True)


def setcmd():
    """Find the virt-viewer / remote-viewer command."""
    try:
        G.vvcmd = Platform.find_virt_viewer()
    except RuntimeError as e:
        logger.error("virt-viewer not found: %s", e)
        sys.exit(1)


def pveauth(username, passwd=None, totp=None):
    """Authenticate against Proxmox VE. Returns (connected, authenticated, error)."""
    hostset = G.hosts[G.current_hostset]
    random.shuffle(hostset["hostpool"])
    err = None

    # Suppress InsecureRequestWarning when SSL verification is disabled
    if not hostset["verify_ssl"]:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    for hostinfo in hostset["hostpool"]:
        host = hostinfo["host"]
        port = hostinfo.get("port", 8006)
        try:
            if hostset["token_name"] and hostset["token_value"]:
                G.proxmox = proxmoxer.ProxmoxAPI(
                    host,
                    user=f"{username}@{hostset['backend']}",
                    token_name=hostset["token_name"],
                    token_value=hostset["token_value"],
                    verify_ssl=hostset["verify_ssl"],
                    port=port,
                )
            elif totp:
                G.proxmox = proxmoxer.ProxmoxAPI(
                    host,
                    user=f"{username}@{hostset['backend']}",
                    otp=totp,
                    password=passwd,
                    verify_ssl=hostset["verify_ssl"],
                    port=port,
                )
            else:
                G.proxmox = proxmoxer.ProxmoxAPI(
                    host,
                    user=f"{username}@{hostset['backend']}",
                    password=passwd,
                    verify_ssl=hostset["verify_ssl"],
                    port=port,
                )
            return True, True, None
        except proxmoxer.backends.https.AuthenticationError as e:
            return True, False, e
        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
        ) as e:
            err = e
    return False, False, err


def getvms(listonly=False):
    """Get list of VMs from Proxmox cluster."""
    vms = []
    try:
        online_nodes = []
        for node in G.proxmox.cluster.resources.get(type="node"):
            if node.get("status") == "online":
                online_nodes.append(node["node"])

        for vm in G.proxmox.cluster.resources.get(type="vm"):
            if vm["node"] not in online_nodes:
                continue
            if vm.get("template"):
                continue
            if G.guest_type == "both" or G.guest_type == vm["type"]:
                if listonly:
                    vms.append(
                        {"vmid": vm["vmid"], "name": vm["name"], "node": vm["node"]}
                    )
                else:
                    vms.append(vm)
        return vms
    except proxmoxer.core.ResourceException:
        logger.exception("Error getting VMs")
        return []
    except requests.exceptions.ConnectionError:
        logger.exception("Connection error querying Proxmox")
        return []


def process_vms(vms):
    """Process raw VM data into a clean format for the frontend."""
    processed = []
    for vm in vms:
        if vm.get("status") == "unknown":
            continue
        state = "stopped"
        disabled = False
        if vm.get("status") == "running":
            if "lock" in vm:
                state = vm["lock"]
                if state in ("suspending", "suspended"):
                    disabled = True
                    if state == "suspended":
                        state = "starting"
            else:
                state = "running"
        processed.append(
            {
                "vmid": vm["vmid"],
                "name": vm["name"],
                "node": vm["node"],
                "type": vm["type"],
                "state": state,
                "disabled": disabled,
            }
        )
    return processed


def vmaction(vmnode, vmid, vmtype, action="connect"):
    """Perform a VM action: connect or reload (reset)."""
    try:
        if vmtype == "qemu":
            vmstatus = G.proxmox.nodes(vmnode).qemu(str(vmid)).status.get("current")
        else:
            vmstatus = G.proxmox.nodes(vmnode).lxc(str(vmid)).status.get("current")
    except Exception:
        logger.exception("Unable to get VM status for %s on node %s", vmid, vmnode)
        return {"success": False, "error": "Unable to get VM status"}

    if action == "reload":
        # Stop the VM
        try:
            if vmtype == "qemu":
                jobid = (
                    G.proxmox.nodes(vmnode).qemu(str(vmid)).status.stop.post(timeout=28)
                )
            else:
                jobid = (
                    G.proxmox.nodes(vmnode).lxc(str(vmid)).status.stop.post(timeout=28)
                )
        except proxmoxer.core.ResourceException:
            logger.exception("Unable to stop VM %s on node %s", vmid, vmnode)
            return {"success": False, "error": "Unable to stop VM"}

        # Wait for stop to complete
        stopped = False
        for _ in range(30):
            try:
                jobstatus = G.proxmox.nodes(vmnode).tasks(jobid).status.get()
            except (
                proxmoxer.core.ResourceException,
                requests.exceptions.ConnectionError,
            ) as e:
                logger.debug(
                    "Transient error polling stop-job status for VM %s: %s",
                    vmid,
                    e,
                )
                jobstatus = {}
            if "exitstatus" in jobstatus:
                if jobstatus["exitstatus"] != "OK":
                    return {"success": False, "error": "Unable to stop VM"}
                stopped = True
                break
            time.sleep(1)
        if not stopped:
            return {"success": False, "error": "Timeout waiting for VM to stop"}

    # Refresh status
    try:
        if vmtype == "qemu":
            vmstatus = G.proxmox.nodes(vmnode).qemu(str(vmid)).status.get("current")
        else:
            vmstatus = G.proxmox.nodes(vmnode).lxc(str(vmid)).status.get("current")
    except Exception:
        logger.exception("Unable to refresh VM status for %s on node %s", vmid, vmnode)
        return {"success": False, "error": "Unable to get VM status"}

    # Start VM if not running
    if vmstatus["status"] != "running":
        try:
            if vmtype == "qemu":
                jobid = (
                    G.proxmox.nodes(vmnode)
                    .qemu(str(vmid))
                    .status.start.post(timeout=28)
                )
            else:
                jobid = (
                    G.proxmox.nodes(vmnode).lxc(str(vmid)).status.start.post(timeout=28)
                )
        except proxmoxer.core.ResourceException:
            logger.exception("Unable to start VM %s on node %s", vmid, vmnode)
            return {"success": False, "error": "Unable to start VM"}

        started = False
        for _ in range(30):
            try:
                jobstatus = G.proxmox.nodes(vmnode).tasks(jobid).status.get()
            except (
                proxmoxer.core.ResourceException,
                requests.exceptions.ConnectionError,
            ) as e:
                logger.debug(
                    "Transient error polling start-job status for VM %s: %s",
                    vmid,
                    e,
                )
                jobstatus = {}
            if "exitstatus" in jobstatus:
                if jobstatus["exitstatus"] != "OK":
                    return {"success": False, "error": "Unable to start VM"}
                started = True
                break
            time.sleep(1)
        if not started:
            return {"success": False, "error": "Timeout waiting for VM to start"}

    if action == "reload":
        return {"success": True, "message": f'{vmstatus["name"]} reset successfully'}

    # Connect via SPICE
    try:
        if vmtype == "qemu":
            spiceconfig = G.proxmox.nodes(vmnode).qemu(str(vmid)).spiceproxy.post()
        else:
            spiceconfig = G.proxmox.nodes(vmnode).lxc(str(vmid)).spiceproxy.post()
    except proxmoxer.core.ResourceException:
        logger.exception(
            "Unable to connect to VM %s on node %s via SPICE", vmid, vmnode
        )
        return {
            "success": False,
            "error": (
                f"Unable to connect to VM {vmid}. " "Is SPICE display configured?"
            ),
        }

    # Build virt-viewer configuration
    confignode = ConfigParser()
    confignode["virt-viewer"] = {}
    for key, value in spiceconfig.items():
        if key == "proxy":
            val = value[7:].lower()
            if val in G.spiceproxy_conv:
                confignode["virt-viewer"][key] = f"http://{G.spiceproxy_conv[val]}"
            else:
                confignode["virt-viewer"][key] = f"{value}"
        else:
            confignode["virt-viewer"][key] = f"{value}"

    if G.addl_params:
        for key, value in G.addl_params.items():
            confignode["virt-viewer"][key] = f"{value}"

    inifile = StringIO("")
    confignode.write(inifile)
    inifile.seek(0)
    inistring = inifile.read()

    if G.inidebug:
        logger.debug("SPICE Config:\n%s", inistring)

    # Launch virt-viewer
    pcmd = [G.vvcmd]
    if G.kiosk and G.viewer_kiosk:
        pcmd.extend(["--kiosk", "--kiosk-quit", "on-disconnect"])
    elif G.fullscreen:
        pcmd.append("--full-screen")
    pcmd.append("-")

    process = subprocess.Popen(pcmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        process.communicate(input=inistring.encode("utf-8"), timeout=5)
    except subprocess.TimeoutExpired:
        pass

    return {"success": True, "message": f'Connected to {vmstatus["name"]}'}


# ---------------------------------------------------------------------------
# Flask Routes
# ---------------------------------------------------------------------------


@app.before_request
def update_activity_and_check_timeout():
    """Update activity timestamp and check for session/server timeout."""
    # Update activity timestamp for authenticated users
    if G.authenticated and G.session_timeout > 0:
        # Check if session expired
        if G.last_activity_time:
            elapsed = time.time() - G.last_activity_time
            if elapsed >= G.session_timeout:
                # Session expired
                G.authenticated = False
                G.proxmox = None
                G.last_activity_time = None
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Session expired"}), 401
                flash("Your session has expired due to inactivity.", "warning")
                return redirect(url_for("login"))

        # Update activity timestamp for this request
        G.last_activity_time = time.time()


@app.route("/")
def index():
    if G.authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    groups = list(G.hosts.keys())
    hostset = G.hosts[G.current_hostset]

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        totp = request.form.get("totp", "").strip() or None

        connected, authenticated, error = pveauth(username, passwd=password, totp=totp)

        if not connected:
            flash(
                f"Unable to connect to any VDI server. "
                f"Are you connected to the network? Error: {error}",
                "error",
            )
        elif not authenticated:
            flash("Invalid username and/or password, please try again!", "error")
        else:
            G.authenticated = True
            if G.session_timeout > 0:
                G.last_activity_time = time.time()
            if hostset.get("auto_vmid"):
                vms = getvms()
                for vm in vms:
                    if vm["vmid"] == hostset["auto_vmid"]:
                        vmaction(vm["node"], vm["vmid"], vm["type"])
                        return redirect(url_for("dashboard"))
                flash(
                    f"No VDI instance with ID {hostset['auto_vmid']} found!", "warning"
                )
            return redirect(url_for("dashboard"))

    return render_template(
        "login.html",
        title=G.title,
        groups=groups,
        current_group=G.current_hostset,
        show_groups=len(groups) > 1,
        show_totp=hostset["totp"],
        show_pwreset=hostset.get("pwresetcmd") is not None,
        default_user=hostset["user"],
        has_token=bool(hostset.get("token_name") and hostset.get("token_value")),
        has_logo=G.imagefile is not None,
        kiosk=G.kiosk,
    )


@app.route("/dashboard")
def dashboard():
    if not G.authenticated:
        return redirect(url_for("login"))
    vms = process_vms(getvms())
    return render_template(
        "dashboard.html",
        title=G.title,
        vms=vms,
        show_reset=G.show_reset,
        show_hibernate=G.show_hibernate,
        has_logo=G.imagefile is not None,
        kiosk=G.kiosk,
        vm_count=len(vms),
    )


@app.route("/api/vms")
def api_vms():
    if not G.authenticated:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify(process_vms(getvms()))


@app.route("/api/session-status")
def api_session_status():
    """Return session timeout status."""
    if not G.authenticated:
        return jsonify({"authenticated": False}), 401

    response = {"authenticated": True, "session_timeout_enabled": G.session_timeout > 0}

    if G.session_timeout > 0 and G.last_activity_time:
        elapsed = time.time() - G.last_activity_time
        remaining = max(0, G.session_timeout - elapsed)
        response["session_remaining_seconds"] = int(remaining)

    return jsonify(response)


@app.route("/api/server-status")
def api_server_status():
    """Return server shutdown status (no auth required)."""
    response = {"server_shutdown_enabled": G.server_shutdown_timeout > 0}

    if G.server_shutdown_timeout > 0 and G.server_start_time:
        elapsed = time.time() - G.server_start_time
        remaining = max(0, G.server_shutdown_timeout - elapsed)
        response["server_remaining_seconds"] = int(remaining)

    return jsonify(response)


@app.route("/vm/<int:vmid>/connect", methods=["POST"])
def connect_vm(vmid):
    if not G.authenticated:
        return jsonify({"error": "Not authenticated"}), 401
    vms = getvms()
    for vm in vms:
        if vm["vmid"] == vmid:
            result = vmaction(vm["node"], vmid, vm["type"], action="connect")
            return jsonify(result)
    return jsonify({"success": False, "error": f"VM {vmid} not found"}), 404


@app.route("/vm/<int:vmid>/reset", methods=["POST"])
def reset_vm(vmid):
    if not G.authenticated:
        return jsonify({"error": "Not authenticated"}), 401
    vms = getvms()
    for vm in vms:
        if vm["vmid"] == vmid:
            result = vmaction(vm["node"], vmid, vm["type"], action="reload")
            return jsonify(result)
    return jsonify({"success": False, "error": f"VM {vmid} not found"}), 404


@app.route("/switch-group")
def switch_group():
    group = request.args.get("group", G.current_hostset)
    if group in G.hosts:
        G.current_hostset = group
        G.authenticated = False
        G.proxmox = None
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    G.authenticated = False
    G.proxmox = None
    G.last_activity_time = None
    return redirect(url_for("login"))


@app.route("/logo")
def serve_logo():
    if G.imagefile and os.path.exists(G.imagefile):
        return send_file(os.path.abspath(G.imagefile))
    return "", 404


@app.route("/password-reset", methods=["POST"])
def password_reset():
    cmd = G.hosts[G.current_hostset].get("pwresetcmd")
    if cmd:
        try:
            subprocess.Popen(cmd, shell=True)
            flash("Password reset launched successfully.", "success")
        except Exception as e:
            flash(f"Unable to open password reset: {e}", "error")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def check_server_shutdown():
    """Background thread that monitors server shutdown timeout."""
    while True:
        if G.server_shutdown_timeout > 0 and G.server_start_time:
            elapsed = time.time() - G.server_start_time
            if elapsed >= G.server_shutdown_timeout:
                logger.info("Server shutdown timeout reached, shutting down")
                os._exit(0)
        time.sleep(5)  # Check every 5 seconds


def is_certificate_valid(cert_path):
    """Check if certificate exists and is not expired.

    Args:
        cert_path: Path to certificate file

    Returns:
        True if certificate is valid and not expired, False otherwise
    """
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from datetime import datetime, UTC

        with open(cert_path, "rb") as f:
            cert_data = f.read()

        cert = x509.load_pem_x509_certificate(cert_data, default_backend())

        # Check not expired
        now = datetime.now(UTC)
        if cert.not_valid_after < now:
            return False  # Expired

        # Check not used before validity period
        if cert.not_valid_before > now:
            return False  # Not yet valid

        return True
    except Exception as e:
        logger.debug("Certificate validity check failed for %s: %s", cert_path, e)
        return False  # Invalid or unreadable


def generate_self_signed_cert():
    """Generate or reuse self-signed certificate for localhost.

    Generates a new self-signed certificate valid for localhost if one doesn't
    exist or if the existing certificate is expired. Stores certificate and
    private key in platform-specific config directory.

    Returns:
        tuple: (cert_path, key_path) or (None, None) if generation failed
    """
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from datetime import datetime, timedelta, UTC
        import ipaddress
    except ImportError:
        logger.error("cryptography module required for HTTPS support")
        logger.error("Install the cryptography package to enable HTTPS")
        return None, None

    try:
        # Get SSL directory path (platform-specific via Platform class)
        ssl_dir = Platform.get_ssl_directory()
        cert_path = os.path.join(ssl_dir, "localhost.crt")
        key_path = os.path.join(ssl_dir, "localhost.key")

        # Check if valid certificate already exists
        if os.path.exists(cert_path) and os.path.exists(key_path):
            # Verify not expired (check certificate validity)
            if is_certificate_valid(cert_path):
                return cert_path, key_path

        # Generate new certificate
        logger.info("Generating self-signed certificate for localhost")

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        # Generate certificate
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
            ]
        )

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(UTC))
            .not_valid_after(datetime.now(UTC) + timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        x509.DNSName("localhost"),
                        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                    ]
                ),
                critical=False,
            )
            .sign(private_key, hashes.SHA256())
        )

        # Write private key
        with open(key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        # Set private key permissions (owner read/write only)
        os.chmod(key_path, 0o600)

        # Write certificate
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Set certificate permissions (owner read/write, others read)
        os.chmod(cert_path, 0o644)

        logger.info("Self-signed certificate generated successfully")

        return cert_path, key_path

    except Exception:
        logger.exception("Error generating self-signed certificate")
        return None, None


def main():
    parser = argparse.ArgumentParser(description="Proxmox VDI Client")
    parser.add_argument(
        "--config_type",
        choices=["file", "http"],
        default="file",
        help="Config source type (default: file)",
    )
    parser.add_argument(
        "--config_location", default=None, help="Config file path or HTTP URL"
    )
    parser.add_argument(
        "--config_username", default=None, help="HTTP basic auth username"
    )
    parser.add_argument(
        "--config_password", default=None, help="HTTP basic auth password"
    )
    parser.add_argument(
        "--ignore_ssl",
        action="store_false",
        default=True,
        help="Ignore SSL certificate errors for config download",
    )
    parser.add_argument(
        "--port", type=int, default=5000, help="Web server port (default: 5000)"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Web server bind address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="Do not auto-open browser on start"
    )
    parser.add_argument(
        "--log-level",
        default=None,
        help="Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)",
    )
    args = parser.parse_args()

    # Phase 1: bootstrap logging before config is loaded
    _log_level_str = args.log_level or os.environ.get("LOG_LEVEL", "INFO")
    _log_level = getattr(logging, _log_level_str.upper(), logging.INFO)
    logging.basicConfig(
        level=_log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )
    for _noisy in ("werkzeug", "proxmoxer", "requests", "urllib3"):
        logging.getLogger(_noisy).setLevel(logging.WARNING)

    setcmd()

    if not loadconfig(
        config_location=args.config_location,
        config_type=args.config_type,
        config_username=args.config_username,
        config_password=args.config_password,
        ssl_verify=args.ignore_ssl,
    ):
        return 1

    # Phase 2: apply ini log_level if CLI/env didn't override
    if not args.log_level and not os.environ.get("LOG_LEVEL") and G.log_level:
        _ini_level = getattr(logging, G.log_level.upper(), None)
        if _ini_level:
            logging.getLogger().setLevel(_ini_level)

    # Generate SSL certificate if localhosttls is enabled
    ssl_context = None
    if G.localhosttls:
        try:
            cert_path, key_path = generate_self_signed_cert()
            if cert_path and key_path:
                G.ssl_cert_path = cert_path
                G.ssl_key_path = key_path

                # Create SSL context
                import ssl

                ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain(cert_path, key_path)

                logger.info("HTTPS enabled with self-signed certificate")
                logger.info("Certificate path: %s", cert_path)
            else:
                logger.warning("Failed to setup HTTPS, falling back to HTTP")
                G.localhosttls = False
        except Exception:
            logger.exception("Failed to setup HTTPS, falling back to HTTP")
            G.localhosttls = False
            ssl_context = None

    # Auto-login with API token (single cluster only)
    hostset = G.hosts[G.current_hostset]
    if (
        hostset["user"]
        and hostset["token_name"]
        and hostset["token_value"]
        and len(G.hosts) == 1
    ):
        logger.info("Auto-authenticating with API token")
        connected, authenticated, error = pveauth(hostset["user"])
        if connected and authenticated:
            G.authenticated = True
            if G.session_timeout > 0:
                G.last_activity_time = time.time()
            logger.info("API token authentication successful")
        else:
            logger.error("API token authentication failed: %s", error)

    # Set server start time for shutdown countdown
    if G.server_shutdown_timeout > 0:
        G.server_start_time = time.time()
        logger.info(
            "Server shutdown scheduled in %d seconds (%d minutes)",
            G.server_shutdown_timeout,
            G.server_shutdown_timeout // 60,
        )
        # Launch shutdown monitor thread
        shutdown_thread = Thread(target=check_server_shutdown, daemon=True)
        shutdown_thread.start()

    if not args.no_browser:
        protocol = "https" if G.localhosttls and ssl_context else "http"
        Thread(
            target=lambda: (
                time.sleep(1.5),
                webbrowser.open(f"{protocol}://{args.host}:{args.port}"),
            ),
            daemon=True,
        ).start()

    protocol = "https" if ssl_context else "http"
    logger.info("PVE VDI Client running at %s://%s:%d", protocol, args.host, args.port)
    app.run(
        host=args.host,
        port=args.port,
        debug=False,
        threaded=True,
        ssl_context=ssl_context,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
