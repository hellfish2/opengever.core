from Testing.makerequest import makerequest
from ftw.builder import Builder
from ftw.builder import create
from ftw.builder import session
from opengever.core.builder import get_repo_folders
from opengever.core.builder import initalize_file_list
from optparse import OptionParser
from zope.app.component.hooks import setSite
import time
from opengever.core.builder import get_docs_in_dossier

def run_import(app, options):

    # setup request and get plone site
    app = makerequest(app)
    plone = app.unrestrictedTraverse(options.site)

    #setup site
    setSite(plone)
    session.current_session = session.factory()
    session.current_session.file_path = options.file_path
    session.current_session.repofolders = list(get_repo_folders())
    session.current_session.files_in_folders = initalize_file_list(int(options.dossiers), int(options.files))
    session.current_session.get_docs_in_dossier = get_docs_in_dossier
    start = time.time()
    print "Starting import:\n ------------------"
    create(Builder('gever').having(**{'num_dossiers': int(options.dossiers), 'num_files': int(options.files)}))
    elapsed = time.time() - start
    print "Done in %.0f seconds" % elapsed
    # Patch the inital version from opengever document


def main():

    # check if we have a zope environment aka 'app'
    mod = __import__(__name__)
    if not ('app' in dir(mod) or 'app' in globals()):
        print "Must be run with 'zopectl run'."
        return

    parser = OptionParser()
    parser.add_option("-d", "--dossiers", dest="dossiers",
                      )
    parser.add_option("-f", "--files", dest="files")
    parser.add_option("-p", "--path", dest="file_path", default=u'files')
    parser.add_option("-s", "--site", dest="site", default=u'/Plone')
    (options, args) = parser.parse_args()

    run_import(app, options)


if __name__ == '__main__':
    main()
