import base64
import json
import googleapiclient.discovery

ORGANIZATION_URL = "https://your_url"
COMPUTER = googleapiclient.discovery.build("compute", "v1")
PROJECT_ID = "your-project-id"
WHITELIST_STRING = ["any_name_denoting_whitelist"]


def send_msg_to_your_organization(url, msg):
    # edit yourself or delete this method
    pass


def is_in_whitelist(source_service_name, whitelist_str):
    for s in whitelist_str:
        if source_service_name.find(s) != -1:
            return True
    return False


def get_firewalls_status(computer, project_id, firewalls_name):
    try:
        request = computer.firewalls().list(project=project_id, filter=f"name={firewalls_name}")
        response = request.execute()
        if len(response["items"]) != 1:
            raise ValueError(f"len(response['items'])=={len(response['items'])} is not 1.")
        return response["items"]
    except Exception as e:
        send_msg_to_your_organization(ORGANIZATION_URL, f"List firewalls error: {e}")
        raise ValueError(f"List firewalls error: {e}")


def check_IP_valid(firewalls_info):
    try:
        if not isinstance(firewalls_info["sourceRanges"], list):
            firewalls_info["sourceRanges"] = [firewalls_info["sourceRanges"]]
        for IP_str in firewalls_info["sourceRanges"]:
            if IP_str.find("0.0.0.0") != -1:
                send_msg_to_your_organization(
                    ORGANIZATION_URL, f"Invalid Firewalls: {firewalls_info['name']}. IP: {IP_str} is found."
                )
                break
    except Exception as e:
        send_msg_to_your_organization(ORGANIZATION_URL, f"Get firewalls IP error: {e}")
        print(f"Get firewalls IP error: {e}")


def firewalls_update_detect(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    # Parser event response
    try:
        pubsub_message = base64.b64decode(event["data"]).decode("utf-8")
        json_content_msg = json.loads(pubsub_message)
        update_firewalls_name = json_content_msg["protoPayload"]["resourceName"].split("/")[-1]
    except Exception as e:
        send_msg_to_your_organization(ORGANIZATION_URL, f"Parser event input error: {e}")
        print(f"Parser event input error: {e}")

    # Check if in white list
    if is_in_whitelist(update_firewalls_name, WHITELIST_STRING):
        print(f"Firewalls {update_firewalls_name} is in whitelist.")
        return

    # Get information from event firewalls
    firewalls_status = get_firewalls_status(COMPUTER, PROJECT_ID, update_firewalls_name)
    check_IP_valid(firewalls_status[0])
