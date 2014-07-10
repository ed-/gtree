#!/usr/bin/env python

import json
import operator
import urllib2

BASE_URL = "https://review.openstack.org"

def fetch_json_data(url):
    try:
        U = urllib2.urlopen(url)
        data = [line.rstrip() for line in U.readlines()][1:]
        return json.loads('\n'.join(data))
    except urllib2.HTTPError:
        return {}

def fetch_open_reviews():
    URL = "%s/changes/?q=status:open+solum" % BASE_URL
    return fetch_json_data(URL)


class Review(object):
    owner = None
    subject = None
    parent_subject = None
    children = None

    def __init__(self, review_dict):
        self.owner = review_dict['owner']['name']
        self.subject = review_dict['subject']

        review_id = review_dict['id']
        URL = "%s/changes/%%s/detail?o=current_revision&o=current_commit" % BASE_URL
        details = fetch_json_data(URL % review_id)

        current_revision = details.get('current_revision')
        current_revision = details.get('revisions', {}).get(current_revision)
        parents = current_revision.get('commit', {}).get('parents', [])
        if parents:
            self.parent_subject = parents[0]['subject']

        self.children = []

    def __str__(self):
        return "%s (%s)" % (self.subject, self.owner)

    def __repr__(self):
        return str(self)

    def tree(self, prefix=''):
        headline = '%s%s' % (prefix, str(self))
        if not self.children:
            return headline
        childlines = '\n'.join([c.tree(prefix + '  ') for c in self.children])
        return '%s\n%s' % (headline, childlines)

    @property
    def depth(self):
        if not self.children:
            return 0
        return 1 + max([c.depth for c in self.children])

def show_review_tree():
    reviews = [Review(r) for r in fetch_open_reviews()]
    subjects = [r.subject for r in reviews]
    children = [r for r in reviews if r.parent_subject in subjects]
    children.sort(key=operator.attrgetter('depth'))
    while children:
        child = children[0]
        reviews.remove(child)
        parent = [r for r in reviews if r.subject == child.parent_subject][0]
        parent.children.append(child)

        subjects = [r.subject for r in reviews]
        children = [r for r in reviews if r.parent_subject in subjects]
        children.sort(key=operator.attrgetter('depth'))
    reviews = sorted(reviews, key=operator.attrgetter('depth'), reverse=True)
    for r in reviews:
        print r.tree()

if __name__ == '__main__':
    show_review_tree()
