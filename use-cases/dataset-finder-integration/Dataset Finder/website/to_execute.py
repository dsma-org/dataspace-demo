import sys, json, random, os, re
from fuzzywuzzy import fuzz
from datetime import datetime

def find_similar_words(word_list, word_x, threshold):
    if not bool(word_x): threshold = 0
    word_x_lower = word_x.lower()
    return list(
        {word for word in word_list for word_in_exp in expand_word_list([word], len(word_x.split()))
         if fuzz.ratio(word_in_exp.lower(), word_x_lower) >= threshold})

def generate_adjacent_combinations(word, max_elements):
    word_tokens = word.lower().split()
    return [' '.join(comb) for i in range(1, min(len(word_tokens), max_elements) + 1)
            for comb in zip(*(word_tokens[j:] for j in range(i)))]

def expand_word_list(word_list, max_elements):
    expanded_list = {word.lower() for word in word_list}
    for word in word_list:
        expanded_list.update(generate_adjacent_combinations(word, max_elements))
    return list(expanded_list)

def open_json_file(file_name):
    file_path = os.path.join(os.path.dirname(__file__), file_name)
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def extract_emails_from_text(text):
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)

def create_title_email_file(data, filepath):
    result = []
    for dictionary in data:
        rdmo_title = [dictionary['RDMOtitle']]
        contact_persons = []

        for question_dict in dictionary['questions']:
            question = question_dict['question']
            if question == 'Who are the responsible contact persons for this project?':
                answer = question_dict['answer']
                for contact_email in answer.get('text_answer'):
                    contact_persons.extend(extract_emails_from_text(contact_email))

        result.append({'rdmo_title': rdmo_title, 'contact_persons': contact_persons})

    with open(filepath, 'w', encoding='utf-8') as json_file:
        json.dump(result, json_file, indent=4, ensure_ascii=False)

def get_workstreams(data):
    workstreams = set()
    for dictionary in data:
        for question_dict in dictionary['questions']:
            question = question_dict['question']
            answer = question_dict['answer']
            if question == 'What workstreams are involved?':
                for workstream in answer['option_answer']:
                    workstreams.add(workstream)
    return sorted(list(workstreams))

def load_and_process_workstreams():
    data_grabber_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    file_path = os.path.join(data_grabber_dir, 'data_grabber', 'target', 'sampleX.json')

    data = open_json_file(file_path)
    workstreams = get_workstreams(data)
    return workstreams

def update_contact_persons(contact_personsX):
    # some random data for testing
    contact_persons = [
    'John Doe; ABC; J.Doe@ABC.rwth-aachen.de;0000-1111-2222-3333',
    'Jane Smith; DEF; J.Smith@DEF.rwth-aachen.de;1111-2222-3333-4444',
    'Emily Johnson; GHI; E.Johnson@GHI.rwth-aachen.de;2222-3333-4444-5555',
    'Michael Brown; JKL; M.Brown@JKL.rwth-aachen.de;3333-4444-5555-6666',
    'Sarah Williams; MNO; S.Williams@MNO.rwth-aachen.de;4444-5555-6666-7777',
    'David Lee; PQR; D.Lee@PQR.rwth-aachen.de;5555-6666-7777-8888',
    'Emma Garcia; STU; E.Garcia@STU.rwth-aachen.de;6666-7777-8888-9999',
    'Christopher Martinez; VWX; C.Martinez@VWX.rwth-aachen.de;7777-8888-9999-0000',
    'Olivia Hernandez; YZA; O.Hernandez@YZA.rwth-aachen.de;8888-9999-0000-1111',
    'Daniel Gonzalez; BCD; D.Gonzalez@BCD.rwth-aachen.de;9999-0000-1111-2222',
    'Sophia Lopez; EFG; S.Lopez@EFG.rwth-aachen.de;0000-1111-2222-3333',
    'Liam Wilson; HIJ; L.Wilson@HIJ.rwth-aachen.de;1111-2222-3333-4444',
    'Ava Campbell; KLM; A.Campbell@KLM.rwth-aachen.de;2222-3333-4444-5555',
    'Noah Young; NOP; N.Young@NOP.rwth-aachen.de;3333-4444-5555-6666',
    'Isabella Hall; QRS; I.Hall@QRS.rwth-aachen.de;4444-5555-6666-7777'
    ]
    num_entries = len(contact_personsX)
    contact_personsX.clear()
    random_entries = random.sample(contact_persons, num_entries)
    contact_personsX.extend(random_entries)

def search_all_strings(data_list, keyword, no_keyword = False):
    filtered_list = []
    include_real_names = True
    for item in data_list:
        all_answers = [item['RDMOtitle']]
        for question_dict in item['questions']:
            # if dont_include_all_questions and question_dict['question'] in ["Provide a short description of the project.", "Provide a brief description of your data set."]:
            if not include_real_names and question_dict['question'] in ["Who are the responsible contact persons for this project?", "Who is responsible for the data of this project after the end of the project?"]:
                continue
            else:
                if 'answer' in question_dict:
                    if 'option_answer' in question_dict['answer']:
                        all_answers.extend(question_dict['answer']['option_answer'])
                    if 'text_answer' in question_dict['answer']:
                        all_answers.extend(question_dict['answer']['text_answer'])
                if isinstance(question_dict['answer'], list):
                    for ans in question_dict['answer']:
                        if 'option_answer' in ans:
                            all_answers.extend(ans['option_answer'])
                        if 'text_answer' in ans:
                            all_answers.extend(ans['text_answer'])

        fuzzy_word = find_similar_words(all_answers, keyword, 85)
        if fuzzy_word:
            if not item in filtered_list:
                filtered_list.append(item)

    return filtered_list

def search_json_file(data, keyword, workstreams_bool, keys_bool, contact_bool, title_bool, no_keyword = False):
    '''
    Searches through a JSON data for dictionaries containing a specific keyword in 'text_answer' or 'added_keywords'.
    If a match is found, creates a new dictionary with relevant fields and adds it to the result list.

    Args:
        data (dict): The JSON data as a dictionary.
        keyword (str): The keyword to search for.

    Returns:
        list: A list of dictionaries containing relevant fields for the matching dictionaries.
    '''
    a = len(data)
    filtered_data = []
    if no_keyword:
        filtered_data = search_all_strings(data, keyword, True)
    else:
        filtered_data = search_all_strings(data, keyword)

    main_list = []
    for i in data:
        if not i in filtered_data:
            main_list.append(i)
    result = []
    result2 = []

    
    # for dictionary in data:
    for dictionary in filtered_data:
        show_contacts = False # set Ture to show real user information
        user_agrees = True # set False if you dont want the project to be displayed in the dataset finder
        project_title = None
        rdmo_title = [dictionary['RDMOtitle']]
        project_description = None
        contact_persons = None
        workstreams = None
        dataset_description_list = None
        keywords = []
        temp_keywords_with_added = []
        kind_of_research_data_dict_list = None
        keyword_dict_list = None
        pid_list = None


        for question_dict in dictionary['questions']:
            question = question_dict['question']
            answer = question_dict['answer']
            if question == 'What is the project title/topic?':
                project_title = answer['text_answer']
            elif question == 'Provide a short description of the project.':
                project_description = answer['text_answer']
            elif question == 'Who are the responsible contact persons for this project?':
                # contact_persons = answer['text_answer'] if show_contacts else []
                contact_persons = answer['text_answer']
            elif question == 'What workstreams are involved?':
                workstreams = answer['option_answer']
            elif question == 'Provide a brief description of your data set.':
                dataset_description_list = answer
            elif question == 'What kind of research data is it?':
                kind_of_research_data_dict_list = question_dict['answer']
            elif question_dict['question'] == 'Enter a few content keywords.':
                keyword_dict_list = question_dict['answer']
            elif question_dict['question'] == 'PID of the dataset or of related works':
                pid_list = question_dict['answer']
            elif question_dict['question'] == 'Opt-out - Display of non-personal project information':
                contains_no = any("No " in item for item in answer['option_answer']) # true if "No " in string. No = The Dataset Finder must not find the project.
                if contains_no:
                    user_agrees = False
            elif question_dict['question'] == 'Opt-in - Display of personal information':
                contains_yes = any("Yes " in item for item in answer['option_answer']) # true if "Yes " in string. Yes = Personal information (Name, Institut, E-Mail, ORCID) of the persons contained in this DMP may be listed by the IoP Dataset Finder.
                if contains_yes:
                    show_contacts = True

                    
        for keyword_dict in keyword_dict_list:
            kind_keywords = keyword_dict['text_answer']
            if kind_of_research_data_dict_list:
                for i in kind_of_research_data_dict_list:
                    if i['dataset'] == keyword_dict['dataset']:
                        kind_keywords = i['text_answer']
            keywords.append(keyword_dict['text_answer'] + kind_keywords)
            temp_keywords_with_added.append(keyword_dict['text_answer'] + keyword_dict['added_keywords'] + kind_keywords)

        fuzzy_word = keyword
        if (not show_contacts):
            # contact_person = update_contact_persons(contact_persons)
            contact_persons = ["Personal data is not disclosed."]
        contact_personsX = [conpers for conpers in contact_persons] if len(contact_persons) > 1 else contact_persons
        new_dict = edit_data(fuzzy_word, dictionary, project_title, project_description, contact_personsX, workstreams, dataset_description_list, keywords, keyword, pid_list)

        if not new_dict in result2 and user_agrees:
            result2.append(new_dict)
        continue

        # adding "what kind of reseach data?" to keywords
        for keyword_dict in keyword_dict_list:
            kind_keywords = keyword_dict['text_answer']
            if kind_of_research_data_dict_list:
                for i in kind_of_research_data_dict_list:
                    if i['dataset'] == keyword_dict['dataset']:
                        kind_keywords = i['text_answer']
            keywords.append(keyword_dict['text_answer'] + kind_keywords)
            temp_keywords_with_added.append(keyword_dict['text_answer'] + keyword_dict['added_keywords'] + kind_keywords)
        
        if (not show_contacts):
            contact_person = update_contact_persons(contact_persons)
        if (temp_keywords_with_added and keys_bool) or not bool(keyword):
            for keyword_list in temp_keywords_with_added:
                fuzzy_word = find_similar_words(keyword_list, keyword, 85)
                if fuzzy_word:
                    contact_personsX = [[conpers] for conpers in contact_persons] if len(contact_persons) > 1 else contact_persons
                    new_dict = edit_data(fuzzy_word, dictionary, project_title, project_description, contact_persons, workstreams, dataset_description_list, keywords, keyword)
                    if not new_dict in result:
                        result.append(new_dict)
                    continue
        
        # if (contact_persons and contact_bool) or not bool(keyword):
        if (contact_persons) or not bool(keyword):
            fuzzy_word = find_similar_words([word for persons in contact_persons if isinstance(persons, str) and len(persons) > 10 for word in persons.replace(",", ";").split(";")], keyword, 80)
            if fuzzy_word:
                contact_personsX = [conpers for conpers in contact_persons] if len(contact_persons) > 1 else contact_persons
                new_dict = edit_data(fuzzy_word, dictionary, project_title, project_description, contact_personsX, workstreams, dataset_description_list, keywords, keyword)
                if not new_dict in result:
                    result.append(new_dict)
                continue

        if (workstreams and workstreams_bool) or not bool(keyword):
            fuzzy_word = find_similar_words(workstreams, keyword, 90)
            if fuzzy_word:
                new_dict = edit_data(fuzzy_word, dictionary, project_title, project_description, contact_persons, workstreams, dataset_description_list, keywords, keyword)
                if not new_dict in result:
                    result.append(new_dict)
                continue

        if (project_title and title_bool) or not bool(keyword):
            fuzzy_word = find_similar_words(project_title, keyword, 85)
            if fuzzy_word:
                new_dict = edit_data(fuzzy_word, dictionary, project_title, project_description, contact_persons, workstreams, dataset_description_list, keywords, keyword)
                if not new_dict in result:
                    result.append(new_dict)
                continue
        
        if (rdmo_title and title_bool) or not bool(keyword):
            fuzzy_word = find_similar_words(rdmo_title, keyword, 85)
            if fuzzy_word:
                new_dict = edit_data(fuzzy_word, dictionary, project_title, project_description, contact_persons, workstreams, dataset_description_list, keywords, keyword)
                if not new_dict in result:
                    result.append(new_dict)
                continue

    return result2

def filter_keywords(fuzzy_word, keywords):
    return list(set(word for word in fuzzy_word if word in keywords))

def edit_data(fuzzy_word, dictionary, project_title, project_description, contact_persons, workstreams, dataset_description_list, keywords, keyword, pid_list):
    datasets, dataset_decs = extract_values_from_dataset(dataset_description_list)
    pid_datasets, pid_url = extract_values_from_dataset(pid_list)
    datasets = datasets[0] if len(datasets) == 1 else datasets
    keywords = keywords[0] if len(keywords) == 1 else keywords
    dataset_decs = dataset_decs[0] if len(dataset_decs) == 1 else dataset_decs
    new_dict = result_data_dict(fuzzy_word, dictionary, project_title, project_description, contact_persons, workstreams, datasets, keywords, dataset_decs, keyword, pid_datasets, pid_url)
    return new_dict

def result_data_dict(fuzzy_word, dictionary, project_title, project_description, contact_persons, workstreams, dataset, text_answer, dataset_description, keyword, pid_datasets, pid_url):
    project_title = concatenate_strings_from_list(project_title)
    project_description = concatenate_strings_from_list(project_description)
    contact_persons = [[contact_persons]] if not isinstance(contact_persons, list) else contact_persons
    workstreams = [workstreams] if workstreams and not isinstance(workstreams[0], list) else workstreams
    fuzzy_word = fuzzy_word if isinstance(fuzzy_word, list) else [fuzzy_word]
    dataset = [dataset] if dataset and not isinstance(dataset, list) else dataset
    dataset_description = [dataset_description] if dataset_description and not isinstance(dataset_description, list) else dataset_description
    # pid_datasets = [pid_datasets] if pid_datasets and not isinstance(pid_datasets, list) else pid_datasets
    pid_url = [pid_url] if pid_url and not isinstance(pid_url, list) else pid_url
    text_answer = [text_answer] if text_answer and not isinstance(text_answer, list) else text_answer
    if isinstance(text_answer, list):
        if len(text_answer)==0 or not isinstance(text_answer[0], list):
            text_answer = [text_answer]

    for question_dict in dictionary['questions']:
        if question_dict['question'] == 'What other file formats are created in your project?':
            other_created_file_formats = question_dict['answer']
        elif question_dict['question'] == 'Which data types, in terms of file formats, are created in your project?':
            data_types = question_dict['answer']
        elif question_dict['question'] == 'Do you need special software to process the research data and if so, which one?':
            special_software = question_dict['answer']
        elif question_dict['question'] == 'To what extent are data incurred for your data set or what data volume can be expected for the data set?':
            data_volume = question_dict['answer']
        elif question_dict['question'] == 'How is the data set stored and backed up during the project period?':
             data_storage = question_dict['answer']

        if not keyword:
            fuzzy_word = []
        
    new_dict = {
        'RDMOtitle': dictionary['RDMOtitle'],
        'Project title': project_title,
        'Project description': project_description,
        'Contact persons': contact_persons,
        'Workstreams': workstreams,
        'Dataset': dataset,
        'Dataset description': dataset_description,
        'Keywords': text_answer,
        'Searched word': fuzzy_word,
        'pid': pid_url,
        'Created': dictionary.get('additional', [{}])[0].get('created'),
        'Updated': dictionary.get('additional', [{}])[0].get('updated'),
        'User match' : [keyword],
        'File formats': merge_lists(create_output(dataset, data_types), create_output(dataset, other_created_file_formats)),
        'Special Software': create_output(dataset, special_software),
        'Data volume': create_output(dataset, data_volume),
        'Data storage': create_output(dataset, data_storage)

    }
    return new_dict

def merge_lists(list1, list2):
    for sublist1, sublist2 in zip(list1, list2):
        if sublist1:
            if 'Other' in sublist1:
                sublist1.remove('Other')
                sublist1.extend(sublist2)
    return list1

def create_output(dataset, other_file_format):
    output = [[] for _ in range(len(dataset))]
    for item in other_file_format:
        dataset_name = item['dataset']
        text_answer = item['text_answer']
        option_answer = item['option_answer']
        
        for i, data_entry in enumerate(dataset):
            if isinstance(data_entry, list) and data_entry[0] == dataset_name:
                output[i] = text_answer + option_answer
                break
            elif isinstance(data_entry, str) and data_entry == dataset_name:
                output[i] = text_answer + option_answer
                break
    return output

def concatenate_strings_from_list(input_list):
    if isinstance(input_list, list) and all(isinstance(item, str) for item in input_list) and len(input_list) > 0:
        return ", ".join(input_list)
    else:
        return input_list
    
def extract_values_from_dataset(list_of_dicts):
    dataset_values = [[d["dataset"]] for d in list_of_dicts if "dataset" in d]
    text_answer_values = [d["text_answer"] for d in list_of_dicts if "text_answer" in d]
    return dataset_values, text_answer_values

def merge_dicts_with_identical_values(dict_list, words):
    merged_dict_list = []
    for curr_dict in dict_list:
        match_found = False
        for merged_dict in merged_dict_list:
            if all(curr_dict[key] == merged_dict[key] for key in curr_dict if key != "Searched word" and key != "User match"):
                for word in curr_dict["Searched word"]:
                    if word not in merged_dict["Searched word"]:
                        merged_dict["Searched word"].append(word)
                for word in curr_dict["User match"]:
                    if word not in merged_dict["User match"]:
                        merged_dict["User match"].append(word)
                match_found = True
                break
        if not match_found:
            merged_dict_list.append(curr_dict)

    if not words:
        for merged_dict in merged_dict_list:
            merged_dict["User match"] = []
            merged_dict["Searched word"] = []
    return merged_dict_list

def get_data(search_json_file, results, data, workstreams_bool, keys_bool, contact_bool, title_bool, word, no_keyword = False):
    search_result = search_json_file(data, word, workstreams_bool, keys_bool, contact_bool, title_bool, no_keyword)
    if search_result:
        for result in search_result:
            if result not in results:
                results.append(result)

def apply_filters(merged_dicts, workstream_filter, data_type_filter, chair_filter, logical_and=True):
    filters = [
        ("Workstreams", workstream_filter),
        ("Data Types", data_type_filter),
        ("Chair", chair_filter)
    ]
    filtered_dicts = merged_dicts
    for field, filter_list in filters:
        if any(filter_list) and any(filter_list[0].strip()):
            filtered_dicts = [d for d in filtered_dicts if (all if logical_and else any)(recursive_list_contains_value(d.get(field, []), value) for value in filter_list)]

    return filtered_dicts

def recursive_list_contains_value(nested_list, value):
    return any(isinstance(item, list) and recursive_list_contains_value(item, value) or item == value for item in nested_list)

def sort_dictionaries(data, key='RDMOtitle', date_key=None, ascending=True):
    date_format = '%d.%m.%Y %H:%M'
    sorted_data = sorted(data, key=lambda x: get_key(x), reverse=not ascending)
    if date_key:
        for item in sorted_data:
            if date_key in item and isinstance(item[date_key], str):
                try:
                    item_date = datetime.strptime(item[date_key], date_format)
                    item[date_key] = item_date.strftime(date_format)
                except ValueError:
                    pass
        sorted_data = sorted(sorted_data, key=lambda x: datetime.strptime(x.get(date_key, '01.01.1970 00:00'), date_format) if isinstance(x.get(date_key), str) else None, reverse=not ascending)
        for item in sorted_data:
            if date_key in item and isinstance(item[date_key], str):
                try:
                    item[date_key] = datetime.strptime(item[date_key], date_format).strftime(date_format)
                except ValueError:
                    pass
    return sorted_data

def get_key(item):
    keys = key.split('.')
    current = item
    for k in keys:
        current = current.get(k)
        if current is None:
            return ''
        elif isinstance(current, list):
            if len(current) > 0:
                current = current[0]
            else:
                return ''
    return current

def return_formatted_pid_list(data):
    results = []
    workstreams_bool, keys_bool, contact_bool, title_bool = True,True,True,True
    word = ""
    words=[""]
    get_data(search_json_file, results, data, workstreams_bool, keys_bool, contact_bool, title_bool, word, no_keyword=True)
    merged_dicts = merge_dicts_with_identical_values(results, words)
    return merged_dicts


if __name__ == '__main__':
    words = json.loads(sys.argv[1])
    workstream_filter = json.loads(sys.argv[2])
    sort_by = sys.argv[3]
    sort_order = sys.argv[4]
    and_or_filter = sys.argv[5] != "OR"

    data_grabber_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    file_path = os.path.join(data_grabber_dir, 'data_grabber', 'target', 'sampleXanonymized.json')
    data_type_filter = [""]
    chair_filter = [""]

    results = []
    data = open_json_file(file_path) #json file mit den infors wie bei pids
    workstreams_bool, keys_bool, contact_bool, title_bool = True,True,True,True
    if words:
        for word in words:
            get_data(search_json_file, results, data, workstreams_bool, keys_bool, contact_bool, title_bool, word)
    else: get_data(search_json_file, results, data, workstreams_bool, keys_bool, contact_bool, title_bool, "")

    merged_dicts = merge_dicts_with_identical_values(results, words)

    key = sort_by if sort_by in ['RDMOtitle', 'Project title'] else 'RDMOtitle'
    date_key = sort_by if sort_by in ['Created', 'Updated'] else None
    ascending = sort_order == 'ascending'

    sorted_dicts = sort_dictionaries(merged_dicts, key=key, date_key=date_key, ascending=ascending)
    print(json.dumps(apply_filters(sorted_dicts, workstream_filter, data_type_filter, chair_filter, and_or_filter)))