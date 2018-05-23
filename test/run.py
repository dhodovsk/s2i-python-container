import time
import subprocess
import os

import conu


WEB_APPS = [s + "-test-app" for s in ["standalone", "setup", "setup-requirements", "django", "numpy",
                                      "app-home", "npm-virtualenv-uwsgi", "locale", "mod-wsgi", "pipenv"]]

test_dir = subprocess.check_output(["readlink", "-zf", subprocess.check_output(["dirname", "\"${BASH_SOURCE[0]}\""])])
image_dir = subprocess.check_output(["readlink", "-zf", test_dir+"/.."])

# if version is null ERROR version must be set

IMAGE_NAME = "centos/python-27-centos7"

test_port = 8080

cid_file = ""
s2i_args = ""
global cid_file, s2i_args, CONTAINER_ARGS


def info(text):
    print('\033[1m' + '[INFO] ' + text + '\033[0m')


def image_exists(image_name):  # if exists should return true
    with open(os.devnull, 'w') as devnull:
        subprocess.call(['docker', 'inspect', image_name], stdout=devnull, stderr=devnull)


def container_exists():  # if exists should return true
    image_exists(subprocess.check_output(["cat", cid_file]).strip())


def container_ip():  # should return IP address
    return subprocess.check_output(["docker", "inspect", "--format=\"{{ .NetworkSettings.IPAddress }}\"",
                     subprocess.check_output(["cat", cid_file]).strip()])


def run_s2i_build(text):
    info("Building the {} application image ...".format(text))
    subprocess.call(["s2i", "build", s2i_args, "file://{}/${}".format(test_dir, text),
                     IMAGE_NAME, IMAGE_NAME + '-testapp'])


def prepare(image):
    if (image_exists(IMAGE_NAME)):
        print("ERROR: The image {} must exist before this script is executed.".format(IMAGE_NAME))
        # exit 1
    info("Preparing to test {} ...".format(image))
    # EXECUTE THIS IN TERMINAL #
    # pushd ${test_dir}/${1} >/dev/null
    # subprocess.call(["git", "init"])
    # subprocess.call(["git", "config", "user.email", "\"build@localhost\"",
    #                 "&&", "git", "config", "user.name", "\"builder\""])
    # subprocess.call(["git", "add", "-A", "&&", "git", "commit", "-m", "\"Sample commit\""])
    # popd >/dev/null


def run_test_application():
    # EXECUTE THIS IN TERMINAL #
    # subprocess.call(["docker", "run", "--user=100001", CONTAINER_ARGS,
    #                 "--rm", "--cidfile=", cid_file, IMAGE_NAME+"-testapp"])
    pass


def cleanup_app():
    info("Cleaning up app container ...")
    if os.path.isfile(cid_file):
        if container_exists:
            subprocess.call(["docker", "stop", subprocess.check_output(["cat", cid_file]).strip()])


def cleanup(smth):
    info("Cleaning up the test application image")
    if image_exists(IMAGE_NAME + "-testapp"):
        subprocess.call(["docker", "rmi", "-f", IMAGE_NAME+"-testapp"])
    subprocess.call(["rm", "-rf", test_dir+"/"+smth+"/.git"])


def check_result(smth):
    result = str(smth)
    if result != "0":
        info("TEST FAILED {}".format(result))
        # cleanup(absolutely not smth) somehow get image name from here
        return result  # exit(result)


def wait_for_cid():
    max_attempts = 10
    sleep_time = 1
    attempt = 1
    # result = 1
    info("Waiting for application container to start $CONTAINER_ARGS ...")
    while attempt <= max_attempts:
        if os.path.isfile(cid_file) and os.stat(cid_file).st_size > 0: break
        attempt += 1
        time.sleep(sleep_time)
        pass


def test_s2i_usage():
    info("Testing 's2i usage' ...")
    with open(os.devnull, 'w') as devnull:
        subprocess.call(["s2i", "usage", s2i_args, IMAGE_NAME], stdout=devnull, stderr=devnull)


def test_docker_run_usage():
    info("Testing 'docker run' usage ...")
    with open(os.devnull, 'w') as devnull:
        subprocess.call(["docker", "run", IMAGE_NAME], stdout=devnull, stderr=devnull)


def test_scl_usage(first, second, third):
    run_cmd = first
    expected = second
    cid_file = third

    info("Testing the image SCL enable")

    print(run_cmd, expected, cid_file)  # pass

    # out=subprocess.check_output(["docker", "run", "--rm", IMAGE_NAME,
    #                             "/bin/bash", "-c", run_cmd]) # 2>&1 stderr to stdout
    # if ! echo "${out}" | grep -q "${expected}"; then
    #    print "ERROR[/bin/bash -c " + run_cmd + "] Expected " + expected + ", got " + out
    #    return 1

    # out=subprocess.check_output(["docker", "exec", subprocess.check_output(["cat", cid_file]).strip(),
    #                             "/bin/bash", "-c", run_cmd]) # 2>&1 stderr to stdout
    # if ! echo "${out}" | grep -q "${expected}"; then
    #    echo "ERROR[exec /bin/bash -c "${run_cmd}"] Expected '${expected}', got '${out}'"
    #    return 1

    # out=$(docker exec $(cat ${cid_file}) /bin/sh -ic "${run_cmd}" 2>&1)
    # if ! echo "${out}" | grep -q "${expected}"; then
    #    echo "ERROR[exec /bin/sh -ic "${run_cmd}"] Expected '${expected}', got '${out}'"
    #    return 1

    return 1  # pass


def test_connection():
    info("Testing the HTTP connection (http://{}:{} {} ...".format(container_ip(), test_port, CONTAINER_ARGS))
    max_attempts = 30
    sleep_time = 1
    attempt = 1
    result = 1
    while attempt <= max_attempts:
        # response_code=$(curl -s -w %{http_code} -o /dev/null http://$(container_ip):${test_port}/)
        # status = exit status of last task
        # if status == 0:
            # if response_code == 200:
                # result = 0
            # break
        attempt += 1
        time.sleep(sleep_time)

    return result


def test_application():
    cid_file = subprocess.check_output(["mktemp", "-u", "--suffix=.cid"]).strip()
    # Verify that the HTTP connection can be established to test application container
    run_test_application()

    # Wait for the container to write it's CID file
    wait_for_cid()

    res = test_scl_usage("python --version", "Python $VERSION.", cid_file)
    check_result(res)
    res = test_scl_usage("node --version", "^v[0-9]*\.[0-9]*\.[0-9]*", cid_file)
    check_result(res)
    res = test_scl_usage("npm --version", "^[0-9]*\.[0-9]*\.[0-9]*", cid_file)
    check_result(res)
    test_connection()
    check_result(res)
    cleanup_app()

# Since we built the candidate image locally, we don't want S2I attempt to pull
# it from Docker hub
# s2i_args="--pull-policy=never"

# Verify the 'usage' script is working properly when running the base image with 's2i usage ...'
# test_s2i_usage()
# check_result(exit status of last task)

# Verify the 'usage' script is working properly when running the base image with 'docker run ...'
# test_docker_run_usage()
# check_result(exit status of last task)

"""
for app in WEB_APPS:
    prepare(app)
    run_s2i_build(app)
    # check_result(exit status of last task)

    # test application with default user
    test_application()

    # test application with random user
    CONTAINER_ARGS = "-u 12345"
    test_application()

    info("All test for the {} finished successfully.".format(app))
    cleanup(app)
"""

x = subprocess.check_output(["python", "--version"]).strip()
print x

info("All tests finished successfully.")

conu.DockerImage.run_via_binary()

