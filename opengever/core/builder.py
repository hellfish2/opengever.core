from faker import Factory
from ftw.builder import Builder
from ftw.builder import builder_registry
from ftw.builder import create
from ftw.builder import session
from ftw.builder.builder import PloneObjectBuilder
from opengever.core.file import get_random_file
from opengever.core.user import get_random_user
from opengever.testing.builders import DocumentBuilder
from opengever.testing.builders import DossierBuilder
from zope.component.hooks import getSite
import os
import random


class GeverBuilder(PloneObjectBuilder):

    def create(self, **kwargs):
        num_dossiers = self.arguments['num_dossiers']
        for counter in range(0, num_dossiers):
            dossier = create(Builder('randomdossier'))
            print "created Dossier %i out of %i" % (counter + 1, num_dossiers)
            docs_in_dossier = self.session.get_docs_in_dossier(counter)
            for doc_count in range(0, docs_in_dossier):
                create(Builder('randomdocument').within(dossier))
                print "created file %i out of %i" % (doc_count + 1,
                                                     docs_in_dossier
                                                     )
            print "filled Dossier %i out of %i" % (counter + 1, num_dossiers)

builder_registry.register('gever', GeverBuilder)


class RandomDossierBuilder(DossierBuilder):

    def create(self, **kwargs):
        portal = getSite()
        faker = Factory.create()
        self.container = portal.restrictedTraverse(get_random_repofolder())
        self.arguments['title'] = faker.sentence().decode('utf-8')
        self.arguments['responsible'] = get_random_user(portal)
        return super(RandomDossierBuilder, self).create(**kwargs)

builder_registry.register('randomdossier', RandomDossierBuilder)


class RandomDocumentBuilder(DocumentBuilder):

    def create(self, **kwargs):
        self.arguments['file'] = get_random_file(
            session.current_session.file_path
            )
        return super(RandomDocumentBuilder, self).create(**kwargs)

builder_registry.register('randomdocument', RandomDocumentBuilder)


def get_repo_folders():
    portal = getSite()
    catalog = portal.portal_catalog
    repo_folders = catalog.search(
        {'portal_type': 'opengever.repository.repositoryfolder'}
        )
    parents = []
    all = []
    for repo_folder in repo_folders:
        all.append(repo_folder.getPath())
        parents.append(os.path.split(repo_folder.getPath())[0])
    return set(all).difference(set(parents))


def get_random_repofolder():
    return random.choice(session.current_session.repofolders)

def get_docs_in_dossier(index):
    return session.current_session.files_in_folders['index']

def initalize_file_list(dossiers, files):
    dossierslist = []
    files_overall = 0
    average = files/dossiers
    min = average / 2
    max = average * 1.5
    for counter in range(0, dossiers):
        files_in_dossier = random.randint(min, max)
        if files_overall + files_in_dossier > files:
            files_in_dossier = files - files_overall
        files_overall += files_in_dossier
        dossierslist.append[files_in_dossier]
    if files_overall < files:
        index = random.randint(0, dossiers)
        dossierslist[index] += files - files_overall
    return dossierslist
