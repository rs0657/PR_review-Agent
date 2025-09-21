from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="pr-review-agent",
    version="1.0.0",
    author="PR Review Agent Team",
    author_email="team@pr-review-agent.com",
    description="AI-powered Pull Request Review Agent with multi-platform support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pr-review-agent/pr-review-agent",
    project_urls={
        "Bug Tracker": "https://github.com/pr-review-agent/pr-review-agent/issues",
        "Documentation": "https://pr-review-agent.readthedocs.io/",
        "Source Code": "https://github.com/pr-review-agent/pr-review-agent",
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Environment :: Console",
        "Typing :: Typed",
    ],
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "pylint>=2.15.0",
            "mypy>=1.0.0",
            "isort>=5.10.0",
            "bandit>=1.7.0",
            "safety>=2.0.0",
            "pre-commit>=2.20.0",
            "responses>=0.20.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
        "all": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "pylint>=2.15.0",
            "mypy>=1.0.0",
            "isort>=5.10.0",
            "bandit>=1.7.0",
            "safety>=2.0.0",
            "pre-commit>=2.20.0",
            "responses>=0.20.0",
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pr-review=pr_review_agent.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "pr_review_agent": [
            "config/*.yaml",
            "templates/*.md",
        ],
    },
    keywords=[
        "pull-request",
        "code-review",
        "ai",
        "automation",
        "github",
        "gitlab",
        "bitbucket",
        "static-analysis",
        "quality-assurance",
        "development-tools",
    ],
    zip_safe=False,
)
