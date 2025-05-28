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

import numpy as np
import random
from statistics import mean
from pathlib import Path
from pprint import pformat, pprint
from helpers import run_prediction_processing, tree
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve


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
    results = run_prediction_processing(fn=process, predictions=predictions)

    # the results contains a list with directory that contains the ground truths and predictions
    # now concatenate the results into a single list
    data = {'ground_truth': [], 'prediction': [], 'patient_id': [], 'image_name': []}



    # calculate the metrics
    for item in results:
        data['ground_truth'].append(item['ground_truth'])
        data['prediction'].append(item['prediction'])
        data['patient_id'].append(item['patient_id'])
        data['image_name'].append(item['image_name'])

    flattened_data = {
        'ground_truth': np.concatenate(data['ground_truth']).tolist(),
        'prediction': np.concatenate(data['prediction']).tolist(),
        'patient_id': np.concatenate(data['patient_id']).tolist(),
        'image_name': np.concatenate(data['image_name']).tolist(),
    }

    print("Calculating metrics...")
    metrics = bootstrap_metrics(flattened_data['ground_truth'], flattened_data['prediction'], flattened_data['patient_id'], n_iterations=1000, sample_size=10, imbalance_ratio=100)

    print(metrics)

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

    # Option 2: upload it as a tarball to Grand Challenge
    # Go to phase settings and upload it under Ground Truths. Your ground truth will be extracted to `ground_truth_dir` at runtime.
    ground_truth_dir = Path("/opt/ml/input/data/ground_truth")
    with open(
        ground_truth_dir / "a_tarball_subdirectory" / "val_metadata.json", "r"
    ) as f:
        val_metadata = json.load(f)

    report += "\nLoaded val_metadata:\n"
    report += pformat(val_metadata)

    # Now we can match the image name with the ground truth
    if image_name_stacked_barretts_esophagus_endoscopy_images not in val_metadata:
        raise RuntimeError(
            f"Image name {image_name_stacked_barretts_esophagus_endoscopy_images} not found in validation metadata!"
        )

    gt_data = val_metadata[image_name_stacked_barretts_esophagus_endoscopy_images]

    ground_truth = []
    patient_id = []
    image_name = []

    # match idx predictions to idx ground truth
    for idx in range(0, len(result_stacked_neoplastic_lesion_likelihoods)):
        label = gt_data[idx]["class"]
        if label == "ndbe":
            ground_truth.append(0)
        else:
            ground_truth.append(1)
        patient_id.append(gt_data[idx]["patient_id"])
        image_name.append(gt_data[idx]["filename"])


    # For now, we will just report back some bogus metric
    return {
        "ground_truth": ground_truth,
        "prediction": result_stacked_neoplastic_lesion_likelihoods,
        "patient_id": patient_id,
        "image_name": image_name,
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


def bootstrap_metrics(y_true, y_pred, patient_ids, n_iterations=1000, sample_size=100, imbalance_ratio=1):
    """
    Compute metrics on the full test set and perform patient-level bootstrapping for confidence intervals.

    Args:
        y_true: Ground truth labels (per image)
        y_pred: Predicted probabilities (per image)
        patient_ids: Patient ID corresponding to each image
        n_iterations: Number of bootstrap iterations
        sample_size: Number of neoplasia patients per bootstrap sample
        imbalance_ratio: Ratio of NDBE to neoplasia patients

    Returns:
        Dictionary containing:
            - full_dataset_metrics: AUC, AUPRC, PPV@90 on the full dataset
            - bootstrapped_metrics: Median and 95% CI for each metric
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    patient_ids = np.array(patient_ids)

    # Map each patient ID to indices of their images
    patient_to_indices = {}
    for idx, pid in enumerate(patient_ids):
        patient_to_indices.setdefault(pid, []).append(idx)

    # Map each patient to a binary label (1 if any image is neoplasia)
    patient_labels = {
        pid: int(np.any(y_true[indices] == 1)) for pid, indices in patient_to_indices.items()
    }

    neoplasia_patients = [pid for pid, label in patient_labels.items() if label == 1]
    ndbe_patients = [pid for pid, label in patient_labels.items() if label == 0]

    # --------------------
    # Metrics on full dataset
    # --------------------
    auc_full = roc_auc_score(y_true, y_pred)
    auprc_full = average_precision_score(y_true, y_pred)
    precisions, recalls, _ = precision_recall_curve(y_true, y_pred)
    ppv_90_full = np.interp(0.9, recalls[::-1], precisions[::-1])

    # --------------------
    # Bootstrapping
    # --------------------
    bootstrapped_metrics = []

    for _ in range(n_iterations):
        # Sample neoplasia and NDBE patients
        sampled_neoplasia = np.random.choice(neoplasia_patients, size=sample_size, replace=True)
        sampled_ndbe = np.random.choice(ndbe_patients, size=sample_size * imbalance_ratio, replace=True)

        sampled_patients = np.concatenate([sampled_neoplasia, sampled_ndbe])

        # Gather all image indices from these patients
        sampled_indices = []
        for pid in sampled_patients:
            sampled_indices.extend(patient_to_indices[pid])
        sampled_indices = np.array(sampled_indices)

        y_true_sample = y_true[sampled_indices]
        y_pred_sample = y_pred[sampled_indices]

        # Calculate metrics
        auc = roc_auc_score(y_true_sample, y_pred_sample)
        auprc = average_precision_score(y_true_sample, y_pred_sample)
        precisions, recalls, _ = precision_recall_curve(y_true_sample, y_pred_sample)
        ppv_90 = np.interp(0.9, recalls[::-1], precisions[::-1])

        bootstrapped_metrics.append((auc, auprc, ppv_90))

    bootstrapped_metrics = np.array(bootstrapped_metrics)

    bootstrapped_summary = {
        "Score": np.median(bootstrapped_metrics[:, 2]),

        "PPV@90RECALL": np.median(bootstrapped_metrics[:, 2]),
        "PPV@90RECALL 95% CI Lower Bound": np.percentile(bootstrapped_metrics[:, 2], 2.5),
        "PPV@90RECALL 95% CI Upper Bound": np.percentile(bootstrapped_metrics[:, 2], 97.5),

        "AUROC": np.median(bootstrapped_metrics[:, 0]),
        "AUROC 95% CI Lower Bound": np.percentile(bootstrapped_metrics[:, 0], 2.5),
        "AUROC 95% CI Upper Bound": np.percentile(bootstrapped_metrics[:, 0], 97.5),

        "AUPRC": np.median(bootstrapped_metrics[:, 1]),
        "AUPRC 95% CI Lower Bound": np.percentile(bootstrapped_metrics[:, 1], 2.5),
        "AUPRC 95% CI Upper Bound": np.percentile(bootstrapped_metrics[:, 1], 97.5),

        'AUROC Full Dataset': auc_full,
        'AUPRC Full Dataset': auprc_full,
        'PPV@90RECALL Full Dataset': ppv_90_full
    }

    return bootstrapped_summary



if __name__ == "__main__":
    raise SystemExit(main())
