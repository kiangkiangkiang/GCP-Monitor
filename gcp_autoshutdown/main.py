import googleapiclient.discovery
from collections import defaultdict

COMPUTER = googleapiclient.discovery.build("compute", "v1")
PROJECT_ID = "your-project-id"


def do_shutdown(project_id, computer, shutdown_instances):
    for area in shutdown_instances:
        for instance in shutdown_instances[area]:
            try:
                computer.instances().stop(project=project_id, zone=area, instance=instance["name"]).execute()
            except Exception as e:
                continue


def get_all_instances(project_id, computer):
    try:
        all_zones = computer.zones().list(project=project_id).execute()
        all_instances = defaultdict(list)
        for zone in all_zones["items"]:
            instances = computer.instances().list(project=PROJECT_ID, zone=zone["name"]).execute()
            if instances.get("items"):
                all_instances[zone["name"]].extend(instances["items"])
        return all_instances
    except Exception as e:
        raise ValueError(f"Instance Reminder Error in get_all_instances(): {e}")


def filter_instances_by_status(all_instances, filter_status):
    result_instances = defaultdict(list)
    for area in all_instances:
        for instance in all_instances[area]:
            try:
                if instance["status"] not in filter_status:
                    continue
                result_instances[area].append(instance)
            except Exception as e:
                continue
    return result_instances


def main(event, context):
    # Read All Area
    all_instances = get_all_instances(PROJECT_ID, COMPUTER)

    # filter with RUNNING
    shutdown_instances = filter_instances_by_status(all_instances, filter_status=["PROVISIONING", "STAGING", "RUNNING"])

    # Shutdown
    do_shutdown(PROJECT_ID, COMPUTER, shutdown_instances)
