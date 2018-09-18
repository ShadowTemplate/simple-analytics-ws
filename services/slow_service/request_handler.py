import random
import time


def get_content_name(content_id):
    """"Emulate a slow service providing content name associated to content
    id"""

    # sleep between 1 and 3 seconds
    millis = random.randint(1000, 3000)
    time.sleep(float(millis) / 1000)
    return "Content name for id {} required {} ms".format(content_id, millis)
