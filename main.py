#!/usr/bin/env python

import json
import urllib2

def fetch_json_data(url):
    try:
        U = urllib2.urlopen(url)
        data = [line.rstrip() for line in U.readlines()][1:]
        return json.loads('\n'.join(data))
    except urllib2.HTTPError:
        return {}

def fetch_open_reviews():
    URL = "https://review.openstack.org/changes/?q=status:open+solum"
    return fetch_json_data(URL)

def fetch_review_detail(review):
    review_id = review.get('id')
    URL = "https://review.openstack.org/changes/%s/detail?o=current_revision&o=current_commit"
    return fetch_json_data(URL % review_id)

def get_parent_commit(review):
    detail = fetch_review_detail(review)
    current_revision = detail.get('current_revision')
    current_revision = detail.get('revisions', {}).get(current_revision)
    parents = current_revision.get('commit', {}).get('parents', [])
    if not parents:
        return None
    return parents[0]['subject']

def get_heritage(reviews):
    subjects = set([r.get('subject') for r in reviews])

    heritage = []
    for review in reviews:
        subject = review.get('subject')
        parent = get_parent_commit(review)
        if parent not in subjects:
            parent = None
        heritage.append((parent, subject))
    return heritage

def build_tree(heritage, head=None):
    tree = {}
    children = [c for (p, c) in heritage if p == head]
    for child in children:
        tree[child] = build_tree(heritage, head=child)
    return tree

def print_tree(tree, prefix=''):
    for commit, children in tree.items():
        print "%s%s" % (prefix, commit)
        if children:
            print_tree(children, prefix + '  ')

if __name__ == '__main__':
    print_tree(build_tree(get_heritage(fetch_open_reviews())))
