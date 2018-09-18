import datetime
import google.appengine.ext.ndb as ndb
import json
import logging as log
import ndb_model

from google.appengine.api import memcache
from google.appengine.api import namespace_manager
from google.appengine.api import urlfetch


def add_event(customer_id, content_id, time, user_ip, user_user_agent,
              user_location):
    """Store event and content name in Datastore"""

    log.info(
        "customer_id: {}, content_id {}, event_time {}, ip {}, user_agent {}, "
        "location {}".format(
            customer_id, content_id, time, user_ip, user_user_agent,
            user_location))

    previous_namespace = namespace_manager.get_namespace()
    try:
        namespace_manager.set_namespace(customer_id)
        load_content_name_if_needed(content_id)
        ndb_model.Event(
            content_id=content_id,
            time=datetime.datetime.fromtimestamp(time / 1000.0),
            user_ip=user_ip,
            user_user_agent=user_user_agent,
            user_location=user_location).put()
        log.info("Stored Event entity")
        return True
    except Exception as ex:
        log.warning("Unable to store entity")
        log.warning(ex.message)
        return False
    finally:
        namespace_manager.set_namespace(previous_namespace)


def load_content_name_if_needed(content_id):
    """Ensure content name associated to content id is stored in the system by
    using an appropriate service (Memcache, Datastore or external API)"""

    # check if item in Memcache
    if check_if_cached(content_id):
        return
    log.info("Missing Content entity for id {} in Memcache".format(content_id))

    # check if item in Datastore
    content_entity = ndb.Key(ndb_model.Content.__name__, content_id).get()
    if content_entity:
        log.info("Content entity for id {} already present in Datastore"
                 .format(content_id))
        add_to_cache(content_id)
        return
    log.info("Missing Content entity for id {} in Datastore".format(
        content_id))

    # load item with external API request
    content_name = load_content_name(content_id)
    log.info("Retrieved content name: {}".format(content_name))
    ndb_model.Content(id=content_id, content_name=content_name).put()
    add_to_cache(content_id)


def add_to_cache(content_id):
    """Add content name associated to content id to Memcache"""

    try:
        memcache.add(content_id, True)
        log.info("Added key to Memcache: {}".format(content_id))
    except Exception as ex:
        log.info("Unable to add key to Memcache: {}".format(content_id))
        log.info(ex.message)


def check_if_cached(content_id):
    """Check if content name associated to content id is present in Memcache"""

    try:
        if memcache.get(content_id):
            log.info("Content entity for id {} already present in Memcache"
                     .format(content_id))
            return True
    except Exception as ex:
        log.info("Unable to load key from Memcache: {}".format(content_id))
        log.info(ex.message)
    return False


def load_content_name(content_id):
    """Load content name from external Slow Service and cache result"""

    log.info("Fetching content name from external service...")
    slow_service_url = "https://simple-analytics-ws.appspot.com/"
    slow_service_api = "_ah/api/service/v1/slowservice/content/{}/detail"
    url = slow_service_url + slow_service_api.format(content_id)
    try:
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            content = json.loads(result.content).get(u"content")
            return content
        else:
            raise RuntimeError("Unable to load content name from slow service")
    except Exception as ex:
        log.warning(ex.message)
        raise RuntimeError("Unable to load content name from slow service")
