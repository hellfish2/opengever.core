from opengever.testing.builders import DossierBuilder
from opengever.testing.builders import DocumentBuilder
from faker import Factory
from opengever.core.user import get_random_user
from opengever.core.file import get_random_file
from zope.component.hooks import getSite
from ftw.builder import builder_registry
import random
from ftw.builder import create
from ftw.builder import Builder
import os
from ftw.builder import session
from ftw.builder.builder import PloneObjectBuilder

class GeverBuilder(PloneObjectBuilder):

    def create(self, **kwargs):
        num_dossiers = self.arguments['num_dossiers']
        num_files = self.arguments['num_files']
        docs_per_dossier = num_files/num_dossiers
        for counter in range(0, num_dossiers):
            dossier = create(Builder('randomdossier'))
            print "created Dossier %i out of %i" % (counter +1, num_dossiers)

            docs_in_dossier = random.randint(docs_per_dossier/2, docs_per_dossier*1.5)
            for doc_count in range(0, docs_in_dossier):
                create(Builder('randomdocument').within(dossier))
                print "created file %i out of %i" % (doc_count +1, docs_in_dossier)
            print "filled Dossier %i out of %i" % (counter +1, num_dossiers)

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
        self.arguments['file'] = get_random_file(session.current_session.file_path)
        return super(RandomDocumentBuilder, self).create(**kwargs)

builder_registry.register('randomdocument', RandomDocumentBuilder)

def get_repo_folders():
    portal = getSite()
    catalog = portal.portal_catalog
    repo_folders = catalog.search({'portal_type':'opengever.repository.repositoryfolder'})
    parents = []
    all = []
    for repo_folder in repo_folders:
        all.append(repo_folder.getPath())
        parents.append(os.path.split(repo_folder.getPath())[0])
    return set(all).difference(set(parents))

def get_random_repofolder():
    return random.choice(session.current_session.repofolders)
