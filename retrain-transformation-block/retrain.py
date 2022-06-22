import requests
import time, sys, argparse

api_url = "https://studio.edgeimpulse.com/v1/api/"

def wait_job(project_id: int, api_key: str, job_id: int, interval: int) -> bool: 
    """Sleep while periodically polling for a job to finish. Returns boolean for job finishing successfully 
    """
    request_url = api_url + str(project_id) + "/jobs/" + str(job_id) + "/status"
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key
    }

    # loop until inner response either fails or returns job finished
    while True:
        response = requests.request("GET", request_url, headers=headers)
        try:
            assert response.status_code == 200 
            response_json = response.json()
            assert response_json['success'] == True

            if 'finished' in response_json['job'].keys():
                success = bool(response_json['job']['finishedSuccessful'])
                print("job {} finished, job success: {}".format(job_id, success))
                return success
        except:
            print("Failed to fetch status for job: ", job_id)
            print(response, flush=True)
            sys.exit()

        print("waiting for job {} to finish...".format(job_id), flush=True)
        time.sleep(interval)


def retrain(project_id: int, api_key: str) -> None:
    """Retrain a project using the last DSP and learning configuration
    """
    request_url = api_url + str(project_id) + "/jobs/retrain"

    headers = {
        "Accept": "application/json",
        "x-api-key": api_key
    }

    print("starting retrain job for project:", project_id, flush=True)
    response = requests.request("POST", request_url, headers=headers)

    try:
        assert response.status_code == 200 
        response_json = response.json()
        assert response_json['success'] == True
        job_id = response_json['id']

        # wait till job completes successfully 
        assert wait_job(args.project_id, args.project_api_key, job_id, 30) == True
        print("retrain job complete", flush=True) 
    except:
        print("ERROR: retrain job failed", flush=True) 
        print(response, flush=True)
        sys.exit()


def evaluate_model(project_id: int, api_key: str) -> list[dict]:
    """ Run model testing, wait for the job to finish, and return a parsed json of the results.
    For the format of the returned json, see https://docs.edgeimpulse.com/reference/getevaluatejobresult
    """

    # request to evaluate the model against the test dataset
    request_url = api_url + str(project_id) + "/jobs/evaluate"
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key
    }
    print("starting evaluate job for project:", project_id, flush=True)
    response = requests.request("POST", request_url, headers=headers)

    try:
        assert response.status_code == 200 
        response_json = response.json()
        assert response_json['success'] == True
        job_id = response_json['id']
        # wait for job to complete successfully, otherwise will get out of date results
        assert wait_job(project_id, api_key, job_id, 30) == True
    except:
        print("ERROR: evaluate job failed", flush=True) 
        print(response, flush=True)
        sys.exit()

    # request to get evaluation results
    request_url = api_url + str(project_id) + "/deployment/evaluate"
    headers = {
        "Accept": "application/json",
        "x-api-key": api_key,
    }
    response = requests.request("GET", request_url, headers=headers)

    try:
        assert response.status_code == 200 
        response_json = response.json()
        assert response_json['success'] == True
        return response_json['result']
    except:
        print("ERROR: failed to obtain evaluation results", flush=True) 
        print(response, flush=True)
        sys.exit()


def store_version(project_id: int, api_key: str) -> int:
    """Stores a new project version. The version will be private

    This method does not wait for version storage to complete. The job ID is returned to check status
    """
    request_url = api_url + str(project_id) + "/jobs/version"

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }

    payload = {
        "description": "automated version - saved by pipeline",
        "makePublic": False
    }

    print("storing version for project:", project_id, flush=True)
    response = requests.request("POST", request_url, json=payload, headers=headers)

    try:
        assert response.status_code == 200 
        response_json = response.json()
        assert response_json['success'] == True
        return response_json['id']
    except:
        print("ERROR: failed to store version", flush=True) 
        print(response, flush=True)
        sys.exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Retrain Project Transform')
    parser.add_argument('--project-id', type=int, required=True)
    parser.add_argument('--project-api-key', type=str, required=True)

    args, unknown = parser.parse_known_args()

    retrain(args.project_id, args.project_api_key)
    evaluate_model(args.project_id, args.project_api_key)
    store_version(args.project_id, args.project_api_key)
