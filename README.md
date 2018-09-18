# System Design

## Exercise 1a: simple analytics web service

We are required to design a simple analytics web service (SAWS) to track visits 
to a generic content from anonymous users.

The first apparent capability of this service is to store events in a 
persistent way, just for logging purpose.
However, while designing this service, it is reasonable to consider another 
use case typical of this kind of systems: analyze collected data to gather 
some insights.

SAWS has to log data from **anonymous** users.
This requirement simplifies the design, since we can ignore user-related 
aspects, such as authentication, and proceed with a straightforward 
general-purpose logging service.
This service can in principle be flexible enough to be used by different 
customers, even if requirements only involve one website.
So, with little additional effort, it is possible to design a multitenant 
architecture.
Planning multitenancy right now can reduce costs in the future without 
over-engineering risks.

SAWS should be designed to sustain a logging traffic coming from 100 millions 
of users per day (100Mud). This number is fairly big: 100Mud is the volume of 
very large websites, such as LinkedIn or Tumbler.
This requirement will mainly drive the design since it defines the most 
important feature our system needs: **high scalability**.

SAWS is required to fetch external data from a slow service before logging 
events.
This may represents a harsh bottleneck and SAWS performance will probably be 
inversely proportional to its dependency from such service.
We aim to design a system as decoupled as possible from the slow service by 
relying on some expedients, such as **caching**.
This will be required both to achieve SAWS scalability and to avoid flooding 
the slow service with requests.

We are now able to sketch an initial architecture:

```
 _______________________
| 5. API                |
|_______________________|
| 4. Load Balancer      |
|_______________________|
| 3. Back End Instances |
|_______________________|
| 2. Caching Layer      |
|_______________________|
| 1. Persistency Layer  |
|_______________________|
```

### 1. Persistency Layer

The `Persistency Layer` will store traffic events.
It is required to have a very high throughput, since it is reasonable to expect
the number of events SAWS will receive to be an order of magnitude larger than 
the number of daily users. In the best case 100Mud will trigger 100 millions of
requests circa.

Events can be considered as atomic entities, with few relationships among them.
For such reason, a scalable NoSQL database is suitable for the system (we can 
safely assume that no operation will involve joining entries). 

Many of these requests will involve the same contents and this assumption can 
be exploited to achieve better performance.

An appropriate model for the entities could be the following:

```
Event
 ______________
| * ID         |
| * Content ID |———·
| * Time       |   |
| * IP         |   |
| * User Agent |   |
| * Location   |   |
| * ...        |   |
|______________|   |
                   |
Content            |
 _______________   |
| * ID           |—·
| * Content Name |
|________________|
```

Events and contents have been split.

Each stored event will have a unique identifier, the id of the 
content required by the user, a timestamp of the request and a set of 
user-related attributes, such as IP, browser user agent, etc.
Since users are anonymous, the information available will be those typically 
provided by an HTTP(S) packet, such as 
[header content](https://en.wikipedia.org/wiki/List_of_HTTP_header_fields).

On the contrary, the content entity will only have a unique identifier and the 
name fetched from the slow external service.

Storing contents separately from events allows us to avoid redundancy and save
space (hundreds of events will be associated to the same content), enable 
caching as explained below, and permit an easier way to keep content names 
updated (every future change on the slow service side will impact only one 
associated entity on SAWS).

### 2. Caching Layer

The `Caching Layer` is responsible to minimize the interactions between SAWS 
and the external slow service for shared benefits.

Whenever a new event is required to be stored, this caching layer is expected 
to perform an external API call only if strictly necessary.
The algorithm implemented at this level may be follow this logic:

```
01. process_event(ev):
02.   if ev.content_id not in cache:
03.   # content_id may have been processed, but removed from the cache (cache miss)
04.      if ev.content_id not in persistency_layer:
05.        # content_name has never been fetched yet
06.        content_name = slow_service.get_content_name(ev.content_id)
07.        persistency_layer.store_content_entity(ev.content_id, content_name)
08.      # content_name has been fetched, but is missing in the cache
09.      cache.add(ev.content_id)
10.   persistency_layer.store_event_entity(ev) 
```

Whenever a new event has to be logged, this layer first checks if the content 
id is cached.
If so, there is no need to invoke the slow service and the event can be 
immediately passed to the underlying layer, handling the request in a short 
time.
However, we expect the cache to be volatile: we may get a cache miss even if the
entity has been processed (for instance, a long time ago in a 
[LRU cache](https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU))).
In this case, we first query the fast `Persistency Layer` to check if the 
entity is really missing.
If so, we are forced to call the external slow service, generate 
and save a new content entity, cache the result and process the event.
Otherwise we can just update the cache and store the event as before.

This algorithm ensures we will call the external slow service only once for 
each new content.
At the same time, it doesn't ensure content name in the `Persistency Layer` to
be updated.

### 3-4. Back End Instances + Load Balancer

These machines will serve requests performed to our web services.
We can think of bare-metal servers or virtual machines that will receive tasks 
by a load balancer put on top of the architecture.
Tuning resources for an on-premise ad-hoc cluster could be difficult and we may
instead opt to rely on a Platform as a Service.
This choice will delegate the scalability issue to the service provider (e.g. 
Amazon Web Services, Google Cloud Platform, Microsoft Azure, etc.), allowing us
to solely focus on the application.
These providers usually take care of dynamically replicating instances and 
balance traffic when there are load spikes.

However, managing a cluster is still feasible.
Great attention must be paid to keep always allocated the required minimal 
resources to avoid high cost (is the tracking service used homogeneously 
during the day? Are requests geographically distributed homogeneously? How much 
does it take on average to complete a request?).
A detailed costs-benefits analysis will clarify if in the long term it is more 
convenient leveraging on an external service or running a cluster.

### 5. API

SAWS functionality can be exposed with a minimal `API`.
In order to log events it is sufficient to offer, for instance, an `addEvent` 
method in a RESTful API.
Customers will be able to `POST` new events with a simple HTTP request. The 
response may contain the identifier of the newly stored event on SAWS.

In order to achieve the maximal flexibility, SAWS may also implement the full 
set of [CRUD functions](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete)
(`deleteEvent`, `listEvents`, ...).
By doing so, customers will be able to manage their stored events as well as 
retrieve data and perform analyses (e.g. time series) on their own.

Only authenticated requests should be processed and each customer should be 
able to prove its identity while issuing API calls to prevent security flaws.
An existing protocol such as OAuth 2.0 will be sufficient for this requirement.

An API endpoint for `addEvent` may be:

```
POST analyticsservice/{customerId}/event 
```

with a JSON request body as the following:

```
{
   "content_id":"Content042",
   "time":1537093281464,
   "user_info":{
      "ip":"93.150.106.176",
      "user_agent":"Mozilla Firefox",
      "location":"Bari"
   }
} 
```

Customers will be free to place analytics hooks in the form of API calls either 
in their back ends, while serving client requests, or in their front ends, when 
pages are loaded.
The first approach is more secure and completely transparent to the user for 
a number of reasons: it doesn't require user resources, it can't be tampered or
prevented, API call results can be easily processed, etc. 

### A proof of concept

A proof of concept (PoC) of the architecture just described has been developed 
in Python 2.7 and deployed on the Google Cloud Platform.

```
 _______________________      ________________________
| 5. API                | -> | Google Cloud Endpoints | 
|_______________________| -> |________________________|
| 4. Load Balancer      | -> |                        | 
|_______________________| -> | Google App Engine      |
| 3. Back End Instances | -> |                        |
|_______________________| -> |________________________|
| 2. Caching Layer      | -> | Google Memcache        |
|_______________________| -> |________________________|
| 1. Persistency Layer  | -> | Google Cloud Datastore |
|_______________________| -> |________________________|
```

Four different services have been used to implement the layers.
In particular:

* The `Persistency Layer` relies on 
[Google Cloud Datastore](https://cloud.google.com/datastore/docs/concepts/overview),
a NoSQL document database built for automatic scaling and high performance, as 
necessary for the global throughput requirement;

* The `Caching Layer` relies on 
[Google Memcache](https://cloud.google.com/appengine/docs/standard/python/memcache/),
a fast in-memory data cache useful in front of a persistent storage, ideal for 
temporary values without strict requirements on cache hits. The 
[implemented storing algorithm](https://github.com/ShadowTemplate/simple-analytics-ws/blob/master/services/analytics_service/request_handler.py#L42)
is the one described above;

* The `Back End Instances` and the `Load Balancer` are provided by 
[Google App Engine](https://cloud.google.com/appengine/),
a fully managed serverless application platform. It solves the issue of 
over/under provisioning by automatically scaling depending on SAWS traffic and 
consumes resources only when code is running;

* The `API` is exposed via 
[Google Cloud Endpoints](https://cloud.google.com/endpoints/),
a scalable, fast and secure proxy and distributed architecture using Open API 
Specification and providing insights monitoring and logging.

The application is running at 
[https://simple-analytics-ws.appspot.com/](https://simple-analytics-ws.appspot.com/).

SAWS API and the external slow service API are deployed together for 
convenience.
They can be explored via the APIs Explorer automatically generated by Google 
Cloud Endpoints at 
[https://apis-explorer.appspot.com/apis-explorer/?base=https://simple-analytics-ws.appspot.com/_ah/api#p/service/v1/](https://apis-explorer.appspot.com/apis-explorer/?base=https://simple-analytics-ws.appspot.com/_ah/api#p/service/v1/).

This PoC version doesn't require (OAuth 2.0) authentication and the API can be 
tested either via UI or via command line, for instance with *curl*.

The external slow service is mocked by waiting some seconds before replying. 
However, SAWS is able to efficiently use Memcache whenever possible.

For example, when we try to add an event for customer `customerABC`, related to
the content `Content42`, SAWS has to invoke the external slow service and 
requires more than 4 seconds to respond:

```
$ time curl -X POST -k 'https://simple-analytics-ws.appspot.com/_ah/api/service/v1/analyticsservice/customerABC/event' --data '{ "content_id": "Content42", "time": 1537093281464, "user_info" : { "ip": "93.150.106.176", "user_agent" : "Mozilla Firefox", "location" : "Bari"} }'

{
 "content": true
}
real    0m4.275s
user    0m0.012s
sys     0m0.017s

```

However, if we try to add a new event related to the same content, SAWS will 
find the item in Memcache and respond in 1 second:

```
$ time curl -X POST -k 'https://simple-analytics-ws.appspot.com/_ah/api/service/v1/analyticsservice/customerABC/event' --data '{ "content_id": "Content42", "time": 1537093370563, "user_info" : { "ip": "95.142.92.126", "user_agent" : "Mozilla Firefox", "location" : "Padua"} }'

{
 "content": true
}
real    0m1.000s
user    0m0.015s
sys     0m0.011s
```

For the sake of completeness, the commands required to generate and deploy the 
Open API Specification JSON are reported (*gcloud* is required):

```
$ git clone https://github.com/ShadowTemplate/simple-analytics-ws.git
$ cd simple-analytics-ws/
$ python2.7 lib/endpoints/endpointscfg.py get_openapi_spec api.google_cloud_endpoints.services_api.ServicesApi --hostname simple-analytics-ws.appspot.com
$ gcloud endpoints services deploy servicev1openapi.json
$ gcloud endpoints configs list --service=simple-analytics-ws.appspot.com
```

## Exercise 1b: batch enrichment

We will proceed by analysing requirements one at a time.

The first business requirement states:

```
· grant 2 years of retention for event data
```

In order to satisfy this requirement we have to guarantee our `Persistency 
Layer` to be able to retain data for that period of time.

If we are leveraging on a third-party service it may be sufficient to verify 
the service level agreement (SLA) of our provider.
The vast majority of services doesn't set an upper bound or an expiration date
as long as service costs are being paid.
However, some of them may delete data that have not been accessed for a long 
time, so particular attention should be paid in this case.
One workaround could be configuring a time to live (TTL) on entities and a 
cron job to periodically refresh them before deletion.
An alternative could be configuring an automatic (and possibly incremental) 
back up on another service.

The latest approach is also viable if we are managing the `Persistency Layer`
on our own, with an on-premise solution.
In this case we will also probably consider some replication mechanism to 
reduce the risk of data loss.

On the other hand, the same requirement may also mean that we are authorized to
remove from our storage obsolete entities.
In this case, we may set up a cron job to automatically fetch and delete events
(and perhaps contents) older than 2 years, thus saving space and money along 
with making the system overall more efficient (e.g. faster `listEvents` API
responses).

The second business requirement states:

```
· update data, when there are model changes, in less than 1 week
```

This requirement also involves the `Persistency Layer`, but from a flexibility 
point of view.
In fact, we must now ensure it has the ability to add or remove attributes from 
stored entities, in a reasonable amount of time.

This capability is usually provided by NoSQL databases, such as the ones 
considered before.
They typically adopt flexible schemas and adding/removing attributes is often 
performed in linear time by storing an updated version of the object that will
override the previous one.

Deleting attributes can be generally considered a safe operation, however 
adding new ones could introduce some inconsistencies.
In fact, previously-stored entities will lack newly-introduced attributes and 
SAWS will be almost certainly unable to compute the missing values for old 
events.
So, missing values must be taken into consideration application-wise.
Having the possibility to differentiate between entities, for example with a 
version attribute (v1, v2, etc.), could be of great help.

The next requirement states:

```
· both the content detail service and the report service are "slow", so they are not designed to sustain a "flood" of requests
```

It is unclear if the "reporting" and the "contentDetail" webservices have 
direct access to the `Persistency Layer` of the analytics service or not.
We will suppose a case in which all the three services share the two 
bottommost layers of the architecture:

```
 __________________________________ 
| SAWS | reporting | contentDetail | 
|______|___________|_______________|
| Caching Layer                    |
|__________________________________|
| Persistency Layer                |
|__________________________________|
```

In order to speed up the two new services we may rely on the shared cache.

We can expect content entities to be reasonably small and to fit in the cache.
A LRU policy will probably best suit our needs since it will hold the contents
most frequently accessed by users.

On the contrary, caching events can be difficult or impossible.
Is there any reason to believe that some of them will be fetched more often 
than others? Or are they usually retrieved all together to perform some 
aggregate analyses?
It could be helpful to have further details on the type of reports offered by 
the service to evaluate whether is possible to (incrementally? off-line?) 
pre-compute and cache some metrics and distribute them faster.

If there is no possibility to cache values or pre-compute metrics another 
solution to mitigate the problem could involve designing an API capable of 
returning paginated results.
This approach is common in very large systems and consists in returning 
small-size data chunks along with a cursor (index) to fetch the next piece of 
information.
By doing so, for instance, the `listEvents` will return only the latest X 
events (X=10, 25, 50, 100, etc) in a shorter time.
This could be reasonable because customers will probably be interested in 
getting reports on recent events and trends.
Only if long-term analyses are required then the entire storage needs to be 
scanned.
For this purpose it will be necessary to index events according to their 
timestamp.
As a final note, paginated results may be small enough to be entirely cached as 
well.

The last point to be considered is:

```
· content name might change unpredictaly and we need to grant all views data is consistent with the up-to-date name for the whole retention.
```

This issue about back end inconsistency is non-trivial and involves a trade-off
analysis.
It happens if the content name in the `Persistency Layer` of SAWS is 
inconsistent with a new version of the same content in the slow service 
(regardless of how the "reporting" and the "contentDetail" webservices are 
built).

If the slow webservice doesn't provide a push system to send updates to SAWS,
there will come for sure a moment in which content names in the `Persistency 
Layer` will be obsolete.

One possibility to solve the issue is to periodically pull the external service 
for updates and check if something has changed.
This can be done automatically with a cron job (e.g. every 5/10/30 minutes) 
for every entity and/or in other moments (e.g. every 1000 new logged events).
There is an obvious trade-off in this pull mechanism: the more we will 
perform calls to the slow service to keep information updated the more we will 
flood it with requests.
In addition, this approach doesn't prevent the "reporting" and "contentDetail" 
webservices accessing stale objects, since content names will be updated only 
with a periodically (more pull requests, higher probability of correct 
data).
However, this approach has the advantage to not impact in any way the 
performance of the "reporting" and "contentDetail" webservices, since SAWS 
won't have to perform additional operations while serving their requests.

On the contrary, another interesting approach is to trigger a content name 
update check if and only if someone is interested in reading (an updated 
version of) it.
In fact, storing obsolete data is not an issue as long as no one is interested 
in reading them.
In this scenario, as soon as one of the three services receives an API call 
involving a content it can query the slow service and check inconsistencies, 
update the associated entity if needed (it is unique in the model designed 
above), and then reply.
API responses will be always slower, because services will be forced to invoke 
the external slow service, but they will guarantee up-to-date and consistent 
contents.

As a final note, it is important to remember to invalidate cache whenever 
appropriate.
