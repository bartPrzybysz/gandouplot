# Growthplot

A command line utility for generating infant growth charts for the Gandou database.

## Setup

Place the growthplot_config.json in the growthplot directory.
```
growthplot
|   ...
|   growthplot.exe
|   growthplot_config.json
|   ...
```

The growthplot_config.json file should contain the following:
``` json
{
    "server": "localhost or fus-elearning.org",
    "database": "gandou",
    "username": "username here",
    "password": "password here"
}
```

## Usage

Using the command line, navigate to the growthplot directory. Then run growthplot.exe with the patient's id in the first positional parameter:
```bash
cd path/to/growthplot
growthplot 1234
```
Generating the plots will take a minute. The results will be stored in a file called TEMP.pdf (overwritten every time the application runs).

## Development Setup
Use Python 3.7+

``` bash
pip install pipenv
git clone https://github.com/bartPrzybysz/gandouplot.git
cd gandouplot
pipenv install --dev
```

#### To view notebooks:
``` bash
pipenv run jupyter lab
```
Note that relative paths in the notebooks may not work.

#### To build project:
In growthplot.spec, change the `pathex` parameter to the absolute path of src/growthplot.py.

Then run:
``` bash
pipenv run pyinstaller growthplot_onedir.spec
```

