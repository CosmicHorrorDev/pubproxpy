from setuptools import setup


with open("README.md", "r") as f:
    readme = f.read()

setup(
    name="pubproxpy",
    version="0.1.1",
    description="A public proxy list provider using the pubproxy.com API",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/LovecraftianHorror/pubproxpy",
    author="LovecraftianHorror",
    author_email="LovecraftianHorror@pm.me",
    packages=["pubproxpy"],
    python_requires=">=3.6.0",
    install_requires=["requests>=2.22.0"],
    license="GPLv3",
    zip_safe=False,
)
