import base64
import json
import googleapiclient.discovery

COMPUTER = googleapiclient.discovery.build("compute", "v1")
PROJECT_ID = "your-project-id"
WHITELIST_STRING = ["any_name_denoting_whitelist"]
WHITELIST_TAG = {"whitelist": "true"}


def get_instance_information(this_zone, instance_name):
    try:
        instance_info = (
            COMPUTER.instances().list(project=PROJECT_ID, zone=this_zone, filter=f"name={instance_name}").execute()
        )
        if len(instance_info["items"]) != 1:
            raise ValueError(
                "Invalid number of instances got in monitoringInstances. Num of instance got: {len(instance_info['items'])}."
            )
        return instance_info["items"][0]
    except Exception as e:
        raise ValueError(f"Instance Update Monitoring Error: {e}")


def is_in_whitelist_name(resource_name, whitelist_str):
    for s in whitelist_str:
        if resource_name.find(s) != -1:
            return True
    return False


def parser_event_for_instance(event):
    try:
        pubsub_message = base64.b64decode(event["data"]).decode("utf-8")
        json_content_msg = json.loads(pubsub_message)
        source_details = json_content_msg["protoPayload"]["resourceName"]
        start_index = source_details.find("zones/") + 6
        end_index = source_details.find("/instance")
        this_zone = source_details[start_index:end_index]
        update_instances_name = source_details.split("/")[-1]
    except Exception as e:
        raise ValueError(f"Parser event input error: {e}")
    return this_zone, update_instances_name


def is_in_whitelist_tag(resource_info, whitelist_tag):
    try:
        if resource_info.get("labels"):
            for whitelist_key in whitelist_tag:
                if not isinstance(whitelist_tag[whitelist_key], str):
                    raise ValueError(f"Items in WHITELIST_TAG must be str: {whitelist_tag[whitelist_key]}")

                this_instance_whitelist_value = resource_info["labels"].get(whitelist_key)

                if this_instance_whitelist_value:
                    if this_instance_whitelist_value == whitelist_tag[whitelist_key]:
                        return True
        return False
    except Exception as e:
        raise ValueError(e)


def instances_update_detect(event, context):
    # Get instance information
    this_zone, instance_name = parser_event_for_instance(event)
    instance_info = get_instance_information(this_zone, instance_name)

    # Check if in white list
    if is_in_whitelist_name(instance_name, WHITELIST_STRING) or is_in_whitelist_tag(instance_info, WHITELIST_TAG):
        print(f"Instances {instance_name} is in whitelist.")
        return

    # monitoring 1: security boot must be true
    this_secure = instance_info["shieldedInstanceConfig"]["enableSecureBoot"]
    if not this_secure:
        print(
            f"GCP Instance Secure Boot must be True: \n - Instance ID: {instance_info['id']}.\n"
            f" - Instance area: {this_zone}.\n - Instance name: {instance_name}.\n"
            f" - enableSecureBoot: {this_secure}"
        )
        return

    # monitoring 2: must have firewall tag
    internet_tags = instance_info["tags"].get("items")
    if not internet_tags:
        print(
            f"GCP Instance without Internet Tags Error: \n - Instance ID: {instance_info['id']}.\n"
            f" - Instance area: {this_zone}.\n - Instance name: {instance_name}."
        )
        return
