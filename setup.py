#!/usr/bin/env python3
"""
Setup script for BMasterAI
"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bmasterai",
    version="0.2.1",
    author="Travis Burmaster",
    author_email="travis@burmaster.com",
    description="A comprehensive Python framework for building multi-agent AI systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/travis-burmaster/bmasterai",
    project_urls={
        "Bug Tracker": "https://github.com/travis-burmaster/bmasterai/issues",
        "Documentation": "https://github.com/travis-burmaster/bmasterai#readme",
        "Source Code": "https://github.com/travis-burmaster/bmasterai",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "integrations": [
            "discord.py>=2.0.0",
            "slack-sdk>=3.19.0",
            "pymongo>=4.0.0",
            "redis>=4.0.0",
            "celery>=5.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bmasterai=bmasterai.cli:main",
        ],
    },
    keywords="ai agents multi-agent automation monitoring logging",
    include_package_data=True,
    zip_safe=False,
)
