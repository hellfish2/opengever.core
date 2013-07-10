from optparse import OptionParser
from Testing.makerequest import makerequest
from zope.app.component.hooks import setSite
from ftw.builder import session
from opengever.core.builder import get_repo_folders
from ftw.builder import create
from ftw.builder import Builder
import transaction
import time


def run_import(app, options):

    # setup request and get plone site
    app = makerequest(app)
    plone = app.unrestrictedTraverse(options.site)

    #setup site
    setSite(plone)
    session.current_session = session.factory()
    session.current_session.file_path = options.file_path
    session.current_session.repofolders = list(get_repo_folders())
    start = time.time()
    print "Starting import:\n ------------------"
    create(Builder('gever').having(**{'num_dossiers': int(options.dossiers), 'num_files': int(options.files)}))
    print "commiting Transaction"
    transaction.commit()
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
