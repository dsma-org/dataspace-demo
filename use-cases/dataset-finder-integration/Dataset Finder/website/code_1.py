from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response, session, url_for, send_from_directory
from flask_mail import Mail, Message
from flask_session import Session
from to_execute import get_workstreams, open_json_file, create_title_email_file, return_formatted_pid_list
from visu import get_matplotlib_chart, get_dataformats, get_other_dataformats, get_storage_types, get_publication, get_dataset_storage_amount, get_subsequent_use
from auth import get_auth_data, is_token_expired, refresh_access_token
from email_client import send_email_to_owner
from bs4 import BeautifulSoup
import subprocess, json, os, time, re, requests
from urllib.parse import urlparse

app = Flask(__name__)


app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 31536001
Session(app)

def login_required(f):
    def inner_function(*args, **kwargs):
        if not session.get('exp'):

            return redirect('/')
        return f(*args, **kwargs)
    return inner_function

def is_authenticated():
    exp = session.get('exp')
    if exp and not is_token_expired(exp):
        return True
    else:
        return False


@app.route('/')
def index():
    code = request.args.get('code')
    if code:
        try: 
            access_token, refresh_token, sub, exp = get_auth_data(code, "", "")
        except Exception as e:
            return render_template('login.html')
        session['exp'] = exp

    exp = session.get('exp')
    if exp and not is_token_expired(exp):
        return redirect('/main')
    
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    code = request.form.get('code')
    username = request.form.get('username')
    password = request.form.get('password')
    try: 
        access_token, refresh_token, sub, exp = get_auth_data(code, username, password)
    except Exception as e:
        return render_template('login.html')    
    if not is_token_expired(exp):
        # Authenticate using code
        session['exp'] = exp
        # Redirect to main page after successful login
        return redirect('/main')

    else:
        # Invalid login attempt, redirect back to login page
        return redirect('/')

@app.route('/main')
def main():
    if not is_authenticated():
        return redirect('/')
    if not session.get('consent_given'):
        return redirect(url_for('privacy_warning'))
    
    update_session_activity()
    session.setdefault('sort_by', 'Updated')
    session.setdefault('sort_order', 'descending')
    session.setdefault('logicOperator', 'OR')
    search_list = session.get('search_list', [])
    workstreams = app.config['WORKSTREAMS']
    selected_WS = session.get('selected_workstreams', [])

    curr_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    file_path = os.path.join(curr_dir, 'data_grabber', 'target', 'sampleX.json')
    last_updated = os.path.getmtime(file_path)
    last_updated_str = time.strftime('%H:%M %d.%m.%Y', time.localtime(last_updated))

    return render_template('index.html', search_list=search_list, workstreams=workstreams, app=app, selected_WS=selected_WS, last_updated=last_updated_str)


@app.route('/wrong-website')
def wrong_website():
    return render_template('wrong_website.html')


@app.route('/privacy_warning', methods=['GET', 'POST'])
def privacy_warning():
    if not is_authenticated():
        return redirect('/')

    if request.method == 'POST':
        session['consent_given'] = True
        return redirect(url_for('index'))

    if session.get('consent_given'):
        return redirect(url_for('index'))

    return render_template('privacy_warning.html')

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/imprint')
def imprint():
    return render_template('imprint.html')

@app.route('/give_consent', methods=['POST'])
def give_consent():
    if not is_authenticated():
        return redirect('/')

    session['consent_given'] = True
    return redirect(url_for('index'))

@app.route('/add_word', methods=['POST'])
def add_word():
    if not is_authenticated():
        return redirect('/')

    word_list = request.form['word'].split(',')
    session['search_list'] = []
    for word in word_list:
        word = word.strip()
        if word:
            search_list = session.get('search_list', [])
            if not word in search_list:
                search_list.append(word)
                session['search_list'] = search_list
    return redirect(url_for('index'))

@app.route('/execute', methods=['POST'])
def execute():
    if not is_authenticated():
        return redirect('/')

    search_list = session.get('search_list', [])
    sort_by = session.get('sort_by')
    sort_order = session.get('sort_order')
    logic_operator = session.get('logicOperator')
    workstream_filter = session.get('selected_workstreams', [])
    result = execute_python_code(search_list, workstream_filter, sort_by, sort_order, logic_operator)
    for entry in result:
        if 'Contact persons' in entry and isinstance(entry['Contact persons'], list):
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}'
            orcid_pattern = r'\d{4}-\d{4}-\d{4}-\d{3}[X\d]'
            chair_pattern = r'[;,]\s*([^;,]+)[;,]'

            contact_info = []
            for contact in entry['Contact persons']:
                contact_parts = re.split(r'[;,]', contact)
                name = contact_parts[0].strip()
                email_matches = re.findall(email_pattern, contact)
                orcid_matches = re.findall(orcid_pattern, contact)
                chair_matches = re.findall(chair_pattern, contact)

                email = ', '.join(email_matches) if email_matches else None
                orcid = orcid_matches[0] if orcid_matches else None
                chair = chair_matches[0] if chair_matches else None

                contact_info.append({
                    'Name': name,
                    'Chair': chair,
                    'Email': email,
                    'ORCID': orcid
                })

            entry['Contact Info'] = contact_info

    if not isinstance(result, list):
        result = []
    return result, search_list

@app.route('/sortX', methods=['GET'])
def sortX():
    sort_by = request.args.get('sort_by')
    sort_order = request.args.get('sort_order')
    session['sort_by'] = sort_by
    session['sort_order'] = sort_order
    return  '', 204

@app.route('/dropdown', methods=['POST'])
def dropdown():
    session['selected_workstreams'] = []
    selected_WS = request.form.getlist('numbers')
    workstreams = session.get('selected_workstreams', [])
    workstreams = [number for number in workstreams if number not in selected_WS]  # Remove unchecked numbers
    workstreams.extend(selected_WS)  # Add checked numbers
    session['selected_workstreams'] = workstreams
    return '', 204

@app.route('/andor', methods=['POST'])
def andor():
    logic_operator = request.form.get('logicOperator')
    session['logicOperator'] = logic_operator
    return '', 204

@app.route('/click', methods=['POST'])
def click_function():
    add_word()
    search_list = session.get('search_list', '')
    sort_by = session.get('sort_by', 'Updated')
    sort_order = session.get('sort_order', 'descending')
    logic_operator = session.get('logicOperator', 'OR')
    selected_WS = session.get('selected_workstreams', [])

    redirect_url = url_for('results', sort_by=sort_by, sort_order=sort_order,
                           logicOperator=logic_operator, search_list=','.join(search_list),
                           selected_workstreams=','.join(selected_WS))

    return redirect(redirect_url)

@app.route('/results')
def results():
    # access url params
    sort_by = request.args.get('sort_by', 'Updated')
    sort_order = request.args.get('sort_order', 'descending')
    logic_operator = request.args.get('logicOperator', 'OR')
    search_list = request.args.getlist('search_list')[0].split(',') if request.args.getlist('search_list') else []
    selected_workstreams = request.args.getlist('selected_workstreams')[0].split(',') if request.args.getlist('selected_workstreams') else []

    session_vars = {
        'sort_by': sort_by,
        'sort_order': sort_order,
        'logicOperator': logic_operator,
        'search_list': search_list,
        'selected_workstreams': selected_workstreams
    }
    session.update(session_vars)

    result, _ = execute()
    return render_template('results.html', result=result, search_list=session.get('search_list'), app=app, word=", ".join(search_list), selected_WS=session.get('selected_workstreams'), transform_dataset=transform_dataset)



    
def make_urls_clickable(text):
    if isinstance(text, list):
        # Apply make_urls_clickable to each item in the list and return a list of results
        return [make_urls_clickable(item) for item in text]
    
    if not isinstance(text, str):
        return text
    
    url_pattern = re.compile(r'(https?://[^\s]+)')
    
    def replace_with_link(match):
        url = match.group(0)
        display_name = get_display_name(url, use_image=True)
        return f'<a href="{url}" target="_blank">{display_name}</a>'
    
    return url_pattern.sub(replace_with_link, text)



def get_display_name(url, first_time = False,use_image=True):
    url_name_pairs = {}
    if not first_time:
        url_name_pairs = app.config['url_name_pairs']
    
    
    if url in url_name_pairs:
        subdomain = url_name_pairs[url]
        if subdomain == "Coscine" and use_image:
            return '<img src="/static/coscine.png" alt="Coscine" style="height: 16px; width: auto;">'
        return subdomain
    
    try:
        response = requests.get(url, allow_redirects=True)
        final_url = response.url
        
        parsed_url = urlparse(final_url)
        domain_parts = parsed_url.netloc.split('.')
        
        if domain_parts[0] in ['www', 'm']:
            domain_parts.pop(0)
        
        if len(domain_parts) > 2:
            subdomain = domain_parts[0].capitalize()
        elif len(domain_parts) == 2:
            subdomain = domain_parts[0].capitalize() 
        else:
            subdomain = domain_parts[-1].capitalize() 
        
        if subdomain == "Coscine" and use_image:
            return '<img src="/static/coscine.png" alt="Coscine" style="height: 16px; width: auto;">'
        else:
            return subdomain
    
    except requests.exceptions.RequestException as e:
        print(f"Error accessing URL: {e}")
        return url

# register function in Jinja2 environment
app.jinja_env.globals.update(get_display_name=get_display_name)
app.jinja_env.globals.update(make_urls_clickable=make_urls_clickable)

@app.route('/reset', methods=['POST'])
def reset():
    session['selected_workstreams'] = []
    session['search_list'] = []
    session['logicOperator'] = 'OR'
    session['sort_by'] = 'Updated'
    session['sort_order'] = 'descending'
    return redirect(url_for('main'))

@app.route('/logout', methods=['POST'])
def logout():
    session['exp'] = False
    return redirect('/')

def execute_python_code(words, workstream_filter, sort_by, sort_order, logic_operator):
    file_path = os.path.join(get_file_directory(), 'website', 'to_execute.py')
    words_json = json.dumps(words)
    workstream_filter_json = json.dumps(workstream_filter)

    command = ['python', file_path, words_json, workstream_filter_json, sort_by, sort_order, logic_operator]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    if error:
        a_err = error.decode()
        return f'An error occurred: {a_err}'

    result = parse_output(output.decode())
    return result

def get_file_directory():
    directory = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    return directory

def parse_output(output):
    try:
        result = json.loads(output)
        return result
    except json.JSONDecodeError as e:
        return f'Error decoding JSON output: {str(e)}'

def update_session_activity():
    session['last_activity'] = time.time()

@app.template_filter('highlight_matching_words')
def highlight_matching_words(text, searched_words):
    if text:
        if isinstance(text, list):
            text = ' '.join(text)
        highlighted_text = text
        for searched_word in searched_words:
            pattern = re.compile(re.escape(searched_word), re.IGNORECASE)
            highlighted_text = pattern.sub(f'<span class="highlight-word">\g<0></span>', highlighted_text)
        return highlighted_text
    return " "

def transform_dataset(value):
    if isinstance(value, list):
        result = ', '.join(map(str, value))
    else:
        result = str(value)
    return result


@app.route('/details', methods=['GET', 'POST'])
def details():
    if request.method == 'POST':
        print("post methode gewaehlt")
    elif request.method == 'GET':
        print("get methode gewaehlt")
        content = request.args.get('content')

        soup = BeautifulSoup(content, 'html.parser')

        dataset = soup.select_one('.reduce-spacing strong:contains("Dataset") + br + span').text.strip()

        dataset = soup.select_one('.reduce-spacing strong:contains("Dataset") + br + span').text.strip()
        dataset_description = soup.select_one('.reduce-spacing strong:contains("Dataset Description") + br + span').text.strip()
        keywords = soup.select_one('.reduce-spacing strong:contains("Keywords") + br + span').text.strip()
        file_formats = soup.select_one('.reduce-spacing strong:contains("File Formats") + br + span').text.strip()
        software = soup.select_one('.reduce-spacing strong:contains("Software") + br + span').text.strip()
        data_volume = soup.select_one('.reduce-spacing strong:contains("Data Volume") + br + span').text.strip()
        storage = soup.select_one('.reduce-spacing strong:contains("Storage") + br + span').text.strip()

        # Create a dictionary with extracted information
        extracted_info = {
            'Dataset': dataset,
            'Dataset Description': dataset_description,
            'Keywords': keywords,
            'File Formats': file_formats,
            'Software': software,
            'Data Volume': data_volume,
            'Storage': storage,

        }
        
        # Use url_for to generate the URL dynamically
        dynamic_url = url_for('details_dataset', dataset=dataset)

        return render_template('details.html', extracted_info=extracted_info, dynamic_url=dynamic_url)

    return "Invalid request"

@app.route('/details/<dataset>')
def details_dataset(dataset):
    # return "Details for dataset"
    return f"Details for dataset: {dataset}"

@app.route('/statistics')
def statistics():
    if not is_authenticated():
        return redirect('/')

    get_matplotlib_chart()
    get_dataformats()
    get_other_dataformats()
    get_storage_types()
    get_publication()
    get_dataset_storage_amount()
    get_subsequent_use()

    image_files = [
        'formats-chart.png',
        'other-formats-chart.png',
        'publication.png',
        'storage_amount.png',
        'storage_types.png',
        'ws-chart.png',
        'subsequent.png'
    ]
    image_paths = [url_for('static', filename='images/' + filename) for filename in image_files]

    return render_template('statistics_public.html', image_paths=image_paths)

def load_workstreams(data):
    workstreams = get_workstreams(data)
    app.config['WORKSTREAMS'] = workstreams

def get_sorting_data():
    data = ['Project title','Project description','Contact persons','Workstreams','Dataset','Dataset description','Keywords','Searched word','Created','Updated']
    data2 = ['Project title','Created','Updated']
    app.config['sorting_list'] = data2

def load_nbr_projects_datasets(data):
    total_unique_datasets = 0
    for entry in data:
        unique_datasets = set()
        for question in entry['questions']:
            if 'answer' in question:
                if isinstance(question['answer'], list):
                    for answer in question['answer']:
                        unique_datasets.add(answer['dataset'])
        total_unique_datasets += len(unique_datasets)
    app.config['NumDATASETS'] = total_unique_datasets
    app.config['NumPROJECTS'] = len(data)


@app.route('/contact_form')
def contact_form():
    return render_template('contact_form.html')

@app.route('/send_email', methods=['POST'])
def send_email():
    rdmo_title = session.get('rdmo_title_sess')
    subject = request.form['subject']
    message = request.form['message']
    sender_mail = request.form['sender_mail']

    result = send_email_to_owner(subject, message, sender_mail, ContactPersons(rdmo_title))
    return result

def ContactPersons(rdmo_title):
    title_email_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'data_grabber', 'target', 'titleEmail.json')
    data = open_json_file(title_email_file_path)

    emails = []
    for entry in data:
        if 'rdmo_title' in entry and entry['rdmo_title'][0] == rdmo_title:
            if 'contact_persons' in entry:
                emails.extend(entry['contact_persons'])

    return emails


@app.route('/execute_flask_function', methods=['POST'])
def execute_flask_function():
    data = request.get_json()
    rdmo_title = data.get('rdmoTitle')

    if rdmo_title is not None:
        session['rdmo_title_sess'] = rdmo_title
        return jsonify({'message': 'Function executed successfully'}), 200
    else:
        return jsonify({'error': 'Entry ID or RDMO title not provided'}), 400
    
def get_urls(data):
    urls = []
    url_pattern = re.compile(r'https?://[^\s/$.?#].[^\s]*')
    for entry in data:
        for text in entry.get('text_answer', []):
            found_urls = url_pattern.findall(text)
            urls.extend(found_urls)
    return urls

def get_contact_info(result):

    search_list = session.get('search_list', [])
    sort_by = session.get('sort_by')
    sort_order = session.get('sort_order')
    logic_operator = session.get('logicOperator')
    workstream_filter = session.get('selected_workstreams', [])
    
    for entry in result:
        if 'Contact persons' in entry and isinstance(entry['Contact persons'], list):
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}'
            orcid_pattern = r'\d{4}-\d{4}-\d{4}-\d{3}[X\d]'
            chair_pattern = r'[;,]\s*([^;,]+)[;,]'

            contact_info = []
            for contact in entry['Contact persons']:
                contact_parts = re.split(r'[;,]', contact)
                name = contact_parts[0].strip()
                email_matches = re.findall(email_pattern, contact)
                orcid_matches = re.findall(orcid_pattern, contact)
                chair_matches = re.findall(chair_pattern, contact)

                email = ', '.join(email_matches) if email_matches else None
                orcid = orcid_matches[0] if orcid_matches else None
                chair = chair_matches[0] if chair_matches else None

                contact_info.append({
                    'Name': name,
                    'Chair': chair,
                    'Email': email,
                    'ORCID': orcid
                })

            entry['Contact Info X'] = contact_info

    if not isinstance(result, list):
        result = []
    return result, search_list 

@app.route('/links')
def links():
    total_links = app.config['Total_Links_PIDS']
    formatted_pid_list = return_formatted_pid_list(total_links)
    formatted_pid_list, _ = get_contact_info(formatted_pid_list)
    return render_template('links.html', links=total_links, result=formatted_pid_list)

@app.route('/coscine_links')
def coscine_links():
    coscine_links = app.config['Total_Coscine_PIDS']
    cached_links = coscine_links[:] # faster processing
    pid_metadata = [(pid, len(pid)) for pid in coscine_links]
    pid_mod = [pid for pid, length in pid_metadata if length % 2 == 0]
    formatted_pid_list = return_formatted_pid_list(coscine_links)
    formatted_pid_list, contact_info = get_contact_info(formatted_pid_list)
    cloned_pid_list = [pid for pid in formatted_pid_list]
    active_pids = [pid for pid in cloned_pid_list if pid.get('status') == 'active']
    pid_lgh = sum([len(pid) for pid in active_pids])
    return render_template('coscine_links.html', links=coscine_links, result=formatted_pid_list)


def load_total_coscine_stats(data):
    project_coscine_set = set()
    project_all_set = set()
    parsed_data = {}
    coscine_pids = []
    total_pids = []


    for dictionary in data:
        result = []
        for question_dict in dictionary['questions']:
            question = question_dict['question']
            answer = question_dict['answer']

            if question == 'Provide a brief description of your data set.':
                dataset_description_list = answer
                a = get_urls(dataset_description_list)
                result.extend(a)
            elif question == 'PID of the dataset or of related works':
                pid_list = answer
                b = get_urls(pid_list)
                result.extend(b)

        if result:
            for url in result:
                res = get_display_name(url,True)
                dict_id = json.dumps(dictionary, sort_keys=True) 
                if "Coscine" in res:
                    coscine_pids.append(url)
                    project_coscine_set.add(dict_id)
                    res = "Coscine"
                if "rwth-aachen" in url:
                    res = "connector"
                project_all_set.add(dict_id)
                total_pids.append(url)
                parsed_data[url] = res


    project_coscine = [json.loads(dict_id) for dict_id in project_coscine_set]
    project_all = [json.loads(dict_id) for dict_id in project_all_set]

    app.config['NumLinksPids'] = len(total_pids)
    app.config['NumCoscine'] = len(coscine_pids)
    app.config['Total_Links_PIDS'] = project_all
    app.config['Total_Coscine_PIDS'] = project_coscine
    app.config['url_name_pairs'] = parsed_data


def load_stuff():
    data_grabber_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    file_path = os.path.join(data_grabber_dir, 'data_grabber', 'target', 'sampleXanonymized.json')
    file_path_to_sampleX = os.path.join(data_grabber_dir, 'data_grabber', 'target', 'sampleX.json')
    title_email_file_path = os.path.join(data_grabber_dir, 'data_grabber', 'target', 'titleEmail.json')
    data = open_json_file(file_path)
    create_title_email_file(open_json_file(file_path_to_sampleX), title_email_file_path)
    load_nbr_projects_datasets(data)
    load_workstreams(data)
    load_total_coscine_stats(data)
    get_sorting_data()

if __name__ == '__main__':
    load_stuff()
    app.run(host='0.0.0.0')
