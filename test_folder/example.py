# Import standard libraries
import argparse
import asyncio
import json
import os
import sys
import time
from datetime import date, datetime
from logging import Logger, StreamHandler, getLogger

# Import third-party modules
import aiofiles
from aiohttp import ClientSession

# Import private modules
from cec_python_google_cloud_async.billing import get_billing_info
from cec_python_google_cloud_async.folders import get_folder_ancestry
from cec_python_google_cloud_async.helpers import get_automation_project_details
from cec_python_google_cloud_async.monitoring import list_time_series
from cec_python_google_cloud_async.projects import (
    list_active_projects,
    test_iam_permissions,
)
from cec_python_google_cloud_async.serviceusage import list_enabled_services
from cec_python_google_cloud_async.storage import (
    list_buckets,
    list_objects,
    upload_object,
)
from cec_python_google_cloud_async.timeseries import write_resource_label_filter
from cec_python_google_cloud_async.utilities import (
    format_bytes,
    get_data_from_file,
    get_folder_hierarchy,
    output_csv,
)

assert sys.version_info >= (3, 9), "Script requires Python 3.9+."

log_level = "INFO"
logger = getLogger(__name__)
logger.setLevel(level=log_level.upper())
logger.addHandler(StreamHandler(sys.stdout))


def get_lifecycle_rules(bucket: dict):
    lifecycle_rules_count = 0
    deletion_rule = False
    noncurrent_version_deletion_rule = False
    transition_rule = False
    noncurrent_version_transition_rule = False

    if lifecycle := bucket.get("lifecycle"):
        lifecycle_rules_count = len(lifecycle["rule"])
        for rule in bucket["lifecycle"].get("rule"):
            action_type = rule["action"].get("type")
            condition = rule["condition"]

            non_current_version_flags = (
                not condition.get("isLive", True)
                or condition.get("daysSinceNoncurrentTime") is not None
                or condition.get("noncurrentTimeBefore") is not None
                or condition.get("numNewerVersions") is not None
            )

            if action_type == "Delete":
                if non_current_version_flags:
                    noncurrent_version_deletion_rule = True
                else:
                    deletion_rule = True

            elif action_type == "SetStorageClass":
                if non_current_version_flags:
                    noncurrent_version_transition_rule = True
                else:
                    transition_rule = True

    return {
        "LifecycleRulesCount": lifecycle_rules_count,
        "DeletionRule": deletion_rule,
        "TransitionRule": transition_rule,
        "NonCurrentVersionTransitionRule": noncurrent_version_transition_rule,
        "NonCurrentVersionDeletionRule": noncurrent_version_deletion_rule,
        "LifecycleDeletionRule": None,
    }


async def write_output(line: dict, file_name: str) -> None:
    async with aiofiles.open(file_name, "a") as file:
        await file.write(f"{json.dumps(line)}")
        await file.write("\n")


async def process_buckets(file_name: str, project: str, service_account: str, session: ClientSession, logger: Logger) -> None:
    if buckets := await list_buckets(project=project, service_account=service_account, session=session, logger=logger):

        # Get the folder ancestry for the project
        folder_ancestry = await get_folder_ancestry(project=project, service_account=service_account, session=session, logger=logger)

        # Get the top-level and sub-folder to include in the output
        top_level_folder, sub_folder = get_folder_hierarchy(folder_ancestry=folder_ancestry)

        # Specify the metric type to include in the filter
        metric_object = "storage.googleapis.com/storage/object_count"
        metric_bucket = "storage.googleapis.com/storage/total_bytes"

        for bucket in buckets:
            logger.info(f"Project: {project}. BucketId: {bucket['id']}. BucketName: {bucket['name']}. Location: {bucket['location']}.")

            # Set the UTC timestamp to use for the BigQuery import
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %X")

            # Use today as the date for the filter
            today = f"{datetime.strftime(datetime.now(), '%Y-%m-%d')}T00%3A00%3A00.000Z"

            # Build the monitoring filter using todays date and a range of 1 minute
            filters = write_resource_label_filter(
                metric_name=metric_object, resource_label="bucket_name", resource_name=bucket["name"], start_time=today, end_time=today
            )

            # Get the count of objects in the bucket from Cloud Monitoring
            object_metric = await list_time_series(
                filters=filters, project=project, service_account=service_account, session=session, logger=logger
            )

            # Initialize new dictionary to capture storage class and object count
            object_count_per_storage_class = {}

            # Calculate the object count
            if object_metric:
                for metrics in object_metric:
                      storage_class = metrics.get("metric", {}).get("labels", {}).get("storage_class")
                     object_count = metrics.get("points")[0].get("value").get("int64Value") if metrics.get("points") is not None else 0
                    object_count_per_storage_class[storage_class] = object_count

            # Build the monitoring filter using todays date and a range of 1 minute
            filters = write_resource_label_filter(
                   metric_name=metric_bucket, resource_label="bucket_name", resource_name=bucket["name"], start_time=today, end_time=today
            )

            # Get the size of the bucket from Cloud Monitoring
            bucket_metric = await list_time_series(
             filters=filters, project=project, service_account=service_account, session=session, logger=logger
            )

            # Initialize new dictionary to capture storage class and bucket size bytes
            bucket_size_bytes_per_storage_class = {}

            # Calculate the bucket size bytes
            if bucket_metric:
                for metrics in bucket_metric:
                    storage_class = metrics.get("metric", {}).get("labels", {}).get("storage_class")
                    bucket_size_bytes = metrics.get("points")[0].get("value").get("doubleValue") if metrics.get("points") is not None else 0
                    bucket_size_bytes_per_storage_class[storage_class] = bucket_size_bytes

            # Determine whether versioning is enabled for the bucket
            versioning = "versioning" in bucket and bucket["versioning"]["enabled"]

            # Determine if a retention policy exists on the bucket
            retention_policy = "False"
            retention_period = None

            if retention := bucket.get("retentionPolicy"):
                retention_policy = "True"
                secs_in_day = 86400
                retention_period = round(int(retention["retentionPeriod"]) / secs_in_day)

            lifecycle_rules = get_lifecycle_rules(bucket)

            if not object_metric and not bucket_metric:
                try:
                    list_of_objects = await list_objects(
                        bucket_name=bucket["name"], service_account=service_account, session=session, logger=logger
                    )
                    objectcount = len([item["name"] for item in list_of_objects]) if list_of_objects else 0
                    bucketsize = sum([int(item["size"]) for item in list_of_objects]) if list_of_objects else 0
                except Exception as e:
                    logger.error(f"unable to extract objects for {bucket['name']}, error code: {e}")
                    objectcount = 0
                    bucketsize = 0

                output = {
                    "Timestamp": timestamp,
                    "ParentFolder": top_level_folder,
                    "SubFolder": sub_folder,
                    "ProjectId": project,
                    "BucketId": bucket["id"],
                    "BucketName": bucket["name"],
                    "Location": bucket["location"],
                    "LocationType": bucket["locationType"],
                    "StorageClass": bucket["storageClass"],
                    "ObjectCount": objectcount,
                    "BucketSizeBytes": bucketsize,
                    "BucketSizeFormatted": format_bytes(bucketsize),
                    "Versioning": versioning,
                    "RetentionPolicy": retention_policy,
                    "RetentionPolicyPeriodDays": retention_period,
                    "TimeCreated": bucket["timeCreated"].split(".")[0].replace("T", " "),
                    "Updated": bucket["updated"].split(".")[0].replace("T", " "),
                    "SoftDeleteEnabled": "softDeletePolicy" in bucket and int(bucket["softDeletePolicy"]["retentionDurationSeconds"]) > 0,
                    "ProjectNumber": bucket["projectNumber"],
                }

                output.update(lifecycle_rules)
                await write_output(line=output, file_name=file_name)

            else:
                all_storage_classes = set(object_count_per_storage_class.keys()).union(bucket_size_bytes_per_storage_class.keys())

                for storage in all_storage_classes:
                    count = object_count_per_storage_class.get(storage, 0)
                    bucketsizebytes = bucket_size_bytes_per_storage_class.get(storage, 0)

                    output = {
                        "Timestamp": timestamp,
                        "ParentFolder": top_level_folder,
                        "SubFolder": sub_folder,
                        "ProjectId": project,
                        "BucketId": bucket["id"],
                        "BucketName": bucket["name"],
                        "Location": bucket["location"],
                        "LocationType": bucket["locationType"],
                        "StorageClass": storage,
                        "ObjectCount": count,
                        "BucketSizeBytes": bucketsizebytes,
                        "BucketSizeFormatted": format_bytes(bucketsizebytes),
                        "Versioning": versioning,
                        "RetentionPolicy": retention_policy,
                        "RetentionPolicyPeriodDays": retention_period,
                        "TimeCreated": bucket["timeCreated"].split(".")[0].replace("T", " "),
                        "Updated": bucket["updated"].split(".")[0].replace("T", " "),
                        "SoftDeleteEnabled": "softDeletePolicy" in bucket
                        and int(bucket["softDeletePolicy"]["retentionDurationSeconds"]) > 0,
                        "ProjectNumber": bucket["projectNumber"],
                    }

                    output.update(lifecycle_rules)
                    await write_output(line=output, file_name=file_name)

    else:
        logger.debug(f"No storage buckets were found in the project: {project}.")


async def main(service_account: str, text_file_name: str, csv_file_name: str, project_ids: list[str] = None) -> None:
    async with ClientSession() as session:

        tasks = []

        today = date.today()

        # Get the automation project details for this organisation including the name of the GCS bucket to upload the output CSV file to
        automation_project_details = await get_automation_project_details(service_account=service_account, session=session, logger=logger)

        if not (automation_bucket_name := automation_project_details.get("bucket_name")):
            raise ValueError("No storage bucket name was found.")

        # Set the scope of projects to create coroutines for
        if project_ids:
            logger.info(f"{len(project_ids)} project(s) specified in arguments, scoping to these projects only...")
            project_scope = list(project_ids)
        else:
            logger.info("All projects required. Getting a list of all active projects...")
            active_projects = await list_active_projects(service_account=service_account, session=session, logger=logger)

            if active_projects:
                project_scope = [project["projectId"] for project in active_projects]
            else:
                raise ValueError("Failed to list all active projects")

        logger.info(f"Processing {len(project_scope)} project(s)..")

        # Loop through each project in scope and create coroutine task
        for index, project_id in enumerate(project_scope, start=1):
            logger.info(f"Processing project {index}/{len(project_scope)}: {project_id}..")

            # Get the project billing info to allow us to check if billing is enabled as, if it is not,
            # we have no API access to the project
            billing_info = await get_billing_info(project=project_id, service_account=service_account, session=session, logger=logger)

            if billing_info and billing_info.get("billingEnabled", False):

                # Get the enabled services for the project to allow us to check if the required API is enabled
                # If it is not then we have no API access to the project and it is safe to assume that the service that
                # we are querying is not in use
                enabled_services = await list_enabled_services(
                    project=project_id, service_account=service_account, session=session, logger=logger
                )

                # Verify that the required GCP APIs are enabled on the project.
                api_name = "storage-api.googleapis.com"

                if enabled_services and next((x for x in enabled_services if x["config"]["name"] == api_name), None):

                    logger.debug(f"{api_name} enabled for {project_id}")

                    # Define the permissions required to list the metrics
                    permissions = ["storage.buckets.list"]

                    # Check that we have the permissions required before we proceed
                    iam_permissions = await test_iam_permissions(
                        permissions=permissions, project=project_id, service_account=service_account, session=session, logger=logger
                    )

                    if iam_permissions and set(permissions).issubset(iam_permissions):

                        # Generate new async task and add to task list
                        tasks.append(
                            asyncio.create_task(
                                process_buckets(
                                    file_name=text_file_name,
                                    project=project_id,
                                    service_account=service_account,
                                    session=session,
                                    logger=logger,
                                )
                            )
                        )

                    else:
                        logger.warning(f"The '{permissions}' permissions were not found for the project: {project_id}.")
                else:
                    logger.warning(f"The '{api_name}' API is not enabled for the project: {project_id}.")
            else:
                logger.warning(f"Billing is not enabled for the project: {project_id}. Enable billing to enable API access.")

        try:
            if tasks:
                logger.info(f"Async task(s) created. {len(tasks)} coroutine(s) in the task list. Awaiting...")
                await asyncio.gather(*tasks)

        finally:
            if os.path.exists(text_file_name):
                logger.info(f"Getting data from {text_file_name} and outputting to {csv_file_name}...")
                info = get_data_from_file(text_file_name)

                output_csv(file_name=csv_file_name, data=info, csv_headers=list(info[0].keys()))
                os.remove(text_file_name)

            # Attempt to upload the output CSV file to GCS
            if os.path.exists(csv_file_name):
                logger.info("Upload the CSV file to GCS...")

                # Define the object name (e.g. 'gcp-cost-analysis/2020-04-07/gcp-cost-analysis-script-2020-04-07-09-22-17.csv')
                object_name = f"gcp-cost-analysis/{today}/{csv_file_name}"

                await upload_object(
                    bucket_name=automation_bucket_name,
                    object_name=object_name,
                    file_path=csv_file_name,
                    content_type="text/csv",
                    service_account=service_account,
                    session=session,
                    logger=logger,
                )


if __name__ == "__main__":
    utc_now = datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")

    argparser = argparse.ArgumentParser(description="Retrieve Google Bucket Size and Location.")
    argparser.add_argument(
        "--project-ids", metavar="projectids", required=False, nargs="+", help="Optional. Include to specify specific project IDs."
    )
    argparser.add_argument(
        "--service-account",
        metavar="serviceaccount",
        required=False,
        type=str,
        help="Optional. Include to specify the name of a Service Account or a Service Account Key File.",
    )
    argparser.add_argument(
        "--text-file-name",
        metavar="textfilename",
        required=False,
        type=str,
        default=f"gcp-bucket-details-{utc_now}.txt",
        help="Optional. Include to specify the name of the TXT file.",
    )
    argparser.add_argument(
        "--csv-file-name",
        metavar="csvfilename",
        required=False,
        type=str,
        default=f"gcp-bucket-details-{utc_now}",
        help="Optional. Include to specify the name of the CSV file.",
    )
    argparser.add_argument(
        "--log-level",
        metavar="loglevel",
        required=False,
        type=str,
        help='Optional. Include to specify a log level other than the default of "INFO".',
    )
    argparser.add_argument(
        "--build-no",
        metavar="buildno",
        required=False,
        type=str,
        help="Build no concourse build",
    )

    start = time.time()

    args = argparser.parse_args()
    logger.setLevel(args.log_level.upper()) if args.log_level else logger.setLevel("INFO")

    logger.debug(f"Args: {args}")

    if os.path.exists(args.text_file_name):
        os.remove(args.text_file_name)

    asyncio.run(
        main(
            project_ids=args.project_ids,
            service_account=args.service_account,
            text_file_name=args.text_file_name,
            csv_file_name=args.csv_file_name + (f"_{args.build_no}" if args.build_no else "") + ".csv",
        )
    )

    logger.info(f"Total execution time was {round((time.time() - start), 2)} seconds.")
