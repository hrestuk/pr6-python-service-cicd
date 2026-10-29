def test_required_files_exist(host):
    assert host.file("/app/app.py").is_file
    assert host.file("/app/requirements.txt").is_file

def test_python_process_runs_as_non_root(host):
    process = host.process.get(user="appuser", comm="python")

    assert process.user == "appuser"
    assert process.euid != 0

def test_application_port_is_listening(host):
    assert host.socket("tcp://0.0.0.0:5000").is_listening
