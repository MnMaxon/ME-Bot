from setuptools import setup

setup(
    name="me",
    version="0.2",
    py_modules=["me"],
    install_requires=[
        "aiohttp==3.9.0b0",
        "discord",
        "click",
        "pathlib",
        "pandas",
        "fastapi",
        "uvicorn",
        "fastapi-discord",
        "gunicorn",
    ],
    # entry_points={
    #     'console_scripts': [
    #         '__main__ = me.__main__:main',
    #     ],
    # },
)
