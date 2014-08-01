import os,sys
import json
import time
import logging
import logging.handlers
#import hashlib

from lib import xmltodict
from lib import collections
from EnforceSchema import ensureList

try:
  import cPickle as pickle
except ImportError:
  import pickle
try:
  from ads.ADSExports import ADSRecords
except ImportError:
  sys.path.append('/proj/ads/soft/python/lib/site-packages')
  try:
    from ads.ADSExports import ADSRecords
  except ImportError:
    print "Unable to import ads.ADSExports.ADSRecords!"
    print "We will be unable to query ADS-classic for records!"

logfmt = '%(levelname)s\t%(process)d [%(asctime)s]:\t%(message)s'
datefmt= '%m/%d/%Y %H:%M:%S'
formatter = logging.Formatter(fmt=logfmt,datefmt=datefmt)
logger = logging.getLogger(__file__)
fn = os.path.join(os.path.dirname(__file__),'..','logs','ReadRecords.log')
rfh = logging.handlers.RotatingFileHandler(filename=fn,maxBytes=2097152,backupCount=3,mode='a') #2MB file
rfh.setFormatter(formatter)
ch = logging.StreamHandler() #console handler
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.addHandler(rfh)
logger.setLevel(logging.DEBUG)

def readRecordsFromADSExports(records):
  '''
  records: [(bibcode,JSON_fingerprint),...]
  '''
  #h = hashlib.sha1(json.dumps(records)).hexdigest()
  if not records:
    return []

  targets = dict(records)


  s = time.time()
  records = ADSRecords('full','XML')
  failures = []
  for bibcode in targets.keys():
    try:
      records.addCompleteRecord(bibcode)
    except KeyboardInterrupt:
      raise
    except:
      failures.append(bibcode)
  records = records.export()
  if not records.content:
    logger.warning('readRecordsFromADSExports: Recieved %s records, but ADSExports didn\'t return anything!' % len(records))
    return []
  ttc = time.time()-s
  rate = len(targets)/ttc

  records = ensureList(xmltodict.parse(records.__str__())['records']['record'])
  assert(len(records)==len(targets)-len(failures))
  logger.info("readRecordsFromADSExports: Read %(num_records)s records in %(duration)0.1f seconds (%(rate)0.1f rec/sec)" % 
    {
      'num_records': len(records),
      'duration': ttc,
      'rate': rate,
    })
  if failures:
    logger.warning("readRecordsFromADSExports: ADSExports failed to retrieve %s/%s records" % (len(failures),len(records)))

  for r in records:
    r['JSON_fingerprint'] = targets[r['@bibcode']]

  # import uuid
  # with open('%s.pickle' % uuid.uuid4(),'w') as fp:
  #   pickle.dump(records,fp)
  return records

def readRecordsFromPickles(records,files):
  '''
  records: [(bibcode,JSON_fingerprint),...]
  '''
  if not records:
    return []
  targets = dict(records)
  records = []

  for file_ in files:
    with open(file_) as fp:
      recs = pickle.load(fp)

  records.extend( [r for r in recs if r['@bibcode'] in targets] )

  for r in records:
    r['JSON_fingerprint'] = targets[r['@bibcode']]
  logger.info('readRecordsFromPickles: Read %s records from %s files' % (len(records),len(files)))
  return records