import random
import time


def get_content_name(content_id):
    # emulate a slow service by sleeping for a random period of time between 1
    # and 3 seconds before responding
    millis = random.randint(1000, 3000)
    time.sleep(float(millis) / 1000)
    return "Content name for id {} required {} ms".format(content_id, millis)
