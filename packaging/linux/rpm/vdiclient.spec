Name:           pve-vdiclient
Version:        2.0.2
Release:        1%{?dist}
Summary:        Flask-based web client for Proxmox VE VDI

License:        ASL 2.0
URL:            https://github.com/jbergquist/PVE-VDIClient
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel >= 3.12
BuildRequires:  python3-setuptools
BuildRequires:  python3-pip

Requires:       python3 >= 3.12
Requires:       python3-flask >= 3.0.0
Requires:       python3-requests
Requires:       python3-urllib3
Requires:       virt-viewer
Recommends:     python3-proxmoxer
Recommends:     python3-gobject
Recommends:     libayatana-appindicator

%description
PVE VDI Client provides a modern web interface for accessing virtual
desktops in Proxmox VE environments. It supports SPICE protocol for
remote desktop access and integrates with virt-viewer for launching
VM console sessions.

Features:
- Web-based login and VM selection
- SPICE protocol support for virtual desktops
- Integration with Proxmox VE authentication
- Support for multiple Proxmox clusters
- Session timeout and auto-shutdown
- Compatible with PVE 7, 8, and 9

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install

# Install desktop file
install -D -m 0644 packaging/linux/vdiclient.desktop \
    %{buildroot}%{_datadir}/applications/vdiclient.desktop

# Install icon
install -D -m 0644 vdiclient/static/vdiclient.png \
    %{buildroot}%{_datadir}/pixmaps/vdiclient.png

# Install example config
install -D -m 0644 vdiclient.ini.example \
    %{buildroot}%{_docdir}/%{name}/vdiclient.ini.example

%files
%license LICENSE
%doc README.md
%{python3_sitelib}/vdiclient/
%{python3_sitelib}/pve_vdiclient-*.egg-info/
%{_bindir}/vdiclient
%{_datadir}/applications/vdiclient.desktop
%{_datadir}/pixmaps/vdiclient.png
%{_docdir}/%{name}/vdiclient.ini.example

%changelog
* Sat Mar 01 2026 jbergquist <jb+gh@bergnet.se> - 2.0.2-1
- Initial RPM package release
- Refactored as proper Python package
- Platform abstraction layer for cross-platform support
- Security improvements (eliminated shell injection risks)
- XDG Base Directory specification compliance
- Support for pip installation
- Compatible with Proxmox VE 7, 8, and 9
