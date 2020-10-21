import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hexamma",
    version="0.0.1",
    author="Jan Wychowaniak",
    author_email="43786923+janwychowaniak@users.noreply.github.com",
    description="Simple folder structure graph generator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/janwychowaniak/hexamma",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    scripts=['hexamma'],
)
