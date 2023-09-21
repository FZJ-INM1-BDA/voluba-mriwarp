# Installation

=== "Windows"

    1. Install the following prerequisites
        - Python 3.8 or higher
        - [ANTs Eotapinoma](https://github.com/ANTsX/ANTs/releases/tag/v2.4.4)

    1. Clone voluba-mriwarp from GitHub

        ```powershell
        git clone https://github.com/FZJ-INM1-BDA/voluba-mriwarp.git
        ```

    1. Create a virtual environment

        ```powershell
        cd voluba-mriwarp
        python -m venv venv
        ./venv/Scripts/activate
        ```

    1. Install all Python requirements with pip

        ```powershell
        pip install -r requirements.txt
        ```

    1. Run voluba-mriwarp:

        ```powershell
        python start_app.py
        ```

=== "Linux"

    1. Install the following prerequisites:
        - Python 3.8 or higher
        - [ANTs Eotapinoma](https://github.com/ANTsX/ANTs/releases/tag/v2.4.4)

    1. Clone voluba-mriwarp from GitHub

        ```bash
        git clone https://github.com/FZJ-INM1-BDA/voluba-mriwarp.git
        ```

    1. Create a virtual environment

        ```bash
        cd voluba-mriwarp
        python -m venv venv
        source venv/bin/activate
        ```

    1. Install all Python requirements with pip

        ```bash
        pip install -r requirements.txt
        ```

    1. Run voluba-mriwarp:

        ```bash
        python start_app.py
        ```
