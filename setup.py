from setuptools import setup, find_packages

setup(
    name="telegram-bot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "python-telegram-bot==20.7",
        "python-dotenv==1.0.0",
        "openai>=1.61.1",
        "httpx>=0.25.2",
        "Pillow>=10.0.0",  # для обработки изображений
    ],
    extras_require={
        'test': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.23.0',
            'pytest-cov>=4.1.0',
        ],
    },
)
