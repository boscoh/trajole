import setuptools

setuptools.setup(
    name="rshow",
    description="rshow",
    version="1.3.4",
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "addict",
        "docopt",
        "fastapi",
        "mdtraj",
        "numpy",
        "parmed",
        "psutil",
        "pydash",
        "rseed",
        "starlette",
        "uvicorn",
    ],
    entry_points="""
        [console_scripts]
        rshow=rshow.cli:cli
    """,
    python_requires=">=3.6",
    package_data={
        "rshow": [
            "rshow/server/local/client/**",
            "rshow/server/lounge/client/**",
            "rshow/server/local/client/assets/**",
            "rshow/server/lounge/client/assets/**",
        ]
    },
    include_package_data=True,
)
