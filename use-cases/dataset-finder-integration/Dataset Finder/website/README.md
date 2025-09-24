# Search and Execute Application

This application is a Flask-based web application that allows users to search for keywords in a JSON file and execute Python code based on the search results. It provides a simple user interface for adding words to search for, displaying the added words, deleting words, and executing the search.

## Files

The following files are included in this application:

1. `code_1.py`: This is the main Flask application file. It defines the routes and logic for adding words, deleting words, executing the search, and rendering templates.
2. `to_execute.py`: This file contains the Python code that is executed based on the search results. It includes functions for finding similar words, opening and searching a JSON file, and generating search results.
3. `index.html`: This HTML template is used to render the main page of the application. It includes a form for adding words, displays the added words, and provides options to delete all words and execute the search.
4. `results.html`: This HTML template is used to render the search results page. It displays the search results in a list format.

## Dependencies

The application relies on the following dependencies:

- Flask: A web framework used for creating the application and handling requests.
- fuzzywuzzy: A library for fuzzy string matching, used for finding similar words in the search functionality.
- Bootstrap: A CSS framework used for styling the HTML templates.

## Requirements

- Python 3.9.13
- `pip install -r requirements.txt`


## Getting Started

To run the application, follow these steps:

1. Run the Flask application by executing the `code_1.py` file:
2. Access the application by opening a web browser and navigating to `http://localhost:5000` or `http://127.0.0.1:5000/`.

## Usage

- On the main page, enter a word in the input field and click the "+" button to add it to the search list.
- The added words will be displayed below. Click the "x" button next to a word to delete it.
- To delete all words, click the "Delete All" button.
- Once at least one word is added, the "Execute" button becomes enabled. Click it to execute the search and view the results on the results page.

## Customization

- Modify the `to_execute.py` file to customize the logic for searching and generating search results based on your JSON data structure.
- Customize the HTML templates (`index.html` and `results.html`) to change the appearance and layout of the application.

