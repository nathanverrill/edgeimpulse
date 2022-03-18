# Transform Block: Retrain Project

## Overview

This is a generic transformation block for automatically retraining a project as part of an organization data pipeline. This transform performs the following steps:

1. Run a `retrain` job, rerunning the last configuration of DSP and training with any newly added data
2. Wait for retraining to complete
3. Run the newly trained model against the project's test dataset
4. Save a new project version (private) 

## Usage

1. Add this as a **standalone** transform block to an organization of choice via:
```
edge-impulse-blocks init
edge-impulse-blocks push
```

* Note: all transform block specific files are ignored by git

2. Then navigate to the Edge Impulse webpage for the organization, and edit the transform block via:
` Data transformation -> Transformation blocks -> 'three dots on the right' -> Edit transformation block`

3. Add the following to `CLI Arguments`
```
--project-id <your_project_id>
--project-api-key <api_key>
```

Make sure the api key has the `admin` role, and is the `development key` for the project.

**Important Note:** Any users in the organization will be able to see the project API key used with this transform block. If the API key needs to be more carefully controlled, modify this implementation to make use of the 'Secrets' available on your organization's Transform tab. These will be passed to the block as an environment variable.
