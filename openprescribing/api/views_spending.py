from rest_framework.decorators import api_view
from rest_framework.response import Response
import view_utils as utils


PRESCRIBING_TABLE = '[ebmdatalab:hscic.prescribing]'
CCG_TABLE = '[ebmdatalab:hscic.eccg]'
PRACTICE_TABLE = '[ebmdatalab:hscic.epraccur]'


@api_view(['GET'])
def total_spending(request, format=None):
    codes = utils.param_to_list(request.query_params.get('code', []))
    codes = utils.get_bnf_codes_from_number_str(codes)
    query = _get_query_for_total_spending(codes)
    data = utils.run_query(query['querystr'], query['cols'])
    return Response(data)


@api_view(['GET'])
def spending_by_ccg(request, format=None):
    codes = utils.param_to_list(request.query_params.get('code', []))
    codes = utils.get_bnf_codes_from_number_str(codes)
    orgs = utils.param_to_list(request.query_params.get('org', []))
    query = _get_query_for_ccg(codes, orgs)
    data = utils.run_query(query['querystr'], query['cols'])
    return Response(data)


@api_view(['GET'])
def spending_by_practice(request, format=None):
    codes = utils.param_to_list(request.query_params.get('code', []))
    codes = utils.get_bnf_codes_from_number_str(codes)
    orgs = utils.param_to_list(request.query_params.get('org', []))

    # Don't support national queries: BigQuery complains about the size
    # the response.
    if not orgs:
        err = 'Error: You must supply a list of organisations'
        return Response(err, status=400)

    query = _get_query_for_practice(codes, orgs)
    data = utils.run_query(query['querystr'], query['cols'])
    return Response(data)


def _get_query_for_total_spending(codes):
    query = 'SELECT SUM(actual_cost) AS actual_cost, '
    query += 'SUM(items), '
    query += 'SUM(quantity), '
    query += 'DATE(month) AS date'
    query += "FROM %s " % PRESCRIBING_TABLE
    if codes:
        query += " WHERE ("
        for i, c in enumerate(codes):
            query += "bnf_code LIKE '%s%%' " % c
            if (i != len(codes) - 1):
                query += ' OR '
        query += ") "
    query += "GROUP BY date ORDER BY date"
    return {
        'querystr': query,
        'cols': ['actual_cost', 'items', 'quantity', 'date']
    }


def _get_query_for_ccg(codes, orgs):
    query = 'SELECT pr.pct, pc.name, '
    query += 'DATE(pr.month) AS month, '
    query += "SUM(pr.items), "
    query += 'SUM(pr.actual_cost), '
    query += 'SUM(pr.quantity) '
    query += "FROM %s pr " % PRESCRIBING_TABLE
    query += "JOIN %s pc ON pr.pct=pc.org_code " % CCG_TABLE
    query += "WHERE ("
    for i, c in enumerate(codes):
        query += "pr.bnf_code LIKE '%s%%' " % c
        if (i != len(codes) - 1):
            query += ' OR '
    if orgs:
        query += ") AND ("
        for i, org in enumerate(orgs):
            query += "pr.pct='%s' " % org
            if (i != len(orgs) - 1):
                query += ' OR '
    query += ") GROUP BY pr.pct, pc.name, month "
    query += "ORDER BY month, pr.pct"
    print query
    return {
        'querystr': query,
        'cols': ['row_id', 'row_name', 'date',
                 'items', 'actual_cost', 'quantity']
    }


def _get_query_for_practice(codes, orgs):
    query = 'SELECT pr.practice, '
    query += "pc.name, "
    query += "pc.prescribing_setting, "
    query += "pc.provider_purchaser, "
    query += "DATE(pr.month) AS date, "
    query += 'SUM(pr.actual_cost), '
    query += 'SUM(pr.items), '
    query += 'SUM(pr.quantity) '
    query += "FROM %s pr " % PRESCRIBING_TABLE
    query += "JOIN %s pc ON pr.practice=pc.org_code " % PRACTICE_TABLE
    query += "WHERE ("
    for i, c in enumerate(codes):
        query += "pr.bnf_code LIKE '%s%%' " % c
        if (i != len(codes) - 1):
            query += ' OR '
    if orgs:
        query += ") AND ("
        for i, c in enumerate(orgs):
            if len(c) == 3:
                query += "pr.pct='%s' " % c
                if (i != len(orgs) - 1):
                    query += ' OR '
            else:
                query += "pr.practice='%s' " % c
                if (i != len(orgs) - 1):
                    query += ' OR '
    query += ") GROUP BY pr.practice, pc.name, pc.prescribing_setting, "
    query += "pc.provider_purchaser, date "
    query += "ORDER BY date, pr.practice"
    print query
    return {
        'querystr': query,
        'cols': ['row_id', 'row_name', 'setting', 'ccg', 'date',
                 'actual_cost', 'items', 'quantity']
    }
