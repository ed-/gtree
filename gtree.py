#!/usr/bin/env python

import json
import operator
import urllib2

def fetch_json_data(url):
    try:
        U = urllib2.urlopen(url)
        data = [line.rstrip() for line in U.readlines()][1:]
        return json.loads('\n'.join(data))
    except urllib2.HTTPError:
        return {}

def fetch_open_reviews(base_url, project):
    url = "%s/changes/?q=status:open+%%s" % base_url
    return fetch_json_data(url % project)

def fetch_merged_reviews(base_url, project):
    url = "%s/changes/?q=status:merged+%%s" % base_url
    return fetch_json_data(url % project)


class Review(object):
    owner = None
    subject = None
    parent_subject = None
    children = None
    number = None
    baseurl = None

    def __init__(self, review_dict, base_url):
        self.owner = review_dict['owner']['name']
        self.subject = review_dict['subject']
        self.baseurl = base_url
        self.number = review_dict['_number']

        review_id = review_dict['id']
        url = "%s/changes/%%s/detail?o=current_revision&o=current_commit" % base_url
        details = fetch_json_data(url % review_id)

        current_revision = details.get('current_revision')
        current_revision = details.get('revisions', {}).get(current_revision)
        parents = current_revision.get('commit', {}).get('parents', [])
        if parents:
            self.parent_subject = parents[0]['subject']

        self.children = []

    def __str__(self):
        return "%s (%s) - %s" % (self.subject, self.owner, self.url)

    def __repr__(self):
        return str(self)

    def tree(self, prefix=''):
        headline = '%s%s' % (prefix, str(self))
        if not self.children:
            newline = '\n' if prefix else ''
            return '%s%s' % (headline, newline)
        childlines = '\n'.join([c.tree(prefix + '  ') for c in self.children])
        return '%s\n%s' % (headline, childlines)

    @property
    def depth(self):
        if not self.children:
            return 0
        return 1 + max([c.depth for c in self.children])

    @property
    def url(self):
        return "%s/#/c/%s/" % (self.baseurl, self.number)

def show_review_tree(baseurl, project):
    reviews = [Review(r, baseurl)
               for r in fetch_open_reviews(baseurl, project)]
    subjects = [r.subject for r in reviews]
    children = [r for r in reviews if r.parent_subject in subjects]
    children.sort(key=operator.attrgetter('depth'))
    while children:
        child = children[0]
        try:
            reviews.remove(child)
        except ValueError:
            children.remove(child)
            continue
        if child.subject.startswith('Updated from global requirements'):
            continue
        parents = [r for r in reviews if r.subject == child.parent_subject]
        parent = parents[0]
        parent.children.append(child)

        subjects = [r.subject for r in reviews]
        children = [r for r in reviews if r.parent_subject in subjects]
        children.sort(key=operator.attrgetter('depth'))
    reviews = sorted(reviews, key=operator.attrgetter('depth'), reverse=True)
    for r in reviews:
        print r.tree()

def show_merge_stats(baseurl, project):
    reviews = [Review(r, baseurl)
               for r in fetch_merged_reviews(baseurl, project)]
    owners = {}
    for r in reviews:
        owner = r.owner
        owners[owner] = owners.get(owner, 0) + 1

    print "Total merged: %i reviews" % len(reviews)
    print
    for o in sorted(owners):
        print "%-30s: %3i" % (o, owners[o])


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--project', default='solum')
    ap.add_argument('--baseurl', default='https://review.openstack.org')
    ap.add_argument('--merged', action='store_true')
    parsed = ap.parse_args()

    if parsed.merged:
        show_merge_stats(parsed.baseurl, parsed.project)
    else:
        show_review_tree(parsed.baseurl, parsed.project)
