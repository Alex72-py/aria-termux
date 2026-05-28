"""
Setup script for ARIA.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aria-agent",
    version="1.0.0",
    author="ARIA Development Team",
    author_email="dev@aria-agent.dev",
    description="Terminal-native AI co-pilot for Termux/Android development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Alex72-py/aria-termux",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Android",
        "Operating System :: POSIX :: Linux",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Terminals",
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich>=13.0.0",
    ],
    extras_require={
        "google": ["google-generativeai>=0.3.0"],
    },
    entry_points={
        "console_scripts": [
            "aria=aria.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
