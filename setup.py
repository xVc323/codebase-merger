from setuptools import setup

setup(
    name="codebase-merger",
    version="0.1.0",
    description="Merge an entire GitHub repository codebase into a single file",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/codebase-merger",
    author="GitHub Codebase Merger Developers",
    author_email="your.email@example.com",
    py_modules=["codebase_merger"],
    scripts=["codebase_merger_gui.py"],
    entry_points={
        "console_scripts": [
            "codebase-merger=codebase_merger:main",
            "codebase-merger-gui=codebase_merger_gui:main"
        ],
    },
    install_requires=[],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
) 