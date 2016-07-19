from rest_framework.decorators import api_view
from rest_framework.response import Response
import view_utils as utils


@api_view(['GET'])
def total_spending(request, format=None):
    codes = utils.param_to_list(request.query_params.get('code', []))
    codes = utils.get_bnf_codes_from_number_str(codes)
    subdivide = request.GET.get('subdivide', None)

    if subdivide:
        if codes:
            if len(codes) > 1:
                err = 'Error: You can only subdivide a single code'
                return Response(err, status=400)
            elif len(codes[0]) > 11:
                err = 'Error: Code to subdivide must be 11 characters or fewer'
                return Response(err, status=400)

    spending_type = utils.get_spending_type(codes)
    if spending_type is False:
        err = 'Error: Codes must all be the same length'
        return Response(err, status=400)

    if subdivide:
        query = _get_query_for_total_spending_with_subdivide(codes)
    else:
        query = _get_query_for_total_spending(codes)

    if spending_type != 'presentation':
        codes = [c + '%' for c in codes]

    data = utils.execute_query(query, [codes])
    return Response(data)


@api_view(['GET'])
def spending_by_ccg(request, format=None):
    codes = utils.param_to_list(request.query_params.get('code', []))
    codes = utils.get_bnf_codes_from_number_str(codes)
    orgs = utils.param_to_list(request.query_params.get('org', []))

    spending_type = utils.get_spending_type(codes)
    if spending_type is False:
        err = 'Error: Codes must all be the same length'
        return Response(err, status=400)

    if not spending_type or spending_type == 'bnf-section' \
       or spending_type == 'chemical':
        query = _get_query_for_chemicals_or_sections_by_ccg(codes, orgs,
                                                            spending_type)
    else:
        query = _get_query_for_presentations_by_ccg(codes, orgs)

    if spending_type == 'bnf-section' or spending_type == 'product':
        codes = [c + '%' for c in codes]

    data = utils.execute_query(query, [codes, orgs])
    return Response(data)


@api_view(['GET'])
def spending_by_practice(request, format=None):
    codes = utils.param_to_list(request.query_params.get('code', []))
    codes = utils.get_bnf_codes_from_number_str(codes)
    orgs = utils.param_to_list(request.query_params.get('org', []))
    date = request.query_params.get('date', None)

    spending_type = utils.get_spending_type(codes)
    if spending_type is False:
        err = 'Error: Codes must all be the same length'
        return Response(err, status=400)
    if spending_type == 'bnf-section' or spending_type == 'product':
        codes = [c + '%' for c in codes]

    if not date and not orgs:
        err = 'Error: You must supply either '
        err += 'a list of practice IDs or a date parameter, e.g. '
        err += 'date=2015-04-01'
        return Response(err, status=400)

    org_for_param = None
    if not spending_type or spending_type == 'bnf-section' \
       or spending_type == 'chemical':
        # We can do presentation queries indexed by PCT ID, which is faster.
        # We have yet to update the *_by_practice matviews with PCT ID.
        # So for these queries, expand the CCG ID to a list of practice IDs.
        expanded_orgs = utils.get_practice_ids_from_org(orgs)
        if codes:
            query = _get_chemicals_or_sections_by_practice(codes,
                                                           expanded_orgs,
                                                           spending_type,
                                                           date)
            org_for_param = expanded_orgs
        else:
            query = _get_total_spending_by_practice(expanded_orgs, date)
            org_for_param = expanded_orgs
    else:
        query = _get_presentations_by_practice(codes, orgs, date)
        org_for_param = orgs
    data = utils.execute_query(
        query, [codes, org_for_param, [date] if date else []])
    return Response(data)


def _wrap_query_with_dates(query, headers=[], order_by=[]):
    """Wrap a query with an outer query that adds dates for all dates for
    which we have prescribing data.

    This makes charts consistent, because they always span the entire
    range of possible dates, regardless of if the query selects (for
    example) chemicals with very sparse prescribing data.
    """
    defaults = {'actual_cost': 0,
                'items': 0,
                'quantity': 0,
                'code': "''",
                'bnf_code': "''",
                'name': "''",
                'row_id': "'n/a'",
                'row_name': "'n/a'",
                'ccg': "'n/a'",
                'setting': 0}
    prologue = 'SELECT DISTINCT log.current_at AS date'
    for header in headers:
        prologue += ", COALESCE(%s, %s) as %s " % (header, defaults[header], header)
    prologue += 'FROM frontend_importlog log LEFT JOIN ('

    epilogue = (") AS values ON values.date = log.current_at "
                "WHERE log.category = 'prescribing' ORDER BY log.current_at")
    for col in order_by:
        epilogue += ", %s" % col
    return "%s %s %s" % (prologue, query, epilogue)


def _get_query_for_total_spending(codes):
    query = 'SELECT SUM(cost) AS actual_cost, '
    query += 'SUM(items) AS items, '
    query += 'SUM(quantity) AS quantity, '
    query += 'processing_date AS date '
    query += "FROM vw__presentation_summary "
    if codes:
        query += " WHERE ("
        for i, c in enumerate(codes):
            query += "presentation_code LIKE %s "
            if (i != len(codes) - 1):
                query += ' OR '
        query += ") "
    query += "GROUP BY date"
    return _wrap_query_with_dates(
        query,
        headers=['actual_cost', 'items', 'quantity'])


def _get_query_for_total_spending_with_subdivide(codes):
    '''
    TODO: Deal with the case where there are no subsections,
    e.g. section 2.12. In this case we should jump straight to
    chemical level.
    '''
    code = codes[0] if len(codes) else None
    end_char = 0
    if not code:
        end_char = 2
    elif len(code) == 2 or len(code) == 4 or len(code) == 9:
        end_char = len(code) + 2
    elif len(code) == 6:
        end_char = 9
    elif len(code) == 11:
        end_char = 15

    query = ('SELECT SUM(cost) AS actual_cost, SUM(items) AS items, '
             'SUM(quantity) AS quantity, '
             'SUBSTR(vwps.presentation_code, 1, %s) AS code, '
             'frontend_section.number_str AS bnf_code, '
             'processing_date AS date, '
             'frontend_section.name AS name '
             'FROM vw__presentation_summary vwps '
             'LEFT JOIN frontend_section ON '
             'frontend_section.bnf_id'
             '=SUBSTR(vwps.presentation_code, 1, %s) ' % (end_char, end_char))
    if code:
        query += 'WHERE vwps.presentation_code LIKE %s '
        code += '%'
    query += 'GROUP BY code, name, number_str, date '
    return _wrap_query_with_dates(
        query,
        headers=['actual_cost', 'items', 'quantity', 'code',
                 'bnf_code', 'name'],
        order_by=['code'])


def _get_query_for_chemicals_or_sections_by_ccg(codes, orgs, spending_type):

    query = ('SELECT pr.pct_id as row_id, '
             "pc.name as row_name, "
             'pr.processing_date as date, '
             'SUM(pr.cost) AS actual_cost, '
             'SUM(pr.items) AS items, '
             'SUM(pr.quantity) AS quantity '
             "FROM vw__chemical_summary_by_ccg pr "
             "JOIN frontend_pct pc ON pr.pct_id=pc.code "
             "AND pc.org_type='CCG' ")
    if spending_type:
        query += " WHERE ("
        if spending_type == 'bnf-section':
            for i, c in enumerate(codes):
                query += "pr.chemical_id LIKE %s "
                if (i != len(codes) - 1):
                    query += ' OR '
            codes = [c + '%' for c in codes]
        else:
            for i, c in enumerate(codes):
                query += "pr.chemical_id=%s "
                if (i != len(codes) - 1):
                    query += ' OR '
        query += ") "
    if orgs:
        query += "AND ("
        for i, org in enumerate(orgs):
            query += "pr.pct_id=%s "
            if (i != len(orgs) - 1):
                query += ' OR '
        query += ") "
    query += "GROUP BY pr.pct_id, pc.code, date"
    return _wrap_query_with_dates(
        query, headers=['row_id', 'row_name', 'actual_cost',
                        'items', 'quantity'], order_by=['row_id'])


def _get_query_for_presentations_by_ccg(codes, orgs):
    query = ('SELECT pr.pct_id as row_id, '
             "pc.name as row_name, "
             'pr.processing_date as date, '
             "SUM(pr.items) AS items, "
             'SUM(pr.cost) AS actual_cost, '
             'SUM(pr.quantity) AS quantity '
             "FROM vw__presentation_summary_by_ccg pr "
             "JOIN frontend_pct pc ON pr.pct_id=pc.code "
             "AND pc.org_type='CCG' "
             " WHERE (")
    for i, c in enumerate(codes):
        query += "pr.presentation_code LIKE %s "
        if (i != len(codes) - 1):
            query += ' OR '
    if orgs:
        query += ") AND ("
        for i, org in enumerate(orgs):
            query += "pr.pct_id=%s "
            if (i != len(orgs) - 1):
                query += ' OR '
    query += ') GROUP BY pr.pct_id, pc.code, date'
    return _wrap_query_with_dates(
        query, headers=['row_id', 'row_name', 'actual_cost',
                        'items', 'quantity'], order_by=['row_id'])


def _get_total_spending_by_practice(orgs, date):
    query = ('SELECT pr.practice_id AS row_id, '
             "pc.name AS row_name, "
             "pc.setting AS setting, "
             "pc.ccg_id AS ccg, "
             'pr.processing_date AS date, '
             'pr.cost AS actual_cost, '
             'pr.items AS items, '
             'pr.quantity AS quantity '
             "FROM vw__practice_summary pr "
             "JOIN frontend_practice pc ON pr.practice_id=pc.code ")
    if orgs or date:
        query += "WHERE "
    if date:
        query += "pr.processing_date=%s "
    if orgs:
        if date:
            query += "AND "
        query += "("
        for i, org in enumerate(orgs):
            query += "pr.practice_id=%s "
            # if len(org) == 3:
            #     query += "pr.pct_id=%s "
            # else:
            #     query += "pr.practice_id=%s "
            if (i != len(orgs) - 1):
                query += ' OR '
        query += ")"
    return _wrap_query_with_dates(
        query, headers=['row_id', 'row_name', 'actual_cost', 'ccg', 'setting',
                        'items', 'quantity'], order_by=['row_id'])


def _get_chemicals_or_sections_by_practice(codes, orgs, spending_type,
                                           date):
    query = ('SELECT pr.practice_id AS row_id, '
             "pc.name AS row_name, "
             "pc.setting AS setting, "
             "pc.ccg_id AS ccg, "
             "pr.processing_date AS date, "
             'SUM(pr.cost) AS actual_cost, '
             'SUM(pr.items) AS items, '
             'SUM(pr.quantity) AS quantity '
             "FROM vw__chemical_summary_by_practice pr "
             "JOIN frontend_practice pc ON pr.practice_id=pc.code ")
    has_preceding = False
    if spending_type:
        has_preceding = True
        query += " WHERE ("
        if spending_type == 'bnf-section':
            for i, c in enumerate(codes):
                query += "pr.chemical_id LIKE %s "
                if (i != len(codes) - 1):
                    query += ' OR '
            codes = [c + '%' for c in codes]
        else:
            for i, c in enumerate(codes):
                query += "pr.chemical_id=%s "
                if (i != len(codes) - 1):
                    query += ' OR '
        query += ") "
    if orgs:
        if has_preceding:
            query += " AND ("
        else:
            query += " WHERE ("
        for i, org in enumerate(orgs):
            query += "pr.practice_id=%s "
            # if len(org) == 3:
            #     query += "pr.pct_id=%s "
            # else:
            #     query += "pr.practice_id=%s "
            if (i != len(orgs) - 1):
                query += ' OR '
        query += ") "
        has_preceding = True
    if date:
        if has_preceding:
            query += " AND ("
        else:
            query += " WHERE ("
        query += "pr.processing_date=%s) "
    query += "GROUP BY pr.practice_id, pc.code, date"
    return _wrap_query_with_dates(
        query, headers=['row_id', 'row_name', 'actual_cost',  'setting', 'ccg',
                        'items', 'quantity'], order_by=['row_id'])


def _get_presentations_by_practice(codes, orgs, date):
    query = ('SELECT pr.practice_id AS row_id, '
             "pc.name AS row_name, "
             "pc.setting AS setting, "
             "pc.ccg_id AS ccg, "
             "pr.processing_date AS date, "
             'SUM(pr.actual_cost) AS actual_cost, '
             'SUM(pr.total_items) AS items, '
             'CAST(SUM(pr.quantity) AS bigint) AS quantity '
             "FROM frontend_prescription pr "
             "JOIN frontend_practice pc ON pr.practice_id=pc.code "
             "WHERE (")
    for i, c in enumerate(codes):
        query += "pr.presentation_code LIKE %s "
        if (i != len(codes) - 1):
            query += ' OR '
    if orgs:
        query += ") AND ("
        for i, c in enumerate(orgs):
            if len(c) == 3:
                query += "pr.pct_id=%s "
            else:
                query += "pr.practice_id=%s "
            if (i != len(orgs) - 1):
                query += ' OR '
    if date:
        query += "AND pr.processing_date=%s "
    query += ") GROUP BY pr.practice_id, pc.code, date"
    return _wrap_query_with_dates(
        query, headers=['row_id', 'row_name', 'actual_cost', 'ccg', 'setting',
                        'items', 'quantity'], order_by=['row_id'])
