import yaml
import pprint
import time

from skullpy import *
from skullpy.txn import *

from skull.common import *
from skull.common.proto import *

import ranking

CFG_MIN_TTL = 0
CFG_MAX_TTL = 0

##
# Module Init Entry, be called when start phase
#
# @param config  A parsed yamlObj
#
def module_init(config):
    logger.debug("py module init")
    logger.info('ModuleInit', 'config: {}'.format(pprint.pformat(config)))

    global CFG_MIN_TTL
    global CFG_MAX_TTL
    CFG_MIN_TTL = config['min_ttl']
    CFG_MAX_TTL = config['max_ttl']
    return

##
# Module Release Function, be called when shutdown phase
#
def module_release():
    logger.debug("py module release")
    return

##
# Module Runnable Entry, be called when this module be picked up in current
#  workflow
#
# @param txn Transaction context
#
# @return - True if no error
#         - False if error occurred
def module_run(txn):
    sharedData = txn.data()
    question = sharedData.question

    rank_query = service_ranking_rank_req_pto.rank_req()
    rank_query.question = question
    rank_query.qtype = 1

    for record in sharedData.record:
        rank_query.rRecord.add(ip = record.ip, expiredTime = int(time.time()) + record.ttl)

    ret = txn.iocall('ranking', 'rank', rank_query, api_cb=_ranking_response)
    if ret == Txn.IO_OK:
        return True
    else:
        logger.error("Ranking_E1", "Ranking iocall failed, ret: {}".format(ret))
        return False

def _ranking_response(txn, iostatus, api_name, request_msg, response_msg):
    if iostatus != Txn.IO_OK:
        logger.error("Ranking_E2", "Ranking response IO error: {}".format(iostatus))
        return False

    #print "response: {}".format(response_msg)
    sharedData = txn.data()

    # If the total records count <= 1, just store and return
    nrecords = len(response_msg.result)
    if nrecords <= 1:
        for record in response_msg.result:
            sharedData.rankingRecord.add(ip = record.ip, ttl = record.ttl)
        return True

    # Do the score and rank
    scoringResults = ranking.score(response_msg.result)
    rankingResults = ranking.rank(scoringResults)

    global CFG_MIN_TTL
    for record in rankingResults:
        # Recalculate ttl when there is no scoring information and ttl > CFG_MIN_TTL
        ttl = record['ttl']
        latency = record['avgLatency']

        if latency == 0 and ttl > CFG_MIN_TTL:
            ttl = CFG_MIN_TTL
        elif ttl > CFG_MAX_TTL:
            ttl = CFG_MAX_TTL

        sharedData.rankingRecord.add(ip = record['ip'], ttl = ttl)

    return True

