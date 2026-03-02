"""Setup configuration for PVE VDI Client."""

import os
from setuptools import setup

# Read version from vdiclient/__init__.py
version = {}
with open(os.path.join("vdiclient", "__init__.py")) as f:
    exec([line for line in f if line.startswith("__version__")][0], version)

# Read long description from README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pve-vdiclient",
    version=version["__version__"],
    author="jbergquist",
    author_email="",
    description="Flask-based web client for Proxmox VE Virtual Desktop Infrastructure",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jbergquist/PVE-VDIClient",
    project_urls={
        "Bug Tracker": "https://github.com/jbergquist/PVE-VDIClient/issues",
        "Source Code": "https://github.com/jbergquist/PVE-VDIClient",
    },
    packages=["vdiclient"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Framework :: Flask",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
    ],
    python_requires=">=3.12",
    install_requires=[
        "flask>=3.0.0",
        "requests>=2.31.0",
        "urllib3>=2.0.0",
        "proxmoxer>=2.0.0",
    ],
    extras_require={
        "dev": [
            "black",
            "flake8",
            "mypy",
            "pytest",
        ],
    },
    entry_points={
        "console_scripts": [
            "vdiclient=vdiclient.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "vdiclient": [
            "templates/*.html",
            "static/*.css",
            "static/*.js",
            "static/*.png",
            "static/*.ico",
        ],
    },
    zip_safe=False,
)
