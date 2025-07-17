# Setup script for SCP installation
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="support-context-protocol",
    version="0.1.0",
    author="Support Engineering Team",
    author_email="support@example.com",
    description="Intelligent, memory-based case triage system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/scp",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Office/Business :: Groupware",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "vector": [
            "faiss-cpu>=1.7.4",
            "sentence-transformers>=2.2.2",
        ],
    },
    entry_points={
        "console_scripts": [
            "scp=scp.__main__:run_cli",
            "scp-api=scp.__main__:run_api",
        ],
    },
    include_package_data=True,
    package_data={
        "scp": ["*.py"],
    },
)
