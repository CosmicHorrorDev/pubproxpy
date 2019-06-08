from setuptools import setup


setup(
    name="pubproxpy",
    version="0.1.0",
    description="A public proxy list provider using the pubproxy.com API",
    url="https://github.com/LovecraftianHorror/pubproxpy",
    author="LovecraftianHorror",
    author_email="LovecraftianHorror@pm.me",
    packages=["pubproxpy"],
    python_requires=">=3.6.0",
    install_requires=["requests>=2.22.0"],
    zip_safe=False,
)
