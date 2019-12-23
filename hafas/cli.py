import argparse
import sqlite3
import logging
import datetime

import requests


DEFAULT_ORIGIN_EXT_ID = '900210010'  # Falkensee Bhf: bb
DEFAULT_DEST_EXT_ID = '900023201'  # Berlin Zoo

logging.basicConfig(level=logging.INFO)


def _monitor_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--access-id', dest='access_id', help='the HAFAS access id',
                        required=True)
    parser.add_argument('--base-url', dest='base_url', help='the HAFAS API base URL',
                        default='http://demo.hafas.de/openapi/vbb-proxy')
    parser.add_argument('--db', dest='db', help='the sqlite3 file', required=True)
    parser.add_argument('--duration', dest='duration', help='the duration from now in minutes',
                        default=120, type=int)
    return parser.parse_args()


class Trips(object):
    def __init__(self, access_id, base_url, origin_ext_id, dest_ext_id, rt_mode=None):
        self.base_params = {
            'accessId': access_id,
            'format': 'json',
            'originExtId': origin_ext_id,
            'destExtId': dest_ext_id,
            'rtMode': rt_mode or 'REALTIME',
        }
        self.url = '{}/trip'.format(base_url)

    def _parse_time(self, d, t):
        date_time_str = '{} {}'.format(d, t)
        date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
        return date_time_obj

    def _create_trip_page_result(self, raw_result):
        result = {
            'next_context': raw_result['scrF'],
            'trips': []
        }
        for trip in raw_result['Trip']:
            trip_id = trip['ctxRecon']
            begin = trip['LegList']['Leg'][0]['Origin']
            end = trip['LegList']['Leg'][-1]['Destination']
            start_time = self._parse_time(begin['date'], begin['time'])
            start_time_rt = start_time
            if begin.get('rtTime'):
                start_time_rt = self._parse_time(begin['rtDate'], begin['rtTime'])
            end_time = self._parse_time(end['date'], end['time'])
            end_time_rt = end_time
            if end.get('rtTime'):
                end_time_rt = self._parse_time(end['rtDate'], end['rtTime'])
            lines = [x['Product']['line'] for x in trip['LegList']['Leg'] if x['type'] != 'WALK']
            result['trips'].append({
                'id': trip_id,
                'lines': len(lines)-1,
                'changes': len(lines),
                'start': start_time,
                'start_rt': start_time_rt,
                'end': end_time,
                'end_rt': end_time_rt,
                'has_delay': (start_time_rt-start_time_rt).total_seconds() != 0,
            })

        return result

    def _query_trip_page(self, context):
        if context:
            params = {
                'context': context,
            }
            params.update(self.base_params)
        else:
            params = self.base_params

        try:
            response = requests.get(self.url, params=params)
        except requests.exceptions.RequestException as ex:
            logging.error('request error while querying trip: %s', ex)
            logging.error(ex.response)
            return None

        if response.status_code >= 400:
            logging.error('error while querying trip: %i\n%s',
                          response.status_code, response.content)
            return None

        return response.json()

    def query_trips(self, duration):
        result = {}
        start = datetime.datetime.now()
        end = start + duration
        next_context = None
        query_more = True
        while query_more:
            single_raw_result = self._query_trip_page(next_context)
            single_result = self._create_trip_page_result(single_raw_result)
            for trip in single_result['trips']:
                if trip['start'] < end:
                    result[trip['id']] = trip
            query_more = single_result['trips'][-1]['start'] < end
            next_context = single_result['next_context']

        return result


def monitor():
    args = _monitor_args()
    trips = Trips(args.access_id, args.base_url,
                  DEFAULT_ORIGIN_EXT_ID, DEFAULT_DEST_EXT_ID)
    result = trips.query_trips(datetime.timedelta(minutes=args.duration))
    conn = sqlite3.connect(args.db)
    c = conn.cursor()
    c.execute('''create table if not exists trips
                 (id text, start date, start_rt date, end date, end_rt date, has_delay integer, changes integer)''')
    for trip in result.items():
        trip = trip[1]
        c.execute('''update trips
                     set start=?, start_rt=?, end=?, end_rt=?, changes=?, has_delay=?
                     where id=?''',
                  (trip['start'], trip['start_rt'], trip['end'], trip['end_rt'], trip['changes'], trip['has_delay'], trip['id']))
        c.execute('''insert into trips (id, start, start_rt, end, end_rt, has_delay, changes)
                     select ?,?,?,?,?,?,?
                     where (select changes() = 0)''',
                  (trip['id'], trip['start'], trip['start_rt'], trip['end'], trip['end_rt'], trip['has_delay'], trip['changes']))
    conn.commit()
    conn.close()
