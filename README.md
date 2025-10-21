# PyClue


A Python command-line interface (CLI) tool designed to generate `Code Property Graphs` (CPGs), which include `Abstract Syntax Trees` (AST), `Control Flow` (CF), and `Data Flow` (DF) graphs. This tool also infers types of Python symbols using the generated CPG, aiding in static code analysis and understanding of Python codebases.


**Clone source code**

For `Unix`-based systems:
```sh
git clone https://github.com/SMART-Dal/pyclue.git
cd pyclue
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For `Windows` systems:
```sh
git clone https://github.com/SMART-Dal/pyclue.git
cd pyclue
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage
```sh
python pyclue <TARGET_PATH> <OUTPUT_PATH>
```
`<TARGET_PATH>`: Target to repository directory _[**REQUIRED**]_ <br>
`<OUTPUT_PATH>`: Path to store generated graph and other data _[**REQUIRED**]_ <br>

### Additional CLI Options
To explore other command-line interface (CLI) options, you can use the following command:
```sh
python pyclue --help
```
This will display a list of all available options and their descriptions.