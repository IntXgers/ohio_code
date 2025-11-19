from setuptools import setup, find_packages

setup(
    name="ohio_caselaw",
    version="0.1.0",
    description="Ohio Case Law Citation Analysis and LMDB Database",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "lmdb",
    ],
)