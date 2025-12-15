from setuptools import setup, find_packages

setup(
    name="job-portal-profile-refresh-automation",
    version="1.0.0",
    description="Serverless automation to refresh job portal profiles using Playwright and AWS services",
    author="",
    author_email="",
    packages=find_packages(),
    install_requires=[
        "boto3>=1.34.0",
        "botocore>=1.34.0",
        "playwright>=1.40.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
