# PWP SPRING 2024
# Inventory Sytstem for Foodmarket Chain
# Group information
* Student 1. Alexis Chambers	Alexis.Chambers@oulu.fi
* Student 2. Zeeshan	Talha	Talha.Zeeshan@student.oulu.fi
* Student 3. Reed	Connor	Connor.Reed@student.oulu.fi
* Student 4. Chakal	Khalil	Khalil.Chakal@oulu.fi


## Project Setup

Clone the repository to your local machine using git clone
```
git clone https://github.com/khacha329/PWP_CrustyCrabs.git
```
To ensure your python packages are protected, set up a virtual environment to keep a clean system

```
python -m venv /path/to/myEnv
```
Activate the virtual environment

```
c:\path\to\the\virtualenv\Scripts\activate.bat
```

cd to directory with project files

```
cd ./path/to/Project/Files
```

Install the required python packages in the virtual environment using the requirements.txt file located in the root directory of this project

```
pip install -r requirements.txt 
```

Intall inventory manager package in developer mode:
Navigate to /PWP_CrustyCrabs/

Run:

```
pip install -e .
```


## Initialize and Populate DB

To intialize the database and populate it with dummy data follow the [README file](https://github.com/khacha329/PWP_CrustyCrabs/blob/main/inventorymanager/README.md) under the inventorymanager folder



## Clean Code / Documentation

Run these to format code and imports:

```
isort inventorymanager
black inventorymanager
```

VS code has an extension AutoDocstring, to use set cursor directly below method and press Ctrl+Shift+2.


## Testing

Run all Tests: `pytest`
Run all Tests with coverage: `pytest --cov-report term-missing --cov=inventorymanager`
Or Run tests in VS Code tests tab. 

Postman link: https://app.getpostman.com/join-team?invite_code=a11c54208bc216362b9fde402feec912&target_code=437ef75d1e1193f934e96cb340c4f083    

__Remember to include all required documentation and HOWTOs, including how to create and populate the database, how to run and test the API, the url to the entrypoint and instructions on how to setup and run the client__


