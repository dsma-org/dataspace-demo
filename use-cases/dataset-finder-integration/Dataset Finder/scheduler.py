import schedule, time, os, subprocess

def run_daily_job():
    # daily restart at 2 a.m.
    schedule.every().day.at("02:00").do(run_main)

def run_main():
    # execute main.py
    current_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    main_path = os.path.join(current_dir, 'app', 'data_grabber', 'main.py')
    token = os.environ.get('RDMO_TOKEN')

    while True:
        try:
            subprocess.run(['python', main_path, token], check=True)
            break  # exit loop if subprocess completes successfully
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")
            print("Retrying...")
            time.sleep(60) # rerun after 60 seconds

    # subprocess.run(['python', main_path, token])

def run_code_1():
    # execute code_1.py
    current_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    code1_path = os.path.join(current_dir, 'app', 'website', 'code_1.py')
    subprocess.Popen(['python', code1_path])

if __name__ == "__main__":
    run_daily_job()
    run_main()
    run_code_1()

    while True:
        schedule.run_pending()
        time.sleep(60)
