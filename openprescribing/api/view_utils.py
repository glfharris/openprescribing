import itertools
from django.db import connection
from django.shortcuts import get_object_or_404
from frontend.models import Practice, Section
from oauth2client.client import GoogleCredentials
from googleapiclient.discovery import build


def param_to_list(str):
    params = []
    if str:
        params = str.split(',')
        params = filter(None, params)
    return params


def convert_data(rows, cols):
    data = []
    for row in rows:
        d = {}
        for i, c in enumerate(cols):
            d[c] = row['f'][i]['v']
        data.append(d)
    return data


def run_query(query, cols):
    PROJECT_ID = 620265099307
    credentials = GoogleCredentials.get_application_default()
    bigquery_service = build('bigquery', 'v2', credentials=credentials)
    query_request = bigquery_service.jobs()
    query_data = {
        'query': query
    }
    query_response = query_request.query(
        projectId=PROJECT_ID,
        body=query_data).execute()
    print query_response
    data = convert_data(query_response['rows'], cols)
    return data


def get_bnf_codes_from_number_str(codes):
    # Convert BNF strings (3.4, 3) to BNF codes (0304, 03).
    converted = []
    for code in codes:
        if '.' in code:
            section = get_object_or_404(Section, number_str=code)
            converted.append(section.bnf_id)
        elif len(code) < 3:
            section = get_object_or_404(
                Section, bnf_chapter=code, bnf_section=None)
            converted.append(section.bnf_id)
        else:
            # it's a presentation, not a section
            converted.append(code)
    return converted
