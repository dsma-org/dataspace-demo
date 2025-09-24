from to_execute import open_json_file
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os, time, re

def get_ws_data():
    data_grabber_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    file_path = os.path.join(data_grabber_dir, 'data_grabber', 'target', 'sampleX.json')
    data = open_json_file(file_path)
    ws_result = []
    contact_result = []
    data_type = []
    other_data_type = []
    data_storage_type = []
    publishing = []
    keywords = []
    storage = []
    subsequent_use = []

    for dictionary in data:
        for question_dict in dictionary['questions']:
            question = question_dict['question']
            answer = question_dict['answer']

            if question == 'What workstreams are involved?':
                ws_result.append(answer.get('option_answer', []))
            elif question == 'Who are the responsible contact persons for this project?':
                contact_result.append(answer.get('text_answer', []))
            elif question == 'Which data types, in terms of file formats, are created in your project?':
                extract_answer_data(answer, data_type)
            elif question == 'What other file formats are created in your project?':
                extract_answer_data(answer, other_data_type)
            elif question == 'How is the data set stored and backed up during the project period?':
                extract_answer_data(answer, data_storage_type)
            elif question == 'Enter a few content keywords.':
                for keyword_dict in question_dict['answer']:
                    if keyword_dict['option_answer']:
                        keywords.append(keyword_dict['option_answer'])
                    if keyword_dict['text_answer']:
                        keywords.append(keyword_dict['text_answer'])
            elif question == 'Do you plan to publish the data? If yes, where?':
                if answer:
                    for i in answer:
                        option_answer = i['option_answer']
                        if option_answer:
                            publishing.append(option_answer)
                else:
                    publishing.append(['No Data'])

            elif question == 'Does this data set lend itself to subsequent use in other contexts?':
                if answer:
                    for i in answer:
                        option_answer = i['option_answer']
                        if option_answer:
                            subsequent_use.append(option_answer)
                else:
                    subsequent_use.append(['No Data'])


            elif question == 'To what extent are data incurred for your data set or what data volume can be expected for the data set?':
                for q_dict in question_dict['answer']:
                    if q_dict['option_answer']:
                        storage.append(q_dict['option_answer'])

            
    return [ws_result, contact_result, data_type, other_data_type, data_storage_type, publishing, keywords, storage, subsequent_use]

def extract_answer_data(answer, data_type_list):
    if answer:
        for i in answer:
            text_answer = i['text_answer']
            option_answer = i['option_answer']
            if text_answer:
                data_type_list.append(text_answer)
            if option_answer:
                data_type_list.append(option_answer)

def count_elements_occurrences(input_list):
    element_counts = {}
    
    for sublist in input_list:
        if not sublist:
            element = "No Data"
            element_counts[element] = element_counts.get(element, 0) + 1
        else:
            for element in sublist:
                element_counts[element] = element_counts.get(element, 0) + 1

    element_counts["Total Projects"] = len(input_list)
    return element_counts
 
def wrap_label(label, max_length=30):
    if len(label) > max_length:
        return '\n'.join([label[i:i+max_length] for i in range(0, len(label), max_length)])
    else:
        return label

def visualize_element_counts(data_counts, file_name, x_axis, chart_title, chart_rotation, chart_fontsize, dpi=400):
    data_grabber_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    save_path = os.path.join(data_grabber_dir, 'website', 'static', 'images', file_name)
    if os.path.exists(save_path):
        # get the modification time of the file
        file_mtime = os.path.getmtime(save_path)
        current_time = time.time()
        a = current_time - file_mtime
        if current_time - file_mtime < 86400:
            # create a new image every X seconds. Right now, every day
            return save_path

    categories = list(data_counts.keys())
    counts = list(data_counts.values())

    if "Total Projects" in categories:
        total_projects_index = categories.index("Total Projects")
        total_projects_count = counts.pop(total_projects_index)
        categories.remove("Total Projects")

    wrapped_categories = [wrap_label(category) for category in categories]
    bar_widths = [len(label) for label in wrapped_categories]

    max_figure_width = 16
    total_width = sum(bar_widths) + 4
    fig_width = min(total_width, max_figure_width)

    fig, ax = plt.subplots(figsize=(fig_width, 6))

    bars = ax.bar(wrapped_categories, counts, alpha=0.7, edgecolor='black', linewidth=1.2, zorder=2)

    plt.xlabel(x_axis, fontsize=12)
    plt.ylabel('Counts', fontsize=12)
    if chart_title == 'RDMO Project Distribution':
        plt.title(chart_title + f' (Total Projects: {total_projects_count})', fontsize=16)
    else: 
        plt.title(chart_title, fontsize=16)
    plt.xticks(rotation=chart_rotation, ha='center', fontsize=chart_fontsize)
    plt.yticks(fontsize=10)

    ax.set_axisbelow(True)
    ax.grid(axis='y', linestyle='--', alpha=0.7, zorder=0)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() - 0.5, str(count),
                 ha='center', va='top', fontsize=10, fontweight='bold', color='white', zorder=3, alpha=1)

    plt.tight_layout()
    plt.savefig(save_path, dpi=dpi)
    plt.close()
    return save_path


def extract_names_from_list(input_list):
    name_pattern = r'\b[A-Za-zÄÖÜßäöü-]+\s+[A-Za-zÄÖÜßäöü-]+(?!\s*[A-Za-z]+\s*:)\b'
    names = []
    for item in input_list:
        names.extend(re.findall(name_pattern, item))
    return names

def sort_keys(input_dict):
    sorted_keys = sorted(input_dict.keys())
    sorted_dict = {key: input_dict[key] for key in sorted_keys}
    return sorted_dict

def get_matplotlib_chart():
    raw_data = get_ws_data()[0]
    return visualize_element_counts(sort_keys(count_elements_occurrences(raw_data)), 'ws-chart.png', 'Workstreams', 'RDMO Project Distribution',45,10)

def get_person_data():
    persons = get_ws_data()[1]
    all_names = [extract_names_from_list(sub_list) for sub_list in persons]
    flat_names = count_elements_occurrences(sorted(all_names))
    for dont_include in ['Total Projects', 'WZL MQ-MS', 'No Data', 'Communication Science']:
        flat_names.pop(dont_include)
    return visualize_element_counts(sort_keys(flat_names), 'persons-chart.png', 'Persons', 'Responsible Persons in all RDMO Projects',75,5)

def get_dataformats():
    formats = get_ws_data()[2]
    ce = count_elements_occurrences(formats)
    ce.pop('Total Projects')
    return visualize_element_counts(sort_keys(ce), 'formats-chart.png', 'Data Formats', 'Created Datatypes in all Projects',45,10)

def get_other_dataformats():
    formats = get_ws_data()[3]
    ce = count_elements_occurrences(formats)
    ce.pop('Total Projects')
    return visualize_element_counts(sort_keys(ce), 'other-formats-chart.png', 'Other Data Formats', 'Other Created Datatypes in all Projects',75,5)

def get_storage_types():
    storages = get_ws_data()[4]
    ce = count_elements_occurrences(storages)
    ce.pop('Total Projects')
    return visualize_element_counts(sort_keys(ce), 'storage_types.png', 'Storage Type', 'How the Data is Stored During Project Period',75,5)

def get_publication():
    pubs = get_ws_data()[5]
    cleaned_list = [[item[0].replace(", here", "").replace(", because", "")] for item in pubs]
    ce = count_elements_occurrences(cleaned_list)
    return visualize_element_counts(sort_keys(ce), 'publication.png', 'Answer', 'Do you plan to publish the data?',45,10)

def get_dataset_storage_amount():
    storage_amount = get_ws_data()[7]
    ce = count_elements_occurrences(storage_amount)
    ce.pop('Total Projects')
    return visualize_element_counts(sort_keys(ce), 'storage_amount.png', 'Data Volume', 'Expected data volume for the data sets',45,5)


def get_subsequent_use():
    pubs = get_ws_data()[8]
    cleaned_list = [[item[0].replace(", as follows", "").replace(", because", "")] for item in pubs]
    ce = count_elements_occurrences(cleaned_list)
    return visualize_element_counts(sort_keys(ce), 'subsequent.png', 'Answer', 'Does this data set lend itself to subsequent use in other contexts?',45,10)


def count_words(word_list):
    word_counts = {}
    
    for phrase in word_list:
        # Split each phrase into words using whitespace and commas as separators
        words = [word.strip() for word in phrase.lower().split(',')]

        for word in words:
            # Remove '#' and leading/trailing spaces from words
            word = word.strip('# ')

            if word:
                # Update the word count dictionary
                if word in word_counts:
                    word_counts[word] += 1
                else:
                    word_counts[word] = 1

    # Sort the word counts in descending order by count
    sorted_word_counts = dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True))

    return sorted_word_counts

def get_top_words(word_list, x):
    word_counts = {}
    
    for phrase in word_list:
        # Split each phrase into words using whitespace and commas as separators
        words = [word.strip() for word in phrase.lower().split(',')]

        for word in words:
            # Remove '#' and leading/trailing spaces from words
            word = word.strip('# ')

            if word:
                # Update the word count dictionary
                if word in word_counts:
                    word_counts[word] += 1
                else:
                    word_counts[word] = 1

    # Sort the word counts in descending order by count
    sorted_word_counts = dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True))

    # Get the top x words
    top_words = list(sorted_word_counts.keys())[:x]

    return top_words

def get_keywords():
    keys = get_ws_data()[6]
    ce = count_elements_occurrences(keys)
    keylist = []
    for i in keys:
        keylist.extend(i)