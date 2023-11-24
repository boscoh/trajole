import setuptools

setuptools.setup(
    name="rshow",
    description="rshow",
    version="1.6.5",
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "addict",
        "alphaspace2",
        "docopt",
        "easytrajh5>=0.2.5",
        "fastapi",
        "foamdb>=0.4.0",
        "mdtraj",
        "numpy",
        "parmed",
        "path",
        "psutil",
        "pydash",
        "python-multipart",
        "rich",
        "rseed>=2.7.6",
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
