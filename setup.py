"""
avwx_api_core Package Setup
"""

from setuptools import setup, find_namespace_packages


setup(
    name="avwx-api-core",
    version="0.1.0",
    description="Core components for AVWX APIs",
    url="https://github.com/avwx-rest/avwx-api-core",
    author="Michael duPont",
    author_email="michael@dupont.dev",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">= 3.11",
    install_requires=[
        "dicttoxml @ git+https://github.com/avwx-rest/dicttoxml",
        "quart-openapi @ git+https://github.com/flyinactor91/quart-openapi@1e894cba8dbb14a41d4ed5dc5d9c6cfb5990ae57",
        "avwx-engine>=1.9",
        "dnspython~=2.7",
        "pymongo>=4.13",
        "pyyaml~=6.0",
        "quart~=0.20",
        "voluptuous~=0.15",
    ],
    packages=find_namespace_packages(include=["avwx_api_core*"]),
    package_data={"avwx_api_core.data": ["navaids.json"]},
    tests_require=["pytest-asyncio~=0.20"],
)
