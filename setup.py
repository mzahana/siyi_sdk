from setuptools import find_packages, setup

setup(
    name="siyi_sdk",
    version="0.1.0",
    description="Python package implementation for Siyi SDK.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Mohamed Abdelkader",
    author_email="mohamedashraf123@gmail.com",
    packages=find_packages(exclude=["*/test",".github"]),
    install_requires=["opencv-python>=4.0.0", "imutils", "ffmpeg-python"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
