import json, sys, os, time, requests, concurrent.futures
from langdetect import detect
from googletrans import Translator
from datetime import datetime


def save_json_response(response, filename):
    # Function to save the JSON response to a file
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(response.json(), file, ensure_ascii=False)

def parse_cookie_list(raw_cookies):
    cookies = {}
    for cookie in raw_cookies:
        cookies[cookie['name']] = cookie['value']
    return cookies


def retrieve_rdmo_data(file_name, cookies, project_id):
    urls = {
        'allProjects.json':     'https://rdmo.rwth-aachen.de/api/v1/projects/projects/',
        'questionValues.json':  'https://rdmo.rwth-aachen.de/api/v1/projects/values/'
    }
    request_url = ''

    if file_name in urls:
        request_url = urls[file_name]
    else:
        base_url = 'https://rdmo.rwth-aachen.de/api/v1/projects/projects/'
        
        request_url = base_url + str(project_id) + '/questionsets/' + file_name + '/'

    headers = {
        'Authorization': f'Token {cookies}',
        'Accept-Language': 'en-US,en;q=0.9'
        }
    
    if file_name == 'questionValues.json':
        print("s")
    if file_name == 'allProjects.json':
        all_projects = get_all_rdmo_projects(cookies, request_url)
        return_value = all_projects
    else:
        response = requests.get(request_url, headers=headers)
        return_value = response.text

    return_value = return_value
    if return_value:
        print(request_url)
        if isinstance(return_value, (dict, list)):
            return return_value
        else:
            return json.loads(return_value)
    else:
        return return_value
    

def get_all_rdmo_projects(token, base_url, page_size=5000, timeout=30):
    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    if "?" in base_url:
        next_url = f"{base_url}&page_size={page_size}"
    else:
        next_url = f"{base_url}?page_size={page_size}"

    all_projects = []

    while next_url:
        resp = requests.get(next_url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        all_projects.extend(data.get("results", []))
        next_url = data.get("next")
    return all_projects


def extract_text_answers(json_file, cookies):
    '''
    Extracts unique 'text_answer' values from a JSON file based on a specific question.

    Args:
        json_file (str): Path to the JSON file (if not in same directory, else only the name e.g. sample.json).

    Returns:
        list: A list of unique 'text_answer' values.

    '''
    data = open_json_file(json_file, cookies)
    text_answers = set()  # Using a set to ensure uniqueness of elements

    # Iterate over the entries in the JSON data
    for entry in data:
        if entry.get('questions'):  # Check if the 'questions' key exists
            for question in entry['questions']:
                # Check if the 'question' key has the desired value
                if question.get('question') == 'Enter a few content keywords.':
                    # Iterate over the 'answer' list
                    for answer in question.get('answer', []):
                        # Add the 'text_answer' values to the set
                        text_answers.update(answer.get('text_answer', []))

    return list(text_answers)


def process_file(data):
    '''
    Process the JSON data of a single file and extract the relevant information.

    Args:
        data (dict): JSON data loaded from a file.

    Returns:
        tuple: A tuple containing a list of dictionaries representing the extracted information
               and the value of 'next' from the JSON data.
    '''
    results = []
    for question in data['questions']:
        result = {
            'question': question['text'],
            'attribute': question['attribute'],
            'set_attribute': data['attribute'],
            'options': []
        }
        if 'optionsets' in question:
            if(question['optionsets']):
                for option in question['optionsets'][0]['options']:
                    result['options'].append({
                        'id': option['id'],
                        'text': option['text'],
                        'additional_input': option['additional_input']
                    })
        results.append(result)
    return results, data['next']

def open_json_file(file_name, cookies, project_id=None):
    '''
    Open and load a JSON file.

    Args:
        file_name (str): Name of the JSON file to open.

    Returns:
        dict: JSON data loaded from the file.
    '''
    # retrieve_rdmo_data(file_name, cookies)
    # file_path = os.path.join(os.path.dirname(__file__), file_name)

    # with open(file_path, 'r', encoding='utf-8') as f:
    #     data = json.load(f)
    data = retrieve_rdmo_data(file_name, cookies, project_id)
    return data

def iterate_files(start_file, project_data, cookies):
    '''
    Iterate through JSON files based on the 'next' value until a 'null' value is encountered.

    Args:
        start_file (int): Number of the starting JSON file.

    Returns:
        list: A list of dictionaries representing the extracted information from each file.
    '''
    print('-collecting questions...')
    # Generate list with all project ids
    project_ids = [i['id'] for i in project_data]
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_id = {executor.submit(process_id, start_file, cookies, id): id for id in project_ids}
        for future in concurrent.futures.as_completed(future_to_id):
            id = future_to_id[future]
            try:
                result = future.result()
                if result:
                    for result_dict in result:
                        if result_dict not in results:
                            results.append(result_dict)
            except Exception as e:
                print('Error processing ID', id, ':', str(e))
            print('id:', id, '\t#questions:', len(results), '\t', str(project_ids.index(id)+1), '/', str(len(project_data)))
    return results

def process_id(start_file, cookies, id):
    next_file = start_file
    result = []
    while next_file is not None:
        file_name = str(next_file) + '.json'
        data = open_json_file(file_name, cookies, id)
        if data:
            ext_quest, next_file = process_file(data)
            if isinstance(ext_quest, list) and len(ext_quest) > 0:
                result.extend(ext_quest)
            else:
                result.append(ext_quest)
        else:
            next_file = None
    return result

def find_non_leaf_nodes(project_data):
    # Find ids of non-leaf nodes
    non_leaf_ids = set() 
    for item in project_data:
        parent = item.get('parent')  
        if parent is not None:      
            non_leaf_ids.add(parent)  
    return non_leaf_ids




def is_child(lst, current_id, parent_id):
    # Checks if project is a child of internet of production
    for item in lst:
        if item['id'] == current_id:
            if item['parent'] == parent_id:
                return True
            elif item['parent'] is not None:
                return is_child(lst, item['parent'], parent_id)
            else:
                return False
    return False

def get_project_data(cookies):
    print('-parsing project data...')
    data = open_json_file('allProjects.json', cookies)
    # Find ids of non-leaf nodes
    non_leaf_ids = find_non_leaf_nodes(data)

    # Add non-leaf node ids to the list [914, 921, 922] (914=Internet of Production, 921=WS-B1.I, 922=WS-B1.II)
    ids_to_exclude = [914, 921, 922, 1074] + list(non_leaf_ids)
    wrong_projects = []

    # Filter out entries with ids that are not in the ids_to_exclude list'
    # filtered_data = [item for item in data if item['id'] not in ids_to_exclude]
    filtered_data = []
    for item in data:
        if is_child(data, item['id'], 914) and item['id'] not in ids_to_exclude:
            if item['catalog_uri'] == 'http://example.com/terms/questions/IoP':
                filtered_data.append(item)
            else:
                # Only allow the IoP question catalogue
                wrong_projects.append(item)
                continue
            
    # Create a list of dictionaries containing the remaining projects' data
    project_data = [{'id': item['id'], 'RDMOtitle': item['title'], 'parent': item.get('parent'), 'created': item['created'], 'updated': item['updated']} for item in filtered_data]

    return [project_data, wrong_projects] 



def detect_and_translate(keywords, treat_non_english_as_german=False, translate_only_german=False):
    '''
    Detects the language of each word in the input list and translates it to English if necessary.
    
    Args:
        words (list): List of words to be translated.
        treat_non_english_as_german (bool, optional): If True, treats all non-English words as German.
            Defaults to False.
        
    Returns:
        list: List of translated words in English, without duplicates.
    '''
    translator = Translator()
    translated_words = set()

    for words in keywords:
        for word in process_string(words):
            try:
                language = detect(word)
            except:
                # Handle language detection exception
                language = 'en'

            try:
                if translate_only_german and language == 'de':
                    # Translate only German to English
                    translation = translator.translate(word, src='de', dest='en').text
                    translated_words.add(translation)

                elif language != 'en':
                    # Translate non-English words to English based on detected language
                    translation = translator.translate(word, src=language, dest='en').text
                    translated_words.add(translation)

            except:
                # print(f"Translation error for word '{word}'")
                continue  # continue with next word

    return list(translated_words)

def process_string(string):
    '''
    Processes a strings, detecting if a string contains multiple words
    and splitting them if necessary. The processed strings are added to a list
    along with the original strings.

    Args:
        strings (list): A list of strings to process.

    Returns:
        list: A list containing the processed strings.

    '''
    result = []
    if ' ' in string:
        # Split the string at the blank and add the individual words and the original string
        words = string.split()  # Split the string into individual words
        result.extend(words)  # Add the individual words to the result list
        result.append(string)  # Add the original string to the result list
    else:
        # Add the single word to the list
        result.append(string)  # Add the single word to the result list
    return result

def generate_result_list(list_A, list_B, list_C):
    print('-generating result list...')
    result = []
    id_list = [item['id'] for item in list_A]
    title_list = [item['RDMOtitle'] for item in list_A]
    for num,title in zip(id_list, title_list):
        set_dict = create_set_dictionary(list_C, num)

        found_item = next((i for i in list_A if i['id'] == num), None)
        createdDate, updatedDate = (found_item['created'], found_item['updated']) if found_item else (None, None)
        formatted_created_date = datetime.fromisoformat(createdDate).strftime('%d.%m.%Y %H:%M') if createdDate else None
        formatted_updated_date = datetime.fromisoformat(updatedDate).strftime('%d.%m.%Y %H:%M') if updatedDate else None

        result_dict = {'RDMOtitle': title, 'questions': [], 'additional': [{'created': formatted_created_date, 'updated': formatted_updated_date}]}

        
        #list of questions
        for item_B in list_B:
            value_list = []
            for item_C in list_C:
                if item_B['attribute'] == item_C['attribute'] and num == item_C['project']:
                    value_list.append(item_C)
            
            question_options = item_B['options']  # Get the options for the current question
            final_option = []
            final_text = []
            # Iterate over each option within the question
            if question_options:
                for option in question_options:
                    option_id = option['id']  # Get the option ID
                    option_answer = {option['text']}  # Store the option answer as a set
                    additional_input = option['additional_input']  # Check if additional input is required

                    # Iterate over each item in value_list
                    for item_V in value_list:
                        # Check if the option ID matches the 'option' field in list C
                        if item_V['option'] == option_id:
                            text = item_V['text']  # Get the text answer
                            
                            # If additional input is required, add the text answer to the set
                            if additional_input:
                                final_text.append([item_V['set_index'], text])
                            final_option.append([item_V['set_index'], option['text']])

            else:
                # Iterate over each item in value_list
                for item_V in value_list:
                    # Check if the option ID matches the 'option' field in list C
                    if not item_V['option']:
                        text = item_V['text']  # Get the text answer
                        final_text.append([item_V['set_index'], text])
                        # final_option.add(option['text'])

            dataset_list = create_dataset_list(final_option, final_text, set_dict, item_B['set_attribute'], item_B['question'])
            question_dict = {'question': item_B['question'], 'answer': dataset_list}
            result_dict['questions'].append(question_dict)

        result.append(result_dict)
    return result

def create_dataset_list(final_option, final_text, set_dict, set_is_used, question):
    '''
    Create a list of dictionaries based on the given inputs.

    Args:
        final_option (list): List containing sublists with a number in the first position and a string in the second position.
        final_text (list): List containing sublists with a number in the first position and a string in the second position.
        set_dict (dict): Dictionary with numbers as keys and corresponding dataset values.
        set_is_used: Additional variable to determine the behavior.
        question: Additional variable to determine if the current question is about the keywords. If yes, translate them
    Returns:
        list: A list of dictionaries with 'dataset', 'option_answer', and 'text_answer' keys (if set_is_used is not None).
              Otherwise, a dictionary with 'option_answer' and 'text_answer' keys containing all second values from final_option and final_text.

    '''
    # Check if set_is_used is None
    if set_is_used is None:
        # Create a dictionary with only 'option_answer' and 'text_answer' keys
        result_dict = {
            'option_answer': [option[1] for option in final_option],
            'text_answer': [text[1] for text in final_text]
        }

        # Return the resulting dictionary
        return result_dict

    # Create an empty list to store the dictionaries
    result_list = []

    # Iterate over the keys in set_dict
    for key in set_dict:
        # Create a dictionary for each key
        dataset_dict = {
            'dataset': set_dict[key],
            'option_answer': [],
            'text_answer': []
        }

        # Iterate over final_option to find matching values
        for option in final_option:
            if option[0] == key:
                dataset_dict['option_answer'].append(option[1])

        # Iterate over final_text to find matching values
        for text in final_text:
            if text[0] == key:
                dataset_dict['text_answer'].append(text[1])

        # Check if both option_answer and text_answer are empty
        if dataset_dict['option_answer'] or dataset_dict['text_answer']:
            # Append the dataset_dict to the result_list
            result_list.append(dataset_dict)
                
        # Check if item_B['question'] is equal to 'Enter a few content keywords.'
        if question == 'Enter a few content keywords.':
                # If the condition is true, create a new key 'added_keywords' in dataset_dict,
                # translate the keywords from text_answer to english and add them to the new key
                # force translation from de to en -> if word is not en, it is assumed to be de
                dataset_dict['added_keywords'] = detect_and_translate(dataset_dict['text_answer'], treat_non_english_as_german=False, translate_only_german=True)

    # Return the resulting list of dictionaries
    return result_list

def create_set_dictionary(question_answers, number):
    '''
    Create a dictionary based on the given data list.

    Args:
        data (list): List containing dictionaries with project, set_index, attribute, and text values.
        number (int): The number to compare against the project value in each dictionary.

    Returns:
        dict: A dictionary with set_index as keys and corresponding text values.

    '''

    # Create an empty dictionary to store the results
    result_dict = {}

    # Iterate over each dictionary in the data list
    for item in question_answers:
        # Check if project value matches the given number and attribute value is 111
        if item['project'] == number and item['attribute'] == 111:
            # Add the set_index as key and text as value to the result_dict
            result_dict[item['set_index']] = item['text']

    # Return the resulting dictionary
    return result_dict


def open_json_file2(file_name):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def anonymize_data(input_file, output_file):
    # create new json file with anonymized data according to answered questions
    data=open_json_file2(input_file)
    for project in data:
        opt_in_answer = None
        responsible_persons_answer = None

        for question in project['questions']:
            if question['question'] == "Opt-in - Display of personal information":
                opt_in_answer = question['answer']['option_answer']
            if question['question'] == "Who are the responsible contact persons for this project?":
                responsible_persons_answer = question['answer']['text_answer']

        if not any("Yes " in item for item in opt_in_answer):
            for question in project['questions']:
                if question['question'] == "Who are the responsible contact persons for this project?":
                    question['answer']['text_answer'] = ["Personal data is not disclosed."]
                elif question['question'] == "Who is responsible for the data of this project after the end of the project?":
                    question['answer']['text_answer'] = ["Personal data is not disclosed."]

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

def main():
    start_time = time.time()
    
    cookies = sys.argv[1] # cookies = RDMO Token

    project_data = get_project_data(cookies)
    
    result_list = generate_result_list(project_data[0], iterate_files(537, project_data[0], cookies), open_json_file('questionValues.json', cookies))

    data_grabber_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    file_path = os.path.join(data_grabber_dir, 'data_grabber', 'target', 'sampleX.json')

    wrong_projects_file_path = os.path.join(data_grabber_dir, 'data_grabber', 'target', 'wrong_projects.json')
    os.makedirs(os.path.dirname(wrong_projects_file_path), exist_ok=True)
    with open(wrong_projects_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(project_data[1], json_file, indent=4, ensure_ascii=False)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as outfile:
        json.dump(result_list, outfile, indent=4, ensure_ascii=False)

    anonymize_data(file_path, os.path.join(data_grabber_dir, 'data_grabber', 'target', 'sampleXanonymized.json'))

    print('--- %s seconds ---' % (time.time() - start_time))

if __name__ == '__main__':
    main()
