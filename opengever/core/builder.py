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

    def create(self, num_dossiers=0, num_files=0):
        docs_per_dossier = num_files/num_dossiers
        for counter in range(1, num_dossiers):
            dossier = create(Builder('randomdossier'))
            docs_in_dossier = random.randint(docs_per_dossier/2, docs_per_dossier*1.5)
            for doc_count in range(1, docs_in_dossier):
                create(Builder('randomdocument').within(dossier))

builder_registry.register('gever', GeverBuilder)

class RandomDossierBuilder(DossierBuilder):

    @property
    def container(self):
        return get_random_repofolder()

    def __call__(self):
        portal = getSite()
        faker = Factory.create()
        self.arguments['title'] = faker.sentence()
        self.arguments['responsible'] = get_random_user(portal)

builder_registry.register('randomdossier', RandomDossierBuilder)

class RandomDocumentBuilder(DocumentBuilder):

    def __call__(self, file_path):
        faker = Factory.create()
        self.arguments['title'] = faker.sentence()
        self.arguments['file'] = get_random_file(file_path)

builder_registry.register('randomddocument', RandomDocumentBuilder)

def get_repo_folders():
    portal = getSite()
    catalog = portal.portal_catalog
    repo_folders = catalog({'portal_type':'opengever.repository.repositoryfolder'})
    parents = set()
    all = set()
    for repo_folder in repo_folders:
        all.append(repo_folder)
        parents.append(os.path.split(repo_folder)[0])
    return all.difference(parents)

def get_random_repofolder():
    return random.choice(session.current_session.repofolders)
