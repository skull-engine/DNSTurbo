import yaml
import pprint

from skullpy import *

from skull.common import *
from skull.common.proto import *

from dnslib import *

##
# Module Init Entry, be called when start phase
#
# @param config  A parsed yamlObj
#
def module_init(config):
    logger.debug("py module init")
    logger.info('0', 'config: {}'.format(pprint.pformat(config)))
    return

##
# Module Release Function, be called when shutdown phase
#
def module_release():
    logger.debug("py module release")
    return

##
# Input data unpack function, be called if this module is the 'first' module in
#  the workflow and there is input data incoming
#
# @param txn  Transaction context which is used for getting shared transaction
#              data or invoking service `iocall`
# @param data Input data
#
# @return - > 0: How many bytes consumed
#         - = 0: Need more data
#         - < 0: Error occurred
#
def module_unpack(txn, data):
    #logger.debug("request module unpack")

    # Parse dns request
    request = DNSRecord.parse(data)
    question = str(request.q.qname)
    question_type = request.q.qtype
    request_id = request.header.id

    rawRecord = DNSRecord(DNSHeader(id=request_id, qr=1, aa=1, ra=1), q=request.q)

    #logger.debug("question: {}, type: {}, {}".format(question, question_type, QTYPE[question_type]))

    # Store data into txn sharedData
    sharedData = txn.data()
    sharedData.question = question
    sharedData.request_id = request_id
    sharedData.rawRequest = bytes(rawRecord.pack())

    # Increase counters
    mod_metrics = metrics.module()
    mod_metrics.request.inc(1)

    domain_counter = metrics.domain(question)
    domain_counter.request.inc(1)
    return len(data)

##
# Module Runnable Entry, be called when this module be picked up in current
#  workflow
#
# @param txn Transaction context
#
# @return - True if no error
#         - False if error occurred
def module_run(txn):
    return True
