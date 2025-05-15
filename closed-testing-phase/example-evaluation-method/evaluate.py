"""
The following is a simple example evaluation method.

It is meant to run within a container. Its steps are as follows:

  1. Read the algorithm output
  2. Associate original algorithm inputs with a ground truths via predictions.json
  3. Calculate metrics by comparing the algorithm output to the ground truth
  4. Repeat for all algorithm jobs that ran for this submission
  5. Aggregate the calculated metrics
  6. Save the metrics to metrics.json

To run it locally, you can call the following bash script:

  ./do_test_run.sh

This will start the evaluation and reads from ./test/input and writes to ./test/output

To save the container and prep it for upload to Grand-Challenge.org you can call:

  ./do_save.sh

Any container that shows the same behaviour will do, this is purely an example of how one COULD do it.

Reference the documentation to get details on the runtime environment on the platform:
https://grand-challenge.org/documentation/runtime-environment/

Happy programming!
"""

import json


import random
from statistics import mean
from pathlib import Path
from pprint import pformat, pprint
from helpers import run_prediction_processing, tree

INPUT_DIRECTORY = Path("/input")
OUTPUT_DIRECTORY = Path("/output")


def main():
    print_inputs()

    metrics = {}
    predictions = read_predictions()

    # We now process each algorithm job for this submission
    # Note that the jobs are not in any specific order!
    # We work that out from predictions.json

    # Use concurrent workers to process the predictions more efficiently
    metrics["results"] = run_prediction_processing(fn=process, predictions=predictions)

    # We have the results per prediction, we can aggregate the results and
    # generate an overall score(s) for this submission
    if metrics["results"]:
        metrics["aggregates"] = {
            "my_metric": mean(result["my_metric"] for result in metrics["results"])
        }

    # Make sure to save the metrics
    write_metrics(metrics=metrics)

    return 0


def process(job):
    # The key is a tuple of the slugs of the input sockets
    interface_key = get_interface_key(job)

    # Lookup the handler for this particular set of sockets (i.e. the interface)
    handler = {
        ("stacked-barretts-esophagus-endoscopy-images",): process_interface_0,
    }[interface_key]

    # Call the handler
    return handler(job)


def process_interface_0(
    job,
):
    """Processes a single algorithm job, looking at the outputs"""
    report = "Processing:\n"
    report += pformat(job)
    report += "\n"

    # Firstly, find the location of the results
    location_stacked_neoplastic_lesion_likelihoods = get_file_location(
        job_pk=job["pk"],
        values=job["outputs"],
        slug="stacked-neoplastic-lesion-likelihoods",
    )

    # Secondly, read the results
    result_stacked_neoplastic_lesion_likelihoods = load_json_file(
        location=location_stacked_neoplastic_lesion_likelihoods,
    )

    # Thirdly, retrieve the input file name to match it with your ground truth
    image_name_stacked_barretts_esophagus_endoscopy_images = get_image_name(
        values=job["inputs"],
        slug="stacked-barretts-esophagus-endoscopy-images",
    )

    # Fourthly, load your ground truth
    # Include your ground truth in one of two ways:

    # Option 1: include it in your Docker-container image under resources/
    resource_dir = Path("/opt/app/resources")
    with open(resource_dir / "some_resource.txt", "r") as f:
        truth = f.read()
    report += truth

    # Option 2: upload it as a tarball to Grand Challenge
    # Go to phase settings and upload it under Ground Truths. Your ground truth will be extracted to `ground_truth_dir` at runtime.
    ground_truth_dir = Path("/opt/ml/input/data/ground_truth")
    with open(
        ground_truth_dir / "a_tarball_subdirectory" / "some_tarball_resource.txt", "r"
    ) as f:
        truth = f.read()
    report += truth

    print(report)

    # TODO: compare the results to your ground truth and compute some metrics

    # For now, we will just report back some bogus metric
    return {
        "my_metric": random.choice([1, 0]),
    }


def print_inputs():
    # Just for convenience, in the logs you can then see what files you have to work with
    print("Input Files:")
    for line in tree(INPUT_DIRECTORY):
        print(line)
    print("")


def read_predictions():
    # The prediction file tells us the location of the users' predictions
    return load_json_file(location=INPUT_DIRECTORY / "predictions.json")


def get_interface_key(job):
    # Each interface has a unique key that is the set of socket slugs given as input
    socket_slugs = [sv["interface"]["slug"] for sv in job["inputs"]]
    return tuple(sorted(socket_slugs))


def get_image_name(*, values, slug):
    # This tells us the user-provided name of the input or output image
    for value in values:
        if value["interface"]["slug"] == slug:
            return value["image"]["name"]

    raise RuntimeError(f"Image with interface {slug} not found!")


def get_interface_relative_path(*, values, slug):
    # Gets the location of the interface relative to the input or output
    for value in values:
        if value["interface"]["slug"] == slug:
            return value["interface"]["relative_path"]

    raise RuntimeError(f"Value with interface {slug} not found!")


def get_file_location(*, job_pk, values, slug):
    # Where a job's output file will be located in the evaluation container
    relative_path = get_interface_relative_path(values=values, slug=slug)
    return INPUT_DIRECTORY / job_pk / "output" / relative_path


def load_json_file(*, location):
    # Reads a json file
    with open(location) as f:
        return json.loads(f.read())


def write_metrics(*, metrics):
    # Write a json document used for ranking results on the leaderboard
    write_json_file(location=OUTPUT_DIRECTORY / "metrics.json", content=metrics)


def write_json_file(*, location, content):
    # Writes a json file
    with open(location, "w") as f:
        f.write(json.dumps(content, indent=4))


if __name__ == "__main__":
    raise SystemExit(main())
